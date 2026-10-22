import os
import uuid
import shutil
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user, require_creator
from app.models.user import User
from app.models.video import Video, VideoEpisode
from app.services.openlist_storage import openlist_storage
from app.services.transcode_service import TranscodeService

logger = logging.getLogger(__name__)

router = APIRouter()
transcode_service = TranscodeService()

class CreatorApplyRequest(BaseModel):
    creator_name: str = Field(..., min_length=2, max_length=50, description="创作者别名/名称")
    bio: Optional[str] = Field("", max_length=255, description="创作者简介或创作方向")

class MkdirRequest(BaseModel):
    folder_name: str = Field(..., min_length=1, max_length=100, description="新建文件夹名称")
    parent_path: Optional[str] = Field("/kuake/红果项目资源目录", description="所在网盘父级目录")

@router.post("/apply")
def apply_to_become_creator(
    req: CreatorApplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Standard user applies to become a creator.
    Instantly unlocks creator privileges and studio access.
    """
    current_user.is_creator = True
    current_user.role = "CREATOR"
    current_user.creator_application_status = "APPROVED"
    current_user.creator_bio = req.bio
    if req.creator_name.strip():
        current_user.nickname = req.creator_name.strip()
    
    db.commit()
    db.refresh(current_user)
    return {
        "code": 200,
        "message": "恭喜！您已成功开通创作者权限，尽情上传与创作短剧吧！",
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "nickname": current_user.nickname,
            "role": current_user.role,
            "is_creator": current_user.is_creator,
            "status": current_user.status,
            "creator_application_status": current_user.creator_application_status,
            "creator_bio": current_user.creator_bio
        }
    }

@router.get("/pan/tree")
async def list_cloud_disk_tree(
    path: Optional[str] = "/kuake/红果项目资源目录",
    current_user: User = Depends(require_creator)
):
    """
    Browse directories and files in Quark Cloud Disk for the Creator Studio.
    """
    target_path = path or "/kuake/红果项目资源目录"
    try:
        files = await openlist_storage.list_files(target_path)
    except Exception as e:
        logger.warning(f"Failed to list {target_path}: {e}, falling back to /kuake")
        try:
            files = await openlist_storage.list_files("/kuake")
            target_path = "/kuake"
        except Exception as e2:
            files = []
            logger.error(f"Fallback list failed: {e2}")

    # Calculate parent path for 'Go Up' navigation
    clean_path = target_path.rstrip("/")
    if "/" in clean_path:
        parent_path = clean_path.rsplit("/", 1)[0]
        if not parent_path:
            parent_path = "/"
    else:
        parent_path = "/"

    folders = []
    items = []
    for f in files:
        item_info = {
            "name": f.get("name"),
            "size": f.get("size", 0),
            "is_dir": f.get("is_dir", False),
            "modified": f.get("modified"),
            "thumb": f.get("thumb") or "",
            "path": f"{clean_path}/{f.get('name')}".replace("//", "/")
        }
        if f.get("is_dir"):
            folders.append(item_info)
        else:
            items.append(item_info)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "current_path": target_path,
            "parent_path": parent_path,
            "total_count": len(files),
            "folders": folders,
            "files": items
        }
    }

@router.post("/pan/mkdir")
async def make_cloud_disk_directory(
    req: MkdirRequest,
    current_user: User = Depends(require_creator)
):
    """
    Create a new drama folder in Quark Cloud Disk.
    """
    clean_parent = (req.parent_path or "/kuake/红果项目资源目录").rstrip("/")
    clean_name = req.folder_name.strip().replace("/", "_").replace("\\", "_")
    target_full_path = f"{clean_parent}/{clean_name}"

    try:
        success = await openlist_storage.mkdir(target_full_path)
        if success:
            return {
                "code": 200,
                "message": f"成功在云盘创建剧集文件夹: {clean_name}",
                "data": {
                    "path": target_full_path,
                    "folder_name": clean_name
                }
            }
        else:
            raise HTTPException(status_code=500, detail="创建文件夹失败")
    except Exception as e:
        logger.error(f"mkdir error for {target_full_path}: {e}")
        raise HTTPException(status_code=500, detail=f"云盘创建文件夹失败: {str(e)}")

@router.post("/pan/upload")
async def upload_video_to_cloud_disk(
    file: UploadFile = File(...),
    target_folder: str = Form("/kuake/红果项目资源目录"),
    drama_title: Optional[str] = Form(None),
    episode_title: Optional[str] = Form(None),
    episode_num: Optional[int] = Form(1),
    category: Optional[str] = Form("短剧精选"),
    current_user: User = Depends(require_creator),
    db: Session = Depends(get_db)
):
    """
    Upload video file to Quark Cloud Disk folder, extract FFmpeg metadata & cover,
    and register video episode in MySQL database.
    """
    filename = file.filename or f"episode_{uuid.uuid4().hex[:6]}.mp4"
    temp_dir = os.path.join(settings.UPLOAD_DIR, "creator_temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_local_path = os.path.join(temp_dir, filename)

    try:
        # 1. Save uploaded file locally temporarily
        with open(temp_local_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Extract metadata via FFprobe
        meta = transcode_service.get_video_metadata(temp_local_path)
        duration = meta.get("duration", 0.0)
        width = meta.get("width", 1080)
        height = meta.get("height", 1920)

        # 3. Extract cover poster
        poster_filename = f"poster_{uuid.uuid4().hex[:8]}.jpg"
        poster_local_path = os.path.join(temp_dir, poster_filename)
        transcode_service.generate_poster(temp_local_path, poster_local_path, timestamp_sec=1.0)

        # 4. Upload video to Quark Cloud Disk
        clean_target_folder = target_folder.rstrip("/")
        remote_video_path = f"{clean_target_folder}/{filename}"
        await openlist_storage.upload_file_from_path(remote_video_path, temp_local_path)

        # 5. Upload poster if generated
        remote_poster_path = f"{clean_target_folder}/{poster_filename}"
        if os.path.exists(poster_local_path):
            await openlist_storage.upload_file_from_path(remote_poster_path, poster_local_path)

        # 6. Database record creation
        actual_drama_title = drama_title.strip() if drama_title else os.path.basename(clean_target_folder)
        if actual_drama_title in ["红果项目资源目录", "kuake"]:
            actual_drama_title = os.path.splitext(filename)[0]

        # Check if Video already exists for this drama title
        video = db.query(Video).filter(Video.title == actual_drama_title).first()
        if not video:
            video = Video(
                id=str(uuid.uuid4()),
                title=actual_drama_title,
                description=f"由创作者 @{current_user.nickname or current_user.username} 上传的精选短剧",
                creator_id=current_user.id,
                category=category or "短剧精选",
                tags="网盘直存,4K原画,独家短剧",
                cover_url=f"/storage/posters/{poster_filename}" if os.path.exists(poster_local_path) else "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=600&auto=format&fit=crop&q=80",
                status="READY"
            )
            db.add(video)
            db.flush()

        # Create Episode
        ep_title = episode_title.strip() if episode_title else f"第 {episode_num or 1} 集"
        episode = VideoEpisode(
            id=str(uuid.uuid4()),
            video_id=video.id,
            episode_num=episode_num or 1,
            title=ep_title,
            raw_file_path=remote_video_path,
            cover_url=video.cover_url,
            duration=duration,
            resolution=f"{width}x{height}",
            status="READY"
        )
        db.add(episode)
        db.commit()
        db.refresh(video)
        db.refresh(episode)

        return {
            "code": 200,
            "message": f"短剧《{video.title}》第 {episode.episode_num} 集已成功存入网盘并上线！",
            "data": {
                "drama_id": video.id,
                "drama_title": video.title,
                "episode_id": episode.id,
                "episode_title": episode.title,
                "remote_file_path": remote_video_path,
                "duration": duration,
                "resolution": episode.resolution
            }
        }
    except Exception as e:
        logger.error(f"Error in creator upload: {e}")
        raise HTTPException(status_code=500, detail=f"上传处理失败: {str(e)}")
    finally:
        # Clean up local temp files
        if os.path.exists(temp_local_path):
            os.remove(temp_local_path)

@router.post("/pan/upload-chunk")
async def upload_video_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_creator)
):
    """
    Receive and store a 5MB-10MB video chunk in an isolated temporary task directory.
    Zero memory leaks and low disk overhead.
    """
    chunks_dir = os.path.join(settings.UPLOAD_DIR, "chunks", upload_id)
    os.makedirs(chunks_dir, exist_ok=True)
    chunk_path = os.path.join(chunks_dir, f"chunk_{chunk_index}")

    try:
        with open(chunk_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {
            "code": 200,
            "message": f"分片 {chunk_index} 接收并暂存成功",
            "data": {
                "upload_id": upload_id,
                "chunk_index": chunk_index,
                "size_bytes": os.path.getsize(chunk_path)
            }
        }
    except Exception as e:
        logger.error(f"Failed to save chunk {chunk_index} for upload {upload_id}: {e}")
        raise HTTPException(status_code=500, detail=f"分片 {chunk_index} 保存失败: {str(e)}")

@router.post("/pan/merge-chunk")
async def merge_video_chunks(
    upload_id: str = Form(...),
    total_chunks: int = Form(...),
    filename: str = Form(...),
    target_folder: str = Form("/kuake/红果项目资源目录"),
    drama_title: Optional[str] = Form(None),
    episode_title: Optional[str] = Form(None),
    episode_num: Optional[int] = Form(1),
    category: Optional[str] = Form("短剧精选"),
    current_user: User = Depends(require_creator),
    db: Session = Depends(get_db)
):
    """
    Assemble all uploaded chunks into a complete video, upload directly to OpenList Cloud Disk,
    register in MySQL, and immediately purge all temporary chunks to guarantee 0 local disk footprint.
    """
    chunks_dir = os.path.join(settings.UPLOAD_DIR, "chunks", upload_id)
    if not os.path.exists(chunks_dir):
        raise HTTPException(status_code=400, detail="未找到该任务对应的分片暂存目录，请重新上传")

    # 1. Verify all chunks exist
    for idx in range(total_chunks):
        c_path = os.path.join(chunks_dir, f"chunk_{idx}")
        if not os.path.exists(c_path):
            raise HTTPException(status_code=400, detail=f"分片数据不完整，缺失分片: {idx}/{total_chunks}")

    merged_local_path = os.path.join(chunks_dir, filename)

    try:
        # 2. Sequential assembly without holding whole file in RAM
        with open(merged_local_path, "wb") as outfile:
            for idx in range(total_chunks):
                c_path = os.path.join(chunks_dir, f"chunk_{idx}")
                with open(c_path, "rb") as infile:
                    shutil.copyfileobj(infile, outfile)

        # 3. Metadata extraction
        meta = transcode_service.get_video_metadata(merged_local_path)
        duration_sec = int(meta.get("duration", 0))

        # 4. Poster extraction
        poster_filename = f"poster_{uuid.uuid4().hex[:8]}.jpg"
        poster_local_path = os.path.join(chunks_dir, poster_filename)
        try:
            transcode_service.generate_poster(merged_local_path, poster_local_path, timestamp_sec=1.0)
        except Exception as poster_err:
            logger.warning(f"Poster extraction failed or non-video input: {poster_err}")

        # 5. Upload to OpenList Cloud Disk
        clean_target_folder = target_folder.rstrip("/")
        remote_video_path = f"{clean_target_folder}/{filename}"
        await openlist_storage.upload_file_from_path(remote_video_path, merged_local_path)

        # 6. Upload poster if generated
        remote_poster_path = f"{clean_target_folder}/{poster_filename}"
        if os.path.exists(poster_local_path):
            await openlist_storage.upload_file_from_path(remote_poster_path, poster_local_path)

        # 7. Database records
        actual_drama_title = drama_title.strip() if drama_title else os.path.basename(clean_target_folder)
        if actual_drama_title in ["红果项目资源目录", "kuake"]:
            actual_drama_title = os.path.splitext(filename)[0]

        video = db.query(Video).filter(Video.title == actual_drama_title).first()
        if not video:
            video = Video(
                id=str(uuid.uuid4()),
                title=actual_drama_title,
                summary=f"由创作者 @{current_user.nickname or current_user.username} 分片上传的精选短剧",
                creator_id=current_user.id,
                category=category or "短剧精选",
                cover_url=f"/storage/posters/{poster_filename}" if os.path.exists(poster_local_path) else "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=600&auto=format&fit=crop&q=80",
                status="PUBLISHED"
            )
            db.add(video)
            db.flush()

        ep_title = episode_title.strip() if episode_title else f"第 {episode_num or 1} 集"
        episode = VideoEpisode(
            id=str(uuid.uuid4()),
            video_id=video.id,
            episode_num=episode_num or 1,
            title=ep_title,
            raw_file_path=remote_video_path,
            duration_seconds=duration_sec,
            transcode_status="READY",
            m3u8_url=f"/api/v1/videos/stream/{uuid.uuid4()}"
        )
        episode.m3u8_url = f"/api/v1/videos/stream/{episode.id}"
        db.add(episode)

        # Update video total episodes
        video.total_episodes = db.query(VideoEpisode).filter(VideoEpisode.video_id == video.id).count() + 1
        db.commit()
        db.refresh(video)
        db.refresh(episode)

        logger.info(f"Chunk upload merged successfully for drama {video.title} ep {episode.episode_num}")
        return {
            "code": 200,
            "message": f"短剧《{video.title}》第 {episode.episode_num} 集分片合并入云成功！",
            "data": {
                "drama_id": video.id,
                "drama_title": video.title,
                "episode_id": episode.id,
                "episode_title": episode.title,
                "remote_file_path": remote_video_path,
                "duration_seconds": duration_sec
            }
        }
    except Exception as e:
        logger.error(f"Error during chunk merge: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"分片合并入云失败: {str(e)}")
    finally:
        # 8. Force purge temporary chunks to preserve zero local disk footprint
        try:
            if os.path.exists(chunks_dir):
                shutil.rmtree(chunks_dir, ignore_errors=True)
                logger.info(f"Temporary chunks directory {chunks_dir} safely purged.")
        except Exception as cleanup_err:
            logger.warning(f"Cleanup warning for chunks_dir {chunks_dir}: {cleanup_err}")

@router.get("/dramas")
def list_creator_dramas(
    current_user: User = Depends(require_creator),
    db: Session = Depends(get_db)
):
    """
    List all short dramas uploaded by the current creator.
    """
    dramas = db.query(Video).filter(Video.creator_id == current_user.id).all()
    # If this user hasn't uploaded dramas yet, also include all dramas for testing
    if not dramas:
        dramas = db.query(Video).all()

    result = []
    for d in dramas:
        episodes_count = len(d.episodes) if d.episodes else (d.total_episodes or 1)
        result.append({
            "id": d.id,
            "title": d.title,
            "description": getattr(d, "summary", "") or "",
            "category": d.category,
            "cover_url": d.cover_url,
            "episodes_count": episodes_count,
            "play_count": getattr(d, "view_count", 0) or 0,
            "status": d.status,
            "created_at": d.created_at.strftime("%Y-%m-%d %H:%M") if d.created_at else ""
        })

    return {
        "code": 200,
        "message": "success",
        "data": result
    }

@router.post("/pan/sync-dramas")
async def sync_quark_dramas(
    current_user: User = Depends(require_creator),
    db: Session = Depends(get_db)
):
    """
    Scan Quark Cloud Disk folders, auto-detect short dramas and episodes,
    and map them into MySQL.
    """
    from app.services.cloud_drama_sync import cloud_drama_sync
    res = await cloud_drama_sync.scan_and_sync_all(db=db)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "同步短剧失败"))
    return {
        "code": 200,
        "message": f"成功从夸克网盘同步短剧，共计发现并映射 {res.get('total_synced_dramas')} 部短剧作品！",
        "data": res
    }

class DramaUpdateRequest(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    status: Optional[str] = None

class EpisodeUpdateRequest(BaseModel):
    title: Optional[str] = None
    episode_num: Optional[int] = None
    climax_seconds: Optional[float] = None

@router.get("/dramas/{drama_id}/episodes")
def get_drama_episodes(
    drama_id: str,
    current_user: User = Depends(require_creator),
    db: Session = Depends(get_db)
):
    """Fetch all episodes belonging to a specific drama for creator management."""
    drama = db.query(Video).filter(Video.id == drama_id).first()
    if not drama:
        raise HTTPException(status_code=404, detail="短剧不存在")

    episodes = db.query(VideoEpisode).filter(
        VideoEpisode.video_id == drama_id
    ).order_by(VideoEpisode.episode_num.asc()).all()

    result = []
    for ep in episodes:
        # Check if there is a climax subtitle timestamp
        from app.models.video import VideoSubtitleTimeline
        climax_sub = db.query(VideoSubtitleTimeline).filter(
            VideoSubtitleTimeline.episode_id == ep.id,
            VideoSubtitleTimeline.is_climax == True
        ).first()

        result.append({
            "id": ep.id,
            "episode_num": ep.episode_num,
            "title": ep.title,
            "duration_seconds": ep.duration_seconds,
            "status": ep.transcode_status,
            "raw_file_path": ep.raw_file_path,
            "climax_seconds": climax_sub.start_seconds if climax_sub else None,
            "created_at": ep.created_at.strftime("%Y-%m-%d %H:%M") if ep.created_at else ""
        })

    return {
        "code": 200,
        "message": "success",
        "data": {
            "drama_id": drama.id,
            "drama_title": drama.title,
            "total_count": len(result),
            "episodes": result
        }
    }

@router.put("/dramas/{drama_id}")
def update_creator_drama(
    drama_id: str,
    req: DramaUpdateRequest,
    current_user: User = Depends(require_creator),
    db: Session = Depends(get_db)
):
    """Update drama metadata (title, category, description, cover_url, status)."""
    drama = db.query(Video).filter(Video.id == drama_id).first()
    if not drama:
        raise HTTPException(status_code=404, detail="短剧不存在")

    if req.title is not None and req.title.strip():
        drama.title = req.title.strip()
    if req.category is not None:
        drama.category = req.category
    if req.description is not None:
        drama.description = req.description
    if req.cover_url is not None and req.cover_url.strip():
        drama.cover_url = req.cover_url.strip()
    if req.status is not None:
        drama.status = req.status

    db.commit()
    db.refresh(drama)

    return {
        "code": 200,
        "message": f"短剧《{drama.title}》信息已成功保存更新！",
        "data": {
            "id": drama.id,
            "title": drama.title,
            "category": drama.category,
            "description": drama.description,
            "cover_url": drama.cover_url,
            "status": drama.status
        }
    }

@router.put("/episodes/{episode_id}")
def update_creator_episode(
    episode_id: str,
    req: EpisodeUpdateRequest,
    current_user: User = Depends(require_creator),
    db: Session = Depends(get_db)
):
    """Update episode metadata (title, episode_num, climax_seconds)."""
    episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="分集不存在")

    if req.title is not None and req.title.strip():
        episode.title = req.title.strip()
    if req.episode_num is not None:
        episode.episode_num = req.episode_num

    # If climax_seconds provided, set/update climax subtitle timeline
    if req.climax_seconds is not None:
        from app.models.video import VideoSubtitleTimeline
        # Clear existing climax
        existing = db.query(VideoSubtitleTimeline).filter(
            VideoSubtitleTimeline.episode_id == episode_id,
            VideoSubtitleTimeline.is_climax == True
        ).first()
        if existing:
            existing.start_seconds = req.climax_seconds
            existing.end_seconds = req.climax_seconds + 5.0
        else:
            new_climax = VideoSubtitleTimeline(
                id=str(uuid.uuid4()),
                episode_id=episode_id,
                start_seconds=req.climax_seconds,
                end_seconds=req.climax_seconds + 5.0,
                speaker="官方看点",
                content=f"本集高能名场面反转时刻 ({int(req.climax_seconds)}s)",
                is_climax=True
            )
            db.add(new_climax)

    db.commit()
    db.refresh(episode)

    return {
        "code": 200,
        "message": f"分集第 {episode.episode_num} 集信息已成功更新！",
        "data": {
            "id": episode.id,
            "episode_num": episode.episode_num,
            "title": episode.title,
            "climax_seconds": req.climax_seconds
        }
    }

@router.delete("/dramas/{drama_id}")
def delete_creator_drama(
    drama_id: str,
    current_user: User = Depends(require_creator),
    db: Session = Depends(get_db)
):
    """Delete a drama and all its episodes."""
    drama = db.query(Video).filter(Video.id == drama_id).first()
    if not drama:
        raise HTTPException(status_code=404, detail="短剧不存在")

    title = drama.title
    db.delete(drama)
    db.commit()

    return {
        "code": 200,
        "message": f"短剧《{title}》及其分集已成功删除！",
        "data": { "id": drama_id, "title": title }
    }

