# -*- coding: utf-8 -*-
"""
==============================================================================
【模块名称】：CinemaAgent 标准 RAG 数据契约模块 (Datatypes)
【业务定位】：全系统 RAG 检索、图谱分析与智能体流转的核心数据结构定义
【全链路调用位置】：
  1. 页面来源：frontend/src/views/PlayerView.vue（AI伴聊/名场面定位）
  2. 后端入口：backend/app/api/endpoints/agent.py -> backend/app/services/agent_service.py
  3. 流水线核心：backend/app/services/rag/online/pipeline.py
  4. 多路检索器：backend/app/services/rag/online/hybrid_retriever.py
【核心数据契约】：
  - Document: 统一文档/台词切片契约（承载单条字幕台词、时间戳、向量得分与图谱事实）
  - QueryBundle: 用户检索请求实体包（承载用户提问、视频播放秒数、防剧透门控参数）
  - CRAGResult: Corrective RAG 质量校验决策包（包含置信度打分、动作裁决与审查理由）
  - RAGResponse: 完整 RAG 问答响应包（包含最终回答、参考切片、图谱实体与时间跳转锚点）
==============================================================================
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class Document:
    """
    【RAG 统一检索与推理文档切片契约 (Document)】
    
    承载一段从视频字幕、剧本或知识图谱中捞出来的真实剧情文本切片。
    它穿梭于离线切片入库、三路并发检索（向量+BM25+Neo4j）、Cross-Encoder 精排、
    CRAG 质量校验以及最终大模型 Prompt 拼装的全过程。
    
    【核心字段大白话详解】：
    - id (str): 
      切片唯一标识（UUID 字符串），在 MySQL 的 rag_chunks 表中对应主键 id，用于精准索引与去重。
    - text (str): 
      切片核心台词文本（例如：“顾千帆：你若再敢伤她半分，我定让你皇城司抄家绝户！”）。
      【现实意义】：这是供给大模型参考的最真实上下文，AI 必须基于这段文字回答，杜绝凭空胡编。
    - metadata (Dict[str, Any]): 
      附加元数据字典（包含短剧ID drama_id、所属知识库 corpus_id、角色名 speaker、场景 scene 等）。
      【现实意义】：用于多维度过滤或在前端管理中台展示切片属性。
    - embedding (Optional[List[float]]): 
      浮点数高维特征向量列表（如 768 维或 1536 维）。
      【现实意义】：由向量模型 (Embedder) 计算得出，用于在数学空间中与用户问题的向量计算余弦相似度。
    - score (float): 
      相关性匹配评分（范围 0.0 ~ 1.0，分数越高代表与用户提问越吻合）。
      【现实意义】：经过向量相似度计算、BM25 词频匹配、RRF 倒排融合与 Cross-Encoder 重排后的综合得分。
    - chunk_strategy (str): 
      离线切片时所采用的分块策略标识。
      【现实意义】：可选值包括：
        * "fixed": 固定字数切片（如每 250 字一块）；
        * "sliding": 滑动窗口切片（带前后重叠部分，保持上下文连贯）；
        * "dialogue": 基于角色对白轮次的切片；
        * "sentence": 句子/字幕窗口切片（单句时间轴台词）；
        * "graph_triple": 从 Neo4j 知识图谱提取的人物三元组事实。
    - episode_num (int): 
      该切片出现在第几集（整数，如 1 代表第 1 集）。
      【现实意义】：播放器防剧透的核心依据之一，绝不向观看第 1 集的用户泄露第 2 集切片。
    - start_sec (float): 
      该句台词在视频中出现的开始时间秒数（例如 85.5 代表 1 分 25.5 秒）。
      【现实意义】：用于在前端播放器渲染高亮名场面跳转胶囊（[01:25]），用户点击后播放器直接快进到此秒数！
    - end_sec (float): 
      该句台词在视频中结束的时间秒数（例如 90.0 代表 1 分 30 秒）。
    - parent_text (Optional[str]): 
      父级长文本上下文（可选）。
      【现实意义】：用于“小切片检索、大上下文推理”（Small-to-Big）机制：用小粒度句子匹配提高检索精准度，
      但实际喂给大模型时提供周围一大段完整的剧情段落，避免上下文断章取义。
    - source (str): 
      该切片是从哪个检索通道召回出来的（可选值："vector" 向量通路、"bm25" 词频通路、"graph" 图谱通路、"hybrid" 多路融合通路）。
      【现实意义】：用于在前端管理后台可观测性沙盒中追溯该切片的召回途径。
    """
    id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    score: float = 0.0
    chunk_strategy: str = "fixed"
    episode_num: int = 1
    start_sec: float = 0.0
    end_sec: float = 0.0
    parent_text: Optional[str] = None
    source: str = "vector"

    @property
    def time_tag(self) -> str:
        """
        格式化输出人类可读的分秒时间标签字符串，例如将 85.5 秒转换为 '01:25'。
        前端播放器可以直接把该标签显示在名场面定位胶囊按钮上。
        """
        m, s = divmod(int(self.start_sec), 60)
        return f"{m:02d}:{s:02d}"

    def to_dict(self) -> Dict[str, Any]:
        """
        将文档切片对象序列化为标准字典，供 JSON 格式化输出并在 SSE 长连接或 REST API 中直接推给前端。
        """
        return {
            "id": self.id,
            "text": self.text,
            "score": round(self.score, 4),
            "chunk_strategy": self.chunk_strategy,
            "episode_num": self.episode_num,
            "start_sec": self.start_sec,
            "end_sec": self.end_sec,
            "time_tag": self.time_tag,
            "source": self.source,
            "parent_text": self.parent_text,
            "metadata": self.metadata
        }


@dataclass
class QueryBundle:
    """
    【用户检索请求实体包 (QueryBundle)】
    
    封装了从前端播放器一路传递过来的提问文本与播放上下文参数。
    包含了用户提问内容、当前观看短剧ID、当前集数以及精确到秒的播放进度。
    
    【核心字段大白话详解】：
    - query_str (str): 
      观众在前端聊天输入框中输入的提问文本（如：“女主为什么在雨中给男主撑伞？”、“那个反派叫什么名字？”）。
    - drama_id (Optional[str]): 
      当前观看短剧专辑的唯一 ID（UUID 字符串），从前端播放器页面 URL 或短剧元数据中获取。
      【现实意义】：锁定检索范围，防止在检索《高冷千金》时误查出《八零赚钱养家》的剧本台词。
    - episode_num (int): 
      观众当前正在观看的集数（整数，默认为 1）。
      【现实意义】：用于跨集防剧透过滤，确保检索结果不超出观众当前的追剧进度。
    - current_sec (float): 
      观众当前视频播放的精确秒数（浮点数，如 65.5 代表 1 分 05.5 秒）。
      【数据来源】：直接取自前端 PlayerView.vue 中 HTML5 `<video>` 播放器的 `currentTime` 属性。
      【现实核心作用】：
        1. 极严苛防剧透屏障：凡是当前集中时间大于该秒数的台词一律拦截剔除；
        2. 名场面定位锚点：大模型将以该秒数为参照，推荐观众就近回头重温名场面。
    - filters (Dict[str, Any]): 
      扩展元数据过滤条件字典（例如：限定特定人物名称、限定特定场景标签）。
    - embedding (Optional[List[float]]): 
      对用户提问文本预先计算出的向量特征。如果已计算过，后续多步检索可直接复用，避免重复网络调用。
    - top_k (int): 
      期望召回并最终喂给大模型的最优质切片数量上限（默认 3 条），防止 Prompt 膨胀导致推理变慢。
    """
    query_str: str
    drama_id: Optional[str] = None
    episode_num: int = 1
    current_sec: float = 0.0
    filters: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    top_k: int = 3

    @property
    def current_time_tag(self) -> str:
        """
        将观众当前的播放秒数格式化为人类直观的分秒字符串，如 65.5 秒转为 '01:05'。
        """
        m, s = divmod(int(self.current_sec), 60)
        return f"{m:02d}:{s:02d}"


@dataclass
class CRAGResult:
    """
    【Corrective RAG (CRAG) 质量校验决策包】
    
    在多路检索与精排完成后，专门用于对召回切片进行自我反思与质量判决。
    确保召回的台词切片真正能够回答观众的问题，杜绝把风马牛不相及的台词塞给大模型导致胡言乱语。
    
    【核心字段大白话详解】：
    - action (str): 
      CRAG 质量评估给出的行动裁决指令。取值分为三种情况：
      1. "CORRECT"（完全对题，置信度高）：召回的台词非常吻合提问，直接放行进入大模型生成回答；
      2. "AMBIGUOUS"（模棱两可，置信度一般）：台词部分沾边但不够充分，系统会自动从 Neo4j 知识图谱补充更多 2-hop 关系信息；
      3. "INCORRECT"（风马牛不相及，置信度极低）：检索完全跑偏，系统自动触发 Query 改写或降级为通用闲聊口吻，绝不生搬硬套。
    - confidence_score (float): 
      CRAG 综合质量评分（0.0 ~ 1.0，如 0.85 代表 85% 确定切片对题）。
    - reason (str): 
      做出该裁决的客观原因解释（例如：“召回台词高度吻合提问实体与场景，时间轴符合防剧透约束”）。
      【现实意义】：该原因会在管理后台的“RAG 知识中台 & 算法评测”大屏中以可视化形式展现，方便运营人员调优。
    - filtered_documents (List[Document]): 
      经过 CRAG 门禁严格核验后，最终获准保留并送交大模型的优质文档切片列表。
    """
    action: str  # "CORRECT", "AMBIGUOUS", "INCORRECT"
    confidence_score: float
    reason: str
    filtered_documents: List[Document] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典，供可观测性跟踪与管理后台图表渲染。
        """
        return {
            "action": self.action,
            "confidence_score": round(self.confidence_score, 4),
            "reason": self.reason,
            "document_count": len(self.filtered_documents)
        }


