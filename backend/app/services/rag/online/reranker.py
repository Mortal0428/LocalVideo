"""
CinemaAgent 工业级模块化 RAG 深度重排序引擎 (Cross-Encoder Reranker)
对召回融合后的候选文档集合进行深层语义交互打分，精选最终 Top-K 上下文切片。
"""

import jieba
import logging
from typing import List, Dict, Any, Optional
from app.services.rag.core.datatypes import Document
from app.services.rag.offline.embedder import embedder, cosine_similarity

logger = logging.getLogger(__name__)


STOP_WORDS = {
    "的", "了", "和", "是", "在", "与", "为", "谁", "什么", "吗", "呢",
    "啊", "这", "那", "有", "？", "！", "，", "。", "、", "?", "!", ",", ".",
    "：", ":", "个", "怎么", "为何", "哪", "哪个", "到底"
}


class CrossEncoderReranker:
    """
    语义交叉重排序器 (Cross-Encoder Reranker)
    综合字符级重合、关键词覆盖度、向量相似度与时间邻近度完成精排。
    """
    def __init__(self):
        pass

    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 3,
        current_sec: Optional[float] = None
    ) -> List[Document]:
        """对候选文档进行细粒度重排序并截断至 Top-K"""
        if not documents:
            return []

        clean_tokens = [t.strip().lower() for t in jieba.lcut(query) if t.strip()]
        meaningful_tokens = [t for t in clean_tokens if t not in STOP_WORDS]
        query_set = set(meaningful_tokens or clean_tokens)
        q_chars = set(c for c in query.lower() if c.isalnum() and c not in STOP_WORDS)
        query_vec = embedder.embed_text(query)

        scored_docs: List[Document] = []
        for doc in documents:
            target_text = f"{doc.text} {doc.parent_text or ''}"
            doc_tokens = set([t.strip().lower() for t in jieba.lcut(target_text) if t.strip()])
            doc_chars = set(c for c in target_text.lower() if c.isalnum())
            
            # 1. 词汇与字符覆盖率 (Lexical Coverage)
            overlap_count = len(query_set.intersection(doc_tokens))
            word_coverage = (overlap_count / len(query_set)) if query_set else 0.0
            char_coverage = (len(q_chars.intersection(doc_chars)) / len(q_chars)) if q_chars else 0.0
            lexical_score = word_coverage * 0.60 + char_coverage * 0.40

            # 2. 向量语义相似度
            doc_vec = doc.embedding if (doc.embedding and len(doc.embedding) > 0) else embedder.embed_text(doc.text)
            vector_sim = max(0.0, cosine_similarity(query_vec, doc_vec))

            # 3. 基础 RRF 分数继承
            base_score = doc.score

            # 4. 时间轴邻近度加权 (Temporal Proximity)
            time_proximity_boost = 0.0
            if current_sec is not None and doc.start_sec > 0:
                time_diff = abs(doc.start_sec - current_sec)
                if time_diff < 30.0:
                    time_proximity_boost = 0.15
                elif time_diff < 90.0:
                    time_proximity_boost = 0.08

            # 综合重排打分公式
            final_rerank_score = (
                lexical_score * 0.45 +
                vector_sim * 0.30 +
                base_score * 0.15 +
                time_proximity_boost * 0.10
            )

            reranked_doc = Document(
                id=doc.id,
                text=doc.text,
                metadata=dict(doc.metadata),
                embedding=doc.embedding,
                score=round(min(1.0, max(0.0, final_rerank_score)), 4),
                chunk_strategy=doc.chunk_strategy,
                episode_num=doc.episode_num,
                start_sec=doc.start_sec,
                end_sec=doc.end_sec,
                parent_text=doc.parent_text,
                source=doc.source
            )
            scored_docs.append(reranked_doc)

        scored_docs.sort(key=lambda d: d.score, reverse=True)
        return scored_docs[:top_k]


reranker = CrossEncoderReranker()
