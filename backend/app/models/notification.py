import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class SystemAnnouncement(Base):
    """系统全员公告表"""
    __tablename__ = "system_announcements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tag: Mapped[str] = mapped_column(String(50), default="系统公告")  # 系统公告, 活动特惠, 维护通知, 功能更新
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    creator_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[creator_id])


class UserNotification(Base):
    """用户个性化通知消息表 (系统公告/回复我的/收到的赞)"""
    __tablename__ = "user_notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # 接收者
    sender_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # 触发者
    category: Mapped[str] = mapped_column(String(30), nullable=False, index=True)  # ANNOUNCEMENT, REPLY, LIKE
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    video_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    episode_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    comment_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    announcement_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    sender: Mapped[Optional["User"]] = relationship("User", foreign_keys=[sender_id])
