import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, BigInteger, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Video(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    creator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="短剧", index=True)
    status: Mapped[str] = mapped_column(String(20), default="PUBLISHED", index=True)  # PUBLISHED, HIDDEN, DRAFT, BLOCKED
    custom_cover_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    extra_images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list of multiple jpg posters
    total_episodes: Mapped[int] = mapped_column(Integer, default=1)
    view_count: Mapped[int] = mapped_column(BigInteger, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    coin_count: Mapped[int] = mapped_column(Integer, default=0)
    heat_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="videos")
    episodes: Mapped[List["VideoEpisode"]] = relationship(
        "VideoEpisode", back_populates="video", cascade="all, delete-orphan", order_by="VideoEpisode.episode_num"
    )

class VideoEpisode(Base):
    __tablename__ = "video_episodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    episode_num: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    raw_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    m3u8_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    transcode_status: Mapped[str] = mapped_column(String(20), default="QUEUED", index=True)  # QUEUED, PROCESSING, READY, FAILED
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    video: Mapped["Video"] = relationship("Video", back_populates="episodes")
    danmakus: Mapped[List["VideoDanmaku"]] = relationship(
        "VideoDanmaku", back_populates="episode", cascade="all, delete-orphan"
    )
    subtitles: Mapped[List["VideoSubtitleTimeline"]] = relationship(
        "VideoSubtitleTimeline", back_populates="episode", cascade="all, delete-orphan", order_by="VideoSubtitleTimeline.start_seconds"
    )

class VideoSubtitleTimeline(Base):
    __tablename__ = "video_subtitle_timelines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    episode_id: Mapped[str] = mapped_column(String(36), ForeignKey("video_episodes.id", ondelete="CASCADE"), nullable=False, index=True)
    start_seconds: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    end_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    speaker: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_climax: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    episode: Mapped["VideoEpisode"] = relationship("VideoEpisode", back_populates="subtitles")

class SystemCarousel(Base):
    __tablename__ = "system_carousels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tag: Mapped[str] = mapped_column(String(50), default="今日焦点推荐")
    cover_url: Mapped[str] = mapped_column(String(500), nullable=False)
    video_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

