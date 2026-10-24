"""
Agent 9: Master Supervisor & Admin Memory Integrator (CinemaAgent).
Coordinates:
- 0~100 Confidence Intent Routing (`AdvancedRouter`)
- Agent Recommendation Capsules (`recommended_agents`)
- Hot-Pluggable Agent Switch & Graceful Disabled Fallback (`disabled_fallback_msg`)
- Shared Blackboard Context & Auto-Summarization (`BlackboardMemoryIntegrator`)
- Progressive Skills Injection (`match_and_inject_skills`)
- Real-time Telemetry & BI Aggregation for ECharts and `agent-display-5.0`
"""
import time
import json
import uuid
import logging
from typing import Dict, Any, List, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.agent_hub import (
    AgentConfig,
    AgentModelCategoryConfig,
    SkillConfig,
    AgentBlackboardSession,
    ModerationInterruptQueue,
    AgentTelemetryLog,
)
from app.services.agent_fleet.base_and_telemetry import (
    AgentTaskRequest,
    AgentTaskResponse,
    AgentTelemetryCallbackHandler,
    ensure_agent_fleet_seeded,
    resolve_agent_llm_config,
)
from app.services.agent_fleet.skill_registry import ensure_skills_seeded, match_and_inject_skills
from app.services.agent_fleet.blackboard_memory import BlackboardMemoryIntegrator
from app.services.agent_fleet.workers_community import (
    run_agent_1_comment_bot,
    run_agent_2_codex_pet,
)
from app.services.agent_fleet.workers_rag_safety import (
    run_agent_3_agentic_rag,
    run_agent_4_safety_guard,
)
from app.services.agent_fleet.workers_cinema import (
    run_agent_6_multimodal_plot,
    run_agent_7_recommender,
)
from app.services.agent_fleet.workers_creator import (
    run_agent_5_creator_assist,
    run_agent_8_director_crew,
)

logger = logging.getLogger(__name__)

ROUTING_RULES: List[Tuple[str, List[str], str]] = [
    ("agent_1", ["@影伴ai课代表", "@ai", "@课代表", "课代表", "总结这个视频", "30秒速通"], "检测到 @课代表 召唤或分集速通总结意图"),
    ("agent_2", ["灵宠", "小灵狐", "宠物", "喵", "喂食", "陪我聊", "陪伴", "codex"], "检测到个人空间观影灵宠陪伴互动意图"),
    ("agent_3", ["分片", "切块", "rag", "向量", "crag", "哪一秒", "几分几秒", "时间轴检索"], "检测到 Agentic RAG 分片切块与精确时间锚点检索意图"),
    ("agent_4", ["违规", "敏感词", "审核", "风控", "弹幕举报", "辱骂", "封禁"], "检测到弹幕/评论内容安全与违规词风控评审意图"),
    ("agent_5", ["起名", "剧名", "爆款标题", "黄金3秒", "钩子", "宣发", "创作者辅助", "标签推荐"], "检测到创作者中心爆款作品标题与运营辅助意图"),
    ("agent_8", ["分镜", "导演", "写剧本", "剧本创作", "镜头表", "景别", "运镜", "编剧"], "检测到短剧导演剧本与 9:16 分镜表创作意图"),
    ("agent_7", ["推荐", "好看的", "剧荒", "想看", "类似", "选片", "什么剧"], "检测到基于站内真实片库的交互式追问荐剧意图"),
    ("agent_6", ["剧情", "分析", "解读", "为什么", "动机", "伏笔", "反转", "人物关系", "深析"], "检测到多模态（字幕耳+视觉眼+图谱脑）短剧剧情深度分析意图"),
]