@dataclass
class RAGResponse:
    """
    【统一 RAG 问答最终响应实体包】
    
    封装了经过检索、反思、精排与大模型推理后生成的最终成果。
    可直接用于同步 API 返回，也可作为自动化测试与评测套件（Ragas）的标准化输入。
    
    【核心字段大白话详解】：
    - query (str): 
      用户原始提问文本。
    - answer (str): 
      大模型基于真实剧情台词生成的最终回答正文。
    - retrieved_documents (List[Document]): 
      本次问答实际采纳的参考台词切片列表（包含精确时间戳与原文字句）。
    - graph_entities (List[Dict[str, Any]]): 
      从 Neo4j 知识图谱中激活并参与推理的人物节点与关系网络数据（如主角夫妻、敌对势力等）。
    - time_anchors (List[Dict[str, Any]]): 
      AI 分析提炼出的关键时间锚点列表。
      【现实意义】：前端播放器接收到后，会自动在聊天窗中渲染出可点击的快进胶囊卡片，点击即可瞬间定位名场面！
    - crag_status (str): 
      本次问答经历的 CRAG 评估状态（"CORRECT" / "AMBIGUOUS" / "INCORRECT"）。
    - model_used (str): 
      本次问答实际调用的底层大模型名称与提供商（例如 "ollama:deepseek-r1:1.5b"）。
    """
    query: str
    answer: str
    retrieved_documents: List[Document] = field(default_factory=list)
    graph_entities: List[Dict[str, Any]] = field(default_factory=list)
    time_anchors: List[Dict[str, Any]] = field(default_factory=list)
    crag_status: str = "CORRECT"
    model_used: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """
        将完整问答响应序列化为标准字典，方便 JSON 序列化传输或落库记录。
        """
        return {
            "query": self.query,
            "answer": self.answer,
            "retrieved_documents": [doc.to_dict() for doc in self.retrieved_documents],
            "graph_entities": self.graph_entities,
            "time_anchors": self.time_anchors,
            "crag_status": self.crag_status,
            "model_used": self.model_used
        }
