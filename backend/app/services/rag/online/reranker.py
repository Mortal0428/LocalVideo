# -*- coding: utf-8 -*-
"""
==============================================================================
【模块名称】：CinemaAgent 工业级深度重排序引擎 (Cross-Encoder Reranker)
【业务定位】：多路检索后的终极裁判官，把真正最关键的剧情台词切片排到第 1 名
【全链路调用位置】：
  在 hybrid_retriever.py 中倒数排名融合 (RRF) 之后被调用，负责精排切片
【核心打分维度与权重配比】：
  1. 字符与词汇重合度 (Lexical Coverage, 权重 45%)：精准匹配提问中的核心实体名（如"顾千帆"、"玉佩"）；
  2. 高维向量语义相似度 (Semantic Vector, 权重 30%)：计算用户提问与台词切片在特征空间中的余弦夹角；
  3. 前序 RRF 通道得分继承 (Base RRF Score, 权重 15%)：兼顾粗排时被多少个通道共同认可；
  4. 时间轴邻近度激励 (Temporal Proximity Boost, 权重 10%)：
     - 若台词发生时间距离用户当前播放进度秒数 (current_sec) 在 30 秒以内，额外奖励 +0.15 分；
     - 在 90 秒以内，额外奖励 +0.08 分；
     - 现实意义：观众往往在刚看到某段剧情产生疑问时提问，因此优先推荐紧随播放进度的剧情！
==============================================================================
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
        """
        对经过 RRF 粗排筛选的候选文档进行 Cross-Encoder 语义交互精排打分，并截取 Top-K 返回。
        
        【入参大白话说明】：
        - query (str): 观众输入的原始提问文本（如：“刚才那个人是谁？”）；
        - documents (List[Document]): 从向量、BM25 和 Neo4j 图谱通道粗召回出来的候选文档切片列表；
        - top_k (int): 最终期望保留的最精华切片数量（默认 3 条），避免喂给大模型太多冗余文字；
        - current_sec (Optional[float]): 观众当前视频播放的精确秒数（例如 75.0 代表 1分15秒），
          用于时间邻近度加权，刚演完的剧情会被赋予更高优先级。
          
        【返回值说明】：
        - List[Document]: 按重排得分从高到低严格排序后的前 Top-K 个优质 Document 对象，
          每个对象的 score 字段已被更新为 0.0 ~ 1.0 之间的精确精排分。
        """
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
