# -*- coding: utf-8 -*-
"""
==============================================================================
【模块名称】：CinemaAgent BM25 稀疏关键词倒排检索器 (BM25Searcher)
【业务定位】：专门捕获短剧专有名词、主角姓名与标志性道具名称，弥补向量检索的词盲缺陷
【全链路调用位置】：
  在 hybrid_retriever.py 中作为第 2 路召回通道并发执行
【核心工作原理】：
  1. 结合 Jieba 中文精准分词，构建短剧内存级的倒排索引 (BM25Okapi)；
  2. 基于 TF-IDF 演进的 BM25 概率打分公式，对罕见专有名词赋予极高权重；
  3. 支持按 drama_id 动态隔离与失效缓存，单部剧集秒级更新。
==============================================================================
"""

import jieba
import logging
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi

from app.services.rag.core.datatypes import Document

logger = logging.getLogger(__name__)


class BM25Searcher:
    """
    基于短剧语料的 BM25 稀疏检索索引库
    """
    def __init__(self):
        # 内存索引字典: drama_id -> {"bm25": BM25Okapi, "docs": List[Document], "corpus_tokens": List[List[str]]}
        self._indices: Dict[str, Dict[str, Any]] = {}

    def _tokenize(self, text: str) -> List[str]:
        """中文结巴精确分词与清洗"""
        if not text:
            return []
        tokens = jieba.lcut(text.strip())
        return [t.strip().lower() for t in tokens if t.strip() and len(t.strip()) > 0]

    def invalidate(self, drama_id: Optional[str] = None):
        """清除指定短剧或全部 BM25 内存索引缓存"""
        if drama_id:
            self._indices.pop(drama_id, None)
        else:
            self._indices.clear()

    def index_documents(self, documents: List[Document], drama_id: Optional[str] = "default"):
        """针对指定短剧文档集合构建或刷新 BM25 倒排索引"""
        key = drama_id or "default"
        if not documents:
            self._indices[key] = {"bm25": None, "docs": [], "corpus_tokens": []}
            return

        corpus_tokens = [self._tokenize(doc.text) for doc in documents]
        if not any(t_list for t_list in corpus_tokens):
            # 防止全部切片均为空白或标点导致 rank_bm25 出现 ZeroDivisionError
            self._indices[key] = {"bm25": None, "docs": list(documents), "corpus_tokens": corpus_tokens}
            return

        bm25 = BM25Okapi(corpus_tokens)
        self._indices[key] = {
            "bm25": bm25,
            "docs": list(documents),
            "corpus_tokens": corpus_tokens
        }
        logger.info(f"BM25 成功索引 {len(documents)} 篇文档 (drama_id: {key})")

    def search(self, query: str, drama_id: Optional[str] = "default", top_k: int = 10) -> List[Document]:
        """执行 BM25 检索打分并返回 Top-K 结果"""
        key = drama_id or "default"
        idx_data = self._indices.get(key)
        if not idx_data or not idx_data.get("bm25") or not idx_data.get("docs"):
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

        bm25: BM25Okapi = idx_data["bm25"]
        docs: List[Document] = idx_data["docs"]
        scores = bm25.get_scores(tokens)

        # 归一化得分
        max_score = max(scores) if len(scores) > 0 and max(scores) > 0 else 1.0
        
        scored_pairs = []
        for i, sc in enumerate(scores):
            if sc > 0:
                doc_copy = Document(
                    id=docs[i].id,
                    text=docs[i].text,
                    metadata=dict(docs[i].metadata),
                    embedding=docs[i].embedding,
                    score=float(sc / max_score),
                    chunk_strategy=docs[i].chunk_strategy,
                    episode_num=docs[i].episode_num,
                    start_sec=docs[i].start_sec,
                    end_sec=docs[i].end_sec,
                    parent_text=docs[i].parent_text,
                    source="bm25"
                )
                scored_pairs.append(doc_copy)

        scored_pairs.sort(key=lambda x: x.score, reverse=True)
        return scored_pairs[:top_k]


bm25_searcher = BM25Searcher()
