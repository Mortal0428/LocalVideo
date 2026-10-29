"""
==============================================================================
【模块名称】：CinemaAgent 模块化 RAG 在线调度总流水线 (ModularRAGPipeline)
【业务定位】：剧情 AI 伴聊问答的整体流水线指挥官。
【全链路调用位置】：
  前端播放器提问 -> POST /api/v1/agent/chat (endpoints/agent.py) -> 本模块 query() 或 astream_query()
【核心解决的核心问题】：
  1. 统一调度多路混合检索 (向量语义 + BM25关键字 + Neo4j图谱遍历)；
  2. 倒排融合 (RRF) 与 Cross-Encoder 精排重打分，把最相关的台词切片排在最前面；
  3. 执行 Corrective RAG (CRAG) 相关性门禁打分，如果检索结果不对题，自动重写 Query 重试；
  4. 执行 Self-RAG 反思与时间轴防剧透，拦截未来切片；
  5. 组装终极 Prompt 交付底座大模型，生成高质量无剧透的剧情解读。
==============================================================================
"""

import json
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.services.rag.core.datatypes import Document, QueryBundle, RAGResponse, CRAGResult
from app.services.rag.core.tools_toggle_config import tools_config_mgr
from app.services.rag.online.hybrid_retriever import hybrid_retriever
from app.services.rag.online.self_rag_engine import self_rag_engine
from app.services.llm_gateway import llm_gateway
from langsmith import traceable

logger = logging.getLogger(__name__)


