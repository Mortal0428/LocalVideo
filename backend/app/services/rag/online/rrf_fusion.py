"""
CinemaAgent 工业级模块化 RAG 倒数排名融合算法 (RRF Fusion)
公式: score(d) = Σ [ w_c / (k + rank_c(d)) ]
融合向量召回、BM25 词汇召回与 Neo4j 知识图谱事实，实现多通道结果的稳健统一排序。
"""

import logging
from typing import Dict, List, Any, Optional
from app.services.rag.core.datatypes import Document

logger = logging.getLogger(__name__)

DEFAULT_K = 60
DEFAULT_CHANNEL_WEIGHTS = {
    "vector": 1.0,
    "bm25": 0.85,
    "graph": 1.1
}


class RRFFusion:
    """
    倒数排名融合器 (Reciprocal Rank Fusion)
    """
    def __init__(self, k: int = DEFAULT_K, channel_weights: Optional[Dict[str, float]] = None):
        self.k = k
        self.weights = channel_weights or dict(DEFAULT_CHANNEL_WEIGHTS)

    def fuse(
        self,
        channel_results: Dict[str, List[Document]],
        top_n: int = 10
    ) -> List[Document]:
        """
        融合多通道检索结果
        channel_results: {"vector": [...], "bm25": [...], "graph": [...]}
        """
        doc_scores: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}
        doc_sources: Dict[str, set] = {}

        for channel_name, docs in channel_results.items():
            weight = self.weights.get(channel_name, 1.0)
            for rank_0, doc in enumerate(docs):
                rank = rank_0 + 1  # 1-indexed
                # 键值去重: 优先 id，若无则使用前 60 字签名
                doc_key = doc.id if doc.id else doc.text[:60]
                
                rrf_increment = weight / (self.k + rank)
                doc_scores[doc_key] = doc_scores.get(doc_key, 0.0) + rrf_increment

                if doc_key not in doc_map:
                    doc_map[doc_key] = doc
                    doc_sources[doc_key] = {channel_name}
                else:
                    doc_sources[doc_key].add(channel_name)

        # 归一化得分至 [0.0, 1.0]
        max_score = max(doc_scores.values()) if doc_scores else 1.0
        sorted_keys = sorted(doc_scores.keys(), key=lambda k: doc_scores[k], reverse=True)

        fused_documents: List[Document] = []
        for key in sorted_keys[:top_n]:
            base_doc = doc_map[key]
            norm_score = float(doc_scores[key] / max_score)
            fused_sources = "+".join(sorted(doc_sources.get(key, [])))
            
            fused_doc = Document(
                id=base_doc.id,
                text=base_doc.text,
                metadata=dict(base_doc.metadata),
                embedding=base_doc.embedding,
                score=round(norm_score, 4),
                chunk_strategy=base_doc.chunk_strategy,
                episode_num=base_doc.episode_num,
                start_sec=base_doc.start_sec,
                end_sec=base_doc.end_sec,
                parent_text=base_doc.parent_text,
                source=fused_sources
            )
            fused_documents.append(fused_doc)

        return fused_documents


rrf_fusion = RRFFusion()
