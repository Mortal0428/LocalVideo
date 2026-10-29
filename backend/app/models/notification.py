# -*- coding: utf-8 -*-
"""
==============================================================================
【模型文件】：backend/app/models/notification.py
【业务定位】：系统全员公告与个人三分类通知天窗模型
【对应表名】：system_announcements, user_notifications
【核心功能】：
  支撑前台顶栏毛玻璃通知抽屉：
  - SystemAnnouncement: 平台全员广播公告（版本发布、活动通知、停机维护）
  - UserNotification: 用户专属定向通知（系统公告推达、评论被回复、点赞被触发、提及互动）
【对应前端】：
  - 顶栏毛玻璃通知天窗：frontend/src/components/NotificationSkylight.vue
  - 顶栏小铃铛徽标：frontend/src/components/GlobalHeader.vue
  - 管理后台公告发布：frontend/src/views/AdminView.vue
==============================================================================
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class SystemAnnouncement(Base):
    """
    【平台全员公告实体】
    管理员发布的全局广播消息，所有观众均可在通知天窗的“系统公告”Tab 中查阅。
    """
    __tablename__ = "system_announcements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 公告标题
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    
    # 公告详细正文
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 标签类型：SYSTEM(系统维护), ACTIVITY(精彩活动), UPDATE(功能更新)
    tag: Mapped[str] = mapped_column(String(30), default="SYSTEM")
    
    # 发布管理员 ID
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # 是否已激活生效（撤回公告时置为 False）
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class UserNotification(Base):
    """
    【个人消息通知实体】
    记录某个特定用户收到的通知消息。
    分为三大 Tab 分类：
    1. ANNOUNCEMENT: 系统公告推达
    2. REPLY: 评论被回复
    3. LIKE: 短剧或评论收到了赞
    4. MENTION: 评论中 @ 提及
    5. FOLLOW: 新粉丝关注
    """
    __tablename__ = "user_notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # 通知分类：ANNOUNCEMENT(系统公告), REPLY(回复我的), LIKE(收到的赞), MENTION(提及我的), FOLLOW(关注)
    category: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    
    # 通知简明标题
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    
    # 通知内容说明
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 关联资源外键（支持点击跳转到对应实体）
    video_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    episode_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    comment_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    announcement_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)

    # 是否已读：False 统计为未读红点，点击后置为 True 消除红点
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    sender: Mapped[Optional["User"]] = relationship("User", foreign_keys=[sender_id])
