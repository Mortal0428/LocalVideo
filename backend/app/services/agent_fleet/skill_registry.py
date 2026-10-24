"""
Skills Free-Mounting Manager & Progressive Disclosure Engine (CinemaAgent).
Supports:
- Seeded 6 Short-Drama Golden SKILL.md packs
- Automatic discovery of local `.agents/skills/*/SKILL.md` packages
- Targeted binding to specific agents OR 1-click global mounting (`is_global_mount`)
- Progressive disclosure: metadata scan in Thought -> full SKILL.md SOP injection on match
"""
import os
import json
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.agent_hub import SkillConfig

logger = logging.getLogger(__name__)

BUILTIN_SHORT_DRAMA_SKILLS: List[Dict[str, Any]] = [
    {
        "skill_id": "skill_short_drama_hook",
        "name": "黄金前3秒悬念钩子公式",
        "category": "短剧宣发与编剧",
        "description": "竖屏微短剧开篇前3秒留存率提升法则：强身份反差 + 极端情绪冲突 + 倒计时危机钩子。",
        "trigger_keywords": "钩子,黄金3秒,开篇,标题,剧名,爆款,留存,前3秒,简介,创作,剧本",
        "mounted_agents": ["agent_5", "agent_8", "agent_9"],
        "is_global_mount": False,
        "skill_markdown": (
            "# 黄金前3秒悬念钩子公式 (SKILL.md)\n"
            "## 执行 SOP\n"
            "1. **第一秒视觉冲击**：必须给出强反差特写镜头（如狼狈场景与高贵信物同框、突发危机特写）。\n"
            "2. **第二秒台词暴击**：首句台词禁止寒暄，直接抛出核心矛盾、背叛或生死抉择。\n"
            "3. **第三秒悬念留白**：在观众最想知道结果的一瞬切入反转悬念，引导连续追更。"
        ),
    },
    {
        "skill_id": "skill_director_storyboard_sop",
        "name": "竖屏微短剧导演分镜表规范",
        "category": "导演分镜工程",
        "description": "9:16 竖屏微短剧工业级分镜脚本生成标准，涵盖景别（特写/近景/中景）、运镜、情绪张力与音效设计。",
        "trigger_keywords": "分镜,导演,镜头,剧本,景别,特写,运镜,写作,拍摄,场记",
        "mounted_agents": ["agent_8", "agent_5", "agent_6"],
        "is_global_mount": False,
        "skill_markdown": (
            "# 竖屏微短剧导演分镜表规范 (SKILL.md)\n"
            "## 执行 SOP\n"
            "1. **竖屏构图铁律**：9:16画幅优先采用近景（CU）与特写（ECU）捕捉微表情，减少大远景导致的手机端信息丢失。\n"
            "2. **角色外貌锚点锁死**：在分镜前先锁定主角服装、发型与标志性道具，防止跨镜头角色崩坏。\n"
            "3. **标准分镜字段**：每个镜号必须包含【镜号、景别与运镜、画面视觉描述、人物台词与潜台词、BGM/音效卡点、时长预估】。"
        ),
    },
    {
        "skill_id": "skill_multimodal_plot_deconstruct",
        "name": "多模态镜头语言与剧情三路解构单",
        "category": "视听剧情分析",
        "description": "融合字幕时间轴(耳)、关键帧微表情场记(眼)与人物关系图谱(脑)的三路交叉剧情推演技能。",
        "trigger_keywords": "剧情,分析,解读,讲了什么,为什么,伏笔,反转,结局,动机,关系,总结,这集",
        "mounted_agents": ["agent_1", "agent_6", "agent_9"],
        "is_global_mount": True,
        "skill_markdown": (
            "# 多模态镜头语言与剧情三路解构单 (SKILL.md)\n"
            "## 执行 SOP\n"
            "1. **听觉轨（字幕台词）**：提取核心冲突台词与时间锚点 `[mm:ss]`，识别言外之意。\n"
            "2. **视觉轨（关键帧场记）**：结合画面光影冷暖、眼神闪躲与道具特写补充纯文本缺失的潜台词。\n"
            "3. **图谱轨（人物关系网）**：串联前后集人物恩怨、隐藏身份与利益链条，输出结构化深度解读。"
        ),
    },
    {
        "skill_id": "skill_crag_self_reflection",
        "name": "CRAG自反思查询重写与防剧透门控",
        "category": "检索增强工程",
        "description": "对分片切块召回结果进行相关性自检，低分自动触发 Query Rewrite 重搜，并严格锁定播放时间轴防剧透。",
        "trigger_keywords": "检索,分片,切块,台词,哪一集,几分几秒,提到,道具,线索,RAG",
        "mounted_agents": ["agent_3", "agent_6", "agent_9"],
        "is_global_mount": False,
        "skill_markdown": (
            "# CRAG自反思查询重写与防剧透门控 (SKILL.md)\n"
            "## 执行 SOP\n"
            "1. **分片自适应**：台词密集型采用时间轴滑动窗口切块，剧本大纲采用父子层级切块。\n"
            "2. **CRAG 相关性门控**：评估召回片段与问题的语义匹配度，若低于阈值则提取同义实体重写查询。\n"
            "3. **时间轴防剧透**：默认优先引用当前播放进度之前的证据锚点，保护首次观影惊喜感。"
        ),
    },
    {
        "skill_id": "skill_community_safety_rubric",
        "name": "社区弹幕评论分级风控与人机协同守则",
        "category": "内容安全合规",
        "description": "0~100分三级风险量化标准：0~29分直接放行，30~85分触发 LangGraph interrupt 人工复核，86~100分立即拦截。",
        "trigger_keywords": "违规,审核,弹幕,评论,敏感词,辱骂,剧透,风控,举报",
        "mounted_agents": ["agent_4", "agent_9"],
        "is_global_mount": False,
        "skill_markdown": (
            "# 社区弹幕评论分级风控与人机协同守则 (SKILL.md)\n"
            "## 执行 SOP\n"
            "1. **一级快筛（0~29分）**：正常剧情讨论、玩梗吐槽或情绪共鸣，毫秒级放行。\n"
            "2. **二级灰区挂起（30~85分）**：疑似恶意剧透关键大结局、擦边谐音或争议性拉踩，触发 `interrupt()` 挂起至审核员工作台。\n"
            "3. **三级高危熔断（86~100分）**：明确命中违禁词库、人身攻击或违法引流，立即拦截并记录风控流水。"
        ),
    },
    {
        "skill_id": "skill_socratic_drama_recommender",
        "name": "苏格拉底式追问选片与零幻觉校验法",
        "category": "智能推荐与陪伴",
        "description": "严禁编造虚假剧名，100%基于MySQL实库在架作品匹配，并通过口味反问精准锁定用户当下想看的爽点类型。",
        "trigger_keywords": "推荐,好看,剧荒,类似,同款,想看,甜宠,悬疑,逆袭,战神,古装",
        "mounted_agents": ["agent_7", "agent_2", "agent_9"],
        "is_global_mount": False,
        "skill_markdown": (
            "# 苏格拉底式追问选片与零幻觉校验法 (SKILL.md)\n"
            "## 执行 SOP\n"
            "1. **实库硬约束**：所有推荐剧目必须来自系统数据库真实在架列表，严禁凭空捏造剧名。\n"
            "2. **三选一追问**：在给出首轮推荐的同时，主动追问观众偏好（例如：更喜欢快节奏爽感逆袭，还是高智商极限拉扯？）。"
        ),
    },
]


