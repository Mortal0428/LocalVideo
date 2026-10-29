# -*- coding: utf-8 -*-
"""
==============================================================================
【模型文件】：backend/app/models/rag_corpus.py
【业务定位】：高级模块化 RAG 知识库分类、语料文档、切片块与算法评测模型
【对应表名】：rag_corpus_categories, rag_corpora, rag_chunks, rag_eval_runs
【核心功能】：
  支撑影视知识库与大模型增强检索的核心数据底座：
  - RAGCorpusCategory: 知识库多级分类（短剧世界观、人物设定、剧本分集、原声台词）
  - RAGCorpus: 知识文档原始资产（支持上传剧本 TXT/SRT 字幕/Markdown 设定）
  - RAGChunk: 智能切片块（支持固定长度、滑动窗口、句子窗口、父子切片等策略，含向量 Embedding）
  - RAGEvalRun: RAGAS 四维基准评测历史（真实性 Faithfulness、相关性 Relevance、精度 Precision、召回率 Recall）
【对应前端】：
  - RAG 知识中台大屏：frontend/src/components/CinemaAgentRagCenter.vue
  - 播放器剧情伴聊与台词跳秒：frontend/src/views/PlayerView.vue
==============================================================================
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey, Index
from app.core.database import Base

class RAGCorpusCategory(Base):
    """
    【知识库分类实体】
    用于对不同短剧或全平台的知识文档进行树状分类管理。
    """
    __tablename__ = "rag_corpus_categories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="分类主键 ID")
    drama_id = Column(String(64), nullable=True, index=True, comment="所属短剧 ID（为 NULL 表示全平台通用分类）")
    name = Column(String(64), nullable=False, comment="分类名称：如短剧大纲、人物小传、分集剧本、时间轴台词")
    parent_id = Column(String(36), nullable=True, comment="父级分类 ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

class RAGCorpus(Base):
    """
    【知识文档资产实体】
    代表导入平台的一份完整剧本文件、SRT 字幕文件或小说设定。
    """
    __tablename__ = "rag_corpora"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="知识文档全局唯一 ID")
    drama_id = Column(String(64), nullable=True, index=True, comment="关联短剧 ID")
    category_id = Column(String(36), ForeignKey("rag_corpus_categories.id", ondelete="SET NULL"), nullable=True, index=True, comment="分类 ID")
    file_path = Column(String(512), nullable=True, comment="原始上传文件本地存储绝对路径")
    title = Column(String(255), nullable=False, comment="知识文档标题")
    doc_type = Column(String(32), default="script", comment="文档类型: script(剧本), srt_subtitle(字幕), biography(设定小传)")
    content = Column(Text, nullable=False, comment="原始全量纯文本正文")
    metadata_json = Column(Text, nullable=True, comment="扩展元数据 JSON 字典")
    chunk_count = Column(Integer, default=0, comment="切片生成的 Chunk 数量")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

class RAGChunk(Base):
    """
    【知识文本切片块实体】
    知识文档经过离线流水线切片后生成的细粒度文本块。
    包含文本内容、所属剧集、秒数时间轴、向量嵌入与 Token 计数。
    支持向量相似度检索、BM25 全文检索与 Neo4j 实体关联检索三路融合。
    """
    __tablename__ = "rag_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="切片唯一 UUID")
    corpus_id = Column(String(36), ForeignKey("rag_corpora.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属母文档 ID")
    drama_id = Column(String(64), nullable=True, index=True, comment="所属短剧 ID")
    episode_num = Column(Integer, default=1, index=True, comment="所属分集序号（用于防剧透时间门控）")
    start_sec = Column(Float, default=0.0, index=True, comment="时间轴起始秒数")
    end_sec = Column(Float, default=0.0, comment="时间轴结束秒数")
    chunk_index = Column(Integer, default=0, comment="在文档内部的切片序号")
    chunk_strategy = Column(String(32), default="fixed", comment="切片策略: fixed(固定长), sliding_window(滑动窗口), sentence_window(句子窗口), parent_child(父子切片)")
    content = Column(Text, nullable=False, comment="该切片的正文纯文本")
    parent_content = Column(Text, nullable=True, comment="父级大上下文正文（父子切片策略专用）")
    embedding_json = Column(Text, nullable=True, comment="向量模型生成的稠密向量 JSON 列表")
    token_count = Column(Integer, default=0, comment="切片估算 Token 数量")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

class RAGEvalRun(Base):
    """
    【RAGAS 算法四维评测运行实体】
    记录每一次 RAG 自动化评测大模型评测跑分的战报与四项黄金指标。
    """
    __tablename__ = "rag_eval_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="评测任务运行 ID")
    drama_id = Column(String(64), nullable=True, index=True, comment="评测针对的短剧 ID")
    drama_title = Column(String(255), nullable=True, comment="短剧标题")
    status = Column(String(32), default="COMPLETED", index=True, comment="任务状态: PENDING/RUNNING/COMPLETED/FAILED")
    progress = Column(Integer, default=100, comment="当前进度百分比 0-100")
    current_step = Column(String(255), default="已完成", comment="当前正在执行的步骤描述")
    logs_json = Column(Text, nullable=True, comment="实时执行日志 JSON 数组")
    name = Column(String(128), nullable=False, comment="评测批次名称")
    judge_model = Column(String(128), nullable=False, comment="担任裁判的 LLM 模型标识")
    
    # RAGAS 四项黄金评测指标 (0.0 ~ 1.0)
    faithfulness = Column(Float, default=0.0, comment="忠实度 (Faithfulness: 回答是否严格忠实于检索到的剧本上下文，无虚构幻觉)")
    answer_relevance = Column(Float, default=0.0, comment="回答相关性 (Answer Relevance: 回答是否切中用户的问题要害)")
    context_precision = Column(Float, default=0.0, comment="上下文精度 (Context Precision: 检索回来的切片中真正有用信息的占比)")
    context_recall = Column(Float, default=0.0, comment="上下文召回率 (Context Recall: 标答所需关键信息是否都被成功检索召回)")
    f1_score = Column(Float, default=0.0, comment="综合四维调和均值 F1 跑分")
    
    sample_count = Column(Integer, default=0, comment="测试样本问答对数量")
    latency_ms = Column(Float, default=0.0, comment="平均单题推理评测耗时 (毫秒)")
    details_json = Column(Text, nullable=True, comment="每一题的详尽问答对比与扣分原因 JSON")
    created_at = Column(DateTime, default=datetime.now, comment="评测启动时间")
