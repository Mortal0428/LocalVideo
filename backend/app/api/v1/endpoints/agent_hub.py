"""
==============================================================================
【模块名称】：agent_hub.py (智能体战队总控台与技能调度中枢)
【业务职能】：
  管理平台的多智能体战队（Agent Fleet），包括 8 大专业智能体 Pod 的启停与提示词配置、
  动态模型绑定策略、技能库（Skill）热插拔与挂载、用户专属 AI 伴侣宠物以及违规介入队列。
【对应前端】：
  - 核心页面：frontend/src/views/AdminView.vue (智能体战队 Tab)
  - 伴聊弹窗：frontend/src/components/UniversalAgentChatModal.vue
  - 前端通信：frontend/src/api/admin.ts
==============================================================================
"""
from app.models.interaction import VideoDanmaku, UserComment
from app.models.video import Video, VideoEpisode
from app.models.review import SensitiveWord, SensitiveWordProposal, InteractionInspectionLog
from app.services.agent_fleet.pods.specialized_pods import FLEET_POD_REGISTRY
from app.services.moderation_service import moderation_service
from datetime import datetime

"""
CinemaAgent Nine-Agent Fleet, 3-Tier LLM Governance, Skills Manager,
Codex Pet Cabin, HITL Moderation Resume, and Tactical Telemetry REST API.
"""
import json
import uuid
from dataclasses import asdict
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.api.deps import get_optional_user as get_current_user_optional
from app.models.user import User
from app.models.video import Video
from app.models.rag_corpus import RAGCorpusCategory, RAGCorpus, RAGChunk
from app.models.agent_hub import (
    AgentConfig,
    AgentModelCategoryConfig,
    SkillConfig,
    AgentBlackboardSession,
    ModerationInterruptQueue,
    SkillOperationLog,
)
from app.services.rag.offline.chunker import chunker
from app.services.rag.offline.embedder import embedder
from app.services.llm_gateway import llm_gateway
from app.services.agent_fleet.base_and_telemetry import (
    AgentTaskRequest,
    ensure_agent_fleet_seeded,
    resolve_agent_llm_config,
)
from app.services.agent_fleet.skill_registry import ensure_skills_seeded
from app.services.agent_fleet.blackboard_memory import BlackboardMemoryIntegrator
from app.services.agent_fleet.workers_community import (
    get_or_create_user_pet,
    update_user_pet_persona,
    feed_user_pet_with_coins,
    serialize_pet,
)
from app.services.agent_fleet.workers_rag_safety import resume_moderation_interrupt
from app.services.agent_fleet.master_integrator import MasterAgentIntegrator

router = APIRouter()


class AgentUpdatePayload(BaseModel):
    is_enabled: Optional[bool] = None
    model_bind_mode: Optional[str] = None  # GLOBAL_UNIFIED | CATEGORY_GROUP | AGENT_CUSTOM
    provider: Optional[str] = None
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    disabled_fallback_msg: Optional[str] = None
    system_prompt: Optional[str] = None


class BatchBindModePayload(BaseModel):
    model_bind_mode: str  # GLOBAL_UNIFIED | CATEGORY_GROUP


class BatchAgentConfigPayload(BaseModel):
    agent_ids: List[str]
    provider: Optional[str] = None
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    timeout_sec: Optional[float] = None
    model_bind_mode: Optional[str] = "AGENT_CUSTOM"


class CategoryModelUpdatePayload(BaseModel):
    provider: Optional[str] = None
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = None


class SkillUpsertPayload(BaseModel):
    skill_id: Optional[str] = None
    name: str
    category: str = "短剧编导"
    description: str = ""
    trigger_keywords: str = ""
    skill_markdown: str = ""
    mounted_agents: List[str] = []
    is_global_mount: bool = False
    is_enabled: bool = True


class GlobalMountAllPayload(BaseModel):
    is_global_mount: bool = True


class AgentDispatchPayload(BaseModel):
    query: str
    agent_id: str = "agent_9"
    session_id: str = "global_shared_session"
    drama_id: Optional[str] = None
    episode_id: Optional[str] = None
    current_time_sec: float = 0.0
    extra_params: Dict[str, Any] = {}


class BlackboardCompressPayload(BaseModel):
    session_id: str = "global_shared_session"


class PetPersonaPayload(BaseModel):
    pet_name: Optional[str] = None
    persona_key: Optional[str] = None


class PetFeedPayload(BaseModel):
    coin_amount: Optional[int] = None
    coins_to_feed: Optional[int] = None

    def get_amount(self) -> int:
        if self.coin_amount is not None:
            return int(self.coin_amount)
        if self.coins_to_feed is not None:
            return int(self.coins_to_feed)
        return 5


class InterruptResumePayload(BaseModel):
    action: str = "APPROVE"  # APPROVE | REJECT
    reviewer_note: str = ""


