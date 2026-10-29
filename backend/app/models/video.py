# -*- coding: utf-8 -*-
"""
==============================================================================
【模型文件】：backend/app/models/video.py
【业务定位】：全平台短剧主档案、分集切片、SRT字幕时间轴与首页焦点轮播图模型
【对应表名】：videos, video_episodes, video_subtitle_timelines, system_carousels
【核心功能】：
  构建平台短剧的多层级资产体系：
  - Video: 短剧总信息（剧名、简介、主封面、多张画报海报、热度值、总获赞与投币）
  - VideoEpisode: 每一分集的物理视频切片、转码状态、时长与 m3u8 地址
  - VideoSubtitleTimeline: 毫秒级剧本字幕时间轴，支持 AI 剧情高能台词定位与 RAG 检索
  - SystemCarousel: 首页大厅 16:9 沉浸式焦点轮播图
【对应前端】：
  - 首页精选大厅：frontend/src/views/HomeView.vue
  - 视频播放器：frontend/src/views/PlayerView.vue
  - 创作者工作台：frontend/src/views/CreatorStudioView.vue
  - 管理后台短剧与轮播图运营：frontend/src/views/AdminView.vue
==============================================================================
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, BigInteger, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Video(Base):
    """
    【短剧总档案表 ORM 实体】
    代表一部完整的短剧（例如：《逆袭从退婚开始》全 50 集）。
    记录短剧的全局属性、创作者所属、全网热度指标与关联的分集。
    """
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 创作者外键：关联 users.id，若创作者被级联删除则关联短剧同步清理
    creator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 短剧主标题：用于搜索和首页卡片呈现
    title: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    
    # 短剧故事梗概与剧情简介
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 系统默认提取封面直链
    cover_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # 题材分类：如“都市逆袭”、“战神归来”、“穿越古风”、“甜宠虐恋”
    category: Mapped[str] = mapped_column(String(50), default="短剧", index=True)
    
    # 上架状态：PUBLISHED(正常发布), HIDDEN(隐藏下架), DRAFT(草稿箱), BLOCKED(风控封禁)
    status: Mapped[str] = mapped_column(String(20), default="PUBLISHED", index=True)
    
    # 创作者或管理员自定义上传的高清竖屏封面
    custom_cover_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # 多张画报海报 JSON 列表：用于首页卡片和后台详情的焦点画报多图轮播
    extra_images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 短剧总集数统计
    total_episodes: Mapped[int] = mapped_column(Integer, default=1)
    
    # 累计播放总次数
    view_count: Mapped[int] = mapped_column(BigInteger, default=0)
    
    # 累计点赞数：用户点赞时实时自增/自减
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 累计获投金币数：观众在播放器投币打赏时增加
    coin_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 智能综合热度分：根据 view_count*1 + like_count*3 + coin_count*10 综合加权计算，用于首页飙升榜排序
    heat_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    
    # 创建与更新时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 级联关系：创作者多对一，分集列表一对多（按集数升序排列）
    creator: Mapped["User"] = relationship("User", back_populates="videos")
    episodes: Mapped[List["VideoEpisode"]] = relationship(
        "VideoEpisode", back_populates="video", cascade="all, delete-orphan", order_by="VideoEpisode.episode_num"
    )

class VideoEpisode(Base):
    """
    【短剧单集切片实体】
    代表短剧的具体某一集（如第 1 集、第 2 集），包含视频源路径与播放转码状态。
    """
    __tablename__ = "video_episodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 第几集序号：1, 2, 3...
    episode_num: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # 单集副标题：如“第一集 龙王入赘”
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    
    # 原始视频存储路径（本地磁盘绝对路径或网盘相对路径）
    raw_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # 转码切片后的 HLS 流媒体播放清单地址
    m3u8_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # 视频时长（秒）
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    
    # 转码流水线状态：QUEUED(排队中), PROCESSING(转码中), READY(就绪可播), FAILED(转码失败)
    transcode_status: Mapped[str] = mapped_column(String(20), default="QUEUED", index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 级联关系：所属短剧、挂载弹幕列表、挂载台词字幕轴
    video: Mapped["Video"] = relationship("Video", back_populates="episodes")
    danmakus: Mapped[List["VideoDanmaku"]] = relationship(
        "VideoDanmaku", back_populates="episode", cascade="all, delete-orphan"
    )
    subtitles: Mapped[List["VideoSubtitleTimeline"]] = relationship(
        "VideoSubtitleTimeline", back_populates="episode", cascade="all, delete-orphan", order_by="VideoSubtitleTimeline.start_seconds"
    )

class VideoSubtitleTimeline(Base):
    """
    【字幕台词与高能剧情时间轴】
    细致到秒级的时间轴台词切片，用于支持：
    1. 播放器画面精准字幕对齐
    2. RAG 知识检索（观众提问“男主在哪一集说了这句名言”，AI 瞬间检索定位跳秒）
    3. 高能片段（is_climax）标记与快进跳跃
    """
    __tablename__ = "video_subtitle_timelines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    episode_id: Mapped[str] = mapped_column(String(36), ForeignKey("video_episodes.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 台词起始与结束时间戳（浮点秒数，例如 12.5 秒至 15.8 秒）
    start_seconds: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    end_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    
    # 说话人角色名：如“陈玄”、“苏傲雪”、“反派保镖”
    speaker: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # 台词文本正文
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 是否为高能名场面/剧情爆点：True 时前端播放器进度条呈现高能打点小图标
    is_climax: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    episode: Mapped["VideoEpisode"] = relationship("VideoEpisode", back_populates="subtitles")

class SystemCarousel(Base):
    """
    【首页焦点大画报轮播图实体】
    运营人员在后台配置的 16:9 高清全宽轮播海报，直通推荐短剧播放。
    """
    __tablename__ = "system_carousels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # 轮播宣传角标标签：如“今日热度 TOP 1”、“口碑王炸”、“高甜爆笑”
    tag: Mapped[str] = mapped_column(String(50), default="今日焦点推荐")
    
    # 16:9 横版高清壁纸封面地址
    cover_url: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # 关联直达短剧 ID：用户点击轮播图直接跳转到该剧播放页
    video_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # 排序权重（数字越小越靠前）
    sort_order: Mapped[int] = mapped_column(Integer, default=1)
    
    # 是否上架展示
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # 单张轮播停留时长（秒）
    duration_seconds: Mapped[int] = mapped_column(Integer, default=5)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
