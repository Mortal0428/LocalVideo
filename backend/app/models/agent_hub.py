# -*- coding: utf-8 -*-
"""
==============================================================================
【模型文件】：backend/app/models/agent_hub.py
【业务定位】：全平台多智能体战队（Agent Fleet）、三层模型治理、技能注册、黑板记忆与 AI 伴侣模型
【对应表名】：
  - agent_configs: 9 大专业智能体单体配置表
  - agent_model_category_configs: 3 大类别组大模型集中管控配置表
  - agent_skill_configs: 可插拔技能库（SKILL.md）注册表
  - agent_blackboard_sessions: 多智能体协同会商共享黑板记忆表
  - user_companion_pets: 用户专属 AI 观影伴侣（Codex 宠物）表
  - moderation_interrupt_queue: 人机回环（HITL）高危介入队列
  - agent_telemetry_logs: 智能体实时遥测指标流水表
  - agent_evolution_proposals: 智能体自主演化技能提议表
  - skill_operation_logs: 技能挂载与导出操作日志表
【核心功能】：
  支撑系统强大的多智能体战队与自动化工作流，支持单例热拔插与技能编排。
【对应前端】：
  - 管理后台智能体战队总控台：frontend/src/views/AdminView.vue (智能体战队 Tab)
  - 通用智能体会商与伴聊抽屉：frontend/src/components/UniversalAgentChatModal.vue
  - 多智能体圆桌推演画布：frontend/src/components/AgentRoundTableCanvas.vue
==============================================================================
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime
from app.core.database import Base

def _uuid() -> str:
    """生成 36 位标准 UUID 字符串"""
    return str(uuid.uuid4())

class AgentConfig(Base):
    """
    【9 大专业智能体单体配置实体】
    记录每个专业智能体（agent_1 至 agent_9）的运行开关、角色设定、系统提示词、
    以及三层模型绑定模式（全局统一 / 分类组绑定 / 独立自定义）。
    """
    __tablename__ = "agent_configs"

    # 智能体唯一标识：例如 "agent_1" .. "agent_9"
    agent_id = Column(String(36), primary_key=True, index=True)
    
    # 智能体编号：1 至 9
    agent_number = Column(Integer, nullable=False, default=1)
    
    # 智能体名称：如“台词伴聊官”、“毒舌影评猫”、“Agentic RAG 探针”等
    name = Column(String(100), nullable=False)
    
    # 专业角色头衔
    role_title = Column(String(120), nullable=False)
    
    # 所属智能体分类：REASONING_CORE(深度推理组), CREATIVE_STUDIO(创作工坊组), FAST_COMMUNITY(高频社区组)
    category = Column(String(50), nullable=False, default="REASONING_CORE")
    
    # 大模型绑定模式：GLOBAL_UNIFIED(共用全局统一大模型), CATEGORY_GROUP(跟随分类组配置), AGENT_CUSTOM(该智能体专属独立模型)
    model_bind_mode = Column(String(40), nullable=False, default="GLOBAL_UNIFIED")
    
    # 专属大模型提供商（仅在 AGENT_CUSTOM 模式下生效）：如 ollama, deepseek, openai
    provider = Column(String(40), nullable=False, default="ollama")
    
    # 专属模型名：如 deepseek-r1:1.5b, gpt-4o-mini
    model_name = Column(String(100), nullable=False, default="deepseek-r1:1.5b")
    
    # 专属 API 地址与密钥
    base_url = Column(String(255), nullable=True, default="")
    api_key = Column(String(255), nullable=True, default="")
    
    # 采样温度与单次超时限制（秒）
    temperature = Column(Float, nullable=False, default=0.4)
    timeout_sec = Column(Float, nullable=False, default=25.0)
    
    # 是否激活该智能体（支持管理员随时一键禁用）
    is_enabled = Column(Boolean, nullable=False, default=True)
    
    # 禁用状态下的友好降级兜底提示词
    disabled_fallback_msg = Column(
        Text,
        nullable=False,
        default="该专业智能体当前正由管理员维护中，已由 9 号总控智能体为您无缝接管解答。"
    )
    
    # 系统提示词（System Prompt）
    system_prompt = Column(Text, nullable=False, default="")
    
    # 智能体人设背景故事
    backstory = Column(Text, nullable=True, default="")
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AgentModelCategoryConfig(Base):
    """
    【3 大功能分类组大模型集中管控配置实体】
    支持管理员按职能大类为智能体批量配置底座大模型：
    - REASONING_CORE: 深度推理核心组（9号总控、3号RAG探针、6号多模态剧本分析）
    - CREATIVE_STUDIO: 创作工坊组（5号创作者助手、8号导演分镜团队、2号AI观影宠物）
    - FAST_COMMUNITY: 高频社区组（1号评论区伴聊、4号合规安全巡查、7号短剧推荐官）
    """
    __tablename__ = "agent_model_category_configs"

    # 分类唯一键：REASONING_CORE, CREATIVE_STUDIO, FAST_COMMUNITY
    category_key = Column(String(50), primary_key=True, index=True)
    
    # 分类友好显示名
    category_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True, default="")
    
    # 该分类采用的大模型提供商、模型名与通信参数
    provider = Column(String(40), nullable=False, default="ollama")
    model_name = Column(String(100), nullable=False, default="deepseek-r1:1.5b")
    base_url = Column(String(255), nullable=True, default="")
    api_key = Column(String(255), nullable=True, default="")
    temperature = Column(Float, nullable=False, default=0.4)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SkillConfig(Base):
    """
    【可插拔技能库配置实体】
    基于 SKILL.md 规范的可扩展外部技能。
    支持挂载到指定智能体或全平台一键全局挂载，支持关键词动态路由召回。
    """
    __tablename__ = "agent_skill_configs"

    skill_id = Column(String(64), primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    category = Column(String(64), nullable=False, default="短剧编排")
    description = Column(Text, nullable=False, default="")
    
    # 唤醒该技能的关键词（英文逗号分隔）
    trigger_keywords = Column(String(500), nullable=False, default="")
    
    # 完整的 Markdown 规范技能说明文档与工具定义
    skill_markdown = Column(Text, nullable=False, default="")
    
    # 已挂载绑定的智能体 ID 列表（JSON 数组，例如 ["agent_1", "agent_3"]）
    mounted_agents_json = Column(Text, nullable=False, default="[]")
    
    # 是否全平台 9 大智能体全局默认挂载
    is_global_mount = Column(Boolean, nullable=False, default=False)
    
    # 技能是否启用
    is_enabled = Column(Boolean, nullable=False, default=True)
    
    # 技能来源文件路径
    source_path = Column(String(255), nullable=True, default="builtin")
    
    # 历史被命中触发调用的总次数
    hit_count = Column(Integer, nullable=False, default=0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AgentBlackboardSession(Base):
    """
    【多智能体协同共享黑板记忆实体】
    9 大智能体在多轮圆桌会商推演时共用的共享黑板状态空间。
    包含共识事实（shared_facts）、滑动窗口对话记忆与定期自适应上下文压缩总结。
    """
    __tablename__ = "agent_blackboard_sessions"

    session_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    drama_id = Column(String(36), nullable=True, index=True)
    episode_id = Column(String(36), nullable=True, index=True)
    
    # 共享事实池（JSON 字典，记录已确认的人物关系、线索证据）
    shared_facts_json = Column(Text, nullable=False, default="{}")
    
    # 滚动历史摘要（防止上下文爆炸）
    rolling_summary = Column(Text, nullable=False, default="")
    
    # 最近几轮对话原始消息（JSON 数组）
    recent_turns_json = Column(Text, nullable=False, default="[]")
    
    # 累计交互轮次与上下文压缩执行次数
    turn_count = Column(Integer, nullable=False, default=0)
    compression_count = Column(Integer, nullable=False, default=0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserCompanionPet(Base):
    """
    【用户专属 AI 观影伴侣（Codex 宠物）实体】
    2 号智能体在用户个人空间的拟人化呈现。
    支持用户切换人设性格（如毒舌影评喵、元气小柴犬、冷面侦探）、喂食金币升级以及好感度互动。
    """
    __tablename__ = "user_companion_pets"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), unique=True, index=True, nullable=False)
    
    # 宠物名称：如“影评小喵”、“追剧柴柴”
    pet_name = Column(String(64), nullable=False, default="影评小喵")
    
    # 人设性格标识：sharp_critic(毒舌毒评), warm_cheerleader(元气鼓励), silent_detective(冷酷侦探)
    persona_key = Column(String(40), nullable=False, default="sharp_critic")
    persona_label = Column(String(64), nullable=False, default="毒舌影评喵")
    
    # 角色与目标 Prompt
    role_prompt = Column(Text, nullable=False, default="一个一针见血的毒舌短剧吐槽专家。")
    goal_prompt = Column(Text, nullable=False, default="准确识破套路剧情，精确定位剧情反转爆点并犀利点评。")
    backstory_prompt = Column(Text, nullable=False, default="看片三千部的阅片达人，最懂观众的情绪爽点。")
    
    # 等级与经验值（喂食金币可增加经验升级）
    level = Column(Integer, nullable=False, default=1)
    exp = Column(Integer, nullable=False, default=20)
    
    # 当前心情值（0 至 100）
    mood_score = Column(Integer, nullable=False, default=90)
    
    # 累计喂食金币数
    total_coins_fed = Column(Integer, nullable=False, default=0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ModerationInterruptQueue(Base):
    """
    【人机回环（HITL）高危介入队列实体】
    4 号合规审查智能体对风险分在 30~85 分之间的边缘违规弹幕与评论，
    自动暂停流水线并挂起进入该人工介入工单队列，等待审核员一键放行或驳回。
    """
    __tablename__ = "moderation_interrupt_queue"

    interrupt_id = Column(String(36), primary_key=True, default=_uuid, index=True)
    source_type = Column(String(32), nullable=False, default="comment")  # comment(评论) | danmaku(弹幕)
    target_id = Column(String(36), nullable=True, index=True)
    video_id = Column(String(36), nullable=True, index=True)
    episode_id = Column(String(36), nullable=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    username = Column(String(64), nullable=False, default="观众用户")
    content_text = Column(Text, nullable=False)
    
    # 风险评分（0-100）与判定理由
    risk_score = Column(Integer, nullable=False, default=50)
    risk_reason = Column(Text, nullable=False, default="")
    matched_words = Column(String(255), nullable=True, default="")
    
    # 介入状态：PENDING(待介入), APPROVED(人工放行), REJECTED(人工拦截封禁)
    status = Column(String(32), nullable=False, default="PENDING")
    reviewer_username = Column(String(64), nullable=True, default="")
    reviewer_note = Column(Text, nullable=True, default="")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

class AgentTelemetryLog(Base):
    """
    【智能体实时遥测指标流水实体】
    记录智能体每一次被触发调用的链路追踪（Trace ID）、底层解析模型、耗时、Token 吞吐与问答快照。
    驱动管理中台智能体 BI 仪表盘与实时战术大屏。
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
    
    # 毫秒耗时与 Token 消耗
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
    【智能体自主演化技能提议实体】
    智能体在处理高难度追剧推理时，评判模型（Critic）自主提炼总结的高效工具方案。
    以提案形式归档，待管理员审核通过后一键转为正式 SKILL.md。
    """
    __tablename__ = "agent_evolution_proposals"

    id = Column(String(36), primary_key=True, default=_uuid, index=True)
    proposal_title = Column(String(120), nullable=False)
    target_agent_id = Column(String(50), nullable=False, index=True)
    source_session_id = Column(String(64), nullable=True)
    category = Column(String(64), nullable=False, default="编排演进")
    generated_skill_content = Column(Text, nullable=False)
    trigger_keywords = Column(String(255), nullable=False, default="")
    critic_score = Column(Float, nullable=False, default=92.0)
    critic_verdict = Column(Text, nullable=False, default="通过")
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING | APPROVED | REJECTED
    reviewed_by = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    reviewed_at = Column(DateTime, nullable=True)

class SkillOperationLog(Base):
    """
    【技能生命周期操作审计日志实体】
    记录技能的加载、卸载、新建、删除以及切片导出到 RAG 知识库的操作历史。
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
