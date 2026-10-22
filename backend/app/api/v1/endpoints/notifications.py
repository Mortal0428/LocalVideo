from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.notification import UserNotification

router = APIRouter()

class MarkReadAllRequest(BaseModel):
    category: Optional[str] = None

@router.get("")
@router.get("/")
def list_user_notifications(
    category: Optional[str] = Query(None, description="分类过滤: ANNOUNCEMENT, REPLY, LIKE"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的通知列表，支持分类筛选"""
    query = db.query(UserNotification).filter(UserNotification.user_id == current_user.id)
    if category and category.strip():
        query = query.filter(UserNotification.category == category.strip().upper())

    total = query.count()
    items = query.order_by(desc(UserNotification.created_at)).offset((page - 1) * per_page).limit(per_page).all()

    return {
        "code": 200,
        "message": "success",
        "data": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "items": [
                {
                    "id": n.id,
                    "category": n.category,
                    "title": n.title,
                    "content": n.content,
                    "sender_id": n.sender_id,
                    "sender_name": n.sender.nickname or n.sender.username if n.sender else "系统",
                    "sender_avatar": n.sender.avatar_url if n.sender else "",
                    "video_id": n.video_id,
                    "episode_id": n.episode_id,
                    "comment_id": n.comment_id,
                    "announcement_id": n.announcement_id,
                    "is_read": n.is_read,
                    "created_at": n.created_at.strftime("%Y-%m-%d %H:%M:%S") if n.created_at else ""
                }
                for n in items
            ]
        }
    }

@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取各分类未读通知计数"""
    base_query = db.query(UserNotification).filter(
        UserNotification.user_id == current_user.id,
        UserNotification.is_read == False
    )

    total = base_query.count()
    announcements = base_query.filter(UserNotification.category == "ANNOUNCEMENT").count()
    replies = base_query.filter(UserNotification.category == "REPLY").count()
    likes = base_query.filter(UserNotification.category == "LIKE").count()

    return {
        "code": 200,
        "message": "success",
        "data": {
            "total": total,
            "announcements": announcements,
            "replies": replies,
            "likes": likes
        }
    }

@router.post("/{notification_id}/read")
def mark_single_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """单条通知标记已读"""
    item = db.query(UserNotification).filter(
        UserNotification.id == notification_id,
        UserNotification.user_id == current_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="通知不存在或无权操作")

    item.is_read = True
    db.commit()

    return {
        "code": 200,
        "message": "已标记为已读",
        "data": {"id": item.id, "is_read": True}
    }

@router.post("/read-all")
def mark_all_read(
    req: Optional[MarkReadAllRequest] = None,
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """一键全部标为已读，支持分类全量已读"""
    target_category = category or (req.category if req else None)

    query = db.query(UserNotification).filter(
        UserNotification.user_id == current_user.id,
        UserNotification.is_read == False
    )
    if target_category and target_category.strip():
        query = query.filter(UserNotification.category == target_category.strip().upper())

    unread_items = query.all()
    count = len(unread_items)
    for item in unread_items:
        item.is_read = True

    db.commit()

    return {
        "code": 200,
        "message": "全部已读成功",
        "data": {
            "updated_count": count
        }
    }
