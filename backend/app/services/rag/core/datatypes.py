"""
CinemaAgent 标准 RAG 数据契约模块 (Datatypes)
定义全系统通用的 Document、QueryBundle、CRAGResult 与 RAGResponse 数据载体。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class Document:
    """
    RAG 统一检索与推理文档切片契约
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
    source: str = "vector"  # vector, bm25, graph, hybrid

    @property
    def time_tag(self) -> str:
        """格式化输出分秒标签 [mm:ss]"""
        m, s = divmod(int(self.start_sec), 60)
        return f"{m:02d}:{s:02d}"

    def to_dict(self) -> Dict[str, Any]:
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
    用户检索请求实体包
    包含用户问题、短剧ID、当前集数与秒数（防剧透门控核心依据）
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
        m, s = divmod(int(self.current_sec), 60)
        return f"{m:02d}:{s:02d}"


@dataclass
class CRAGResult:
    """
    Corrective RAG 质量校验结果
    """
    action: str  # "CORRECT", "AMBIGUOUS", "INCORRECT"
    confidence_score: float
    reason: str
    filtered_documents: List[Document] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "confidence_score": round(self.confidence_score, 4),
            "reason": self.reason,
            "document_count": len(self.filtered_documents)
        }


@dataclass
class RAGResponse:
    """
    统一 RAG 推理问答响应包
    """
    query: str
    answer: str
    retrieved_documents: List[Document] = field(default_factory=list)
    graph_entities: List[Dict[str, Any]] = field(default_factory=list)
    time_anchors: List[Dict[str, Any]] = field(default_factory=list)
    crag_status: str = "CORRECT"
    model_used: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "answer": self.answer,
            "retrieved_documents": [doc.to_dict() for doc in self.retrieved_documents],
            "graph_entities": self.graph_entities,
            "time_anchors": self.time_anchors,
            "crag_status": self.crag_status,
            "model_used": self.model_used
        }
