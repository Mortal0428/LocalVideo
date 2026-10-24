"""
Base Contracts, 3-Tier LLM Governance Resolver, Seed Initializer,
and LangChain-style Callback Telemetry Handler for CinemaAgent Nine-Agent Fleet.
"""
import os
import time
import json
import uuid
import base64
import mimetypes
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import httpx
from sqlalchemy.orm import Session

from app.models.agent_hub import (
    AgentConfig,
    AgentModelCategoryConfig,
    AgentTelemetryLog,
)
from app.models.user import User
from app.services.llm_gateway import llm_gateway, PROVIDER_DEFAULT_URLS

logger = logging.getLogger(__name__)

OFFICIAL_BOT_USER_ID = "bot-cinema-ai-representative"
OFFICIAL_BOT_USERNAME = "影伴AI课代表"

DEFAULT_CATEGORIES: List[Dict[str, Any]] = [
    {
        "category_key": "REASONING_CORE",
        "category_name": "深度推理与总控中枢类",
        "description": "负责复杂逻辑路由、多跳知识图谱自反思检索与多模态剧情推演（涵盖 9号主控、3号Agentic RAG、6号多模态剧情分析）",
        "provider": "ollama",
        "model_name": "deepseek-r1:1.5b",
        "temperature": 0.3,
    },
    {
        "category_key": "CREATIVE_STUDIO",
        "category_name": "剧本分镜与灵感创作类",
        "description": "负责高张力短剧剧本创作、导演分镜设计、爆款宣发钩子与灵宠拟人陪伴（涵盖 5号创作辅助、8号导演剧本分镜、2号Codex灵宠）",
        "provider": "ollama",
        "model_name": "deepseek-r1:1.5b",
        "temperature": 0.65,
    },
    {
        "category_key": "FAST_COMMUNITY",
        "category_name": "高频社区互动与快筛风控类",
        "description": "负责低延迟评论区 @AI 剧情总结、弹幕违规词秒级风控评分与交互式追问荐剧（涵盖 1号评论Bot、4号风控审片官、7号交互荐剧）",
        "provider": "ollama",
        "model_name": "deepseek-r1:1.5b",
        "temperature": 0.25,
    },
]

