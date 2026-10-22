import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="USER")  # GUEST, USER, CREATOR, REVIEWER, ADMIN
    nickname: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_creator: Mapped[bool] = mapped_column(Boolean, default=False)
    is_reviewer: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # ACTIVE, BANNED
    creator_application_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # PENDING, APPROVED, REJECTED
    creator_bio: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reviewer_application_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # PENDING, APPROVED, REJECTED
    reviewer_bio: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    vip_expire_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    videos: Mapped[List["Video"]] = relationship("Video", back_populates="creator")
    danmakus: Mapped[List["VideoDanmaku"]] = relationship("VideoDanmaku", back_populates="user")
    comments: Mapped[List["UserComment"]] = relationship("UserComment", back_populates="user", foreign_keys="UserComment.user_id")
    histories: Mapped[List["UserWatchHistory"]] = relationship("UserWatchHistory", back_populates="user")