def ensure_skills_seeded(db: Session) -> None:
    """Seed the 6 built-in short-drama skills and scan `.agents/skills` directory."""
    try:
        for sk in BUILTIN_SHORT_DRAMA_SKILLS:
            existing = db.query(SkillConfig).filter(SkillConfig.skill_id == sk["skill_id"]).first()
            if not existing:
                db.add(
                    SkillConfig(
                        skill_id=sk["skill_id"],
                        name=sk["name"],
                        category=sk["category"],
                        description=sk["description"],
                        trigger_keywords=sk["trigger_keywords"],
                        skill_markdown=sk["skill_markdown"],
                        mounted_agents_json=json.dumps(sk["mounted_agents"], ensure_ascii=False),
                        is_global_mount=sk["is_global_mount"],
                        is_enabled=True,
                        source_path="builtin://short-drama-pack",
                        hit_count=5,
                    )
                )
        db.commit()

        # Also scan workspace `.agents/skills/*/SKILL.md` for local external skills
        workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
        skills_dir = os.path.join(workspace_root, ".agents", "skills")
        if os.path.isdir(skills_dir):
            for entry in sorted(os.listdir(skills_dir))[:8]:
                skill_md_path = os.path.join(skills_dir, entry, "SKILL.md")
                if os.path.isfile(skill_md_path):
                    sid = f"ext_skill_{entry.replace('-', '_')}"
                    exists = db.query(SkillConfig).filter(SkillConfig.skill_id == sid).first()
                    if not exists:
                        try:
                            with open(skill_md_path, "r", encoding="utf-8", errors="ignore") as f:
                                raw_md = f.read(2500)
                            db.add(
                                SkillConfig(
                                    skill_id=sid,
                                    name=f"GitHub外部技能 · {entry}",
                                    category="外部GitHub技能库",
                                    description=f"从本地 .agents/skills/{entry}/SKILL.md 自动扫描导入的工程技能插件。",
                                    trigger_keywords=f"{entry},动画,UI,交互,设计,组件",
                                    skill_markdown=raw_md,
                                    mounted_agents_json=json.dumps(["agent_5", "agent_8"], ensure_ascii=False),
                                    is_global_mount=False,
                                    is_enabled=True,
                                    source_path=f".agents/skills/{entry}/SKILL.md",
                                    hit_count=1,
                                )
                            )
                        except Exception:
                            pass
            db.commit()
    except Exception as e:
        logger.warning(f"Skills seed non-fatal warning: {e}")
        db.rollback()


