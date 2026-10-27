"""
CinemaAgent Nine-Agent Fleet, 3-Tier LLM Governance, Skills Manager,
Blackboard Memory Integrator, Codex Companion Pet, and HITL Moderation ORM Models.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime
from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class AgentConfig(Base):
    """
    Configuration for each of the 9 specialized agents (agent_1 to agent_9).
    Supports hot-plugging (is_enabled), graceful disabled fallback prompts,
    and 3-tier LLM binding (GLOBAL_UNIFIED / CATEGORY_GROUP / AGENT_CUSTOM).
    """
    __tablename__ = "agent_configs"

    agent_id = Column(String(36), primary_key=True, index=True)  # e.g. "agent_1" .. "agent_9"
    agent_number = Column(Integer, nullable=False, default=1)
    name = Column(String(100), nullable=False)
    role_title = Column(String(120), nullable=False)
    category = Column(String(50), nullable=False, default="REASONING_CORE")
    # Bind modes: GLOBAL_UNIFIED | CATEGORY_GROUP | AGENT_CUSTOM
    model_bind_mode = Column(String(40), nullable=False, default="GLOBAL_UNIFIED")
    provider = Column(String(40), nullable=False, default="ollama")
    model_name = Column(String(100), nullable=False, default="deepseek-r1:1.5b")
    base_url = Column(String(255), nullable=True, default="")
    api_key = Column(String(255), nullable=True, default="")
    temperature = Column(Float, nullable=False, default=0.4)
    timeout_sec = Column(Float, nullable=False, default=25.0)
    is_enabled = Column(Boolean, nullable=False, default=True)
    disabled_fallback_msg = Column(
        Text,
        nullable=False,
        default="该领域专家智能体当前正由管理员维护调优中，已由 9 号主控智能体为您无缝接管解答。"
    )
    system_prompt = Column(Text, nullable=False, default="")
    backstory = Column(Text, nullable=True, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentModelCategoryConfig(Base):
    """
    3 Functional Category LLM configurations for batch model governance:
    - REASONING_CORE: Agent 9 (Supervisor), Agent 3 (Agentic RAG), Agent 6 (Multimodal Plot)
    - CREATIVE_STUDIO: Agent 5 (Creator Assist), Agent 8 (Director Crew), Agent 2 (Codex Pet)
    - FAST_COMMUNITY: Agent 1 (@AI Comment Bot), Agent 4 (Safety Guard), Agent 7 (Recommender)
    """
    __tablename__ = "agent_model_category_configs"

    category_key = Column(String(50), primary_key=True, index=True)
    category_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True, default="")
    provider = Column(String(40), nullable=False, default="ollama")
    model_name = Column(String(100), nullable=False, default="deepseek-r1:1.5b")
    base_url = Column(String(255), nullable=True, default="")
    api_key = Column(String(255), nullable=True, default="")
    temperature = Column(Float, nullable=False, default=0.4)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SkillConfig(Base):
    """
    Pluggable SKILL.md registry supporting targeted agent binding or 1-click global mounting.
    """
    __tablename__ = "agent_skill_configs"

    skill_id = Column(String(64), primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    category = Column(String(64), nullable=False, default="短剧编导")
    description = Column(Text, nullable=False, default="")
    trigger_keywords = Column(String(500), nullable=False, default="")
    skill_markdown = Column(Text, nullable=False, default="")
    mounted_agents_json = Column(Text, nullable=False, default="[]")  # JSON list of agent_ids
    is_global_mount = Column(Boolean, nullable=False, default=False)
    is_enabled = Column(Boolean, nullable=False, default=True)
    source_path = Column(String(255), nullable=True, default="builtin")
    hit_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentBlackboardSession(Base):
    """
    Shared Blackboard memory across all 9 agents + Sliding-Window Summarization Integrator.
    """
    __tablename__ = "agent_blackboard_sessions"

    session_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    drama_id = Column(String(36), nullable=True, index=True)
    episode_id = Column(String(36), nullable=True, index=True)
    shared_facts_json = Column(Text, nullable=False, default="{}")
    rolling_summary = Column(Text, nullable=False, default="")
    recent_turns_json = Column(Text, nullable=False, default="[]")
    turn_count = Column(Integer, nullable=False, default=0)
    compression_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserCompanionPet(Base):
    """
    Agent 2: Codex Pet Companion in User Space (Persona switching + Coin feeding & leveling).
    """
    __tablename__ = "user_companion_pets"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), unique=True, index=True, nullable=False)
    pet_name = Column(String(64), nullable=False, default="影伴小灵狐")
    persona_key = Column(String(40), nullable=False, default="sharp_critic")
    persona_label = Column(String(64), nullable=False, default="毒舌影评喵")
    role_prompt = Column(Text, nullable=False, default="一针见血的毒舌短剧鉴赏家")
    goal_prompt = Column(Text, nullable=False, default="帮主人识破老套路、精准定位反转爽点与演技细节")
    backstory_prompt = Column(Text, nullable=False, default="阅片三千部的赛博观影灵宠，嘴硬心软，最懂主人看剧口味")
    level = Column(Integer, nullable=False, default=1)
    exp = Column(Integer, nullable=False, default=20)
    mood_score = Column(Integer, nullable=False, default=90)
    total_coins_fed = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModerationInterruptQueue(Base):
    """
    Agent 4: Human-in-the-loop (LangGraph interrupt style) moderation queue
    for borderline comments/danmaku with risk score 30..85.
    """
    __tablename__ = "moderation_interrupt_queue"

    interrupt_id = Column(String(36), primary_key=True, default=_uuid, index=True)
    source_type = Column(String(32), nullable=False, default="comment")  # comment | danmaku
    target_id = Column(String(36), nullable=True, index=True)
    video_id = Column(String(36), nullable=True, index=True)
    episode_id = Column(String(36), nullable=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    username = Column(String(64), nullable=False, default="匿名用户")
    content_text = Column(Text, nullable=False)
    risk_score = Column(Integer, nullable=False, default=50)
    risk_reason = Column(Text, nullable=False, default="")
    matched_words = Column(String(255), nullable=True, default="")
    status = Column(String(32), nullable=False, default="PENDING")  # PENDING | APPROVED | REJECTED
    reviewer_username = Column(String(64), nullable=True, default="")
    reviewer_note = Column(Text, nullable=True, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class AgentTelemetryLog(Base):
    """
    Callback-driven real-time telemetry log for Agent BI Dashboard & agent-display-5.0 Tactical Screen.
    """
    __tablename__ = "agent_telemetry_logs"

    id = Column(String(36), primary_key=True, default=_uuid, index=True)
    trace_id = Column(String(64), nullable=False, index=True)
    agent_id = Column(String(36), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, default="REASONING_CORE")
    resolved_provider = Column(String(40), nullable=False, default="ollama")
    resolved_model = Column(String(100), nullable=False, default="deepseek-r1:1.5b")
    bind_mode = Column(String(40), nullable=False, default="GLOBAL_UNIFIED")
    matched_skills_json = Column(Text, nullable=False, default="[]")
    latency_ms = Column(Float, nullable=False, default=0.0)
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    status = Column(String(40), nullable=False, default="SUCCESS")
    query_preview = Column(String(255), nullable=True, default="")
    response_preview = Column(String(255), nullable=True, default="")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AgentEvolutionProposal(Base):
    """
    Self-Evolving Skills Proposal Table.
    Critic evaluates high-difficulty runs and distills candidate SKILL.md for HITL admin review.
    """
    __tablename__ = "agent_evolution_proposals"

    id = Column(String(36), primary_key=True, default=_uuid, index=True)
    proposal_title = Column(String(120), nullable=False)
    target_agent_id = Column(String(50), nullable=False, index=True)
    source_session_id = Column(String(64), nullable=True)
    category = Column(String(64), nullable=False, default="编导自进化")
    generated_skill_content = Column(Text, nullable=False)
    trigger_keywords = Column(String(255), nullable=False, default="")
    critic_score = Column(Float, nullable=False, default=92.0)
    critic_verdict = Column(Text, nullable=False, default="通过高难演练蒸馏生成")
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING | APPROVED | REJECTED
    reviewed_by = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    reviewed_at = Column(DateTime, nullable=True)


class SkillOperationLog(Base):
    """
    Skills 自由挂载与向量化流转审计日志表
    记录挂载、卸载、新建、删除以及向量化切片存入 RAG 知识库的操作历史
    """
    __tablename__ = "skill_operation_logs"

    id = Column(String(36), primary_key=True, default=_uuid, index=True)
    skill_id = Column(String(64), nullable=False, index=True)
    skill_name = Column(String(128), nullable=False)
    action = Column(String(32), nullable=False, default="EXPORT_RAG")  # EXPORT_RAG | MOUNT_GLOBAL | MOUNT_TARGET | CREATE | DELETE
    operator = Column(String(64), nullable=False, default="管理员")
    target_scope = Column(String(128), nullable=False, default="全平台通用")
    chunks_count = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False, default="SUCCESS")  # SUCCESS | FAILED
    detail_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


