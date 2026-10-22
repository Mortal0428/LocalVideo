import uuid
from typing import Optional, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.core.database import get_db, SessionLocal
from app.models.video import VideoEpisode, Video
from app.models.interaction import VideoDanmaku
from app.models.user import User
from app.services.danmaku_manager import danmaku_manager
from app.services.moderation_service import moderation_service

router = APIRouter()

class DanmakuSendRequest(BaseModel):
    episode_id: str
    content: str
    time_offset: float
    color: Optional[str] = "#FFFFFF"
    font_size: Optional[int] = 18
    user_id: Optional[str] = None

def get_demo_user(db: Session, user_id: Optional[str] = None) -> User:
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return user
    user = db.query(User).first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            username="danmaku_user",
            password_hash="disabled",
            role="USER"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@router.get("/list/{episode_id}")
def get_danmaku_list(episode_id: str, db: Session = Depends(get_db)):
    """Fetch all historical danmakus for an episode sorted by time offset."""
    danmakus = db.query(VideoDanmaku).filter(
        VideoDanmaku.episode_id == episode_id
    ).order_by(asc(VideoDanmaku.time_offset)).all()

    return {
        "code": 200,
        "data": [
            {
                "id": d.id,
                "time_offset": d.time_offset,
                "content": d.content,
                "color": d.color,
                "font_size": d.font_size,
                "created_at": d.created_at.strftime("%Y-%m-%d %H:%M:%S") if d.created_at else ""
            }
            for d in danmakus
        ]
    }

@router.post("/send")
async def send_danmaku_http(req: DanmakuSendRequest, db: Session = Depends(get_db)):
    """Send danmaku via HTTP endpoint with real-time DFA moderation and WebSocket broadcast."""
    user = get_demo_user(db, req.user_id)
    episode = db.query(VideoEpisode).filter(VideoEpisode.id == req.episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # 1. Real-time DFA Content Moderation Check
    has_violation, sanitized_text, matched_words, risk_level = moderation_service.check_text(req.content)
    
    if has_violation and risk_level == "HIGH":
        danmaku_id = str(uuid.uuid4())
        moderation_service.log_violation(
            db,
            video_id=episode.video_id,
            target_type="DANMAKU",
            target_id=danmaku_id,
            content=req.content,
            matched_words=matched_words,
            risk_level="HIGH"
        )
        raise HTTPException(
            status_code=403,
            detail=f"弹幕内容含违规敏感词 ({', '.join(matched_words)})，已阻断发送并记录机审日志！"
        )

    final_content = sanitized_text if has_violation else req.content

    # 2. Persist to MySQL
    danmaku = VideoDanmaku(
        id=str(uuid.uuid4()),
        episode_id=req.episode_id,
        user_id=user.id,
        time_offset=round(req.time_offset, 2),
        content=final_content,
        color=req.color or "#FFFFFF",
        font_size=req.font_size or 18
    )
    db.add(danmaku)
    db.commit()
    db.refresh(danmaku)

    # 3. Broadcast to all active WebSocket clients in this episode
    broadcast_payload = {
        "type": "danmaku",
        "id": danmaku.id,
        "content": danmaku.content,
        "time_offset": danmaku.time_offset,
        "color": danmaku.color,
        "font_size": danmaku.font_size,
        "username": user.username
    }
    await danmaku_manager.broadcast(req.episode_id, broadcast_payload)

    return {
        "code": 200,
        "message": "Danmaku sent successfully",
        "data": broadcast_payload
    }

@router.websocket("/ws/{episode_id}")
async def danmaku_websocket_endpoint(websocket: WebSocket, episode_id: str):
    """Real-time bi-directional WebSocket connection for instant danmaku streaming."""
    await danmaku_manager.connect(episode_id, websocket)
    db = SessionLocal()
    try:
        episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
        video_id = episode.video_id if episode else "default"

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "danmaku")

            if msg_type == "danmaku":
                raw_content = data.get("content", "").strip()
                time_offset = float(data.get("time_offset", 0.0))
                color = data.get("color", "#FFFFFF")
                font_size = int(data.get("font_size", 18))
                user_id = data.get("user_id")

                user = get_demo_user(db, user_id)

                # DFA Moderation Check
                has_violation, sanitized_text, matched_words, risk_level = moderation_service.check_text(raw_content)

                if has_violation and risk_level == "HIGH":
                    danmaku_id = str(uuid.uuid4())
                    moderation_service.log_violation(
                        db,
                        video_id=video_id,
                        target_type="DANMAKU",
                        target_id=danmaku_id,
                        content=raw_content,
                        matched_words=matched_words,
                        risk_level="HIGH"
                    )
                    # Send rejection notice back only to this sender
                    await websocket.send_json({
                        "type": "error",
                        "code": 403,
                        "message": f"弹幕涉敏已拦截: {', '.join(matched_words)}"
                    })
                    continue

                final_content = sanitized_text if has_violation else raw_content

                # Persist
                danmaku = VideoDanmaku(
                    id=str(uuid.uuid4()),
                    episode_id=episode_id,
                    user_id=user.id,
                    time_offset=round(time_offset, 2),
                    content=final_content,
                    color=color,
                    font_size=font_size
                )
                db.add(danmaku)
                db.commit()
                db.refresh(danmaku)

                # Broadcast to all clients
                await danmaku_manager.broadcast(episode_id, {
                    "type": "danmaku",
                    "id": danmaku.id,
                    "content": danmaku.content,
                    "time_offset": danmaku.time_offset,
                    "color": danmaku.color,
                    "font_size": danmaku.font_size,
                    "username": user.username
                })

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        danmaku_manager.disconnect(episode_id, websocket)
    except Exception as e:
        import traceback
        traceback.print_exc()
        danmaku_manager.disconnect(episode_id, websocket)
    finally:
        db.close()