class ModularRAGPipeline:
    """
    模块化高级 RAG 统一执行引擎
    """
    def __init__(self):
        pass

    @traceable(
        name="GraphRAG-ModularPipeline",
        run_type="chain",
        metadata={"subsystem": "graph-rag-neo4j"}
    )
    async def query_stream(
        self,
        bundle: QueryBundle,
        db: Session
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式生成问答接口 (用于 SSE 实时长连接)
        Yields 标准字典事件:
        - {"type": "action_card", "action": "SEEK", ...}
        - {"type": "thought", "content": "..."}
        - {"type": "token", "content": "..."}
        - {"type": "done", "target_time": ..., "time_tag": ..., "self_rag": ..., "crag_status": ...}
        """
        cfg = llm_gateway.get_active_config()
        active_model = cfg.get("chat_model", "deepseek-r1:1.5b")
        active_provider = cfg.get("provider", "ollama")

        # 读取前端热插拔开关状态
        toggles = tools_config_mgr.get_config(db)

        # -------------------------------------------------------------
        # 步骤 1: Self-RAG [Retrieve] 语义意图判定与检索必要性认证
        # -------------------------------------------------------------
        step1_tag = "[Retrieve]"
        if toggles.get("enable_self_rag", True):
            needs_retrieval, step1_tag = self_rag_engine.evaluate_retrieval_need(bundle.query_str)
        else:
            needs_retrieval = True
            step1_tag = "[Retrieve-Forced]"
        
        retrieved_docs: List[Document] = []
        crag_result = CRAGResult(action="CORRECT", confidence_score=1.0, reason="无需检索的通用日常交流")
        graph_entities = []
        best_anchor = None
        time_anchors = []
        compressed_context = ""

        if needs_retrieval:
            # 三路混合召回 (向量 + BM25 + Neo4j) 与 CRAG 质量初评
            try:
                raw_docs, crag_result, graph_entities = hybrid_retriever.retrieve(bundle, db)
            except Exception as e:
                logger.warning(f"RAG 检索阶段异常: {e}")
                raw_docs = []
                crag_result = CRAGResult(action="INCORRECT", confidence_score=0.2, reason="检索异常降级")

            # ---------------------------------------------------------
            # 步骤 2: Self-RAG [Is-Relevant] 防剧透与相关度认证
            # ---------------------------------------------------------
            if toggles.get("enable_self_rag", True):
                retrieved_docs, step2_details = self_rag_engine.filter_relevant_and_anti_spoiler(raw_docs, bundle)
            else:
                retrieved_docs = raw_docs

            # 上下文动态去重压缩与时间戳锚点提取
            compressed_context, time_anchors, best_anchor = self_rag_engine.compress_and_anchor_context(retrieved_docs)
            
            # 若有最佳定位点，立即向前端抛出 SEEK 动作卡片
            if best_anchor:
                action_card = {
                    "type": "action_card",
                    "action": "SEEK",
                    "timestamp": best_anchor["timestamp"],
                    "time_tag": best_anchor["time_tag"],
                    "title": f"定位到剧情名场面 [{best_anchor['time_tag']}]",
                    "desc": best_anchor["scene"]
                }
                yield action_card

            # 合成完整推理 Prompt
            prompt = self_rag_engine.build_inference_prompt(
                bundle=bundle,
                compressed_context=compressed_context,
                crag_reason=crag_result.reason,
                best_anchor=best_anchor
            )
        else:
            prompt = (
                f"你是 CinemaAgent 短剧智能伴读 Agent。\n"
                f"用户正在与你闲聊交流：{bundle.query_str}\n"
                f"请用亲切、生动且专业的影视解说员口吻给予回复。"
            )

        # -------------------------------------------------------------
        # 调用 LLM Gateway 流式生成
        # -------------------------------------------------------------
        full_tokens = []
        async for event in llm_gateway.stream_chat(prompt=prompt):
            event_type = event.get("type")
            if event_type in ("thought", "token", "diagnostic"):
                if event_type == "token":
                    full_tokens.append(event.get("content", ""))
                yield event

        full_answer = "".join(full_tokens).strip()

        # -------------------------------------------------------------
        # 步骤 3 & 4: Self-RAG 忠实度与有用性反思打分
        # -------------------------------------------------------------
        if toggles.get("enable_self_rag", True) and needs_retrieval:
            step3_tag, step3_score = self_rag_engine.verify_faithfulness(full_answer, compressed_context)
            step4_tag, step4_score = self_rag_engine.evaluate_utility(full_answer, bundle.query_str, best_anchor)
        else:
            step3_tag, step3_score = "[Chat-Free]", 1.0
            step4_tag, step4_score = "[Is-Useful-5]", 5.0

        # 抛出完成信号
        jump_sec = best_anchor["timestamp"] if best_anchor else bundle.current_sec
        m, s = divmod(int(jump_sec), 60)
        time_tag = f"{m:02d}:{s:02d}"

        yield {
            "type": "done",
            "target_time": jump_sec,
            "time_tag": time_tag,
            "crag_status": crag_result.action,
            "crag_confidence": crag_result.confidence_score,
            "crag_reason": crag_result.reason,
            "self_rag": {
                "step1_tag": step1_tag,
                "step2_retained": len(retrieved_docs),
                "step3_tag": step3_tag,
                "step3_score": step3_score,
                "step4_tag": step4_tag,
                "step4_score": step4_score
            },
            "model_used": f"{active_provider}:{active_model}"
        }

    async def aquery(self, bundle: QueryBundle, db: Session) -> RAGResponse:
        """
        异步完整问答接口 (用于 FastAPI async 端点与全链路大模型推理)
        """
        toggles = tools_config_mgr.get_config(db)

        # 步骤 1
        if toggles.get("enable_self_rag", True):
            needs_retrieval, step1_tag = self_rag_engine.evaluate_retrieval_need(bundle.query_str)
        else:
            needs_retrieval = True
            step1_tag = "[Retrieve-Forced]"

        retrieved_docs = []
        crag_result = CRAGResult(action="CORRECT", confidence_score=1.0, reason="无需检索的通用闲聊")
        graph_entities = []
        best_anchor = None
        time_anchors = []

        if needs_retrieval:
            try:
                raw_docs, crag_result, graph_entities = hybrid_retriever.retrieve(bundle, db)
            except Exception as e:
                logger.warning(f"RAG aquery 检索异常: {e}")
                raw_docs = []
                crag_result = CRAGResult(action="INCORRECT", confidence_score=0.2, reason="检索异常降级")

            # 步骤 2
            if toggles.get("enable_self_rag", True):
                retrieved_docs, _ = self_rag_engine.filter_relevant_and_anti_spoiler(raw_docs, bundle)
            else:
                retrieved_docs = raw_docs

            compressed_context, time_anchors, best_anchor = self_rag_engine.compress_and_anchor_context(retrieved_docs)
            prompt = self_rag_engine.build_inference_prompt(
                bundle=bundle,
                compressed_context=compressed_context,
                crag_reason=crag_result.reason,
                best_anchor=best_anchor
            )
        else:
            compressed_context = ""
            time_anchors = []
            prompt = (
                f"你是 CinemaAgent 短剧智能伴读 Agent。\n"
                f"用户正在与你交流：{bundle.query_str}\n"
                f"请用亲切、生动且专业的影视解说员口吻给予回复。"
            )

        answer_parts = []
        try:
            async for ev in llm_gateway.stream_chat(prompt=prompt):
                if ev.get("type") == "token":
                    answer_parts.append(ev.get("content", ""))
            answer_text = "".join(answer_parts).strip()
        except Exception as e:
            logger.warning(f"LLM 推理生成异常，降级至上下文线索: {e}")
            answer_text = ""

        if not answer_text:
            if retrieved_docs:
                answer_text = f"根据剧情事实，{retrieved_docs[0].text}。"
                if best_anchor:
                    answer_text += f" 您可以在 [{best_anchor['time_tag']}] 查看该名场面。"
            else:
                answer_text = "根据当前剧集进度，暂无更多剧情线索。"

        cfg = llm_gateway.get_active_config()
        return RAGResponse(
            query=bundle.query_str,
            answer=answer_text,
            retrieved_documents=retrieved_docs,
            graph_entities=graph_entities,
            time_anchors=time_anchors,
            crag_status=crag_result.action,
            model_used=f"{cfg.get('provider')}:{cfg.get('chat_model')}"
        )

    def query(self, bundle: QueryBundle, db: Session) -> RAGResponse:
        """
        同步问答接口 (用于自动化评测与单元测试)
        """
        import concurrent.futures
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(asyncio.run, self.aquery(bundle, db))
                    return future.result(timeout=25.0)
            else:
                return asyncio.run(self.aquery(bundle, db))
        except Exception as e:
            logger.warning(f"同步问答调度异常，启动保底生成: {e}")
            raw_docs, crag_result, graph_entities = hybrid_retriever.retrieve(bundle, db)
            retrieved_docs, _ = self_rag_engine.filter_relevant_and_anti_spoiler(raw_docs, bundle)
            compressed_context, time_anchors, best_anchor = self_rag_engine.compress_and_anchor_context(retrieved_docs)
            if retrieved_docs:
                fallback_ans = f"根据剧本线索：{retrieved_docs[0].text}"
                if best_anchor:
                    fallback_ans += f"（对应画面位于 [{best_anchor['time_tag']}]）"
            else:
                fallback_ans = "剧情伴读为您服务。"

            cfg = llm_gateway.get_active_config()
            return RAGResponse(
                query=bundle.query_str,
                answer=fallback_ans,
                retrieved_documents=retrieved_docs,
                graph_entities=graph_entities,
                time_anchors=time_anchors,
                crag_status=crag_result.action,
                model_used=f"{cfg.get('provider')}:{cfg.get('chat_model')}"
            )

    def trace_query(self, bundle: QueryBundle, db: Session) -> Dict[str, Any]:
        """
        可观测性真实调试沙盒执行器：
        精确记录从 Query 解析、Self-RAG 门控、向量检索、BM25、Neo4j Cypher、RRF 融合、Cross-Encoder、CRAG 校验的每一步真实耗时与命中明细。
        """
        import time
        import uuid
        start_all = time.time()
        
        toggles = tools_config_mgr.get_config(db)
        trace_steps: List[Dict[str, Any]] = []

        # 1. Self-RAG Step 1
        t0 = time.time()
        self_rag_enabled = toggles.get("enable_self_rag", True)
        if self_rag_enabled:
            needs_retrieval, step1_tag = self_rag_engine.evaluate_retrieval_need(bundle.query_str)
            latency_ms = round((time.time() - t0) * 1000.0, 2)
            trace_steps.append({
                "name": "Self-RAG Step 1: Intent & Need Gate",
                "stage": "gateway",
                "enabled": True,
                "latency_ms": latency_ms,
                "count": 1 if needs_retrieval else 0,
                "details": f"认证标签: {step1_tag} - {'触发知识检索' if needs_retrieval else '日常闲聊旁路'}"
            })
        else:
            needs_retrieval = True
            step1_tag = "[Retrieve-Forced]"
            trace_steps.append({
                "name": "Self-RAG Step 1: Intent & Need Gate",
                "stage": "gateway",
                "enabled": False,
                "latency_ms": 0.0,
                "count": 1,
                "details": "门控已手动旁路，默认全量检索"
            })

        retrieved_docs: List[Document] = []
        crag_result = CRAGResult(action="CORRECT", confidence_score=1.0, reason="无需检索")
        graph_entities = []

        if needs_retrieval:
            raw_docs, crag_result, graph_entities, sub_trace_steps = hybrid_retriever.retrieve_with_trace(bundle, db)
            trace_steps.extend(sub_trace_steps)

            # Self-RAG Step 2 Trace
            t1 = time.time()
            if self_rag_enabled:
                retrieved_docs, step2_details = self_rag_engine.filter_relevant_and_anti_spoiler(raw_docs, bundle)
                step2_ms = round((time.time() - t1) * 1000.0, 2)
                trace_steps.append({
                    "name": "Self-RAG Step 2: Anti-Spoiler & Relevance",
                    "stage": "relevance_gate",
                    "enabled": True,
                    "latency_ms": step2_ms,
                    "count": len(retrieved_docs),
                    "details": f"切片质检完成: 过滤前 {len(raw_docs)} 篇 -> 通过 {len(retrieved_docs)} 篇"
                })
            else:
                retrieved_docs = raw_docs
        else:
            trace_steps.append({
                "name": "Hybrid Retrieval Pipeline",
                "stage": "retrieval",
                "enabled": False,
                "latency_ms": 0.0,
                "count": 0,
                "details": "因 Self-RAG 判定无需检索，多路召回流水线整体旁路"
            })

        # Dynamic Compressor & Anchor
        t0 = time.time()
        compressed_context, time_anchors, best_anchor = self_rag_engine.compress_and_anchor_context(retrieved_docs)
        comp_ms = round((time.time() - t0) * 1000.0, 2)
        trace_steps.append({
            "name": "Dynamic Context Compressor",
            "stage": "compression",
            "enabled": True,
            "latency_ms": comp_ms,
            "count": len(time_anchors),
            "details": f"时间轴上下文压缩完成，提取到 {len(time_anchors)} 个高光定位锚点" if time_anchors else "未提取到强时间戳锚点"
        })

        total_latency_ms = round((time.time() - start_all) * 1000.0, 2)

        return {
            "trace_id": f"trace-{uuid.uuid4().hex[:8]}",
            "query": bundle.query_str,
            "episode_num": bundle.episode_num,
            "current_sec": bundle.current_sec,
            "total_latency_ms": total_latency_ms,
            "trace_steps": trace_steps,
            "retrieved_documents": [
                {
                    "id": d.id,
                    "text": d.text,
                    "score": round(d.score, 4) if d.score else 0.0,
                    "chunk_strategy": d.chunk_strategy,
                    "episode_num": d.episode_num,
                    "start_sec": d.start_sec,
                    "end_sec": d.end_sec,
                    "time_tag": f"{int(d.start_sec // 60):02d}:{int(d.start_sec % 60):02d}",
                    "source": getattr(d, "source", "vector_or_bm25")
                }
                for d in retrieved_docs
            ],
            "graph_entities": graph_entities,
            "crag_status": crag_result.action,
            "crag_confidence": round(crag_result.confidence_score, 2),
            "crag_reason": crag_result.reason,
            "best_anchor": best_anchor
        }


rag_pipeline = ModularRAGPipeline()
