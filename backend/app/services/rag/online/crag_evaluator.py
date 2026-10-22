"""
CinemaAgent 工业级模块化 RAG 质量校验器 (Corrective RAG - CRAG Evaluator)
基于《03_05_05_02 Corrective RAG》理念，对重排序后的知识切片进行检索可信度评估，
划分为 CORRECT (高确信)、AMBIGUOUS (边界模糊) 与 INCORRECT (低置信错误) 三类，
驱动自适应知识修正、图谱补全或降级防幻觉。
"""

import jieba
import logging
from typing import List, Dict, Any, Optional
from app.services.rag.core.datatypes import Document, CRAGResult

logger = logging.getLogger(__name__)

THRESHOLD_CORRECT = 0.48
THRESHOLD_AMBIGUOUS = 0.28


class CRAGEvaluator:
    """
    CRAG 检索质量自省评估器
    """
    def __init__(self, correct_threshold: float = THRESHOLD_CORRECT, ambiguous_threshold: float = THRESHOLD_AMBIGUOUS):
        self.correct_threshold = correct_threshold
        self.ambiguous_threshold = ambiguous_threshold

    def evaluate(self, query: str, documents: List[Document]) -> CRAGResult:
        """评估检索文档的相关度与准确性"""
        if not documents:
            return CRAGResult(
                action="INCORRECT",
                confidence_score=0.0,
                reason="未检索到任何匹配知识切片，触发安全降级",
                filtered_documents=[]
            )

        query_tokens = set([t.strip().lower() for t in jieba.lcut(query) if len(t.strip()) > 1])
        
        # 计算最高分与平均分
        scores = [doc.score for doc in documents]
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)

        # 检查核心关键词在候选文档中的覆盖情况
        all_text = " ".join([d.text for d in documents]).lower()
        keyword_hits = sum(1 for kw in query_tokens if kw in all_text)
        hit_ratio = (keyword_hits / len(query_tokens)) if query_tokens else 0.5

        # 综合可信度得分
        confidence = (max_score * 0.50 + avg_score * 0.30 + hit_ratio * 0.20)
        confidence = min(1.0, max(0.0, confidence))

        if confidence >= self.correct_threshold:
            action = "CORRECT"
            reason = f"检索知识高度契合问题 (置信度: {confidence:.2f})，直接注入核心上下文"
            filtered_docs = documents
        elif confidence >= self.ambiguous_threshold:
            action = "AMBIGUOUS"
            reason = f"检索知识具有一定相关性但存在信息盲区 (置信度: {confidence:.2f})，启动图谱多跳知识补全"
            filtered_docs = documents
        else:
            action = "INCORRECT"
            reason = f"检索切片置信度偏低 (置信度: {confidence:.2f})，阻断低质噪声，降级为剧本基础背景答复"
            # 仅保留最高分切片作为弱参考或清空
            filtered_docs = [documents[0]] if documents and documents[0].score >= 0.25 else []

        return CRAGResult(
            action=action,
            confidence_score=round(confidence, 4),
            reason=reason,
            filtered_documents=filtered_docs
        )


crag_evaluator = CRAGEvaluator()
