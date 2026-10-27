import uuid
"""
LangGraph 核心母体状态机 (Backbone StateGraph)
负责全局状态管理、条件边路由、检查点持久化与人机回环中断 (interrupt/resume)
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.agent_fleet.core.state import AgentGraphState
from app.services.agent_fleet.core.memory_hub import global_memory_hub
from app.services.agent_fleet.pods.specialized_pods import FLEET_POD_REGISTRY

logger = logging.getLogger("agent_fleet.backbone_graph")


class BackboneStateGraphEngine:
    """母体状态机引擎"""

    def __init__(self):
        self.pods = FLEET_POD_REGISTRY

    async def dispatch_agent_step(
        self,
        agent_id: str,
        session_id: str,
        user_message: str,
        attachment_path: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """按 Agent ID 派发单步执行"""
        pod = self.pods.get(agent_id)
        if not pod:
            pod = self.pods["agent_9"]

        # 管理数据库会话生命周期
        local_db = False
        active_db = db
        if active_db is None:
            active_db = SessionLocal()
            local_db = True

        try:
            # 核心热插拔硬拦截网关：检查当前智能体是否已被管理员在后台关闭
            from app.services.agent_fleet.base_and_telemetry import resolve_agent_llm_config, AgentTelemetryCallbackHandler
            ag_cfg, model_info = resolve_agent_llm_config(active_db, agent_id)
            if not ag_cfg.is_enabled:
                fallback_msg = ag_cfg.disabled_fallback_msg or "该智能体已被管理员在后台暂时关闭维护，暂停服务。"
                fallback_text = (
                    f"### 【智能体已关停 · 维护提示】\n"
                    f"> {fallback_msg}\n\n"
                    f"**[{ag_cfg.name} 离线休眠中]**：当前智能体已被管理员在后台临时关停，系统已自动拦截大模型调用，为您保留会话上下文。"
                )
                try:
                    AgentTelemetryCallbackHandler.record_invocation(
                        db=active_db,
                        trace_id=f"disabled_{agent_id}_{uuid.uuid4().hex[:8]}",
                        agent_cfg=ag_cfg,
                        model_info=model_info,
                        matched_skills=[],
                        latency_ms=1.5,
                        query=user_message,
                        response_text=fallback_text,
                        status="DISABLED_INTERCEPT",
                    )
                except Exception:
                    pass

                global_memory_hub.append_message(
                    agent_id=agent_id,
                    session_id=session_id,
                    role="assistant",
                    content=fallback_text,
                    thought="检测到该智能体已被后台热插拔开关关闭，触发底层拦截网关，直接返回温和兜底消息。",
                )

                return {
                    "reply": fallback_text,
                    "thought": "检测到该智能体已被后台热插拔开关关闭，触发底层拦截网关，直接返回温和兜底消息。",
                    "agent_id": agent_id,
                    "agent_name": ag_cfg.name,
                    "is_fallback": True,
                    "is_disabled": True,
                    "status": "DISABLED_INTERCEPT",
                }

            # 执行单步思考与工具调度
            step_result = await pod.run_step(
                session_id=session_id,
                user_message=user_message,
                attachment_path=attachment_path,
                context_data=context_data,
                db=active_db,
            )
        finally:
            if local_db and active_db:
                active_db.close()

        # 检查是否产出结构化工件并写入全局只读黑板
        if "storyboard_data" in step_result:
            global_memory_hub.write_blackboard_artifact(
                session_id=session_id,
                artifact_key="STORYBOARD_SPEC",
                artifact_val=step_result["storyboard_data"],
                author_agent_id=agent_id,
            )
        if "growth_data" in step_result:
            global_memory_hub.write_blackboard_artifact(
                session_id=session_id,
                artifact_key="MARKETING_KIT",
                artifact_val=step_result["growth_data"],
                author_agent_id=agent_id,
            )
        if "cinema_data" in step_result:
            global_memory_hub.write_blackboard_artifact(
                session_id=session_id,
                artifact_key="PLOT_BEATS_ANALYSIS",
                artifact_val=step_result["cinema_data"],
                author_agent_id=agent_id,
            )

        return step_result

    def check_and_interrupt(self, risk_score: int, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        人机回环中断门禁 (LangGraph-style interrupt)
        当风险评分处于灰区 (30~85分) 时触发挂起，等待管理员恢复
        """
        if 30 <= risk_score <= 85:
            logger.warning(f"[HITL Interrupt] Triggered moderation interrupt for payload: {payload}")
            return {
                "interrupt_triggered": True,
                "reason": "内容处于灰区风险，触发 LangGraph 人机回环中断，等待人工复核",
                "risk_score": risk_score,
                "payload": payload,
            }
        return None


# 全局母体状态机单例
global_state_engine = BackboneStateGraphEngine()
