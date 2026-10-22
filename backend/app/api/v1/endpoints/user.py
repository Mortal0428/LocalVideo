import logging
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.video import Video, VideoEpisode
from app.models.interaction import UserWatchHistory, UserLike
from app.models.coin import UserCoinWallet

logger = logging.getLogger(__name__)

router = APIRouter()

class ProfileUpdateRequest(BaseModel):
    nickname: Optional[str] = Field(None, max_length=50, description="用户昵称")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像地址")
    bio: Optional[str] = Field(None, max_length=255, description="个人简介")

class ApplyCreatorRequest(BaseModel):
    creator_name: Optional[str] = Field(None, max_length=50, description="创作者称呼")
    bio: Optional[str] = Field(None, max_length=255, description="创作方向与规划")

class ApplyReviewerRequest(BaseModel):
    reviewer_name: Optional[str] = Field(None, max_length=50, description="审核员称呼")
    bio: Optional[str] = Field(None, max_length=255, description="审核经验与专业背景")

@router.get("/profile")
def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get full profile of current authenticated user, including role, status,
    and aggregate stats.
    """
    history_count = db.query(UserWatchHistory).filter(UserWatchHistory.user_id == current_user.id).count()
    likes_count = db.query(UserLike).filter(UserLike.user_id == current_user.id).count()
    
    # Creator stats if applicable
    creator_videos_count = 0
    if current_user.is_creator or current_user.role == "CREATOR":
        creator_videos_count = db.query(Video).filter(Video.creator_id == current_user.id).count()

    # User coins and VIP status
    wallet = db.query(UserCoinWallet).filter(UserCoinWallet.user_id == current_user.id).first()
    coins = wallet.balance if wallet else 50
    vip_expire_str = current_user.vip_expire_at.isoformat() if getattr(current_user, "vip_expire_at", None) else None
    is_vip = bool(current_user.vip_expire_at and current_user.vip_expire_at > datetime.utcnow())

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "nickname": current_user.nickname or current_user.username,
            "avatar_url": current_user.avatar_url or f"https://api.dicebear.com/7.x/bottts/svg?seed={current_user.username}",
            "role": current_user.role,
            "coins": coins,
            "vip_expire_at": vip_expire_str,
            "is_vip": is_vip,
            "is_creator": current_user.is_creator,
            "creator_application_status": current_user.creator_application_status or "NONE",
            "creator_bio": current_user.creator_bio or "",
            "is_reviewer": getattr(current_user, "is_reviewer", False),
            "reviewer_application_status": getattr(current_user, "reviewer_application_status", None) or "NONE",
            "reviewer_bio": getattr(current_user, "reviewer_bio", None) or "",
            "status": current_user.status,
            "created_at": current_user.created_at.strftime("%Y-%m-%d %H:%M") if current_user.created_at else "",
            "stats": {
                "history_count": history_count,
                "likes_count": likes_count,
                "creator_videos_count": creator_videos_count
            }
        }
    }

@router.put("/profile")
def update_user_profile(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update nickname, avatar, or bio of current user.
    """
    user_obj = db.query(User).filter(User.id == current_user.id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    if req.nickname is not None and req.nickname.strip():
        user_obj.nickname = req.nickname.strip()
    if req.avatar_url is not None:
        user_obj.avatar_url = req.avatar_url.strip()
    if req.bio is not None:
        user_obj.creator_bio = req.bio.strip()

    db.commit()
    db.refresh(user_obj)
    return {
        "code": 200,
        "message": "个人资料更新成功",
        "data": {
            "id": user_obj.id,
            "username": user_obj.username,
            "nickname": user_obj.nickname,
            "avatar_url": user_obj.avatar_url,
            "role": user_obj.role
        }
    }

@router.post("/apply-creator")
def apply_creator_qualification(
    req: ApplyCreatorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Apply to become a creator. Sets creator application status to PENDING for admin review.
    """
    user_obj = db.query(User).filter(User.id == current_user.id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    user_obj.creator_application_status = "PENDING"
    if req.bio:
        user_obj.creator_bio = req.bio
    if req.creator_name and req.creator_name.strip():
        user_obj.nickname = req.creator_name.strip()

    db.commit()
    db.refresh(user_obj)
    return {
        "code": 200,
        "message": "创作者资质申请已成功提交！请等待管理员在管理中台审核通过。",
        "data": {
            "id": user_obj.id,
            "username": user_obj.username,
            "nickname": user_obj.nickname,
            "role": user_obj.role,
            "is_creator": user_obj.is_creator,
            "creator_application_status": user_obj.creator_application_status
        }
    }

@router.post("/apply-reviewer")
def apply_reviewer_qualification(
    req: ApplyReviewerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Apply to become a content reviewer. Sets reviewer application status to PENDING for admin review.
    """
    user_obj = db.query(User).filter(User.id == current_user.id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    user_obj.reviewer_application_status = "PENDING"
    if req.bio:
        user_obj.reviewer_bio = req.bio
    if req.reviewer_name and req.reviewer_name.strip():
        user_obj.nickname = req.reviewer_name.strip()

    db.commit()
    db.refresh(user_obj)
    return {
        "code": 200,
        "message": "审核员资质申请已成功提交！请等待管理员在管理中台审核通过。",
        "data": {
            "id": user_obj.id,
            "username": user_obj.username,
            "nickname": user_obj.nickname,
            "role": user_obj.role,
            "is_reviewer": getattr(user_obj, "is_reviewer", False),
            "reviewer_application_status": user_obj.reviewer_application_status
        }
    }

@router.get("/history")
def get_user_watch_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns user's watch history with breakpoint continue-play links.
    """
    histories = (
        db.query(UserWatchHistory)
        .filter(UserWatchHistory.user_id == current_user.id)
        .order_by(desc(UserWatchHistory.updated_at))
        .limit(30)
        .all()
    )

    result = []
    for h in histories:
        ep = db.query(VideoEpisode).filter(VideoEpisode.id == h.last_episode_id).first()
        if not ep:
            continue
        v = db.query(Video).filter(Video.id == ep.video_id).first()
        
        duration = ep.duration_seconds or 120
        progress_pct = min(100, int((h.progress_seconds / duration) * 100)) if duration > 0 else 0

        result.append({
            "history_id": h.id,
            "episode_id": ep.id,
            "video_id": v.id if v else "",
            "drama_title": v.title if v else "微短剧",
            "cover_url": v.cover_url if v else "",
            "episode_num": ep.episode_num,
            "episode_title": ep.title,
            "progress_seconds": h.progress_seconds,
            "duration_seconds": duration,
            "progress_pct": progress_pct,
            "updated_at": h.updated_at.strftime("%Y-%m-%d %H:%M") if h.updated_at else ""
        })

    return {
        "code": 200,
        "message": "success",
        "data": result
    }

@router.get("/likes")
def get_user_likes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns dramas or episodes liked by the current user.
    """
    likes = (
        db.query(UserLike)
        .filter(UserLike.user_id == current_user.id)
        .order_by(desc(UserLike.created_at))
        .limit(30)
        .all()
    )

    result = []
    for l in likes:
        v = db.query(Video).filter(Video.id == l.video_id).first()
        if not v:
            continue
        ep = db.query(VideoEpisode).filter(VideoEpisode.video_id == v.id).order_by(VideoEpisode.episode_num.asc()).first()
        result.append({
            "like_id": l.id,
            "episode_id": ep.id if ep else "",
            "video_id": v.id,
            "drama_title": v.title,
            "cover_url": v.cover_url or "",
            "episode_num": ep.episode_num if ep else 1,
            "episode_title": ep.title if ep else "第1集",
            "created_at": l.created_at.strftime("%Y-%m-%d %H:%M") if l.created_at else ""
        })

    return {
        "code": 200,
        "message": "success",
        "data": result
    }
