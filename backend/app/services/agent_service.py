import os
import json
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.services.skills.timeline_rag_skill import timeline_skill
from app.services.skills.visual_mimo_skill import visual_mimo_skill
from app.services.llm_gateway import llm_gateway

logger = logging.getLogger(__name__)

class AgentService:
    """
    Unified AI Drama Companion Agent Service.
    Integrates Timeline Subtitle RAG Skill + Cloud Multimodal Visual Inspection Skill.
    Delegates all model streaming strictly to singleton LLMGateway.
    Zero fake template fallback texts; outputs transparent system diagnostics on failure.
    """

    def __init__(self):
        pass

    def get_configured_model(self, override_model: Optional[str] = None) -> str:
        """Get the active model name, prioritizing runtime override or gateway config."""
        if override_model and override_model.strip():
            return override_model.strip()
        cfg = llm_gateway.get_active_config()
        return cfg.get("chat_model", "deepseek-r1:1.5b")

    async def chat_stream(
        self,
        db: Session,
        episode_id: str,
        question: str,
        current_video_time: float = 0.0,
        drama_id: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream companion agent chat response using Server-Sent Events (SSE).
        Yields JSON strings formatted as `data: {...}\n\n`.
        """
        cfg = llm_gateway.get_active_config()
        active_model = model_name.strip() if (model_name and model_name.strip()) else cfg.get("chat_model", "deepseek-r1:1.5b")
        active_provider = cfg.get("provider", "ollama")

        # Priority: Check Modular RAG Pipeline with Neo4j, BM25 and Anti-Spoiling
        try:
            from app.services.rag.online.pipeline import rag_pipeline
            from app.services.rag.core.datatypes import QueryBundle
            from app.models.rag_corpus import RAGChunk
            from app.models.video import VideoEpisode

            ep_num = 1
            target_drama_id = drama_id or episode_id
            ep_rec = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
            if ep_rec:
                ep_num = ep_rec.episode_num or 1
                if not drama_id:
                    target_drama_id = ep_rec.video_id or episode_id

            bundle = QueryBundle(
                query_str=question,
                drama_id=target_drama_id,
                episode_num=ep_num,
                current_sec=current_video_time,
                top_k=3
            )
            async for rag_event in rag_pipeline.query_stream(bundle, db):
                yield f"data: {json.dumps(rag_event, ensure_ascii=False)}\n\n"
            return
        except Exception as rag_err:
            logger.warning(f"Modular RAG pipeline fallback to timeline skill: {rag_err}")

        # 1. Timeline Semantic & Subtitle Retrieval
        rag_data = timeline_skill.get_timeline_context(
            db=db,
            episode_id=episode_id,
            current_playback_time=current_video_time,
            user_query=question
        )
        timeline_context = rag_data.get("timeline_context", "")
        matched_chunks = rag_data.get("matched_chunks", [])
        immediate_scene = rag_data.get("immediate_scene")

        # 2. Determine Best Jump Target (SEEK Action Card)
        best_chunk = None
        if matched_chunks:
            best_chunk = matched_chunks[0]
        elif immediate_scene:
            best_chunk = immediate_scene

        jump_sec = best_chunk.get("start", current_video_time) if best_chunk else current_video_time
        m, s = divmod(int(jump_sec), 60)
        time_tag = f"{m:02d}:{s:02d}"

        # 3. Cloud Multimodal Visual Inspection (if user asks about visual appearance/props)
        visual_context = ""
        if visual_mimo_skill.should_trigger_visual_inspection(question):
            try:
                visual_context = await visual_mimo_skill.inspect_scene_visual(
                    video_path="",
                    timestamp_seconds=jump_sec,
                    visual_question=question
                ) or ""
            except Exception as e:
                logger.warning(f"Visual skill inspection failed: {e}")

        # 4. Emit Action Card Event immediately so frontend renders clickable jump pill
        action_card_payload = {
            "type": "action_card",
            "action": "SEEK",
            "timestamp": jump_sec,
            "time_tag": time_tag,
            "title": f"定位到剧情名场面 [{time_tag}]",
            "desc": (best_chunk.get("content") if best_chunk else f"当前播放第 {int(current_video_time)} 秒")[:60]
        }
        yield f"data: {json.dumps(action_card_payload, ensure_ascii=False)}\n\n"

        # 5. Build Comprehensive Prompt
        prompt = (
            f"你是短剧智能伴读 Agent（当前引擎: {active_provider}:{active_model}）。\n"
            f"用户正在观看短剧（当前进度: 约 {int(current_video_time)} 秒）。\n"
            f"以下是时间轴字幕与剧情切片上下文：\n{timeline_context}\n"
        )
        if visual_context:
            prompt += f"\n【云端多模态视觉感知分析】：\n{visual_context}\n"

        prompt += (
            f"\n用户提问：{question}\n"
            f"请用生动、引人入胜的解说风格回答，并在分析关键情节时带上精确时间戳 `[{time_tag} 跳转]`。\n"
            f"回答请保持亲切紧凑，结构清晰。"
        )

        # 6. Stream from LLMGateway (TokenBucket + CircuitBreaker + Tenacity + Multi-Provider)
        has_emitted_tokens = False
        async for event in llm_gateway.stream_chat(prompt=prompt):
            event_type = event.get("type")
            if event_type == "thought":
                thought_event = {"type": "thought", "content": event.get("content", "")}
                yield f"data: {json.dumps(thought_event, ensure_ascii=False)}\n\n"
            elif event_type == "token":
                has_emitted_tokens = True
                token_event = {"type": "token", "content": event.get("content", "")}
                yield f"data: {json.dumps(token_event, ensure_ascii=False)}\n\n"
            elif event_type == "diagnostic":
                # Push transparent diagnostic structure and stream diagnostic message as typewriter tokens
                diag_msg = event.get("diagnostic_message", "【系统高可用网关诊断】大模型不可用")
                for char_chunk in self._chunk_text(diag_msg, chunk_size=4):
                    token_event = {"type": "token", "content": char_chunk}
                    yield f"data: {json.dumps(token_event, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.015)
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        # 7. Emit Finished Event
        done_event = {
            "type": "done",
            "target_time": jump_sec,
            "time_tag": time_tag,
            "model_used": f"{active_provider}:{active_model}"
        }
        yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"

    def _chunk_text(self, text: str, chunk_size: int = 4) -> List[str]:
        """Split text into small slices for streaming typewriter effect."""
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

agent_service = AgentService()
