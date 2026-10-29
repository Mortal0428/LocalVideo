# -*- coding: utf-8 -*-
"""
==============================================================================
【模型导出中枢】：backend/app/models/__init__.py
【架构定位】：全平台 SQLAlchemy ORM 数据模型统一导出与生命周期挂载中枢
【包含数据模型】：
  1. 用户与权限：User (用户账户、角色权限、VIP、创作者与审核员资质)
  2. 媒体与内容：
     - Video (短剧总档案、海报画报、综合热度分)
     - VideoEpisode (短剧单集物理切片、转码流状态、HLS/m3u8 直链)
     - VideoSubtitleTimeline (毫秒级台词剧本时间轴、高能切片、RAG 对齐)
     - SystemCarousel (首页 16:9 沉浸式全宽焦点大图轮播)
  3. 社区与互动：
     - VideoDanmaku (弹幕图层毫秒偏移切片)
     - UserLike (短剧点赞去重)
     - UserComment (两级楼中楼评论树体系)
     - CommentLike (单条评论点赞去重)
     - UserWatchHistory (历史观看足迹与断点秒数)
     - UserFollow (用户与创作者双向关注)
  4. 资产与经济：
     - UserCoinWallet (虚拟金币钱包与防重签到)
     - UserCoinTransaction (双向收支明细资金流水)
     - VideoCoinTip (短剧打赏记录与热度联动)
     - RedemptionCode (口令卡密核销系统)
  5. 多级收藏体系：
     - FavoriteFolder (自定义命名收藏夹、公开/私密、默认保护)
     - FavoriteItem (短剧收藏归档条目)
  6. 消息与全能通知天窗：
     - SystemAnnouncement (全员系统广播公告)
     - UserNotification (三分类个人通知：公告、回复、点赞)
  7. 智能合规风控：
     - ContentReview (短剧内容审核人机协同工单)
     - SensitiveWord (违规敏感词库)
     - SensitiveWordProposal (AI 巡检自主发现新敏感词提案)
     - InteractionInspectionLog (AI 巡检历史归档报告)
  8. 高级模块化 RAG 知识中枢：
     - RAGCorpusCategory (知识库多级分类)
     - RAGCorpus (知识文档资产)
     - RAGChunk (智能切片与 Embedding 向量块)
     - RAGEvalRun (RAGAS 四维基准评测历史)
  9. 多智能体战队（Agent Fleet）：
     - AgentConfig (9 大专业智能体单体配置)
     - AgentModelCategoryConfig (3 大分类组模型热治理)
     - SkillConfig (可插拔技能库 SKILL.md 注册)
     - AgentBlackboardSession (多智能体协同共享黑板记忆)
     - UserCompanionPet (用户专属 AI 观影伴侣)
     - ModerationInterruptQueue (HITL 人机回环高危介入队列)
     - AgentTelemetryLog (智能体实时遥测指标流水)
     - AgentEvolutionProposal (自主演化技能提议)
     - SkillOperationLog (技能操作审计日志)
  10. 系统全局与审计：
     - SystemConfig (全局键值动态热配置表，支持底座与壁纸毫秒热重载)
     - SystemAuditLog (系统全链路安全审计日志流)
==============================================================================
"""
from app.core.database import Base
from app.models.user import User
from app.models.video import Video, VideoEpisode, VideoSubtitleTimeline, SystemCarousel
from app.models.interaction import (
    VideoDanmaku,
    UserLike,
    UserComment,
    CommentLike,
    UserWatchHistory,
    UserFollow,
)
from app.models.review import (
    ContentReview,
    SensitiveWord,
    SensitiveWordProposal,
    InteractionInspectionLog,
)
from app.models.system_config import SystemConfig
from app.models.favorite import FavoriteFolder, FavoriteItem
from app.models.coin import (
    UserCoinWallet,
    UserCoinTransaction,
    VideoCoinTip,
    RedemptionCode,
)
from app.models.notification import SystemAnnouncement, UserNotification
from app.models.rag_corpus import (
    RAGCorpusCategory,
    RAGCorpus,
    RAGChunk,
    RAGEvalRun,
)
from app.models.audit_log import SystemAuditLog
from app.models.agent_hub import (
    AgentConfig,
    AgentModelCategoryConfig,
    SkillConfig,
    AgentBlackboardSession,
    UserCompanionPet,
    ModerationInterruptQueue,
    AgentTelemetryLog,
    AgentEvolutionProposal,
    SkillOperationLog,
)

__all__ = [
    "Base",
    "User",
    "Video",
    "VideoEpisode",
    "VideoSubtitleTimeline",
    "SystemCarousel",
    "VideoDanmaku",
    "UserLike",
    "UserComment",
    "CommentLike",
    "UserWatchHistory",
    "UserFollow",
    "ContentReview",
    "SensitiveWord",
    "SensitiveWordProposal",
    "InteractionInspectionLog",
    "SystemConfig",
    "FavoriteFolder",
    "FavoriteItem",
    "UserCoinWallet",
    "UserCoinTransaction",
    "VideoCoinTip",
    "RedemptionCode",
    "SystemAnnouncement",
    "UserNotification",
    "RAGCorpusCategory",
    "RAGCorpus",
    "RAGChunk",
    "RAGEvalRun",
    "SystemAuditLog",
    "AgentConfig",
    "AgentModelCategoryConfig",
    "SkillConfig",
    "AgentBlackboardSession",
    "UserCompanionPet",
    "ModerationInterruptQueue",
    "AgentTelemetryLog",
    "AgentEvolutionProposal",
    "SkillOperationLog",
]
