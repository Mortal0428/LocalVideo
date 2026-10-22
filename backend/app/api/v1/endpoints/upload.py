import os
import uuid
import json
import shutil
import asyncio
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.video import Video, VideoEpisode
from app.models.user import User
from app.api.deps import get_current_user
from app.services.transcode_service import transcode_service

router = APIRouter()

TEMP_CHUNKS_DIR = os.path.join(settings.UPLOAD_DIR, "temp_chunks")
os.makedirs(TEMP_CHUNKS_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

class UploadInitRequest(BaseModel):
    video_id: Optional[str] = None
    title: str
    episode_num: int = 1
    filename: str
    total_chunks: int
    file_size: int
    file_md5: Optional[str] = None

class UploadCompleteRequest(BaseModel):
    upload_id: str
    episode_id: str
    total_chunks: int

@router.post("/init")
def init_upload(req: UploadInitRequest, db: Session = Depends(get_db)):
    """Initialize a chunked upload session and create an episode record."""
    # Ensure a valid parent video exists or create a default container
    video_id = req.video_id
    if not video_id:
        default_user = db.query(User).first()
        if not default_user:
            default_user = User(username="system_creator", password_hash="disabled", role="CREATOR")
            db.add(default_user)
            db.commit()
            db.refresh(default_user)
        
        default_video = Video(
            title=f"自制合集 - {req.title}",
            summary="通过分片断点续传由系统自动生成的短剧合集",
            creator_id=default_user.id,
            status="PUBLISHED"
        )
        db.add(default_video)
        db.commit()
        db.refresh(default_video)
        video_id = default_video.id
    else:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Parent video not found")

    # Create new episode with QUEUED status
    episode = VideoEpisode(
        video_id=video_id,
        episode_num=req.episode_num,
        title=req.title,
        raw_file_path="upload_pending",
        transcode_status="QUEUED"
    )
    db.add(episode)
    db.commit()
    db.refresh(episode)

    upload_id = str(uuid.uuid4())
    upload_folder = os.path.join(TEMP_CHUNKS_DIR, upload_id)
    os.makedirs(upload_folder, exist_ok=True)

    # Save session metadata
    meta = {
        "upload_id": upload_id,
        "episode_id": episode.id,
        "video_id": video_id,
        "filename": req.filename,
        "total_chunks": req.total_chunks,
        "file_size": req.file_size,
        "file_md5": req.file_md5
    }
    with open(os.path.join(upload_folder, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f)

    return {
        "code": 200,
        "message": "Upload initialized successfully",
        "data": {
            "upload_id": upload_id,
            "episode_id": episode.id,
            "chunk_size": 5 * 1024 * 1024
        }
    }

@router.post("/chunk")
async def upload_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    file: UploadFile = File(...)
):
    """Receive a single chunk file and save to temporary buffer."""
    upload_folder = os.path.join(TEMP_CHUNKS_DIR, upload_id)
    if not os.path.exists(upload_folder):
        raise HTTPException(status_code=404, detail="Upload session not found or expired")

    chunk_filename = f"chunk_{chunk_index}"
    chunk_path = os.path.join(upload_folder, chunk_filename)

    content = await file.read()
    with open(chunk_path, "wb") as f:
        f.write(content)

    return {
        "code": 200,
        "message": f"Chunk {chunk_index} uploaded successfully",
        "data": {
            "upload_id": upload_id,
            "chunk_index": chunk_index,
            "size": len(content)
        }
    }

@router.post("/complete")
async def complete_upload(
    req: UploadCompleteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Merge uploaded chunks, update status, and trigger async background FFmpeg transcode."""
    upload_folder = os.path.join(TEMP_CHUNKS_DIR, req.upload_id)
    if not os.path.exists(upload_folder):
        raise HTTPException(status_code=404, detail="Upload session not found")

    episode = db.query(VideoEpisode).filter(VideoEpisode.id == req.episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Verify all chunks exist
    for idx in range(req.total_chunks):
        chunk_file = os.path.join(upload_folder, f"chunk_{idx}")
        if not os.path.exists(chunk_file):
            raise HTTPException(status_code=400, detail=f"Missing chunk index {idx}")

    # Merge chunks sequentially
    merged_filename = f"{req.episode_id}.mp4"
    merged_path = os.path.join(settings.UPLOAD_DIR, merged_filename)

    with open(merged_path, "wb") as outfile:
        for idx in range(req.total_chunks):
            chunk_file = os.path.join(upload_folder, f"chunk_{idx}")
            with open(chunk_file, "rb") as infile:
                shutil.copyfileobj(infile, outfile)

    # Clean up chunk directory
    shutil.rmtree(upload_folder, ignore_errors=True)

    # Update state to PROCESSING
    episode.transcode_status = "PROCESSING"
    db.commit()

    # Dispatch asynchronous background transcode pipeline
    background_tasks.add_task(
        transcode_service.process_episode_pipeline,
        episode_id=req.episode_id,
        raw_merged_path=merged_path
    )

    return {
        "code": 200,
        "message": "Chunks merged successfully. Transcode pipeline triggered in background.",
        "data": {
            "episode_id": req.episode_id,
            "status": "PROCESSING"
        }
    }

@router.get("/status/{episode_id}")
def get_upload_status(episode_id: str, db: Session = Depends(get_db)):
    """Query current transcoding and upload sync status."""
    episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    return {
        "code": 200,
        "data": {
            "episode_id": episode.id,
            "title": episode.title,
            "transcode_status": episode.transcode_status,
            "duration_seconds": episode.duration_seconds,
            "raw_file_path": episode.raw_file_path,
            "stream_url": episode.m3u8_url
        }
    }


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    本地图片安全上传接口 (支持 JPG, PNG, WEBP, <=10MB).
    保存至 storage/uploads/images/ 并返回静态直链.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="未提供有效文件")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的图片格式 '{ext}'，仅支持: {', '.join(sorted(IMAGE_EXTENSIONS))}"
        )

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"图片大小超出限制 (最大 10MB，当前大小 {len(content) / (1024 * 1024):.2f}MB)"
        )

    file_uuid = str(uuid.uuid4())
    filename = f"{file_uuid}{ext}"

    # Determine storage destinations (write to both root storage and backend storage for zero-downtime static mount)
    root_storage = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../storage"))
    backend_storage = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../storage"))

    for base_storage in [root_storage, backend_storage]:
        target_dir = os.path.join(base_storage, "uploads", "images")
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, filename)
        with open(file_path, "wb") as f:
            f.write(content)

    url = f"/storage/uploads/images/{filename}"
    return {
        "code": 200,
        "message": "图片上传成功",
        "url": url,
        "data": {
            "url": url,
            "filename": filename,
            "size": len(content)
        }
    }

