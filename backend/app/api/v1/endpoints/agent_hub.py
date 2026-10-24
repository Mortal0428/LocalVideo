"""
CinemaAgent Nine-Agent Fleet, 3-Tier LLM Governance, Skills Manager,
Codex Pet Cabin, HITL Moderation Resume, and Tactical Telemetry REST API.
"""
import json
import uuid
from dataclasses import asdict
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

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
    """Return full governance state for 9 agents, 3 model categories, skills, blackboard & HITL queue."""
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
    """Hot-plug toggle (`is_enabled`), update disabled fallback prompt, or change agent LLM binding."""
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
    """1-click switch all 9 agents to GLOBAL_UNIFIED or CATEGORY_GROUP mode."""
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
    """批量对勾选的多个智能体统一写入并持久化模型配置参数"""
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
    """Update LLM configuration for one of the 3 functional agent categories."""
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
    ensure_skills_seeded(db)
    skills = db.query(SkillConfig).order_by(SkillConfig.hit_count.desc()).all()
    return {"code": 200, "data": [_serialize_skill(s) for s in skills]}


@router.post("/skills")
def create_or_import_skill(payload: SkillUpsertPayload, db: Session = Depends(get_db)):
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
    """删除指定的 Skill 技能项"""
    sk = db.query(SkillConfig).filter(SkillConfig.skill_id == skill_id).first()
    if not sk:
        raise HTTPException(status_code=404, detail="未找到该技能")
    skill_name = sk.name
    db.delete(sk)
    db.commit()
    return {"code": 200, "message": f"技能【{skill_name}】已成功删除", "data": {"skill_id": skill_id}}


@router.get("/skills/rag-categories")
def get_rag_categories_for_skills(db: Session = Depends(get_db)):
    """查询知识库分类目录与在架短剧，供技能选择转存目标文件夹"""
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
    """将指定 Skill 文档转存入 RAG 知识库，执行自动分块与真实向量化嵌入"""
    sk = db.query(SkillConfig).filter(SkillConfig.skill_id == skill_id).first()
    if not sk:
        raise HTTPException(status_code=404, detail="未找到该技能")

    drama_id = payload.drama_id
    if not drama_id:
        first_video = db.query(Video).first()
        drama_id = first_video.id if first_video else "default_drama_001"

    # 1. 创建 RAGCorpus
    corpus = RAGCorpus(
        drama_id=drama_id,
        category_id=payload.category_id,
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
    """Unified invocation endpoint for Agents 1~9 with Supervisor Routing, Hot-Plug Fallback & Blackboard."""
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
    uid = current_user.id if current_user else "guest_default_user"
    pet = get_or_create_user_pet(db, uid)
    return {"code": 200, "data": serialize_pet(pet)}


@router.put("/pet/persona")
def switch_user_codex_pet_persona(
    payload: PetPersonaPayload,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    uid = current_user.id if current_user else "guest_default_user"
    data = update_user_pet_persona(db, uid, pet_name=payload.pet_name, persona_key=payload.persona_key)
    return {"code": 200, "message": "2号 Codex 观影灵宠人设已切换", "data": data}


@router.post("/pet/feed")
def feed_user_codex_pet(
    payload: PetFeedPayload,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    uid = current_user.id if current_user else "guest_default_user"
    amt = payload.get_amount()
    try:
        data = feed_user_pet_with_coins(db, uid, coin_amount=amt)
        return {"code": 200, "message": f"成功投喂 {amt} 金币，灵宠经验与心情大幅提升！", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/moderation/interrupts")
def list_moderation_interrupts(db: Session = Depends(get_db)):
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
def get_live_bi_and_tactical_telemetry(db: Session = Depends(get_db)):
    """Real-time BI metrics & agent-display-5.0 Tactical Screen live node telemetry."""
    data = MasterAgentIntegrator.get_bi_and_tactical_telemetry(db)
    return {"code": 200, "data": data}
