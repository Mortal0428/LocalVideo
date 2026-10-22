import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class ContentReview(Base):
    __tablename__ = "content_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)  # PENDING, APPROVED, REJECTED
    auto_check_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 机审与敏感词预检输出
    reject_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

class SensitiveWord(Base):
    __tablename__ = "sensitive_words"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    word: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(20), default="HIGH")  # HIGH, MEDIUM, LOW
    category: Mapped[str] = mapped_column(String(50), default="违禁")  # 涉政, 暴恐, 违禁, 涉黄, 辱骂, 广告
    creator_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