class MasterAgentIntegrator:
    """
    Central orchestrator for the 9-Agent Fleet.
    """

    @staticmethod
    def route_and_recommend(
        db: Session,
        query: str,
        requested_agent_id: str = "agent_9",
    ) -> Tuple[str, bool, int, List[Dict[str, Any]]]:
        """
        Compute 0~100 routing confidence and return top 3 recommended specialist agents.
        If `requested_agent_id` is explicitly `agent_1`..`agent_8`, honors it directly;
        if `agent_9` (Master Supervisor), automatically routes to the highest-scoring specialist.
        """
        ensure_agent_fleet_seeded(db)
        all_agents = {
            a.agent_id: a for a in db.query(AgentConfig).order_by(AgentConfig.agent_number.asc()).all()
        }
        q_lower = (query or "").lower()

        scored: List[Tuple[int, str, str]] = []
        for ag_id, kws, reason in ROUTING_RULES:
            hits = sum(1 for k in kws if k in q_lower)
            if hits > 0:
                conf = min(98, 76 + hits * 8)
                scored.append((conf, ag_id, reason))
            else:
                scored.append((45, ag_id, "可作为协同备选领域专家调用"))

        scored.sort(key=lambda x: x[0], reverse=True)

        recommendations: List[Dict[str, Any]] = []
        for conf, ag_id, reason in scored[:3]:
            ag_obj = all_agents.get(ag_id)
            if ag_obj:
                recommendations.append(
                    {
                        "agent_id": ag_id,
                        "agent_number": ag_obj.agent_number,
                        "name": ag_obj.name,
                        "role_title": ag_obj.role_title,
                        "confidence": conf,
                        "is_enabled": bool(ag_obj.is_enabled),
                        "reason": reason,
                    }
                )

        if requested_agent_id and requested_agent_id != "agent_9" and requested_agent_id in all_agents:
            return requested_agent_id, False, 100, recommendations

        # Supervisor auto-routing
        best_conf, best_ag_id, _ = scored[0]
        if best_conf >= 75:
            return best_ag_id, True, best_conf, recommendations
        # Default to Agent 6 (Multimodal Plot Analyst) for general drama questions
        return "agent_6", True, 82, recommendations

    @classmethod
    async def dispatch(cls, db: Session, req: AgentTaskRequest) -> AgentTaskResponse:
        start_ts = time.time()
        trace_id = f"tr-{uuid.uuid4().hex[:10]}"
        ensure_agent_fleet_seeded(db)
        ensure_skills_seeded(db)

        # 1. Load Shared Blackboard Context
        bb_session = BlackboardMemoryIntegrator.get_or_create_session(
            db=db,
            session_id=req.session_id,
            user_id=req.user_id,
            drama_id=req.drama_id,
            episode_id=req.episode_id,
        )
        blackboard_prompt = BlackboardMemoryIntegrator.build_context_prompt(bb_session)

        # 2. Route & Recommend via Agent 9 Supervisor
        target_agent_id, routed_by_sup, route_conf, recommended_agents = cls.route_and_recommend(
            db=db,
            query=req.query,
            requested_agent_id=req.agent_id,
        )

        ag_cfg, model_info = resolve_agent_llm_config(db, target_agent_id)
        sup_cfg, _ = resolve_agent_llm_config(db, "agent_9")

        # 3. Hot-Plug Switch Check (`is_enabled == False` -> Graceful Fallback Banner)
        if not ag_cfg.is_enabled:
            latency_ms = round((time.time() - start_ts) * 1000.0, 2)
            fallback_banner = (
                f"### 【智能体热插拔兜底提示】\n"
                f"> {ag_cfg.disabled_fallback_msg}\n\n"
                f"**[9号主智能体总控台 · 应急接管回答]**：\n"
                f"您刚才请求了 **{ag_cfg.name}**，由于管理员已在后台临时关闭该智能体，9号主控台已结合全局黑板记忆为您接管响应："
                f"针对您的提问“{req.query[:80]}”，系统已为您保留当前会话上下文，您也可以直接点击下方推荐胶囊切换至其他在线专家智能体。"
            )
            AgentTelemetryCallbackHandler.record_invocation(
                db=db,
                trace_id=trace_id,
                agent_cfg=ag_cfg,
                model_info=model_info,
                matched_skills=[],
                latency_ms=latency_ms,
                query=req.query,
                response_text=fallback_banner,
                status="DISABLED_INTERCEPT",
            )
            bb_snap = BlackboardMemoryIntegrator.append_turn_and_auto_compress(
                db=db,
                session_id=req.session_id,
                agent_id="agent_9_fallback",
                query=req.query,
                answer=fallback_banner,
                user_id=req.user_id,
                drama_id=req.drama_id,
                episode_id=req.episode_id,
            )
            return AgentTaskResponse(
                trace_id=trace_id,
                invoked_agent_id=ag_cfg.agent_id,
                invoked_agent_name=ag_cfg.name,
                routed_by_supervisor=True,
                route_confidence=route_conf,
                recommended_agents=recommended_agents,
                resolved_model_info=model_info,
                matched_skills=[],
                thought_chain=f"检测到 [{ag_cfg.name}] 处于后台热关停状态 (is_enabled=False) -> 触发预设兜底提示 -> 9号主控无缝接管",
                answer=fallback_banner,
                structured_payload={"disabled_agent_id": ag_cfg.agent_id, "fallback_mode": "HOT_PLUG_DISABLED"},
                is_fallback=True,
                fallback_reason="AGENT_DISABLED_BY_ADMIN",
                latency_ms=latency_ms,
                blackboard_snapshot=bb_snap,
            )

        # 4. Progressive Skills Matching & Injection in Thought
        matched_skills, skill_prompt = match_and_inject_skills(db, target_agent_id, req.query)

        # 5. Dispatch to Specialist Worker
        if target_agent_id == "agent_1":
            worker_res = await run_agent_1_comment_bot(
                db=db,
                query=req.query,
                drama_id=req.drama_id,
                episode_id=req.episode_id,
                blackboard_prompt=blackboard_prompt,
                skill_prompt=skill_prompt,
                parent_comment_id=req.extra_params.get("parent_comment_id"),
                root_comment_id=req.extra_params.get("root_comment_id"),
                reply_to_user_id=req.extra_params.get("reply_to_user_id"),
                reply_to_username=req.extra_params.get("reply_to_username"),
            )
        elif target_agent_id == "agent_2":
            worker_res = await run_agent_2_codex_pet(
                db=db,
                query=req.query,
                user_id=req.user_id,
                blackboard_prompt=blackboard_prompt,
                skill_prompt=skill_prompt,
            )
        elif target_agent_id == "agent_3":
            worker_res = await run_agent_3_agentic_rag(
                db=db,
                query=req.query,
                drama_id=req.drama_id,
                episode_id=req.episode_id,
                current_time_sec=req.current_time_sec,
                blackboard_prompt=blackboard_prompt,
                skill_prompt=skill_prompt,
            )
        elif target_agent_id == "agent_4":
            worker_res = await run_agent_4_safety_guard(
                db=db,
                content_text=req.query,
                source_type=req.extra_params.get("source_type", "comment"),
                target_id=req.extra_params.get("target_id"),
                video_id=req.drama_id,
                episode_id=req.episode_id,
                user_id=req.user_id,
                username=req.username or "观众",
                blackboard_prompt=blackboard_prompt,
                skill_prompt=skill_prompt,
            )
        elif target_agent_id == "agent_5":
            worker_res = await run_agent_5_creator_assist(
                db=db,
                query=req.query,
                blackboard_prompt=blackboard_prompt,
                skill_prompt=skill_prompt,
            )
        elif target_agent_id == "agent_7":
            worker_res = await run_agent_7_recommender(
                db=db,
                query=req.query,
                blackboard_prompt=blackboard_prompt,
                skill_prompt=skill_prompt,
            )
        elif target_agent_id == "agent_8":
            worker_res = await run_agent_8_director_crew(
                db=db,
                query=req.query,
                blackboard_prompt=blackboard_prompt,
                skill_prompt=skill_prompt,
            )
        else:
            # Default specialist: Agent 6 Multimodal Plot Deep Analyst
            worker_res = await run_agent_6_multimodal_plot(
                db=db,
                query=req.query,
                drama_id=req.drama_id,
                episode_id=req.episode_id,
                current_time_sec=req.current_time_sec,
                blackboard_prompt=blackboard_prompt,
                skill_prompt=skill_prompt,
            )

        # Prefix supervisor header if routed via Agent 9
        final_answer = worker_res["answer"]
        if routed_by_sup and sup_cfg.is_enabled:
            rec_names = " / ".join([f"【{r['name'].split('·')[-1].strip()}({r['confidence']}%)】" for r in recommended_agents[:2]])
            sup_header = (
                f"> **[9号主控路由 · 置信度 {route_conf}%]** 已自动为您调度 **{ag_cfg.name}** "
                f"（模型策略：`{model_info['bind_mode']} -> {model_info['provider']}:{model_info['model_name']}` | "
                f"推荐协同智能体：{rec_names}）\n\n"
            )
            final_answer = sup_header + final_answer

        total_latency = round((time.time() - start_ts) * 1000.0, 2)
        status_code = "FALLBACK_STATIC" if worker_res.get("is_fallback") else "SUCCESS"

        # 6. Record Telemetry via Callback
        AgentTelemetryCallbackHandler.record_invocation(
            db=db,
            trace_id=trace_id,
            agent_cfg=ag_cfg,
            model_info=model_info,
            matched_skills=matched_skills,
            latency_ms=total_latency,
            query=req.query,
            response_text=final_answer,
            status=status_code,
        )

        # 7. Update Shared Blackboard & Sliding-Window Summarization
        bb_snap = BlackboardMemoryIntegrator.append_turn_and_auto_compress(
            db=db,
            session_id=req.session_id,
            agent_id=ag_cfg.agent_id,
            query=req.query,
            answer=final_answer,
            new_facts={"last_matched_skills": [s["name"] for s in matched_skills]},
            user_id=req.user_id,
            drama_id=req.drama_id,
            episode_id=req.episode_id,
        )

        return AgentTaskResponse(
            trace_id=trace_id,
            invoked_agent_id=ag_cfg.agent_id,
            invoked_agent_name=ag_cfg.name,
            routed_by_supervisor=routed_by_sup,
            route_confidence=route_conf,
            recommended_agents=recommended_agents,
            resolved_model_info=model_info,
            matched_skills=matched_skills,
            thought_chain=worker_res.get("thought", ""),
            answer=final_answer,
            structured_payload=worker_res.get("structured_payload", {}),
            is_fallback=bool(worker_res.get("is_fallback")),
            fallback_reason=worker_res.get("fallback_reason", ""),
            latency_ms=total_latency,
            blackboard_snapshot=bb_snap,
        )

    @staticmethod
    def get_bi_and_tactical_telemetry(db: Session) -> Dict[str, Any]:
        """
        Build comprehensive telemetry payload for:
        1. ECharts Agent BI Data Visualization Dashboard
        2. `agent-display-5.0` 5-Theme Tactical Big Screen Live Bridge
        """
        ensure_agent_fleet_seeded(db)
        ensure_skills_seeded(db)

        agents = db.query(AgentConfig).order_by(AgentConfig.agent_number.asc()).all()
        categories = db.query(AgentModelCategoryConfig).all()
        skills = db.query(SkillConfig).order_by(SkillConfig.hit_count.desc()).all()
        recent_logs = (
            db.query(AgentTelemetryLog)
            .order_by(AgentTelemetryLog.created_at.desc())
            .limit(40)
            .all()
        )
        pending_interrupts = (
            db.query(ModerationInterruptQueue)
            .filter(ModerationInterruptQueue.status == "PENDING")
            .count()
        )
        bb_sessions = db.query(AgentBlackboardSession).count()

        # Per-agent invocation & token aggregations
        agent_stats_map: Dict[str, Dict[str, Any]] = {}
        for a in agents:
            _, res_model = resolve_agent_llm_config(db, a.agent_id)
            agent_stats_map[a.agent_id] = {
                "agent_id": a.agent_id,
                "agent_number": a.agent_number,
                "name": a.name,
                "role_title": a.role_title,
                "category": a.category,
                "is_enabled": bool(a.is_enabled),
                "model_bind_mode": a.model_bind_mode,
                "resolved_provider": res_model["provider"],
                "resolved_model": res_model["model_name"],
                "calls": 0,
                "total_tokens": 0,
                "avg_latency_ms": 0.0,
                "fallback_count": 0,
            }

        total_calls = 0
        total_tokens = 0
        total_latency = 0.0
        fallback_total = 0

        all_logs = db.query(AgentTelemetryLog).all()
        for lg in all_logs:
            total_calls += 1
            total_tokens += lg.total_tokens or 0
            total_latency += lg.latency_ms or 0.0
            if lg.status in ("FALLBACK_STATIC", "DISABLED_INTERCEPT"):
                fallback_total += 1
            if lg.agent_id in agent_stats_map:
                st = agent_stats_map[lg.agent_id]
                st["calls"] += 1
                st["total_tokens"] += lg.total_tokens or 0
                st["avg_latency_ms"] = round(
                    ((st["avg_latency_ms"] * (st["calls"] - 1)) + (lg.latency_ms or 0.0)) / st["calls"],
                    1,
                )
                if lg.status in ("FALLBACK_STATIC", "DISABLED_INTERCEPT"):
                    st["fallback_count"] += 1

        # Category distribution
        cat_distribution = []
        for cat in categories:
            cat_calls = sum(
                v["calls"] for v in agent_stats_map.values() if v["category"] == cat.category_key
            )
            cat_tokens = sum(
                v["total_tokens"] for v in agent_stats_map.values() if v["category"] == cat.category_key
            )
            cat_distribution.append(
                {
                    "category_key": cat.category_key,
                    "category_name": cat.category_name,
                    "provider": cat.provider,
                    "model_name": cat.model_name,
                    "calls": cat_calls,
                    "tokens": cat_tokens,
                }
            )

        # Skill hit rankings
        skill_rankings = [
            {
                "skill_id": s.skill_id,
                "name": s.name,
                "category": s.category,
                "hit_count": s.hit_count or 0,
                "is_global_mount": bool(s.is_global_mount),
                "is_enabled": bool(s.is_enabled),
            }
            for s in skills[:10]
        ]

        return {
            "summary": {
                "total_agents": len(agents),
                "enabled_agents": sum(1 for a in agents if a.is_enabled),
                "total_calls": total_calls,
                "total_tokens": total_tokens,
                "avg_latency_ms": round(total_latency / max(1, total_calls), 1),
                "fallback_rate_pct": round((fallback_total / max(1, total_calls)) * 100.0, 1),
                "total_skills": len(skills),
                "global_mounted_skills": sum(1 for s in skills if s.is_global_mount and s.is_enabled),
                "active_blackboard_sessions": bb_sessions,
                "pending_hitl_interrupts": pending_interrupts,
            },
            "agent_nodes": list(agent_stats_map.values()),
            "category_distribution": cat_distribution,
            "skill_rankings": skill_rankings,
            "recent_traces": [
                {
                    "trace_id": l.trace_id,
                    "agent_id": l.agent_id,
                    "agent_name": l.agent_name,
                    "category": l.category,
                    "resolved_model": f"{l.resolved_provider}:{l.resolved_model}",
                    "bind_mode": l.bind_mode,
                    "matched_skills": json.loads(l.matched_skills_json or "[]"),
                    "latency_ms": l.latency_ms,
                    "total_tokens": l.total_tokens,
                    "status": l.status,
                    "query_preview": l.query_preview,
                    "response_preview": l.response_preview,
                    "created_at": l.created_at.strftime("%H:%M:%S") if l.created_at else "",
                }
                for l in recent_logs
            ],
        }
