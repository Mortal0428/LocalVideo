# -*- coding: utf-8 -*-
"""
==============================================================================
【模型文件】：backend/app/models/review.py
【业务定位】：智能合规风控、人工审核工单、敏感词库与 AI 巡检日志模型
【对应表名】：content_reviews, sensitive_words, sensitive_word_proposals, interaction_inspection_logs
【核心功能】：
  构筑平台内容合规治理防线：
  - ContentReview: 短剧与视频内容审核工单（排队中、已通过、已驳回）
  - SensitiveWord: 平台敏感词库（涉政、暴恐、色情、违禁等分级拦截）
  - SensitiveWordProposal: 4 号合规审查智能体巡检时自主推荐的新增敏感词提案
  - InteractionInspectionLog: AI 批量巡检社区弹幕与评论的历史归档报告
【对应前端】：
  - 安全与合规大屏：frontend/src/views/AdminView.vue (合规审核 Tab)
==============================================================================
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class ContentReview(Base):
    """
    【短剧与视频内容审核工单实体】
    创作者提交短剧或修改剧情后，系统自动生成该审核工单。
    由管理员或合规审核员在管理后台进行人机协同判定。
    """
    __tablename__ = "content_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 提交申请的创作者用户 ID
    submitter_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 审核状态：PENDING(待审核), APPROVED(审核通过并上架), REJECTED(驳回退回草稿)
    review_status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)
    
    # AI 预审初筛意见或审核员人工审批意见说明
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 最终裁决的审核人员 ID
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # AI 智能预审分析报告详情（JSON 格式，包含违规置信度、检测到的关键词）
    ai_audit_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

class SensitiveWord(Base):
    """
    【平台敏感词库实体】
    全站弹幕与评论过滤的基础词库。
    观众发送弹幕或评论时，服务端基于 DFA 算法匹配敏感词并阻断或替换为星号。
    """
    __tablename__ = "sensitive_words"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 敏感词词条（全局唯一）
    word: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    # 敏感级别：HIGH(高危违禁直接拦截), MEDIUM(中度替换为星号), LOW(低度记录巡检日志)
    level: Mapped[str] = mapped_column(String(20), default="HIGH")
    
    # 分类标签：政治、色情、暴恐、广告、辱骂、违禁
    category: Mapped[str] = mapped_column(String(50), default="违禁")
    
    # 创建录入该词的管理员 ID
    creator_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class SensitiveWordProposal(Base):
    """
    【AI 敏感词自主发现提案实体】
    4 号合规审查智能体（Moderation Worker）在后台定期巡检海量社区弹幕和评论时，
    通过大模型语义理解发现的新兴变异黑话、谐音梗与违禁变种词，自动在此发起提案，待管理员一键审批入库。
    """
    __tablename__ = "sensitive_word_proposals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    word: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), default="违禁")
    level: Mapped[str] = mapped_column(String(20), default="HIGH")
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(32), default="danmaku")
    source_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

class InteractionInspectionLog(Base):
    """
    【AI 巡检批次历史归档实体】
    记录每一次 AI 自动化巡检弹幕和评论的战报、检测条数、违规命中数与耗时。
    """
    __tablename__ = "interaction_inspection_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id: Mapped[str] = mapped_column(String(64), index=True)
    target_type: Mapped[str] = mapped_column(String(32), default="comment")
    total_inspected: Mapped[int] = mapped_column(Integer, default=0)
    violation_count: Mapped[int] = mapped_column(Integer, default=0)
    suggested_words_count: Mapped[int] = mapped_column(Integer, default=0)
    cost_ms: Mapped[int] = mapped_column(Integer, default=0)
    llm_status: Mapped[str] = mapped_column(String(64), default="COMPLETED")
    report_summary_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
