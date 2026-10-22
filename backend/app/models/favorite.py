import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FavoriteFolder(Base):
    """
    User-created or default favorites folder for organizing dramas.
    Supports privacy flag (is_public) and default protection (is_default).
    """
    __tablename__ = "favorite_folders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items: Mapped[List["FavoriteItem"]] = relationship(
        "FavoriteItem",
        back_populates="folder",
        cascade="all, delete-orphan",
        order_by="FavoriteItem.created_at.desc()"
    )


class FavoriteItem(Base):
    """
    Individual drama bookmark inside a favorite folder.
    Guarantees unique (folder_id, video_id) pairing per folder.
    """
    __tablename__ = "favorite_items"
    __table_args__ = (
        UniqueConstraint("folder_id", "video_id", name="uq_folder_video_item"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    folder_id: Mapped[str] = mapped_column(String(36), ForeignKey("favorite_folders.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    folder: Mapped["FavoriteFolder"] = relationship("FavoriteFolder", back_populates="items")
    video: Mapped["Video"] = relationship("Video")
