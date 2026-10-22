"""
CinemaAgent 工业级模块化 RAG 数据模型
包含短剧知识库资产 (RAGCorpus)、切片索引表 (RAGChunk) 与算法评测跑分表 (RAGEvalRun)。
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey, Index
from app.core.database import Base


class RAGCorpus(Base):
    __tablename__ = "rag_corpora"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="知识库唯一主键")
    drama_id = Column(String(64), nullable=True, index=True, comment="关联短剧ID")
    title = Column(String(255), nullable=False, comment="知识库文档标题")
    doc_type = Column(String(32), default="script", comment="文档类别: script(剧本), srt_subtitle(字幕), biography(设定人物志)")
    content = Column(Text, nullable=False, comment="原始全量文本")
    metadata_json = Column(Text, nullable=True, comment="元数据JSON")
    chunk_count = Column(Integer, default=0, comment="切片总数")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class RAGChunk(Base):
    __tablename__ = "rag_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="切片主键UUID")
    corpus_id = Column(String(36), ForeignKey("rag_corpora.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属知识库ID")
    drama_id = Column(String(64), nullable=True, index=True, comment="关联短剧ID")
    episode_num = Column(Integer, default=1, index=True, comment="集数(用于防剧透时序门控)")
    start_sec = Column(Float, default=0.0, index=True, comment="起始播放秒数")
    end_sec = Column(Float, default=0.0, comment="结束播放秒数")
    chunk_index = Column(Integer, default=0, comment="切片序号")
    chunk_strategy = Column(String(32), default="fixed", comment="切片策略: fixed, sliding_window, sentence_window, parent_child")
    content = Column(Text, nullable=False, comment="检索用文本块")
    parent_content = Column(Text, nullable=True, comment="扩展父级上下文")
    embedding_json = Column(Text, nullable=True, comment="稠密向量序列化JSON")
    token_count = Column(Integer, default=0, comment="字数或Token估算值")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")


class RAGEvalRun(Base):
    __tablename__ = "rag_eval_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="评测批次ID")
    name = Column(String(128), nullable=False, comment="评测任务名称")
    judge_model = Column(String(128), nullable=False, comment="评测裁判模型标识")
    faithfulness = Column(Float, default=0.0, comment="忠实度(Faithfulness)")
    answer_relevance = Column(Float, default=0.0, comment="回答相关性(Answer Relevance)")
    context_precision = Column(Float, default=0.0, comment="上下文精准率(Context Precision)")
    context_recall = Column(Float, default=0.0, comment="上下文召回率(Context Recall)")
    f1_score = Column(Float, default=0.0, comment="综合四维均分/F1")
    sample_count = Column(Integer, default=0, comment="样本基准数")
    latency_ms = Column(Float, default=0.0, comment="平均评测耗时毫秒")
    details_json = Column(Text, nullable=True, comment="单题明细分析与对比详情")
    created_at = Column(DateTime, default=datetime.utcnow, comment="评测时间")