def _serialize_agent(db: Session, ag: AgentConfig) -> Dict[str, Any]:
    _, resolved = resolve_agent_llm_config(db, ag.agent_id)
    return {
        "agent_id": ag.agent_id,
        "agent_number": ag.agent_number,
        "name": ag.name,
        "role_title": ag.role_title,
        "category": ag.category,
        "model_bind_mode": ag.model_bind_mode,
        "provider": ag.provider,
        "model_name": ag.model_name,
        "base_url": ag.base_url or "",
        "temperature": ag.temperature,
        "timeout_sec": ag.timeout_sec,
        "is_enabled": bool(ag.is_enabled),
        "disabled_fallback_msg": ag.disabled_fallback_msg,
        "system_prompt": ag.system_prompt,
        "backstory": ag.backstory,
        "resolved_model": resolved,
    }


def _serialize_skill(sk: SkillConfig) -> Dict[str, Any]:
    try:
        mounted = json.loads(sk.mounted_agents_json or "[]")
    except Exception:
        mounted = []
    return {
        "skill_id": sk.skill_id,
        "name": sk.name,
        "category": sk.category,
        "description": sk.description,
        "trigger_keywords": sk.trigger_keywords,
        "skill_markdown": sk.skill_markdown,
        "mounted_agents": mounted,
        "is_global_mount": bool(sk.is_global_mount),
        "is_enabled": bool(sk.is_enabled),
        "source_path": sk.source_path,
        "hit_count": sk.hit_count or 0,
    }


