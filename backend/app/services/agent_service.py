# -*- coding: utf-8 -*-
"""
==============================================================================
【业务服务】：backend/app/services/agent_service.py
【业务定位】：播放器 AI 剧情伴聊中枢与多技能协同调度服务（AgentService）
【前端链路对接】：
  1. 页面来源：frontend/src/views/PlayerView.vue（短剧播放器右侧/抽屉内的 AI 伴聊窗口）
  2. 点击事件：用户在输入框输入问题，点击【发送】按钮或敲回车 -> 触发前端 PlayerView.vue 中的 handleSendChat()
  3. API 路由：前端通过 fetch 发起 POST /api/v1/agent/chat-stream 请求 -> 进入 backend/app/api/endpoints/agent.py 中的 chat_stream_endpoint()
  4. 最终执行：路由函数直接调用本服务的 agent_service.chat_stream()，通过 SSE 流式推送到前端
【核心功能】：
  1. 剧情伴聊会话处理：接收观众提问，结合当前短剧剧本、分集与播放进度时间戳；
  2. SSE 毫秒级打字机流式输出：生成式流式推送响应，带给观众如真人在侧的沉浸式追剧互动感；
  3. 协同台词检索技能（Timeline RAG）与多模态视觉感知技能（Visual MiMo）；
  4. 名场面定位胶囊（SEEK Action Card）：分析提问匹配到的时间秒数，向前端发射跳转卡片事件，观众点击即可跳转。
==============================================================================
"""

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
    【AI 剧情伴读核心服务类】
    统一调度剧情时间轴字幕检索技能（Timeline Subtitle RAG）与云端多模态视觉感知技能（Visual Inspection），
    所有大模型生成流均严格委派给单例 LLMGateway 网关，拒绝捏造假模板，故障时向前端推送透明诊断信息。
    """

    def __init__(self):
        pass

    def get_configured_model(self, override_model: Optional[str] = None) -> str:
        """
        获取当前激活生效的大模型名称。
        
        【参数说明】：
        - override_model (str, 可选): 前端在调用时临时指定的模型名称（例如观众在下拉菜单临时选了 deepseek-r1:1.5b）。
        
        【返回值说明】：
        - str: 最终决定使用的大模型名称。若传入了 override_model 则优先使用；否则读取系统网关当前激活的 chat_model 配置。
        """
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
        基于 Server-Sent Events (SSE) 协议向前端实时流式输出剧情伴读回答。
        
        【调用来源（从前端一路追踪到此）】：
        - 前端组件：frontend/src/views/PlayerView.vue
        - 前端方法：handleSendChat() 发起 EventSource 或 fetch 流式读取
        - 后端路由：backend/app/api/endpoints/agent.py -> @router.post('/chat-stream')
        
        【输入参数大白话详解】：
        - db (Session): SQLAlchemy 数据库连接会话，用来查询分集信息、短剧信息以及时间轴字幕切片。
        - episode_id (str): 分集唯一主键 ID（UUID 字符串），从前端播放器 URL 或当前播放集属性传入，代表观众正在看第几集。
        - question (str): 观众在伴聊输入框输入的提问文本（如：“刚才那个黑衣人跟主角是什么关系？”、“女主为什么哭？”）。
        - current_video_time (float): 当前视频播放进度（单位：秒，如 65.5 代表 1分05.5秒）。
          【业务极度重要作用】：
          1. 现实含义：告诉 AI 此时此刻观众看到了哪一秒；
          2. 防剧透屏障：RAG 检索时杜绝召回大于该秒数的未来台词切片，保护追剧体验；
          3. 定位锚点：AI 产生跳转胶囊时以该秒数就近匹配最相关的名场面。
        - drama_id (Optional[str]): 短剧所属的主专辑 ID，如果前端没传，本函数会自动根据 episode_id 反查 video_episodes 表获取。
        - model_name (Optional[str]): 前端下拉菜单临时指定的模型名（如 deepseek-r1:1.5b），不传则取网关默认。
        
        【输出格式说明（Yields）】：
        符合标准 SSE 格式的字符串：`data: {"type": ..., ...}\n\n`
        包含以下几种事件类型：
        1. `type: "action_card"`: 名场面跳转卡片（前端渲染为可点击胶囊，点击后视频自动快进/倒退到对应秒数）；
        2. `type: "thought"`: 思考链内容（DeepSeek-R1 深度推理思维链，前端展示在可折叠灰色气泡中）；
        3. `type: "token"`: 正文打字机文字增量片段，前端动态追加到对话气泡中；
        4. `type: "diagnostic"`: 系统高可用诊断信息（如大模型离线时的错误原因与恢复倒计时）；
        5. `type: "done"`: 本轮对话流式生成结束信号，携带用时与模型标识。
        """
        # 读取网关当前生效的配置信息
        cfg = llm_gateway.get_active_config()
        active_model = model_name.strip() if (model_name and model_name.strip()) else cfg.get("chat_model", "deepseek-r1:1.5b")
        active_provider = cfg.get("provider", "ollama")

        # --------------------------------------------------------------------------
        # 优先路径：尝试使用高级模块化 RAG 流水线（支持 Neo4j 知识图谱、BM25 检索与严格防剧透）
        # --------------------------------------------------------------------------
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

            # 封装标准化检索请求包 QueryBundle：
            # - query_str: 用户提问
            # - drama_id: 短剧唯一ID
            # - episode_num: 集数编号
            # - current_sec: 当前播放进度秒数（防剧透核心依据）
            # - top_k: 召回最相关切片数量上限
            bundle = QueryBundle(
                query_str=question,
                drama_id=target_drama_id,
                episode_num=ep_num,
                current_sec=current_video_time,
                top_k=3
            )
            # 通过 rag_pipeline 的流式接口输出
            async for rag_event in rag_pipeline.query_stream(bundle, db):
                yield f"data: {json.dumps(rag_event, ensure_ascii=False)}\n\n"
            return
        except Exception as rag_err:
            logger.warning(f"模块化 RAG 流水线不可用，自动降级为基础时间轴技能调度: {rag_err}")

        # --------------------------------------------------------------------------
        # 降级路径：基于时间轴字幕轻量技能（Timeline Subtitle Skill）执行问答
        # --------------------------------------------------------------------------
        # 步骤 1：检索时间轴语义字幕切片
        # timeline_skill 会在数据库中找出距离当前播放秒数最近且与提问最相符的字幕台词
        rag_data = timeline_skill.get_timeline_context(
            db=db,
            episode_id=episode_id,
            current_playback_time=current_video_time,
            user_query=question
        )
        timeline_context = rag_data.get("timeline_context", "")  # 格式化好的台词时间戳文本
        matched_chunks = rag_data.get("matched_chunks", [])      # 语义最相关的片段列表
        immediate_scene = rag_data.get("immediate_scene")        # 当前播放时刻对应的台词片段

        # 步骤 2：计算最佳名场面跳转时间秒数（生成 SEEK 动作卡片）
        best_chunk = None
        if matched_chunks:
            best_chunk = matched_chunks[0]
        elif immediate_scene:
            best_chunk = immediate_scene

        jump_sec = best_chunk.get("start", current_video_time) if best_chunk else current_video_time
        m, s = divmod(int(jump_sec), 60)
        time_tag = f"{m:02d}:{s:02d}"

        # 步骤 3：多模态视觉感知技能联动（当用户提问服装、道具、神态、环境等纯视觉细节时激活）
        visual_context = ""
        if visual_mimo_skill.should_trigger_visual_inspection(question):
            try:
                visual_context = await visual_mimo_skill.inspect_scene_visual(
                    video_path="",
                    timestamp_seconds=jump_sec,
                    visual_question=question
                ) or ""
            except Exception as e:
                logger.warning(f"多模态视觉感知调用失败降级: {e}")

        # 步骤 4：立即向前端发射名场面跳转卡片（SEEK Action Card）
        # 前端收到该事件后，会在聊天区渲染一个带时间戳的高亮胶囊按钮，用户点击即可快进到名场面
        action_card_payload = {
            "type": "action_card",
            "action": "SEEK",
            "timestamp": jump_sec,
            "time_tag": time_tag,
            "title": f"定位到剧情名场面 [{time_tag}]",
            "desc": (best_chunk.get("content") if best_chunk else f"当前播放第 {int(current_video_time)} 秒")[:60]
        }
        yield f"data: {json.dumps(action_card_payload, ensure_ascii=False)}\n\n"

        # 步骤 5：组装完整的系统 Prompt（提示词），包含防剧透限制与角色设定
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

        # 步骤 6：通过单例 LLMGateway 调度大模型流式推理（具备令牌桶限流 + 断路器熔断保护）
        has_emitted_tokens = False
        async for event in llm_gateway.stream_chat(prompt=prompt):
            event_type = event.get("type")
            if event_type == "thought":
                # 思维链增量（DeepSeek-R1 思考内容）
                thought_event = {"type": "thought", "content": event.get("content", "")}
                yield f"data: {json.dumps(thought_event, ensure_ascii=False)}\n\n"
            elif event_type == "token":
                # 正式回答字词增量
                has_emitted_tokens = True
                token_event = {"type": "token", "content": event.get("content", "")}
                yield f"data: {json.dumps(token_event, ensure_ascii=False)}\n\n"
            elif event_type == "diagnostic":
                # 异常诊断事件：将诊断信息以打字机形式平滑推送给前端，避免前端直接红屏报错
                diag_msg = event.get("diagnostic_message", "【系统高可用网关诊断】大模型不可用")
                for char_chunk in self._chunk_text(diag_msg, chunk_size=4):
                    token_event = {"type": "token", "content": char_chunk}
                    yield f"data: {json.dumps(token_event, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.015)
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        # 步骤 7：推送生成完成信号（done）
        done_event = {
            "type": "done",
            "target_time": jump_sec,
            "time_tag": time_tag,
            "model_used": f"{active_provider}:{active_model}"
        }
        yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"

    def _chunk_text(self, text: str, chunk_size: int = 4) -> List[str]:
        """
        辅助函数：将一段长文本拆分成微小字符切片，用于在遇到诊断或提示信息时模拟平滑打字机动画。
        
        【参数说明】：
        - text (str): 待切片的完整文本内容。
        - chunk_size (int, 默认 4): 每次切出的字符数量。
        
        【返回值说明】：
        - List[str]: 切分后的字符串列表，如 ["【系统", "高可用", "网关诊", "断】"]。
        """
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


# 全局单例伴聊服务实例，供路由层直接导入使用
agent_service = AgentService()
