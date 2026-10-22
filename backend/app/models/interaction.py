import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class VideoDanmaku(Base):
    __tablename__ = "video_danmakus"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    episode_id: Mapped[str] = mapped_column(String(36), ForeignKey("video_episodes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    time_offset: Mapped[float] = mapped_column(Float, nullable=False, index=True)  # 秒数偏移，例如 12.5s
    content: Mapped[str] = mapped_column(String(200), nullable=False)
    color: Mapped[str] = mapped_column(String(10), default="#FFFFFF")
    font_size: Mapped[int] = mapped_column(Integer, default=18)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="danmakus")
    episode: Mapped["VideoEpisode"] = relationship("VideoEpisode", back_populates="danmakus")

class UserLike(Base):
    __tablename__ = "user_likes"
    __table_args__ = (
        UniqueConstraint("user_id", "video_id", name="uq_user_video_like"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class UserComment(Base):
    __tablename__ = "user_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)  # 直属父级评论ID
    root_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)  # 一级主楼评论ID
    reply_to_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="comments")
    reply_to_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reply_to_user_id])


class CommentLike(Base):
    """用户对评论的点赞去重表"""
    __tablename__ = "comment_likes"
    __table_args__ = (
        UniqueConstraint("user_id", "comment_id", name="uq_user_comment_like"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    comment_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_comments.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class UserWatchHistory(Base):
    __tablename__ = "user_watch_histories"
    __table_args__ = (
        UniqueConstraint("user_id", "video_id", name="uq_user_video_history"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    last_episode_id: Mapped[str] = mapped_column(String(36), nullable=False)
    progress_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="histories")
