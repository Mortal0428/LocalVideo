"""
CinemaAgent 工业级模块化 RAG 核心统一门面 (ModularRAGPipeline)
遵循《03_06 Modular RAG》架构理念，串联离线资产预处理与在线多路召回重排、Self-RAG、CRAG 校验全链路。
对外提供同步查询与 Server-Sent Events (SSE) 异步流式问答标准接口。
"""

import json
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.services.rag.core.datatypes import Document, QueryBundle, RAGResponse, CRAGResult
from app.services.rag.online.hybrid_retriever import hybrid_retriever
from app.services.rag.online.self_rag_engine import self_rag_engine
from app.services.llm_gateway import llm_gateway

logger = logging.getLogger(__name__)


class ModularRAGPipeline:
    """
    模块化高级 RAG 统一执行引擎
    """
    def __init__(self):
        pass

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
        - {"type": "done", "target_time": ..., "time_tag": ...}
        """
        cfg = llm_gateway.get_active_config()
        active_model = cfg.get("chat_model", "deepseek-r1:1.5b")
        active_provider = cfg.get("provider", "ollama")

        # 1. Self-RAG [Retrieve] 门控判定
        needs_retrieval = self_rag_engine.evaluate_retrieval_need(bundle.query_str)
        
        retrieved_docs: List[Document] = []
        crag_result = CRAGResult(action="CORRECT", confidence_score=1.0, reason="无需检索的通用闲聊")
        graph_entities = []
        best_anchor = None

        if needs_retrieval:
            # 2. 三路混合召回 (向量 + BM25 + Neo4j) + 防剧透时序门控 + RRF + Reranker + CRAG
            retrieved_docs, crag_result, graph_entities = hybrid_retriever.retrieve(bundle, db)
            
            # 3. 上下文动态压缩与时间戳锚点提取
            compressed_context, time_anchors, best_anchor = self_rag_engine.compress_and_anchor_context(retrieved_docs)
            
            # 4. 若有最佳定位点，立即向前端抛出 SEEK 动作卡片
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

            # 5. 合成完整推理 Prompt
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

        # 6. 调用 LLM Gateway 流式生成
        async for event in llm_gateway.stream_chat(prompt=prompt):
            event_type = event.get("type")
            if event_type in ("thought", "token", "diagnostic"):
                yield event

        # 7. 抛出完成信号
        jump_sec = best_anchor["timestamp"] if best_anchor else bundle.current_sec
        m, s = divmod(int(jump_sec), 60)
        time_tag = f"{m:02d}:{s:02d}"

        yield {
            "type": "done",
            "target_time": jump_sec,
            "time_tag": time_tag,
            "crag_status": crag_result.action,
            "model_used": f"{active_provider}:{active_model}"
        }

    async def aquery(self, bundle: QueryBundle, db: Session) -> RAGResponse:
        """
        异步完整问答接口 (用于 FastAPI async 端点与全链路大模型推理)
        """
        needs_retrieval = self_rag_engine.evaluate_retrieval_need(bundle.query_str)
        retrieved_docs = []
        crag_result = CRAGResult(action="CORRECT", confidence_score=1.0, reason="无需检索的通用闲聊")
        graph_entities = []
        best_anchor = None
        time_anchors = []

        if needs_retrieval:
            retrieved_docs, crag_result, graph_entities = hybrid_retriever.retrieve(bundle, db)
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
        支持在现有事件循环内通过多线程安全调用，避免死锁或静默跳过大模型推理。
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
            # 纯离线降级方案
            retrieved_docs, crag_result, graph_entities = hybrid_retriever.retrieve(bundle, db)
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


rag_pipeline = ModularRAGPipeline()