def match_and_inject_skills(
    db: Session,
    agent_id: str,
    query: str,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    During the Agent's `Thought` phase:
    1. Filter enabled skills that either have `is_global_mount == True` OR include `agent_id` in `mounted_agents_json`.
    2. Match against query keywords (or include top mounted domain skill so the agent always benefits from its mounted specialty).
    3. Increment `hit_count` and build the progressive disclosure SOP prompt block.
    """
    ensure_skills_seeded(db)
    all_enabled = db.query(SkillConfig).filter(SkillConfig.is_enabled == True).all()

    available_for_agent: List[SkillConfig] = []
    for sk in all_enabled:
        try:
            mounted_list = json.loads(sk.mounted_agents_json or "[]")
        except Exception:
            mounted_list = []
        if sk.is_global_mount or (agent_id in mounted_list):
            available_for_agent.append(sk)

    if not available_for_agent:
        return [], ""

    q_lower = (query or "").lower()
    matched: List[SkillConfig] = []
    for sk in available_for_agent:
        kws = [k.strip().lower() for k in (sk.trigger_keywords or "").split(",") if k.strip()]
        if any(k in q_lower for k in kws):
            matched.append(sk)

    # If no specific keyword matched, attach the primary mounted skill for this agent (up to 2)
    if not matched:
        matched = available_for_agent[:2]
    else:
        matched = matched[:3]

    matched_meta: List[Dict[str, Any]] = []
    sop_blocks: List[str] = []
    for sk in matched:
        sk.hit_count = (sk.hit_count or 0) + 1
        matched_meta.append(
            {
                "skill_id": sk.skill_id,
                "name": sk.name,
                "category": sk.category,
                "is_global_mount": bool(sk.is_global_mount),
                "source_path": sk.source_path,
            }
        )
        sop_blocks.append(f"### 【已激活挂载技能：{sk.name}】\n{sk.skill_markdown}")

    try:
        db.commit()
    except Exception:
        db.rollback()

    injected_prompt = (
        "\n\n【Skills 渐进式披露技能指令注入】\n"
        "你在思考（Thought）阶段已自动命中并挂载以下专业技能规范，请严格遵照执行：\n"
        + "\n\n".join(sop_blocks)
    )
    return matched_meta, injected_prompt
