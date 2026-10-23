"""
CinemaAgent 工业级模块化 RAG 质量校验器 (Corrective RAG - CRAG Evaluator)
基于《03_05_05_02 Corrective RAG》理念，对重排序后的知识切片进行检索可信度评估，
划分为 CORRECT (高确信)、AMBIGUOUS (边界模糊) 与 INCORRECT (低置信错误) 三类，
驱动自适应知识修正、Neo4j 2-Hop 图谱补全或清空降级防幻觉。
"""

import jieba
import logging
from typing import List, Dict, Any, Optional
from app.services.rag.core.datatypes import Document, QueryBundle, CRAGResult
from app.services.rag.core.neo4j_client import graph_service

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

    def evaluate(
        self,
        query: str,
        documents: List[Document],
        bundle: Optional[QueryBundle] = None
    ) -> CRAGResult:
        """
        评估检索文档的相关度与准确性，并执行动态校正分支
        """
        if not documents:
            logger.info("[CRAG] 候选切片为空 -> INCORRECT (清空防幻觉)")
            return CRAGResult(
                action="INCORRECT",
                confidence_score=0.0,
                reason="未检索到任何匹配知识切片，已清空切片阻断幻觉，启用防御性通用答复",
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

        # 综合可信度得分 (0.0 ~ 1.0)
        confidence = (max_score * 0.50 + avg_score * 0.30 + hit_ratio * 0.20)
        confidence = min(1.0, max(0.0, confidence))

        if confidence >= self.correct_threshold:
            # -------------------------------------------------------------
            # 分支 1: CORRECT (高确信)
            # -------------------------------------------------------------
            action = "CORRECT"
            reason = f"检索知识高度契合问题 (置信度: {confidence:.2f} >= {self.correct_threshold})，直接注入核心上下文"
            filtered_docs = list(documents)
            logger.info(f"[CRAG] 判定结果: CORRECT ({confidence:.2f})")

        elif confidence >= self.ambiguous_threshold:
            # -------------------------------------------------------------
            # 分支 2: AMBIGUOUS (边界模糊) -> 真实 Neo4j 2-Hop Cypher 补全
            # -------------------------------------------------------------
            action = "AMBIGUOUS"
            drama_id = bundle.drama_id if bundle else None
            supp_count = 0
            filtered_docs = list(documents)

            # 提取可能相关的实体词
            detected_entities = []
            for t in query_tokens:
                if len(t) >= 2:
                    detected_entities.append(t)
            for d in documents[:3]:
                if d.metadata and "source_entity" in d.metadata:
                    detected_entities.append(d.metadata["source_entity"])
                if d.metadata and "target_entity" in d.metadata:
                    detected_entities.append(d.metadata["target_entity"])

            detected_entities = list(set(detected_entities))[:4]

            # 执行 2-Hop 图谱补全
            if detected_entities:
                for ent in detected_entities:
                    try:
                        subgraph = graph_service.query_entity_subgraph(ent, depth=2, drama_id=drama_id)
                        edges = subgraph.get("edges", [])
                        for edge in edges[:3]:
                            s = edge.get("source")
                            r = edge.get("type")
                            t = edge.get("target")
                            props = edge.get("properties", {})
                            fact_str = f"【CRAG 图谱2-Hop补偿事实】{s} 与 {t} 的关联为「{r}」"
                            supp_id = f"crag-supp-{s}-{r}-{t}"
                            if not any(d.id == supp_id for d in filtered_docs):
                                filtered_docs.append(Document(
                                    id=supp_id,
                                    text=fact_str,
                                    metadata={"source": s, "target": t, "relation": r},
                                    score=0.65,
                                    chunk_strategy="graph_cypher",
                                    episode_num=bundle.episode_num if bundle else 1,
                                    source="crag_neo4j_2hop"
                                ))
                                supp_count += 1
                    except Exception as e:
                        logger.warning(f"[CRAG] 2-Hop 图谱探测异常: {e}")

            reason = f"检索知识存在信息盲区 (置信度: {confidence:.2f})，已动态执行 Neo4j 2-Hop Cypher 成功补偿 {supp_count} 条关系图谱"
            logger.info(f"[CRAG] 判定结果: AMBIGUOUS ({confidence:.2f}), 补偿了 {supp_count} 条三元组")

        else:
            # -------------------------------------------------------------
            # 分支 3: INCORRECT (低置信错误) -> 真实清空防臆造
            # -------------------------------------------------------------
            action = "INCORRECT"
            reason = f"检索切片置信度偏低 (置信度: {confidence:.2f} < {self.ambiguous_threshold})，已清空召回知识以防虚构，启用防御性回答"
            filtered_docs = []
            logger.info(f"[CRAG] 判定结果: INCORRECT ({confidence:.2f}), 已清空所有切片")

        return CRAGResult(
            action=action,
            confidence_score=round(confidence, 4),
            reason=reason,
            filtered_documents=filtered_docs
        )


crag_evaluator = CRAGEvaluator()