@router.get("/overview")
def get_agent_hub_overview(db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [get_agent_hub_overview] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /overview
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    ensure_agent_fleet_seeded(db)
    ensure_skills_seeded(db)

    agents = db.query(AgentConfig).order_by(AgentConfig.agent_number.asc()).all()
    categories = db.query(AgentModelCategoryConfig).all()
    skills = db.query(SkillConfig).order_by(SkillConfig.hit_count.desc()).all()
    bb_sessions = (
        db.query(AgentBlackboardSession)
        .order_by(AgentBlackboardSession.updated_at.desc())
        .limit(10)
        .all()
    )
    interrupts = (
        db.query(ModerationInterruptQueue)
        .order_by(ModerationInterruptQueue.created_at.desc())
        .limit(20)
        .all()
    )

    return {
        "code": 200,
        "data": {
            "global_llm_config": llm_gateway.get_active_config(),
            "agents": [_serialize_agent(db, a) for a in agents],
            "categories": [
                {
                    "category_key": c.category_key,
                    "category_name": c.category_name,
                    "description": c.description,
                    "provider": c.provider,
                    "model_name": c.model_name,
                    "base_url": c.base_url or "",
                    "temperature": c.temperature,
                }
                for c in categories
            ],
            "skills": [_serialize_skill(s) for s in skills],
            "blackboard_sessions": [BlackboardMemoryIntegrator.to_snapshot(b) for b in bb_sessions],
            "moderation_interrupts": [
                {
                    "interrupt_id": m.interrupt_id,
                    "source_type": m.source_type,
                    "video_id": m.video_id,
                    "episode_id": m.episode_id,
                    "username": m.username,
                    "content_text": m.content_text,
                    "risk_score": m.risk_score,
                    "risk_reason": m.risk_reason,
                    "matched_words": m.matched_words,
                    "status": m.status,
                    "reviewer_username": m.reviewer_username,
                    "reviewer_note": m.reviewer_note,
                    "created_at": m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else "",
                }
                for m in interrupts
            ],
        },
    }


@router.put("/agents/{agent_id}")
def update_agent_config(
    agent_id: str,
    payload: AgentUpdatePayload,
    db: Session = Depends(get_db),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [update_agent_config] 业务，负责修改并更新相关系统资产与数据状态。
    对应 HTTP 端点：PUT /agents/{agent_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    ensure_agent_fleet_seeded(db)
    ag = db.query(AgentConfig).filter(AgentConfig.agent_id == agent_id).first()
    if not ag:
        raise HTTPException(status_code=404, detail=f"未找到智能体 {agent_id}")

    if payload.is_enabled is not None:
        ag.is_enabled = payload.is_enabled
    if payload.model_bind_mode is not None:
        ag.model_bind_mode = payload.model_bind_mode.upper()
    if payload.provider is not None:
        ag.provider = payload.provider
    if payload.model_name is not None:
        ag.model_name = payload.model_name
    if payload.base_url is not None:
        ag.base_url = payload.base_url
    if payload.api_key is not None and "***" not in payload.api_key and "..." not in payload.api_key:
        ag.api_key = payload.api_key
    if payload.temperature is not None:
        ag.temperature = float(payload.temperature)
    if payload.disabled_fallback_msg is not None:
        ag.disabled_fallback_msg = payload.disabled_fallback_msg
    if payload.system_prompt is not None:
        ag.system_prompt = payload.system_prompt

    db.commit()
    db.refresh(ag)
    return {"code": 200, "message": f"{ag.name} 配置已热更新生效", "data": _serialize_agent(db, ag)}


@router.post("/model-governance/switch-all")
def batch_switch_model_bind_mode(
    payload: BatchBindModePayload,
    db: Session = Depends(get_db),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [batch_switch_model_bind_mode] 业务，负责批量治理相关系统资产与数据状态。
    对应 HTTP 端点：POST /model-governance/switch-all
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    ensure_agent_fleet_seeded(db)
    mode = payload.model_bind_mode.upper()
    if mode not in ("GLOBAL_UNIFIED", "CATEGORY_GROUP", "AGENT_CUSTOM"):
        raise HTTPException(status_code=400, detail="非法绑定模式")

    agents = db.query(AgentConfig).all()
    for ag in agents:
        ag.model_bind_mode = mode
    db.commit()
    return {
        "code": 200,
        "message": f"全舰 9 大智能体已一键切换至 {mode} 模型治理模式",
        "data": [_serialize_agent(db, a) for a in agents],
    }


@router.post("/agents/batch-configure")
def batch_configure_agents(
    payload: BatchAgentConfigPayload,
    db: Session = Depends(get_db),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [batch_configure_agents] 业务，负责批量治理相关系统资产与数据状态。
    对应 HTTP 端点：POST /agents/batch-configure
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    ensure_agent_fleet_seeded(db)
    if not payload.agent_ids:
        raise HTTPException(status_code=400, detail="未选择任何智能体")

    updated_agents = []
    for aid in payload.agent_ids:
        ag = db.query(AgentConfig).filter(AgentConfig.agent_id == aid).first()
        if not ag:
            continue
        if payload.model_bind_mode:
            ag.model_bind_mode = payload.model_bind_mode.upper()
        if payload.provider:
            ag.provider = payload.provider
        if payload.model_name:
            ag.model_name = payload.model_name
        if payload.base_url is not None:
            ag.base_url = payload.base_url
        if payload.api_key is not None and "***" not in payload.api_key and "..." not in payload.api_key:
            ag.api_key = payload.api_key
        if payload.temperature is not None:
            ag.temperature = float(payload.temperature)
        if payload.timeout_sec is not None:
            ag.timeout_sec = float(payload.timeout_sec)
        updated_agents.append(ag)

    db.commit()
    for ag in updated_agents:
        db.refresh(ag)

    return {
        "code": 200,
        "message": f"成功批量更新 {len(updated_agents)} 个智能体的专属模型配置",
        "data": [_serialize_agent(db, a) for a in updated_agents],
    }


@router.put("/categories/{category_key}")
def update_category_model_config(
    category_key: str,
    payload: CategoryModelUpdatePayload,
    db: Session = Depends(get_db),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [update_category_model_config] 业务，负责修改并更新相关系统资产与数据状态。
    对应 HTTP 端点：PUT /categories/{category_key}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    ensure_agent_fleet_seeded(db)
    cat = (
        db.query(AgentModelCategoryConfig)
        .filter(AgentModelCategoryConfig.category_key == category_key)
        .first()
    )
    if not cat:
        raise HTTPException(status_code=404, detail=f"未找到分类 {category_key}")

    if payload.provider is not None:
        cat.provider = payload.provider
    if payload.model_name is not None:
        cat.model_name = payload.model_name
    if payload.base_url is not None:
        cat.base_url = payload.base_url
    if payload.api_key is not None and "***" not in payload.api_key:
        cat.api_key = payload.api_key
    if payload.temperature is not None:
        cat.temperature = float(payload.temperature)

    db.commit()
    db.refresh(cat)
    return {
        "code": 200,
        "message": f"分类【{cat.category_name}】模型配置已更新",
        "data": {
            "category_key": cat.category_key,
            "category_name": cat.category_name,
            "provider": cat.provider,
            "model_name": cat.model_name,
            "base_url": cat.base_url or "",
            "temperature": cat.temperature,
        },
    }


@router.get("/skills")
def list_skills(db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [list_skills] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /skills
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    ensure_skills_seeded(db)
    skills = db.query(SkillConfig).order_by(SkillConfig.hit_count.desc()).all()
    return {"code": 200, "data": [_serialize_skill(s) for s in skills]}


@router.post("/skills")
def create_or_import_skill(payload: SkillUpsertPayload, db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [create_or_import_skill] 业务，负责新建并录入相关系统资产与数据状态。
    对应 HTTP 端点：POST /skills
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    ensure_skills_seeded(db)
    sid = payload.skill_id or f"skill_custom_{uuid.uuid4().hex[:8]}"
    existing = db.query(SkillConfig).filter(SkillConfig.skill_id == sid).first()
    if existing:
        existing.name = payload.name
        existing.category = payload.category
        existing.description = payload.description
        existing.trigger_keywords = payload.trigger_keywords
        existing.skill_markdown = payload.skill_markdown
        existing.mounted_agents_json = json.dumps(payload.mounted_agents, ensure_ascii=False)
        existing.is_global_mount = payload.is_global_mount
        existing.is_enabled = payload.is_enabled
        db.commit()
        db.refresh(existing)
        return {"code": 200, "message": "技能已更新", "data": _serialize_skill(existing)}

    new_sk = SkillConfig(
        skill_id=sid,
        name=payload.name,
        category=payload.category,
        description=payload.description,
        trigger_keywords=payload.trigger_keywords,
        skill_markdown=payload.skill_markdown,
        mounted_agents_json=json.dumps(payload.mounted_agents, ensure_ascii=False),
        is_global_mount=payload.is_global_mount,
        is_enabled=payload.is_enabled,
        source_path="custom://admin-studio",
        hit_count=0,
    )
    db.add(new_sk)
    db.commit()
    db.refresh(new_sk)
    return {"code": 200, "message": f"技能【{new_sk.name}】创建并挂载成功", "data": _serialize_skill(new_sk)}


@router.put("/skills/{skill_id}")
def update_skill_mounting(
    skill_id: str,
    payload: SkillUpsertPayload,
    db: Session = Depends(get_db),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [update_skill_mounting] 业务，负责修改并更新相关系统资产与数据状态。
    对应 HTTP 端点：PUT /skills/{skill_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    sk = db.query(SkillConfig).filter(SkillConfig.skill_id == skill_id).first()
    if not sk:
        raise HTTPException(status_code=404, detail="未找到该技能")
    sk.name = payload.name or sk.name
    sk.category = payload.category or sk.category
    sk.description = payload.description
    sk.trigger_keywords = payload.trigger_keywords
    sk.skill_markdown = payload.skill_markdown or sk.skill_markdown
    sk.mounted_agents_json = json.dumps(payload.mounted_agents, ensure_ascii=False)
    sk.is_global_mount = payload.is_global_mount
    sk.is_enabled = payload.is_enabled
    db.commit()
    db.refresh(sk)
    return {"code": 200, "message": f"技能【{sk.name}】挂载关系已热生效", "data": _serialize_skill(sk)}


@router.post("/skills/mount-all")
def toggle_all_skills_global_mount(
    payload: GlobalMountAllPayload,
    db: Session = Depends(get_db),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [toggle_all_skills_global_mount] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：POST /skills/mount-all
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    ensure_skills_seeded(db)
    skills = db.query(SkillConfig).all()
    for sk in skills:
        sk.is_global_mount = bool(payload.is_global_mount)
    db.commit()
    return {
        "code": 200,
        "message": "已开启全量技能全局共享挂载" if payload.is_global_mount else "已切换为按指定智能体定向挂载",
        "data": [_serialize_skill(s) for s in skills],
    }


class SkillExportToRagPayload(BaseModel):
    category_id: Optional[str] = None
    drama_id: Optional[str] = None
    strategy: Optional[str] = "fixed"


@router.delete("/skills/{skill_id}")
def delete_skill(skill_id: str, db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [delete_skill] 业务，负责删除并清理相关系统资产与数据状态。
    对应 HTTP 端点：DELETE /skills/{skill_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    sk = db.query(SkillConfig).filter(SkillConfig.skill_id == skill_id).first()
    if not sk:
        raise HTTPException(status_code=404, detail="未找到该技能")
    skill_name = sk.name
    db.delete(sk)
    try:
        op_log = SkillOperationLog(
            skill_id=skill_id,
            skill_name=skill_name,
            action="DELETE",
            operator="管理员",
            target_scope="全平台",
            chunks_count=0,
            status="SUCCESS",
            detail_json="{}"
        )
        db.add(op_log)
    except Exception:
        pass
    db.commit()
    return {"code": 200, "message": f"技能【{skill_name}】已成功删除", "data": {"skill_id": skill_id}}


@router.get("/skills/rag-categories")
def get_rag_categories_for_skills(db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [get_rag_categories_for_skills] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /skills/rag-categories
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    cats = db.query(RAGCorpusCategory).order_by(RAGCorpusCategory.created_at.desc()).all()
    dramas = db.query(Video).filter(Video.status == "PUBLISHED").limit(20).all()
    return {
        "code": 200,
        "data": {
            "categories": [
                {
                    "id": c.id,
                    "name": c.name,
                    "drama_id": c.drama_id,
                    "parent_id": c.parent_id,
                }
                for c in cats
            ],
            "dramas": [
                {"id": d.id, "title": d.title}
                for d in dramas
            ]
        }
    }


@router.post("/skills/{skill_id}/export-to-rag")
def export_skill_to_knowledge_base(
    skill_id: str,
    payload: SkillExportToRagPayload,
    db: Session = Depends(get_db),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [export_skill_to_knowledge_base] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：POST /skills/{skill_id}/export-to-rag
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    sk = db.query(SkillConfig).filter(SkillConfig.skill_id == skill_id).first()
    if not sk:
        raise HTTPException(status_code=404, detail="未找到该技能")

    # 若未指定短剧，严格设定为 global 全局通用资产，避免误绑单一剧目导致不可见
    drama_id = payload.drama_id if payload.drama_id else "global"

    # 1. 查找或自愈创建全局 Skills 技能专区分类
    category_id = payload.category_id
    from app.models.rag_corpus import RAGCorpusCategory
    if not category_id:
        skill_cat = db.query(RAGCorpusCategory).filter(
            or_(
                RAGCorpusCategory.name.like("%Skills%"),
                RAGCorpusCategory.name.like("%技能%")
            )
        ).first()
        if not skill_cat:
            skill_cat = RAGCorpusCategory(
                id="cat_skills_global",
                name="Skills 智能体技能资产库",
                drama_id="global",
                description="由九大智能体总控台自由挂载器动态切片与向量化转存的专业 SOP 技能库"
            )
            db.add(skill_cat)
            db.commit()
            db.refresh(skill_cat)
        category_id = skill_cat.id

    # 创建 RAGCorpus
    corpus = RAGCorpus(
        drama_id=drama_id,
        category_id=category_id,
        title=f"技能库 · {sk.name}",
        doc_type="skill",
        content=sk.skill_markdown or f"# {sk.name}\n{sk.description}",
        metadata_json=json.dumps({
            "skill_id": sk.skill_id,
            "category": sk.category,
            "trigger_keywords": sk.trigger_keywords,
            "source": "skill_export",
        }, ensure_ascii=False),
    )
    db.add(corpus)
    db.commit()
    db.refresh(corpus)

    # 2. 真实离线切片
    docs = chunker.chunk(
        text=corpus.content,
        strategy=payload.strategy or "fixed",
        drama_id=drama_id,
        episode_num=1,
    )

    # 3. 真实向量化嵌入 (Embedder)
    texts = [d.text for d in docs]
    embeddings = embedder.embed_documents(texts)

    # 4. 存入 RAGChunk 表
    created_chunks = 0
    for idx, (doc, emb) in enumerate(zip(docs, embeddings)):
        rag_chunk = RAGChunk(
            corpus_id=corpus.id,
            drama_id=drama_id,
            chunk_index=idx,
            content=doc.text,
            embedding_json=json.dumps(emb),
            chunk_strategy=payload.strategy or "fixed",
            token_count=len(doc.text),
        )
        db.add(rag_chunk)
        created_chunks += 1

    # 关键修正：将真实生成的切片数回写更新至知识库语料主表，确保知识资产树同步非零
    corpus.chunk_count = created_chunks
    db.add(corpus)
    db.commit()

    # 记录 Skills 操作流水日志
    try:
        op_log = SkillOperationLog(
            skill_id=sk.skill_id,
            skill_name=sk.name,
            action="EXPORT_RAG",
            operator="管理员",
            target_scope="全平台通用" if drama_id == "global" else f"短剧专属:{drama_id}",
            chunks_count=created_chunks,
            status="SUCCESS",
            detail_json=json.dumps({
                "strategy": payload.strategy or "fixed",
                "category_id": category_id,
                "vector_dim": len(embeddings[0]) if embeddings else 0,
            }, ensure_ascii=False)
        )
        db.add(op_log)
        db.commit()
    except Exception as log_err:
        pass

    db.commit()

    return {
        "code": 200,
        "message": f"技能【{sk.name}】已成功完成切片与向量化，注入知识库！",
        "data": {
            "corpus_id": corpus.id,
            "drama_id": drama_id,
            "category_id": payload.category_id,
            "chunks_count": created_chunks,
            "vector_dim": len(embeddings[0]) if embeddings else 0,
        }
    }


@router.post("/dispatch")
async def dispatch_agent_task(
    payload: AgentDispatchPayload,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [dispatch_agent_task] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：POST /dispatch
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    uid = current_user.id if current_user else "guest_default_user"
    uname = (current_user.nickname or current_user.username) if current_user else "剧迷朋友"

    req = AgentTaskRequest(
        query=payload.query,
        agent_id=payload.agent_id or "agent_9",
        session_id=payload.session_id or f"session_{uid}",
        user_id=uid,
        username=uname,
        drama_id=payload.drama_id,
        episode_id=payload.episode_id,
        current_time_sec=payload.current_time_sec or 0.0,
        extra_params=payload.extra_params or {},
    )
    res = await MasterAgentIntegrator.dispatch(db, req)
    return {"code": 200, "data": asdict(res)}


@router.post("/blackboard/compress")
def compress_blackboard_memory(
    payload: BlackboardCompressPayload,
    db: Session = Depends(get_db),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [compress_blackboard_memory] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：POST /blackboard/compress
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    snap = BlackboardMemoryIntegrator.force_compress_session(db, payload.session_id)
    return {
        "code": 200,
        "message": f"会话 [{payload.session_id}] 已完成滑动窗口摘要压缩",
        "data": snap,
    }


@router.get("/pet")
def get_user_codex_pet(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [get_user_codex_pet] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /pet
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    uid = current_user.id if current_user else "guest_default_user"
    pet = get_or_create_user_pet(db, uid)
    return {"code": 200, "data": serialize_pet(pet)}


@router.put("/pet/persona")
def switch_user_codex_pet_persona(
    payload: PetPersonaPayload,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [switch_user_codex_pet_persona] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：PUT /pet/persona
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    uid = current_user.id if current_user else "guest_default_user"
    data = update_user_pet_persona(db, uid, pet_name=payload.pet_name, persona_key=payload.persona_key)
    return {"code": 200, "message": "2号 Codex 观影灵宠人设已切换", "data": data}


@router.post("/pet/feed")
def feed_user_codex_pet(
    payload: PetFeedPayload,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [feed_user_codex_pet] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：POST /pet/feed
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    uid = current_user.id if current_user else "guest_default_user"
    amt = payload.get_amount()
    try:
        data = feed_user_pet_with_coins(db, uid, coin_amount=amt)
        return {"code": 200, "message": f"成功投喂 {amt} 金币，灵宠经验与心情大幅提升！", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/moderation/interrupts")
def list_moderation_interrupts(db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [list_moderation_interrupts] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /moderation/interrupts
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    items = (
        db.query(ModerationInterruptQueue)
        .order_by(ModerationInterruptQueue.created_at.desc())
        .limit(30)
        .all()
    )
    return {
        "code": 200,
        "data": [
            {
                "interrupt_id": m.interrupt_id,
                "source_type": m.source_type,
                "video_id": m.video_id,
                "episode_id": m.episode_id,
                "username": m.username,
                "content_text": m.content_text,
                "risk_score": m.risk_score,
                "risk_reason": m.risk_reason,
                "matched_words": m.matched_words,
                "status": m.status,
                "reviewer_username": m.reviewer_username,
                "reviewer_note": m.reviewer_note,
                "created_at": m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else "",
            }
            for m in items
        ],
    }


@router.post("/moderation/interrupts/{interrupt_id}/resume")
def resume_moderation_interrupt_endpoint(
    interrupt_id: str,
    payload: InterruptResumePayload,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [resume_moderation_interrupt_endpoint] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：POST /moderation/interrupts/{interrupt_id}/resume
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    reviewer = current_user.username if current_user else "admin"
    try:
        res = resume_moderation_interrupt(
            db=db,
            interrupt_id=interrupt_id,
            action=payload.action,
            reviewer_username=reviewer,
            reviewer_note=payload.reviewer_note,
        )
        return {"code": 200, "message": f"人机回环审核单已执行 Command(resume={payload.action})", "data": res}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/telemetry/live")
def get_live_bi_and_tactical_telemetry(
    page: int = 1,
    page_size: int = 10,
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [get_live_bi_and_tactical_telemetry] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /telemetry/live
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    data = MasterAgentIntegrator.get_bi_and_tactical_telemetry(
        db, page=page, page_size=page_size, agent_id=agent_id, status=status
    )
    return {"code": 200, "data": data}


class BatchInspectRequest(BaseModel):
    target_type: str = "danmaku"  # danmaku | comment
    limit: int = 30


class ProposalDecideRequest(BaseModel):
    action: str = "ACCEPT"  # ACCEPT | REJECT
    category: Optional[str] = "违禁"
    level: Optional[str] = "HIGH"


class BatchResolveViolationsRequest(BaseModel):
    target_type: str = "danmaku"  # danmaku | comment
    action: str = "DELETE"  # DELETE | PENDING_HITL
    ids: List[str] = []


@router.post("/moderation/batch-inspect")
async def batch_inspect_interactions_endpoint(
    req: BatchInspectRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [batch_inspect_interactions_endpoint] 业务，负责批量治理相关系统资产与数据状态。
    对应 HTTP 端点：POST /moderation/batch-inspect
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    target_type = req.target_type.lower()
    limit = max(1, min(req.limit, 100))
    items = []

    if target_type == "danmaku":
        query_items = (
            db.query(VideoDanmaku)
            .order_by(VideoDanmaku.created_at.desc())
            .limit(limit)
            .all()
        )
        for dm in query_items:
            # 安全级联提取分集与短剧标题，杜绝直接访问不存在的 dm.video 导致异常
            ep = dm.episode or (
                db.query(VideoEpisode).filter(VideoEpisode.id == dm.episode_id).first()
                if dm.episode_id
                else None
            )
            v_title = ep.video.title if (ep and ep.video) else (ep.title if ep else "短剧")
            u_name = dm.user.username if dm.user else "剧迷"
            items.append({
                "id": dm.id,
                "content": dm.content,
                "user_name": u_name,
                "video_title": v_title,
                "created_at": dm.created_at.strftime("%Y-%m-%d %H:%M") if dm.created_at else "",
            })
    else:
        query_items = (
            db.query(UserComment)
            .order_by(UserComment.created_at.desc())
            .limit(limit)
            .all()
        )
        for cm in query_items:
            v = db.query(Video).filter(Video.id == cm.video_id).first()
            v_title = v.title if v else "短剧"
            u_name = cm.user.username if cm.user else "剧迷"
            items.append({
                "id": cm.id,
                "content": cm.content,
                "user_name": u_name,
                "video_title": v_title,
                "created_at": cm.created_at.strftime("%Y-%m-%d %H:%M") if cm.created_at else "",
            })

    pod4 = FLEET_POD_REGISTRY.get("agent_4")
    if not pod4:
        raise HTTPException(status_code=500, detail="4号合规审片官智能体未注册就绪")

    res = await pod4.inspect_interactions_batch(db=db, items=items, interaction_type=target_type)

    # 自动持久化巡检日志与快照报告
    batch_code = f"INSP-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    log_record = InteractionInspectionLog(
        id=str(uuid.uuid4()),
        batch_id=batch_code,
        target_type=target_type,
        total_inspected=res.get("total_inspected", len(items)),
        violation_count=res.get("violation_count", 0),
        suggested_words_count=len(res.get("suggested_words", [])),
        cost_ms=res.get("cost_ms", 0),
        llm_status=res.get("llm_status", "COMPLETED"),
        report_summary_json=json.dumps(res, ensure_ascii=False)
    )
    db.add(log_record)
    db.commit()

    res["batch_id"] = batch_code
    res["log_id"] = log_record.id

    return {
        "code": 200,
        "message": f"4号合规审片官已完成 {len(items)} 条{target_type == 'danmaku' and '弹幕' or '评论'}巡检",
        "data": res
    }


@router.get("/moderation/word-proposals")
def list_word_proposals_endpoint(
    status: str = "PENDING",
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [list_word_proposals_endpoint] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /moderation/word-proposals
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    q = db.query(SensitiveWordProposal)
    if status and status != "ALL":
        q = q.filter(SensitiveWordProposal.status == status)

    items = q.order_by(SensitiveWordProposal.created_at.desc()).limit(100).all()
    pending_total = db.query(SensitiveWordProposal).filter(SensitiveWordProposal.status == "PENDING").count()

    proposals_data = [
        {
            "id": p.id,
            "word": p.word,
            "category": p.category,
            "level": p.level,
            "reason": p.reason,
            "source_type": p.source_type,
            "source_content": p.source_content,
            "status": p.status,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
        }
        for p in items
    ]

    return {
        "code": 200,
        "data": {
            "pending_count": pending_total,
            "items": proposals_data
        }
    }


@router.post("/moderation/word-proposals/{proposal_id}/decide")
def decide_word_proposal_endpoint(
    proposal_id: str,
    payload: ProposalDecideRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [decide_word_proposal_endpoint] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：POST /moderation/word-proposals/{proposal_id}/decide
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    proposal = db.query(SensitiveWordProposal).filter(SensitiveWordProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="自迭代词条建议单据不存在")

    action = payload.action.upper()
    if action == "ACCEPT":
        # 同步写入或更新 SensitiveWord 库
        cleaned_word = proposal.word.strip()
        word_obj = db.query(SensitiveWord).filter(SensitiveWord.word == cleaned_word).first()
        if word_obj:
            word_obj.category = payload.category or proposal.category
            word_obj.level = payload.level or proposal.level
        else:
            word_obj = SensitiveWord(
                id=str(uuid.uuid4()),
                word=cleaned_word,
                category=payload.category or proposal.category,
                level=payload.level or proposal.level
            )
            db.add(word_obj)

        proposal.status = "ACCEPTED"
        proposal.reviewed_at = datetime.utcnow()
        db.commit()

        # 热重载进入全局 DFA 内存自动机
        moderation_service.reload_from_db(db)

        return {
            "code": 200,
            "message": f"成功采纳并录入违规词 [{proposal.word}]，DFA 自动机已热重载生效！",
            "data": {
                "id": proposal.id,
                "word": proposal.word,
                "status": proposal.status
            }
        }
    else:
        proposal.status = "REJECTED"
        proposal.reviewed_at = datetime.utcnow()
        db.commit()
        return {
            "code": 200,
            "message": f"已忽略该违规词建议: [{proposal.word}]",
            "data": {
                "id": proposal.id,
                "word": proposal.word,
                "status": proposal.status
            }
        }


@router.post("/moderation/batch-resolve-violations")
def batch_resolve_violations_endpoint(
    req: BatchResolveViolationsRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [batch_resolve_violations_endpoint] 业务，负责批量治理相关系统资产与数据状态。
    对应 HTTP 端点：POST /moderation/batch-resolve-violations
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    if not req.ids:
        return {"code": 200, "message": "未选中任何违规记录", "affected_count": 0}

    target_type = req.target_type.lower()
    action = req.action.upper()
    affected = 0

    if action == "DELETE":
        if target_type == "danmaku":
            affected = db.query(VideoDanmaku).filter(VideoDanmaku.id.in_(req.ids)).delete(synchronize_session=False)
        else:
            affected = db.query(UserComment).filter(UserComment.id.in_(req.ids)).delete(synchronize_session=False)
        db.commit()
        return {
            "code": 200,
            "message": f"成功下架清理 {affected} 笔违规{target_type == 'danmaku' and '弹幕' or '评论'}！",
            "affected_count": affected
        }
    elif action == "PENDING_HITL":
        # 送入人机回环工单
        for item_id in req.ids:
            exists = db.query(ModerationInterruptQueue).filter(ModerationInterruptQueue.target_id == item_id).first()
            if not exists:
                content_text = ""
                u_name = "剧迷"
                v_id = None
                if target_type == "danmaku":
                    dm = db.query(VideoDanmaku).filter(VideoDanmaku.id == item_id).first()
                    if dm:
                        content_text = dm.content
                        u_name = dm.user.username if dm.user else "剧迷"
                        v_id = dm.video_id
                else:
                    cm = db.query(UserComment).filter(UserComment.id == item_id).first()
                    if cm:
                        content_text = cm.content
                        u_name = cm.user.username if cm.user else "剧迷"
                        v_id = cm.video_id

                if content_text:
                    hitl_item = ModerationInterruptQueue(
                        interrupt_id=str(uuid.uuid4()),
                        source_type=target_type,
                        target_id=item_id,
                        video_id=v_id,
                        username=u_name,
                        content_text=content_text,
                        risk_score=75,
                        risk_reason="4号合规官巡检送入人工复核",
                        status="PENDING"
                    )
                    db.add(hitl_item)
                    affected += 1
        db.commit()
        return {
            "code": 200,
            "message": f"成功转送 {affected} 笔记录至 4号人机回环工单流！",
            "affected_count": affected
        }
    else:
        raise HTTPException(status_code=400, detail="不支持的操作指令")


@router.get("/moderation/inspection-history")
def list_inspection_history_endpoint(
    page: int = 1,
    per_page: int = 20,
    target_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [list_inspection_history_endpoint] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /moderation/inspection-history
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    q = db.query(InteractionInspectionLog)
    if target_type and target_type != "ALL":
        q = q.filter(InteractionInspectionLog.target_type == target_type)

    total = q.count()
    records = q.order_by(InteractionInspectionLog.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for r in records:
        items.append({
            "id": r.id,
            "batch_id": r.batch_id,
            "target_type": r.target_type,
            "total_inspected": r.total_inspected,
            "violation_count": r.violation_count,
            "suggested_words_count": r.suggested_words_count,
            "cost_ms": r.cost_ms,
            "llm_status": r.llm_status,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else ""
        })

    return {
        "code": 200,
        "data": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "items": items
        }
    }


@router.get("/moderation/inspection-history/{log_id}")
def get_inspection_history_detail_endpoint(
    log_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [get_inspection_history_detail_endpoint] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /moderation/inspection-history/{log_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    log_rec = db.query(InteractionInspectionLog).filter(InteractionInspectionLog.id == log_id).first()
    if not log_rec:
        raise HTTPException(status_code=404, detail="巡检记录不存在")

    report_data = json.loads(log_rec.report_summary_json or "{}") if log_rec.report_summary_json else {}
    return {
        "code": 200,
        "data": {
            "id": log_rec.id,
            "batch_id": log_rec.batch_id,
            "target_type": log_rec.target_type,
            "total_inspected": log_rec.total_inspected,
            "violation_count": log_rec.violation_count,
            "suggested_words_count": log_rec.suggested_words_count,
            "cost_ms": log_rec.cost_ms,
            "llm_status": log_rec.llm_status,
            "created_at": log_rec.created_at.strftime("%Y-%m-%d %H:%M:%S") if log_rec.created_at else "",
            "report": report_data
        }
    }

@router.get("/skills/logs")
def list_skill_operation_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    keyword: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [list_skill_operation_logs] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /skills/logs
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    try:
        q = db.query(SkillOperationLog)
        if keyword and keyword.strip():
            kw = f"%{keyword.strip()}%"
            q = q.filter(
                or_(
                    SkillOperationLog.skill_name.like(kw),
                    SkillOperationLog.operator.like(kw),
                    SkillOperationLog.target_scope.like(kw),
                )
            )
        if action and action.strip() and action != "ALL":
            q = q.filter(SkillOperationLog.action == action.strip())

        q = q.order_by(SkillOperationLog.created_at.desc())
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return {
            "code": 200,
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [
                    {
                        "id": l.id,
                        "skill_id": l.skill_id,
                        "skill_name": l.skill_name,
                        "action": l.action,
                        "operator": l.operator,
                        "target_scope": l.target_scope,
                        "chunks_count": l.chunks_count,
                        "status": l.status,
                        "created_at": l.created_at.strftime("%Y-%m-%d %H:%M:%S") if l.created_at else "",
                    }
                    for l in items
                ]
            }
        }
    except Exception as e:
        return {"code": 200, "data": {"total": 0, "page": 1, "page_size": 10, "items": []}}


@router.delete("/skills/logs/{log_id}")
def delete_skill_operation_log(log_id: str, db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [delete_skill_operation_log] 业务，负责删除并清理相关系统资产与数据状态。
    对应 HTTP 端点：DELETE /skills/logs/{log_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    rec = db.query(SkillOperationLog).filter(SkillOperationLog.id == log_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="未找到该审计日志记录")
    db.delete(rec)
    db.commit()
    return {"code": 200, "message": "已成功删除该条审计日志"}


@router.delete("/skills/logs-clear")
def clear_all_skill_operation_logs(db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [agent_hub] 模块中的 [clear_all_skill_operation_logs] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：DELETE /skills/logs-clear
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/agent_hub.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    db.query(SkillOperationLog).delete()
    db.commit()
    return {"code": 200, "message": "已成功清空全部审计流水日志"}
