# -*- coding: utf-8 -*-
"""
==============================================================================
【模型文件】：backend/app/models/favorite.py
【业务定位】：多级命名收藏夹与短剧归档体系模型
【对应表名】：favorite_folders, favorite_items
【核心功能】：
  支持用户创建自定义命名的多级收藏夹（如“下饭神剧”、“反转逆袭必追”）：
  - FavoriteFolder: 收藏文件夹主体（名称、描述、公开/私密、默认保护标志）
  - FavoriteItem: 收藏夹与短剧关联条目（同一个剧可在多个收藏夹中归档）
【对应前端】：
  - 个人中心收藏管理：frontend/src/views/UserProfileView.vue (我的收藏夹)
  - 播放器一键收藏弹窗：frontend/src/views/PlayerView.vue
==============================================================================
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class FavoriteFolder(Base):
    """
    【多级命名收藏文件夹实体】
    支持用户根据喜好创建自定义收藏夹，并支持公开分享或仅自己可见。
    每个新用户在首次收藏时，系统自动为其初始化一个系统默认收藏夹（is_default=True）。
    """
    __tablename__ = "favorite_folders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 收藏夹名称：如“默认收藏夹”、“二刷名场面”
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 收藏夹介绍描述
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # 是否公开可见：True 为全站用户均可在主页查看该收藏夹，False 为私密
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 是否为系统默认收藏夹：默认收藏夹不可被用户物理删除，保证基础收藏兜底
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联归档短剧列表
    items: Mapped[List["FavoriteItem"]] = relationship("FavoriteItem", back_populates="folder", cascade="all, delete-orphan")

class FavoriteItem(Base):
    """
    【收藏夹短剧归档条目实体】
    记录哪一部短剧被归档进了哪一个收藏文件夹。
    联合唯一约束保证同一个短剧在同一个文件夹内只能归档一次。
    """
    __tablename__ = "favorite_items"
    __table_args__ = (
        UniqueConstraint("folder_id", "video_id", name="uq_folder_video_item"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    folder_id: Mapped[str] = mapped_column(String(36), ForeignKey("favorite_folders.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 收藏添加时间戳（用于按收藏时间逆序呈现）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    folder: Mapped["FavoriteFolder"] = relationship("FavoriteFolder", back_populates="items")
