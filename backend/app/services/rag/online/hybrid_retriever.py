"""
==============================================================================
【模块名称】：CinemaAgent 三路混合检索器 (HybridRetriever)
【业务定位】：负责从海量短剧数据中把最精准的台词和人物关系给捞出来。
【全链路调用位置】：
  在 pipeline.py 中被调用，负责并发检索数据库、向量库与 Neo4j
【核心解决的核心问题】：
  1. 单一向量检索的局限：向量检索擅长语义泛化，但对专有名词 (如人名"顾千帆"、特定道具"玉佩") 经常搜漏；
  2. 三路并进召回机制：
     - 路 1 (向量路)：把用户提问转成 Embedding，在 RAGChunk 向量表中找语义最贴近的切片；
     - 路 2 (BM25 路)：精准匹配台词字词频率，绝不漏掉核心人名；
     - 路 3 (Neo4j 图谱路)：通过 Cypher 语句遍历人物图谱三元组，捞出人物之间的夫妻、敌对、暗恋等复杂关系网；
  3. 检索结果粗筛：将三路候选数据汇聚在一起，准备交给下游进行 RRF 倒排融合与重排。
==============================================================================
"""

import time
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.rag_corpus import RAGChunk
from app.services.rag.core.datatypes import Document, QueryBundle, CRAGResult
from app.services.rag.core.neo4j_client import graph_service
from app.services.rag.core.tools_toggle_config import tools_config_mgr
from app.services.rag.offline.embedder import embedder, cosine_similarity
from app.services.rag.online.bm25_searcher import bm25_searcher
from app.services.rag.online.rrf_fusion import rrf_fusion
from app.services.rag.online.reranker import reranker
from app.services.rag.online.crag_evaluator import crag_evaluator

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    三路混合召回引擎 (向量 + BM25 + Neo4j 图谱) + 时间轴防剧透门控
    """
    def __init__(self):
        self._indexed_dramas = set()

    def invalidate_cache(self, drama_id: Optional[str] = None):
        """失效切片与 BM25 索引缓存"""
        if drama_id:
            self._indexed_dramas.discard(drama_id)
        else:
            self._indexed_dramas.clear()
        bm25_searcher.invalidate(drama_id)

    def _ensure_bm25_indexed(self, db: Session, drama_id: Optional[str] = None):
        """确保短剧切片已装载进 BM25 内存索引"""
        key = drama_id or "default"
        if key in self._indexed_dramas:
            return

        query = db.query(RAGChunk)
        if drama_id:
            query = query.filter(RAGChunk.drama_id == drama_id)
        chunks = query.all()

        docs = []
        for ch in chunks:
            docs.append(Document(
                id=ch.id,
                text=ch.content,
                metadata={"drama_id": ch.drama_id, "corpus_id": ch.corpus_id},
                chunk_strategy=ch.chunk_strategy or "fixed",
                episode_num=ch.episode_num or 1,
                start_sec=ch.start_sec or 0.0,
                end_sec=ch.end_sec or 0.0,
                parent_text=ch.parent_content
            ))

        bm25_searcher.index_documents(docs, drama_id=key)
        self._indexed_dramas.add(key)

    def retrieve(
        self,
        bundle: QueryBundle,
        db: Session
    ) -> Tuple[List[Document], CRAGResult, List[Dict[str, Any]]]:
        """
        三路并发召回 + 防剧透过滤 + RRF 融合 + 深度精排 + CRAG 校验
        """
        self._ensure_bm25_indexed(db, bundle.drama_id)

        # 读取工具热插拔开关矩阵
        toggles = tools_config_mgr.get_config(db)

        # ---------------------------------------------------------
        # 通道 1: 稠密向量召回 (Dense Vector Search)
        # ---------------------------------------------------------
        vector_candidates: List[Document] = []
        if toggles.get("enable_dense", True):
            query_vec = bundle.embedding or embedder.embed_text(bundle.query_str)
            
            chunk_query = db.query(RAGChunk)
            if bundle.drama_id:
                chunk_query = chunk_query.filter(RAGChunk.drama_id == bundle.drama_id)
            
            all_chunks = chunk_query.all()
            scored_chunks = []
            for ch in all_chunks:
                # 【时间轴防剧透门控 Spoiling Guard】
                if not self._check_anti_spoiling(ch.episode_num, ch.start_sec, bundle):
                    continue

                # 读取或计算嵌入向量
                doc_vec = None
                if ch.embedding_json:
                    try:
                        doc_vec = json.loads(ch.embedding_json)
                    except Exception:
                        pass
                if not doc_vec:
                    doc_vec = embedder.embed_text(ch.content)

                sim = cosine_similarity(query_vec, doc_vec)
                if sim > 0.15:
                    doc_obj = Document(
                        id=ch.id,
                        text=ch.content,
                        metadata={"drama_id": ch.drama_id, "corpus_id": ch.corpus_id},
                        embedding=doc_vec,
                        score=float(sim),
                        chunk_strategy=ch.chunk_strategy or "fixed",
                        episode_num=ch.episode_num or 1,
                        start_sec=ch.start_sec or 0.0,
                        end_sec=ch.end_sec or 0.0,
                        parent_text=ch.parent_content,
                        source="vector"
                    )
                    scored_chunks.append(doc_obj)

            scored_chunks.sort(key=lambda d: d.score, reverse=True)
            vector_candidates = scored_chunks[:15]

        # ---------------------------------------------------------
        # 通道 2: 稀疏 BM25 召回 (Sparse Keyword Search)
        # ---------------------------------------------------------
        bm25_candidates: List[Document] = []
        if toggles.get("enable_bm25", True):
            raw_bm25 = bm25_searcher.search(bundle.query_str, drama_id=bundle.drama_id, top_k=15)
            for d in raw_bm25:
                # 防剧透门控
                if self._check_anti_spoiling(d.episode_num, d.start_sec, bundle):
                    bm25_candidates.append(d)

        # ---------------------------------------------------------
        # 通道 3: Neo4j Cypher 图谱遍历 (Knowledge Graph Recall)
        # ---------------------------------------------------------
        graph_docs: List[Document] = []
        all_graph_entities: List[Dict[str, Any]] = []
        
        # 探测查询中提及的实体
        detected_entities = self._detect_query_entities(bundle.query_str)
        if toggles.get("enable_neo4j", True):
            for ent_name in detected_entities:
                subgraph = graph_service.query_entity_subgraph(ent_name, depth=1, drama_id=bundle.drama_id)
                nodes = subgraph.get("nodes", [])
                edges = subgraph.get("edges", [])
                for n in nodes:
                    if n not in all_graph_entities:
                        all_graph_entities.append(n)
                
                for edge in edges:
                    s = edge.get("source")
                    r = edge.get("type")
                    t = edge.get("target")
                    props = edge.get("properties", {})
                    edge_ep = props.get("episode_num")
                    edge_sec = props.get("start_sec", 0.0)
                    if edge_ep is not None and not self._check_anti_spoiling(int(edge_ep), float(edge_sec), bundle):
                        continue

                    ev = props.get("evidence", "")
                    fact_str = f"【知识图谱事实】{s} 与 {t} 的关系为「{r}」。说明：{ev}"
                    graph_doc = Document(
                        id=f"graph-{s}-{r}-{t}",
                        text=fact_str,
                        metadata={"source_entity": s, "target_entity": t, "relation": r},
                        score=0.88,
                        chunk_strategy="graph_triple",
                        episode_num=int(edge_ep) if edge_ep is not None else bundle.episode_num,
                        start_sec=float(edge_sec),
                        end_sec=float(edge_sec) + 10.0,
                        source="graph"
                    )
                    graph_docs.append(graph_doc)

        # ---------------------------------------------------------
        # 倒数排名融合 (RRF Fusion)
        # ---------------------------------------------------------
        channel_results = {
            "vector": vector_candidates,
            "bm25": bm25_candidates,
            "graph": graph_docs
        }
        if toggles.get("enable_rrf", True):
            fused_candidates = rrf_fusion.fuse(channel_results, top_n=10)
        else:
            fused_candidates = []
            for clist in channel_results.values():
                for cdoc in clist:
                    if not any(x.text == cdoc.text for x in fused_candidates):
                        fused_candidates.append(cdoc)
            fused_candidates = fused_candidates[:10]

        # ---------------------------------------------------------
        # Cross-Encoder 深度重排序 (Reranker)
        # ---------------------------------------------------------
        if toggles.get("enable_rerank", True):
            reranked_docs = reranker.rerank(
                query=bundle.query_str,
                documents=fused_candidates,
                top_k=bundle.top_k,
                current_sec=bundle.current_sec
            )
        else:
            reranked_docs = fused_candidates[:bundle.top_k]

        # ---------------------------------------------------------
        # CRAG 质量评估器 (Corrective RAG)
        # ---------------------------------------------------------
        if toggles.get("enable_crag", True):
            crag_result = crag_evaluator.evaluate(bundle.query_str, reranked_docs, bundle=bundle)
        else:
            crag_result = CRAGResult(action="CORRECT", confidence_score=1.0, reason="CRAG 过滤器已手动旁路")

        # 若为 AMBIGUOUS，尝试利用图谱补全更多 2-hop 关系信息
        if crag_result.action == "AMBIGUOUS" and detected_entities:
            for ent_name in detected_entities:
                two_hop_sub = graph_service.query_entity_subgraph(ent_name, depth=2, drama_id=bundle.drama_id)
                for edge in two_hop_sub.get("edges", [])[:3]:
                    s = edge.get("source")
                    r = edge.get("type")
                    t = edge.get("target")
                    props = edge.get("properties", {})
                    edge_ep = props.get("episode_num")
                    edge_sec = props.get("start_sec", 0.0)
                    if edge_ep is not None and not self._check_anti_spoiling(int(edge_ep), float(edge_sec), bundle):
                        continue
                    fact_str = f"【图谱延伸补充】{s} -[{r}]-> {t}"
                    supp_doc = Document(
                        id=f"graph-supp-{s}-{r}-{t}",
                        text=fact_str,
                        score=0.60,
                        chunk_strategy="graph_triple",
                        episode_num=int(edge_ep) if edge_ep is not None else bundle.episode_num,
                        source="graph_supp"
                    )
                    if supp_doc.id not in [d.id for d in crag_result.filtered_documents]:
                        crag_result.filtered_documents.append(supp_doc)

        return crag_result.filtered_documents, crag_result, all_graph_entities

    def retrieve_with_trace(
        self,
        bundle: QueryBundle,
        db: Session
    ) -> Tuple[List[Document], CRAGResult, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """带全链路分步耗时与算子命中的可观测检索接口"""
        trace_steps = []
        toggles = tools_config_mgr.get_config(db)

        # 1. Dense Vector
        t0 = time.time()
        dense_enabled = toggles.get("enable_dense", True)
        vector_candidates = []
        if dense_enabled:
            query_vec = bundle.embedding or embedder.embed_text(bundle.query_str)
            chunk_query = db.query(RAGChunk)
            if bundle.drama_id:
                chunk_query = chunk_query.filter(RAGChunk.drama_id == bundle.drama_id)
            all_chunks = chunk_query.all()
            scored_chunks = []
            for ch in all_chunks:
                if not self._check_anti_spoiling(ch.episode_num, ch.start_sec, bundle):
                    continue
                doc_vec = None
                if ch.embedding_json:
                    try:
                        doc_vec = json.loads(ch.embedding_json)
                    except Exception:
                        pass
                if not doc_vec:
                    doc_vec = embedder.embed_text(ch.content)
                sim = cosine_similarity(query_vec, doc_vec)
                if sim > 0.15:
                    doc_obj = Document(
                        id=ch.id,
                        text=ch.content,
                        metadata={"drama_id": ch.drama_id, "corpus_id": ch.corpus_id},
                        embedding=doc_vec,
                        score=float(sim),
                        chunk_strategy=ch.chunk_strategy or "fixed",
                        episode_num=ch.episode_num or 1,
                        start_sec=ch.start_sec or 0.0,
                        end_sec=ch.end_sec or 0.0,
                        parent_text=ch.parent_content,
                        source="vector"
                    )
                    scored_chunks.append(doc_obj)
            scored_chunks.sort(key=lambda d: d.score, reverse=True)
            vector_candidates = scored_chunks[:15]
            dense_ms = round((time.time() - t0) * 1000.0, 2)
            top_sim = f"，最高相似度 {vector_candidates[0].score:.3f}" if vector_candidates else ""
            trace_steps.append({
                "name": "Dense Vector Search",
                "stage": "retrieval",
                "enabled": True,
                "latency_ms": dense_ms,
                "count": len(vector_candidates),
                "details": f"扫描库内切片并计算特征相似度，召回 {len(vector_candidates)} 条候选{top_sim}"
            })
        else:
            trace_steps.append({
                "name": "Dense Vector Search",
                "stage": "retrieval",
                "enabled": False,
                "latency_ms": 0.0,
                "count": 0,
                "details": "算子已关闭，旁路跳过 (Bypassed)"
            })

        # 2. BM25
        t0 = time.time()
        bm25_enabled = toggles.get("enable_bm25", True)
        bm25_candidates = []
        if bm25_enabled:
            raw_bm25 = bm25_searcher.search(bundle.query_str, drama_id=bundle.drama_id, top_k=15)
            for d in raw_bm25:
                if self._check_anti_spoiling(d.episode_num, d.start_sec, bundle):
                    bm25_candidates.append(d)
            bm25_ms = round((time.time() - t0) * 1000.0, 2)
            trace_steps.append({
                "name": "BM25 Sparse Search",
                "stage": "retrieval",
                "enabled": True,
                "latency_ms": bm25_ms,
                "count": len(bm25_candidates),
                "details": f"精确分词倒排检索命中 {len(bm25_candidates)} 条文档"
            })
        else:
            trace_steps.append({
                "name": "BM25 Sparse Search",
                "stage": "retrieval",
                "enabled": False,
                "latency_ms": 0.0,
                "count": 0,
                "details": "算子已关闭，旁路跳过 (Bypassed)"
            })

        # 3. Neo4j Graph
        t0 = time.time()
        neo_enabled = toggles.get("enable_neo4j", True)
        graph_docs = []
        all_graph_entities = []
        detected_entities = self._detect_query_entities(bundle.query_str)
        if neo_enabled:
            for ent_name in detected_entities:
                subgraph = graph_service.query_entity_subgraph(ent_name, depth=1, drama_id=bundle.drama_id)
                for n in subgraph.get("nodes", []):
                    if n not in all_graph_entities:
                        all_graph_entities.append(n)
                for edge in subgraph.get("edges", []):
                    s = edge.get("source")
                    r = edge.get("type")
                    t = edge.get("target")
                    props = edge.get("properties", {})
                    edge_ep = props.get("episode_num")
                    edge_sec = props.get("start_sec", 0.0)
                    if edge_ep is not None and not self._check_anti_spoiling(int(edge_ep), float(edge_sec), bundle):
                        continue
                    ev = props.get("evidence", "")
                    graph_doc = Document(
                        id=f"graph-{s}-{r}-{t}",
                        text=f"【知识图谱事实】{s} 与 {t} 的关系为「{r}」。说明：{ev}",
                        metadata={"source_entity": s, "target_entity": t, "relation": r},
                        score=0.88,
                        chunk_strategy="graph_triple",
                        episode_num=int(edge_ep) if edge_ep is not None else bundle.episode_num,
                        start_sec=float(edge_sec),
                        end_sec=float(edge_sec) + 10.0,
                        source="graph"
                    )
                    graph_docs.append(graph_doc)
            neo_ms = round((time.time() - t0) * 1000.0, 2)
            ent_labels = ", ".join([e.get("name", "") for e in all_graph_entities[:3]])
            details_str = f"Cypher 遍历命中 {len(all_graph_entities)} 个实体 ({ent_labels}) 与 {len(graph_docs)} 条三元组" if all_graph_entities else "未识别到实体关联事实"
            trace_steps.append({
                "name": "Neo4j Graph Cypher",
                "stage": "retrieval",
                "enabled": True,
                "latency_ms": neo_ms,
                "count": len(graph_docs),
                "details": details_str
            })
        else:
            trace_steps.append({
                "name": "Neo4j Graph Cypher",
                "stage": "retrieval",
                "enabled": False,
                "latency_ms": 0.0,
                "count": 0,
                "details": "算子已关闭，旁路跳过 (Bypassed)"
            })

        # 4. RRF Fusion
        t0 = time.time()
        rrf_enabled = toggles.get("enable_rrf", True)
        channel_results = {"vector": vector_candidates, "bm25": bm25_candidates, "graph": graph_docs}
        if rrf_enabled:
            fused_candidates = rrf_fusion.fuse(channel_results, top_n=10)
            rrf_ms = round((time.time() - t0) * 1000.0, 2)
            trace_steps.append({
                "name": "RRF Fusion",
                "stage": "fusion",
                "enabled": True,
                "latency_ms": rrf_ms,
                "count": len(fused_candidates),
                "details": f"倒排排名融合算法生成 {len(fused_candidates)} 个权重候选"
            })
        else:
            fused_candidates = []
            for clist in channel_results.values():
                for cdoc in clist:
                    if not any(x.text == cdoc.text for x in fused_candidates):
                        fused_candidates.append(cdoc)
            fused_candidates = fused_candidates[:10]
            trace_steps.append({
                "name": "RRF Fusion",
                "stage": "fusion",
                "enabled": False,
                "latency_ms": 0.0,
                "count": len(fused_candidates),
                "details": f"已旁路跳过，采用简单并集聚合 ({len(fused_candidates)} 条)"
            })

        # 5. Reranker
        t0 = time.time()
        rerank_enabled = toggles.get("enable_rerank", True)
        if rerank_enabled:
            reranked_docs = reranker.rerank(
                query=bundle.query_str,
                documents=fused_candidates,
                top_k=bundle.top_k,
                current_sec=bundle.current_sec
            )
            rerank_ms = round((time.time() - t0) * 1000.0, 2)
            trace_steps.append({
                "name": "Cross-Encoder Reranker",
                "stage": "rerank",
                "enabled": True,
                "latency_ms": rerank_ms,
                "count": len(reranked_docs),
                "details": f"Cross-Encoder 语义深度重排筛选 Top-{len(reranked_docs)} 优质切片"
            })
        else:
            reranked_docs = fused_candidates[:bundle.top_k]
            trace_steps.append({
                "name": "Cross-Encoder Reranker",
                "stage": "rerank",
                "enabled": False,
                "latency_ms": 0.0,
                "count": len(reranked_docs),
                "details": f"算子已关闭，旁路跳过 (Bypassed，保留前 {len(reranked_docs)} 条)"
            })

        # 6. CRAG
        t0 = time.time()
        crag_enabled = toggles.get("enable_crag", True)
        if crag_enabled:
            crag_result = crag_evaluator.evaluate(bundle.query_str, reranked_docs)
            crag_ms = round((time.time() - t0) * 1000.0, 2)
            trace_steps.append({
                "name": "CRAG Evaluator",
                "stage": "reflection",
                "enabled": True,
                "latency_ms": crag_ms,
                "count": len(crag_result.filtered_documents),
                "details": f"三态置信度判定 [{crag_result.action}] (得分 {crag_result.confidence_score:.2f})，保留 {len(crag_result.filtered_documents)} 条"
            })
        else:
            crag_result = CRAGResult(action="CORRECT", confidence_score=1.0, reason="CRAG 过滤器已手动旁路")
            trace_steps.append({
                "name": "CRAG Evaluator",
                "stage": "reflection",
                "enabled": False,
                "latency_ms": 0.0,
                "count": len(reranked_docs),
                "details": "算子已关闭，旁路跳过 (Bypassed)"
            })

        return crag_result.filtered_documents, crag_result, all_graph_entities, trace_steps

    def _check_anti_spoiling(self, ep_num: int, start_sec: float, bundle: QueryBundle) -> bool:
        """
        防剧透核心判定逻辑：
        1. 切片集数必须 <= 当前用户所看集数
        2. 若在同集内且指定了非负播放秒数，切片发生时间戳不能晚于当前播放秒数 + 20秒（防超前剧透，保留合理缓冲）
        若 bundle.current_sec < 0 则代表非精准防剧透模式（全集可看）
        """
        if ep_num > bundle.episode_num:
            return False
        if ep_num == bundle.episode_num and bundle.current_sec is not None and bundle.current_sec >= 0.0:
            if start_sec > bundle.current_sec + 20.0:
                return False
        return True

    def _detect_query_entities(self, query: str) -> List[str]:
        """识别查询语句中的核心实体名词"""
        known_characters = [
            "苏倾城", "顾夜白", "苏婉儿", "苏正国", "林凤霞",
            "黑金卡", "至尊黑金卡", "暖玉信物", "玉佩", "DNA报告", "亲子鉴定",
            "苏氏集团", "顾氏集团"
        ]
        hits = set()
        for name in known_characters:
            if name in query:
                hits.add(name)
        try:
            for node_name in graph_service.embedded_store.nodes.keys():
                if len(node_name) >= 2 and node_name in query:
                    hits.add(node_name)
        except Exception:
            pass
        return list(hits)


hybrid_retriever = HybridRetriever()