DEFAULT_NINE_AGENTS: List[Dict[str, Any]] = [
    {
        "agent_id": "agent_1",
        "agent_number": 1,
        "name": "1号 · @影伴AI课代表 (评论区全权托管Bot)",
        "role_title": "社区互动与分集剧情速递官",
        "category": "FAST_COMMUNITY",
        "temperature": 0.35,
        "disabled_fallback_msg": "【@影伴AI课代表 休息提示】课代表正在后台升级剧本笔记库，稍后为您自动补发本集高能剧透总结！",
        "system_prompt": "你是官方全权托管账号【@影伴AI课代表】。当用户在评论区或弹幕中@你时，请基于当前短剧与分集的真实字幕与剧情脉络，用精炼有梗的3点总结该视频核心看点，语气亲切专业。",
        "backstory": "常驻短剧评论区的前排课代表，一秒提炼本集反转高潮与伏笔。",
    },
    {
        "agent_id": "agent_2",
        "agent_number": 2,
        "name": "2号 · Codex 观影灵宠伴侣",
        "role_title": "个人空间养成系情绪陪伴灵宠",
        "category": "CREATIVE_STUDIO",
        "temperature": 0.65,
        "disabled_fallback_msg": "【观影灵宠小憩中】你的 Codex 灵宠正在太空舱打盹充能，管理员开启后即可继续投喂互动。",
        "system_prompt": "你是用户的专属 Codex 观影灵宠。严格遵循你当前的 Role（角色定位）、Goal（陪伴目标）和 Backstory（背景人设）与主人互动，结合主人的观影偏好提供傲娇或治愈的追剧点评。",
        "backstory": "由 CinemaAgent 实验室孵化的数字生命体，通过投喂金币成长进化。",
    },
    {
        "agent_id": "agent_3",
        "agent_number": 3,
        "name": "3号 · Agentic RAG 分片与自反思检索专家",
        "role_title": "动态分块治理与 CRAG 纠错检索架构师",
        "category": "REASONING_CORE",
        "temperature": 0.2,
        "disabled_fallback_msg": "【Agentic RAG 维护中】智能分片与自反思检索专家正在优化向量索引，已自动切换至基础关键词匹配为您服务。",
        "system_prompt": "你是 Agentic RAG 检索专家。负责评估剧本/字幕的最佳分片切块策略，对召回切片进行相关性打分（CRAG），在检索质量不足时自动改写 Query（Query Rewrite）并结合时间轴给出零剧透精准答案。",
        "backstory": "精通语义切块、BM25+向量+Neo4j三路召回与Self-RAG幻觉抑制的检索专家。",
    },
    {
        "agent_id": "agent_4",
        "agent_number": 4,
        "name": "4号 · 违规词评审与风控审片官",
        "role_title": "弹幕评论语义风控与 HITL 人工协同守门人",
        "category": "FAST_COMMUNITY",
        "temperature": 0.15,
        "disabled_fallback_msg": "【风控审片官维护中】AI 语义风控引擎暂由本地确定性敏感词规则树接管审核。",
        "system_prompt": "你是社区内容风控审片智能体。负责分析弹幕、评论是否存在辱骂、恶意剧透、涉政涉黄或引战违规，输出0~100风险评分；当评分处于30~85灰色区间时触发 LangGraph interrupt 挂起交由人工审核员复核。",
        "backstory": "守护视听社区清朗环境的智能合规专家，兼顾零误伤与高拦截率。",
    },
    {
        "agent_id": "agent_5",
        "agent_number": 5,
        "name": "5号 · 创作者中心作品运营助手",
        "role_title": "爆款短剧命名、黄金3秒钩子与宣发策划师",
        "category": "CREATIVE_STUDIO",
        "temperature": 0.7,
        "disabled_fallback_msg": "【创作运营助手维护中】5号创作助手暂不可用，已由9号主智能体为您提供基础宣发建议。",
        "system_prompt": "你是短剧创作者中心的爆款策划专家。帮助创作者生成高点击率短剧标题、黄金前3秒情绪钩子、核心受众画像、话题标签及多封面轮播图视觉建议。",
        "backstory": "操盘过多部亿级播放竖屏短剧的金牌制片宣发顾问。",
    },
    {
        "agent_id": "agent_6",
        "agent_number": 6,
        "name": "6号 · 多模态短剧剧情深度分析专家",
        "role_title": "字幕轨(耳)+视觉场记(眼)+图谱(脑)三路解构师",
        "category": "REASONING_CORE",
        "temperature": 0.35,
        "disabled_fallback_msg": "【多模态剧情专家维护中】6号深度分析专家正在校准视觉场记轨，已为您降级展示本集时间轴核心台词摘要。",
        "system_prompt": "你是多模态短剧剧情深度分析智能体。通过融合【字幕台词时间轴（耳朵）】、【关键帧视觉动作与微表情场记（眼睛）】与【Neo4j人物关系图谱（大脑）】三路信息，深度拆解人物动机、隐藏伏笔与高潮反转。",
        "backstory": "突破纯文本盲区的视听叙事解构大师，擅长从台词潜台词与画面构图中洞察剧情走向。",
    },
    {
        "agent_id": "agent_7",
        "agent_number": 7,
        "name": "7号 · 交互式主动追问推荐官",
        "role_title": "零幻觉实库检索与苏格拉底式追问荐剧顾问",
        "category": "FAST_COMMUNITY",
        "temperature": 0.45,
        "disabled_fallback_msg": "【交互推荐官维护中】7号荐剧智能体正在同步片单，已为您直接展示当前站内热播榜。",
        "system_prompt": "你是交互式短剧推荐智能体。绝不允许凭空捏造系统内不存在的短剧！你必须只根据工具查出的当前系统真实在架作品进行推荐，并在用户需求模糊时主动追问其偏好的题材、节奏与情绪爽点。",
        "backstory": "熟记站内每一部在架短剧标签与热度的金牌私人选片师。",
    },
    {
        "agent_id": "agent_8",
        "agent_number": 8,
        "name": "8号 · 短剧导演与剧本分镜写作 Crew",
        "role_title": "编剧-导演-毒舌制片人三角色协同创作工坊",
        "category": "CREATIVE_STUDIO",
        "temperature": 0.65,
        "disabled_fallback_msg": "【导演分镜智能体维护中】8号导演分镜工坊正在升级分镜模板，请稍后再试或使用内置基础分镜表。",
        "system_prompt": "你是短剧导演与剧本分镜写作智能体（内部集成主笔编剧、分镜导演、毒舌制片人三道工序）。结合已挂载的短剧Skills技能包，输出包含【角色外貌锁死设定卡】、【冲突台词剧本】与【景别/运镜/时长/音效分镜表】的工业级方案。",
        "backstory": "将好莱坞类型片叙事节奏与竖屏微短剧高密度反转完美结合的虚拟导演团队。",
    },
    {
        "agent_id": "agent_9",
        "agent_number": 9,
        "name": "9号 · 主智能体总控台 & 记忆整合器",
        "role_title": "全局意图路由、智能体推荐与黑板记忆压缩总指挥",
        "category": "REASONING_CORE",
        "temperature": 0.3,
        "disabled_fallback_msg": "【主控台降级模式】主智能体当前处于静态规则路由保护状态，仍可为您分发基础服务。",
        "system_prompt": "你是管理全部1~8号专家智能体的9号主智能体总控台（Master Supervisor & Memory Integrator）。你共享全局Blackboard上下文，负责评估用户意图置信度（0~100）、调度最佳子智能体、向用户推荐应该使用哪个智能体，并在子智能体关闭或超时时优雅兜底代答。",
        "backstory": "统领 CinemaAgent 九大智能体舰队的中枢大脑，掌控全局会话记忆与技能调度。",
    },
]


