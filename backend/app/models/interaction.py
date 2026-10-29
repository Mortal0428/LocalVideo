# -*- coding: utf-8 -*-
"""
==============================================================================
【模型文件】：backend/app/models/interaction.py
【业务定位】：全平台观众互动体系模型（弹幕、点赞、两级楼中楼评论、历史足迹、关注）
【对应表名】：video_danmakus, user_likes, user_comments, comment_likes, user_watch_histories, user_follows
【核心功能】：
  承载观众在播放器与社区的所有互动数据：
  - VideoDanmaku: 视频弹幕实体（毫秒偏移、文字、颜色、字号）
  - UserLike: 用户对短剧点赞去重实体（保证一人一剧只计一次赞）
  - UserComment: 两级楼中楼评论树实体（支持主楼 root_id、父级 parent_id、@某人 reply_to_user_id）
  - CommentLike: 用户对单条评论点赞去重实体
  - UserWatchHistory: 观看历史足迹（记录播放到哪一集、第几秒，驱动首页续播条）
  - UserFollow: 用户与创作者相互关注关系实体
【对应前端】：
  - 视频播放器：frontend/src/views/PlayerView.vue (弹幕、点赞、评论树、打赏)
  - 首页续播：frontend/src/views/HomeView.vue (继续观看历史条)
  - 个人中心：frontend/src/views/UserProfileView.vue (我的足迹、点赞、关注列表)
==============================================================================
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class VideoDanmaku(Base):
    """
    【视频弹幕实体】
    记录观众在播放视频某一个精确秒数时发送的弹幕。
    支持在播放器画面中实时悬浮漂移渲染。
    """
    __tablename__ = "video_danmakus"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    episode_id: Mapped[str] = mapped_column(String(36), ForeignKey("video_episodes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 弹幕在视频中的时间轴偏移量（单位秒，例如 15.3 秒出现）
    time_offset: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    
    # 弹幕正文内容（限制 200 字以内）
    content: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # 弹幕字体颜色（十六进制 Hex 颜色码，如 #FFFFFF 白色，#00FF00 绿色）
    color: Mapped[str] = mapped_column(String(10), default="#FFFFFF")
    
    # 弹幕字号大小（像素，默认 18px）
    font_size: Mapped[int] = mapped_column(Integer, default=18)
    
    # 发送时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关联的用户与分集
    user: Mapped["User"] = relationship("User", back_populates="danmakus")
    episode: Mapped["VideoEpisode"] = relationship("VideoEpisode", back_populates="danmakus")

class UserLike(Base):
    """
    【短剧点赞去重实体】
    记录某个用户给哪部短剧点了赞。
    数据库联合唯一约束保证同一个用户对同一部短剧只能点赞一次，重复点击则为取消点赞。
    """
    __tablename__ = "user_likes"
    __table_args__ = (
        UniqueConstraint("user_id", "video_id", name="uq_user_video_like"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class UserComment(Base):
    """
    【两级楼中楼评论树实体】
    承载短剧的社交评论区体系：
    - 一级评论（主楼）：parent_id 与 root_id 均为 NULL
    - 二级评论（楼中楼回复）：root_id 指向所属的一级主楼评论 ID；parent_id 指向被回复的评论 ID
    - reply_to_user_id: 被回复的用户 ID（用于前端渲染 @某某）
    """
    __tablename__ = "user_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 直属父级评论 ID（回复谁就是谁的 ID，主楼则为 NULL）
    parent_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # 根级主楼评论 ID（用于把楼中楼所有回复按主楼聚合查询）
    root_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # 被回复人用户 ID（用于在界面上呈现“回复 @张三：”）
    reply_to_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # 评论正文
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 该条评论获得的获赞总数
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="comments")
    reply_to_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reply_to_user_id])

class CommentLike(Base):
    """
    【评论点赞去重实体】
    记录用户给哪一条评论点了赞。
    数据库联合唯一约束保证同一个用户对同一条评论只能点赞一次，再次点击则取消点赞。
    """
    __tablename__ = "comment_likes"
    __table_args__ = (
        UniqueConstraint("user_id", "comment_id", name="uq_user_comment_like"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    comment_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_comments.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class UserWatchHistory(Base):
    """
    【用户观看历史足迹实体】
    记录观众对某部短剧的最后观看进度。
    当用户再次打开该剧时，播放器可根据 last_episode_id 和 progress_seconds 自动跳秒续播。
    首页亦通过此表渲染“继续观看”悬浮横条。
    """
    __tablename__ = "user_watch_histories"
    __table_args__ = (
        UniqueConstraint("user_id", "video_id", name="uq_user_video_history"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 最后观看的分集 ID
    last_episode_id: Mapped[str] = mapped_column(String(36), nullable=False)
    
    # 播放停留在第几秒（浮点数）
    progress_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    
    # 更新时间戳（播放心跳定时刷新此字段）
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="histories")

class UserFollow(Base):
    """
    【用户与创作者关注关系实体】
    记录粉丝 follower_id 关注博主 following_id 的关注关系。
    """
    __tablename__ = "user_follows"
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_user_follower_following"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    follower_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    following_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    follower: Mapped["User"] = relationship("User", foreign_keys=[follower_id])
    following: Mapped["User"] = relationship("User", foreign_keys=[following_id])
