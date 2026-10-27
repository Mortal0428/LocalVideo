import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Integer
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

class SensitiveWordProposal(Base):
    """
    4号智能体（合规审片官）巡检时提炼出的新型敏感词建议单（自迭代待审池）
    """
    __tablename__ = "sensitive_word_proposals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    word: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), default="违禁")  # 涉政, 暴恐, 违禁, 涉黄, 辱骂, 广告
    level: Mapped[str] = mapped_column(String(20), default="HIGH")  # HIGH, MEDIUM, LOW
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(32), default="danmaku")  # danmaku | comment
    source_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)  # PENDING, ACCEPTED, REJECTED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

class InteractionInspectionLog(Base):
    """
    4号合规审片官互动巡检历史记录（批次、统计、大模型状态与报告快照）
    """
    __tablename__ = "interaction_inspection_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id: Mapped[str] = mapped_column(String(64), index=True)
    target_type: Mapped[str] = mapped_column(String(32), default="comment")  # comment | danmaku
    total_inspected: Mapped[int] = mapped_column(Integer, default=0)
    violation_count: Mapped[int] = mapped_column(Integer, default=0)
    suggested_words_count: Mapped[int] = mapped_column(Integer, default=0)
    cost_ms: Mapped[int] = mapped_column(Integer, default=0)
    llm_status: Mapped[str] = mapped_column(String(64), default="COMPLETED")
    report_summary_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