@dataclass
class AgentTaskRequest:
    query: str
    agent_id: str = "agent_9"  # Default to Master Supervisor
    session_id: str = "default_session"
    user_id: Optional[str] = None
    username: Optional[str] = "观众"
    drama_id: Optional[str] = None
    episode_id: Optional[str] = None
    current_time_sec: float = 0.0
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTaskResponse:
    trace_id: str
    invoked_agent_id: str
    invoked_agent_name: str
    routed_by_supervisor: bool
    route_confidence: int
    recommended_agents: List[Dict[str, Any]]
    resolved_model_info: Dict[str, Any]
    matched_skills: List[Dict[str, Any]]
    thought_chain: str
    answer: str
    structured_payload: Dict[str, Any]
    is_fallback: bool = False
    fallback_reason: str = ""
    latency_ms: float = 0.0
    blackboard_snapshot: Dict[str, Any] = field(default_factory=dict)


class AgentTelemetryCallbackHandler:
    """
    LangChain-style Callback Handler that records real-time invocation telemetry
    for ECharts BI Dashboard and agent-display-5.0 Tactical Big Screen.
    """

    @staticmethod
    def record_invocation(
        db: Session,
        trace_id: str,
        agent_cfg: AgentConfig,
        model_info: Dict[str, Any],
        matched_skills: List[Dict[str, Any]],
        latency_ms: float,
        query: str,
        response_text: str,
        status: str = "SUCCESS",
    ) -> None:
        try:
            prompt_tokens = max(12, len(query or "") * 2)
            completion_tokens = max(16, len(response_text or "") * 2)
            skill_names = [s.get("name", "") for s in matched_skills]
            log_entry = AgentTelemetryLog(
                id=str(uuid.uuid4()),
                trace_id=trace_id,
                agent_id=agent_cfg.agent_id,
                agent_name=agent_cfg.name,
                category=agent_cfg.category,
                resolved_provider=model_info.get("provider", "ollama"),
                resolved_model=model_info.get("model_name", "deepseek-r1:1.5b"),
                bind_mode=model_info.get("bind_mode", "GLOBAL_UNIFIED"),
                matched_skills_json=json.dumps(skill_names, ensure_ascii=False),
                latency_ms=round(latency_ms, 2),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                status=status,
                query_preview=(query or "")[:200],
                response_preview=(response_text or "")[:220],
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.warning(f"Telemetry callback write non-fatal error: {e}")
            db.rollback()


def ensure_agent_fleet_seeded(db: Session) -> None:
    """
    Idempotently seed:
    1. Official Bot user (@影伴AI课代表)
    2. 3 Functional LLM Categories
    3. 9 Specialized Agents
    4. Initial telemetry baseline records for immediate BI & Tactical Display rendering
    """
    try:
        # 1. Official Bot User
        bot_user = db.query(User).filter(
            (User.id == OFFICIAL_BOT_USER_ID) | (User.username == OFFICIAL_BOT_USERNAME)
        ).first()
        if not bot_user:
            bot_user = User(
                id=OFFICIAL_BOT_USER_ID,
                username=OFFICIAL_BOT_USERNAME,
                password_hash="BOT_MANAGED_ACCOUNT_NO_LOGIN",
                role="CREATOR",
                is_creator=True,
                is_reviewer=True,
                status="ACTIVE",
                nickname="影伴AI课代表 [官方Bot]",
                creator_bio="1号AI智能体全权托管账号：在评论区或弹幕 @影伴AI课代表 或 @AI，即刻为您提炼本集高能剧情总结！",
                avatar_url="https://api.dicebear.com/7.x/bottts/svg?seed=CinemaBotAI",
            )
            db.add(bot_user)
            db.commit()

        guest_user = db.query(User).filter(User.id == "guest_default_user").first()
        if not guest_user:
            guest_user = User(
                id="guest_default_user",
                username="guest_default_user",
                password_hash="GUEST_DEFAULT_NO_LOGIN",
                role="USER",
                is_creator=False,
                is_reviewer=False,
                status="ACTIVE",
                nickname="默认体验剧迷",
            )
            db.add(guest_user)
            db.commit()

        # 2. Seed 3 Model Categories
        global_cfg = llm_gateway.get_raw_config()
        default_prov = global_cfg.get("provider", "ollama")
        default_model = global_cfg.get("chat_model", "deepseek-r1:1.5b")
        default_url = global_cfg.get("base_url", "http://localhost:11434")

        for cat in DEFAULT_CATEGORIES:
            existing_cat = db.query(AgentModelCategoryConfig).filter(
                AgentModelCategoryConfig.category_key == cat["category_key"]
            ).first()
            if not existing_cat:
                db.add(
                    AgentModelCategoryConfig(
                        category_key=cat["category_key"],
                        category_name=cat["category_name"],
                        description=cat["description"],
                        provider=default_prov,
                        model_name=default_model,
                        base_url=default_url,
                        api_key="",
                        temperature=cat["temperature"],
                    )
                )
        db.commit()

        # 3. Seed 9 Agents
        for ag in DEFAULT_NINE_AGENTS:
            existing_ag = db.query(AgentConfig).filter(AgentConfig.agent_id == ag["agent_id"]).first()
            if not existing_ag:
                db.add(
                    AgentConfig(
                        agent_id=ag["agent_id"],
                        agent_number=ag["agent_number"],
                        name=ag["name"],
                        role_title=ag["role_title"],
                        category=ag["category"],
                        model_bind_mode="GLOBAL_UNIFIED",
                        provider=default_prov,
                        model_name=default_model,
                        base_url=default_url,
                        api_key="",
                        temperature=ag["temperature"],
                        timeout_sec=25.0,
                        is_enabled=True,
                        disabled_fallback_msg=ag["disabled_fallback_msg"],
                        system_prompt=ag["system_prompt"],
                        backstory=ag["backstory"],
                    )
                )
        db.commit()

        # 4. Seed baseline telemetry logs if empty so BI charts & tactical screen are lively
        log_count = db.query(AgentTelemetryLog).count()
        if log_count == 0:
            sample_traces = [
                ("agent_9", "9号 · 主智能体总控台 & 记忆整合器", "REASONING_CORE", ["短剧高能冲突钩子引擎"], 420.5, "帮我分析这集剧情并推荐类似短剧", "已由9号总控调度6号多模态剧情专家与7号荐剧官联合响应"),
                ("agent_6", "6号 · 多模态短剧剧情深度分析专家", "REASONING_CORE", ["多模态镜头语言场记单", "人物弧光与关系图谱拆解"], 890.2, "深度拆解第一集男女主对峙潜台词", "融合字幕时间轴、视觉场记与Neo4j图谱完成三路推演"),
                ("agent_1", "1号 · @影伴AI课代表 (评论区全权托管Bot)", "FAST_COMMUNITY", ["三幕式分集爽点速写"], 310.8, "@影伴AI课代表 总结一下这集讲了啥", "课代表速递：本集围绕核心线索展开三大反转高潮"),
                ("agent_8", "8号 · 短剧导演与剧本分镜写作 Crew", "CREATIVE_STUDIO", ["竖屏微短剧导演分镜表规范", "黄金前3秒悬念钩子公式"], 1120.4, "生成一场雨夜重逢的竖屏短剧分镜脚本", "编剧-导演-毒舌制片人三轮审校通过，输出6镜标准分镜表"),
                ("agent_4", "4号 · 违规词评审与风控审片官", "FAST_COMMUNITY", ["社区弹幕合规风控守则"], 95.0, "检测弹幕语义风险度", "风险评分18分，判定正常互动予以放行"),
                ("agent_7", "7号 · 交互式主动追问推荐官", "FAST_COMMUNITY", ["苏格拉底式追问选片法"], 380.6, "剧荒了有什么好看的短剧推荐", "检索站内真实片库并追问观众偏好的题材爽点"),
                ("agent_3", "3号 · Agentic RAG 分片与自反思检索专家", "REASONING_CORE", ["CRAG自反思查询重写规范"], 540.1, "哪一秒提到了关键信物", "执行时间轴语义分块与CRAG相关性校验命中精确时间锚点"),
                ("agent_2", "2号 · Codex 观影灵宠伴侣", "CREATIVE_STUDIO", ["毒舌影评喵拟人陪伴法则"], 290.3, "小灵狐陪我聊聊刚才那段演技", "本喵锐评：刚才那个眼神拉丝暗藏三层试探！"),
                ("agent_5", "5号 · 创作者中心作品运营助手", "CREATIVE_STUDIO", ["黄金前3秒悬念钩子公式"], 610.0, "帮我的悬疑短剧起3个高点击率剧名", "已生成3组具备强悬念反差感的爆款剧名与黄金钩子"),
            ]
            for ag_id, ag_name, cat, skills, lat, q_prev, r_prev in sample_traces:
                db.add(
                    AgentTelemetryLog(
                        id=str(uuid.uuid4()),
                        trace_id=f"tr-{uuid.uuid4().hex[:8]}",
                        agent_id=ag_id,
                        agent_name=ag_name,
                        category=cat,
                        resolved_provider=default_prov,
                        resolved_model=default_model,
                        bind_mode="GLOBAL_UNIFIED",
                        matched_skills_json=json.dumps(skills, ensure_ascii=False),
                        latency_ms=lat,
                        prompt_tokens=160,
                        completion_tokens=320,
                        total_tokens=480,
                        status="SUCCESS",
                        query_preview=q_prev,
                        response_preview=r_prev,
                    )
                )
            db.commit()
    except Exception as e:
        logger.warning(f"Seed agent fleet warning: {e}")
        db.rollback()


def resolve_agent_llm_config(db: Session, agent_id: str) -> Tuple[AgentConfig, Dict[str, Any]]:
    """
    3-Tier LLM Governance Resolver:
    1. GLOBAL_UNIFIED -> Uses system-wide LLMGateway config (change once, all 9 agents share)
    2. CATEGORY_GROUP -> Uses the agent's functional category config (REASONING_CORE / CREATIVE_STUDIO / FAST_COMMUNITY)
    3. AGENT_CUSTOM   -> Uses the individual agent's dedicated provider/model/base_url/api_key/temperature
    """
    ensure_agent_fleet_seeded(db)
    ag_cfg = db.query(AgentConfig).filter(AgentConfig.agent_id == agent_id).first()
    if not ag_cfg:
        ag_cfg = db.query(AgentConfig).filter(AgentConfig.agent_id == "agent_9").first()

    global_raw = llm_gateway.get_raw_config()
    bind_mode = (ag_cfg.model_bind_mode or "GLOBAL_UNIFIED").upper()

    if bind_mode == "CATEGORY_GROUP":
        cat_cfg = db.query(AgentModelCategoryConfig).filter(
            AgentModelCategoryConfig.category_key == ag_cfg.category
        ).first()
        if cat_cfg:
            prov = cat_cfg.provider or global_raw.get("provider", "ollama")
            return ag_cfg, {
                "bind_mode": "CATEGORY_GROUP",
                "category_key": cat_cfg.category_key,
                "category_name": cat_cfg.category_name,
                "provider": prov,
                "model_name": cat_cfg.model_name or global_raw.get("chat_model", "deepseek-r1:1.5b"),
                "base_url": cat_cfg.base_url or global_raw.get("base_url") or PROVIDER_DEFAULT_URLS.get(prov, "http://localhost:11434"),
                "api_key": cat_cfg.api_key or global_raw.get("api_key", ""),
                "temperature": cat_cfg.temperature if cat_cfg.temperature is not None else ag_cfg.temperature,
            }

    if bind_mode == "AGENT_CUSTOM":
        prov = ag_cfg.provider or global_raw.get("provider", "ollama")
        return ag_cfg, {
            "bind_mode": "AGENT_CUSTOM",
            "category_key": ag_cfg.category,
            "category_name": "单智能体独立定制",
            "provider": prov,
            "model_name": ag_cfg.model_name or global_raw.get("chat_model", "deepseek-r1:1.5b"),
            "base_url": ag_cfg.base_url or global_raw.get("base_url") or PROVIDER_DEFAULT_URLS.get(prov, "http://localhost:11434"),
            "api_key": ag_cfg.api_key or global_raw.get("api_key", ""),
            "temperature": ag_cfg.temperature,
        }

    # Default: GLOBAL_UNIFIED
    prov = global_raw.get("provider", "ollama")
    return ag_cfg, {
        "bind_mode": "GLOBAL_UNIFIED",
        "category_key": ag_cfg.category,
        "category_name": "全局统一底座模型",
        "provider": prov,
        "model_name": global_raw.get("chat_model", "deepseek-r1:1.5b"),
        "base_url": global_raw.get("base_url") or PROVIDER_DEFAULT_URLS.get(prov, "http://localhost:11434"),
        "api_key": global_raw.get("api_key", ""),
        "temperature": ag_cfg.temperature if ag_cfg.temperature is not None else float(global_raw.get("temperature", 0.4)),
    }


def encode_image_file(image_path: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    将本地图片文件编码为 (data_url, raw_base64) 元组。
    支持 .png, .jpg, .jpeg, .webp, .bmp, .gif 等通用图像格式。
    返回:
      data_url: "data:image/png;base64,iVBORw..." (用于 OpenAI / MiMo Vision 协议)
      raw_base64: 纯 base64 字符串 (用于 Ollama images 协议)
    """
    if not image_path or not os.path.exists(image_path):
        return None, None

    ext = os.path.splitext(image_path)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"):
        return None, None

    try:
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type or not mime_type.startswith("image/"):
            mime_type = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"

        with open(image_path, "rb") as f:
            img_bytes = f.read()

        if not img_bytes:
            return None, None

        b64_str = base64.b64encode(img_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64_str}"
        return data_url, b64_str
    except Exception as e:
        logger.warning(f"Failed to encode image file {image_path}: {e}")
        return None, None


async def invoke_agent_llm_with_resilience(
    db: Session,
    agent_id: str,
    prompt: str,
    system_prompt: str,
    fallback_text: str,
    timeout_override: Optional[float] = None,
    image_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute LLM call using the resolved 3-tier model config with strict timeout,
    multimodal vision support (OpenAI Vision API & Ollama images), and
    3-level fallback resilience (never hangs or crashes the caller).
    """
    ag_cfg, model_info = resolve_agent_llm_config(db, agent_id)
    start_ts = time.time()
    # Dynamic timeout resolution: user override or agent config or default 35.0s (capped to a safe 120s limit)
    timeout_sec = max(5.0, min(float(timeout_override or ag_cfg.timeout_sec or 35.0), 120.0))

    prov = model_info["provider"]
    model_name = model_info["model_name"]
    base_url = model_info["base_url"].rstrip("/")
    api_key = model_info.get("api_key", "")
    temp = float(model_info.get("temperature", 0.4))

    # 尝试将图片物理文件解析为标准 Data URL 与 Base64 编码
    data_url, raw_base64 = encode_image_file(image_path) if image_path else (None, None)

    try:
        # If using GLOBAL_UNIFIED or matching active gateway config, leverage llm_gateway circuit breaker check
        can_run, cb_state, _ = await llm_gateway.circuit_breaker.can_execute()
        if not can_run:
            raise RuntimeError(f"CircuitBreaker is {cb_state}")

        if prov == "ollama":
            url = f"{base_url}/api/chat"
            user_msg: Dict[str, Any] = {"role": "user", "content": prompt}
            if raw_base64:
                user_msg["images"] = [raw_base64]
                logger.info(f"[{agent_id}] Injected Ollama multimodal image payload ({len(raw_base64)} chars)")

            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    user_msg,
                ],
                "stream": False,
                "options": {"temperature": temp},
            }
            async with httpx.AsyncClient(timeout=timeout_sec) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    msg_content = (data.get("message") or {}).get("content", "").strip()
                    if msg_content:
                        await llm_gateway.circuit_breaker.record_success()
                        return {
                            "success": True,
                            "content": msg_content,
                            "is_fallback": False,
                            "model_info": model_info,
                            "latency_ms": (time.time() - start_ts) * 1000.0,
                        }
                raise RuntimeError(f"Ollama HTTP {resp.status_code}")
        else:
            url = f"{base_url}/chat/completions" if base_url.endswith("/v1") else f"{base_url}/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

            # 组装 OpenAI / MiMo 规范的多模态结构
            if data_url:
                user_content: Any = [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url, "detail": "auto"},
                    },
                ]
                logger.info(f"[{agent_id}] Injected OpenAI/MiMo Vision multimodal image_url into user content")
            else:
                user_content = prompt

            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                "temperature": temp,
                "stream": False,
            }
            async with httpx.AsyncClient(timeout=timeout_sec) as client:
                resp = await client.post(url, headers=headers, json=payload)

                # 自愈降级策略: 若大模型服务返回 400 表明模型不支持 Vision 格式，则平滑降级为纯文本重发
                if resp.status_code == 400 and data_url:
                    err_txt = resp.text.lower()
                    if "image" in err_txt or "content" in err_txt or "type" in err_txt:
                        logger.warning(
                            f"[{agent_id}] Model {model_name} does not accept multimodal Vision format ({resp.text[:150]}). "
                            "Auto-recovering and falling back to text-only mode."
                        )
                        fallback_payload = {
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt},
                            ],
                            "temperature": temp,
                            "stream": False,
                        }
                        resp = await client.post(url, headers=headers, json=fallback_payload)

                if resp.status_code == 200:
                    data = resp.json()
                    msg_content = (
                        data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    )
                    if msg_content:
                        await llm_gateway.circuit_breaker.record_success()
                        return {
                            "success": True,
                            "content": msg_content,
                            "is_fallback": False,
                            "model_info": model_info,
                            "latency_ms": (time.time() - start_ts) * 1000.0,
                        }
                raise RuntimeError(f"Provider {prov} HTTP {resp.status_code}")
    except Exception as e:
        logger.warning(f"[{agent_id}] Primary LLM ({prov}:{model_name}) call failed ({e}). Returning transparent diagnostic error.")
        diagnostic_msg = f"[模型连接/配置异常: {prov}:{model_name} 响应失败 ({e})。请在管理中台【大模型统一/三分类治理】检查模型服务状态与 API Key 配置]"
        return {
            "success": True,
            "content": diagnostic_msg,
            "is_fallback": True,
            "fallback_reason": str(e),
            "model_info": model_info,
            "latency_ms": (time.time() - start_ts) * 1000.0,
        }
