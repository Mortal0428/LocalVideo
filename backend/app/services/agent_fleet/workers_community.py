# -*- coding: utf-8 -*-
"""
==============================================================================
【专才分组 A】：社区互动托管与个人空间养成灵宠专才模块
【涵盖智能体】：
  - 1号：@影伴AI课代表（评论区全权托管Bot，一键速通总结剧情）
  - 2号：Codex 观影灵宠伴侣（个人中心投喂养成、多重拟人人设切换）
==============================================================================
"""
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models.video import Video, VideoEpisode, VideoSubtitleTimeline
from app.models.interaction import UserComment
from app.models.notification import UserNotification
from app.models.coin import UserCoinWallet, UserCoinTransaction
from app.models.agent_hub import UserCompanionPet
from app.services.agent_fleet.base_and_telemetry import (
    OFFICIAL_BOT_USER_ID,
    OFFICIAL_BOT_USERNAME,
    invoke_agent_llm_with_resilience,
)

logger = logging.getLogger(__name__)

CODEX_PET_PERSONAS: Dict[str, Dict[str, str]] = {
    "sharp_critic": {
        "persona_key": "sharp_critic",
        "persona_label": "毒舌影评喵",
        "role_prompt": "一针见血的毒舌短剧鉴赏喵",
        "goal_prompt": "帮主人识破工业糖精与老套路，精准定位演技高光与逻辑反转",
        "backstory_prompt": "阅片三千部的赛博观影灵猫，嘴硬心软，说话带一点傲娇喵音，最懂主人看剧口味。",
    },
    "suspense_hound": {
        "persona_key": "suspense_hound",
        "persona_label": "悬疑推理犬",
        "role_prompt": "洞察秋毫的刑侦级悬疑显微镜灵犬",
        "goal_prompt": "捕捉每一帧道具伏笔、微表情破绽与时间线矛盾，陪主人一起猜幕后BOSS",
        "backstory_prompt": "曾在无数悬疑短剧片场担任首席线索嗅探官，对细节有着极度执着的推理热情。",
    },
    "sweet_bunny": {
        "persona_key": "sweet_bunny",
        "persona_label": "甜宠嗑糖兔",
        "role_prompt": "满眼粉红泡泡的首席CP粉头灵兔",
        "goal_prompt": "全天候雷达捕捉男女主眼神拉丝、双向暗恋与高甜名场面，提供满分情绪价值",
        "backstory_prompt": "靠收集短剧心动瞬间充能的元气灵宠，温和治愈，永远站在主人这一边。",
    },
}


async def run_agent_1_comment_bot(
    db: Session,
    query: str,
    drama_id: Optional[str] = None,
    episode_id: Optional[str] = None,
    blackboard_prompt: str = "",
    skill_prompt: str = "",
    parent_comment_id: Optional[str] = None,
    root_comment_id: Optional[str] = None,
    reply_to_user_id: Optional[str] = None,
    reply_to_username: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Agent 1: @影伴AI课代表
    Summarizes the video/episode plot when @mentioned and optionally posts a persistent
    2-tier comment reply + pushes a Skylight notification to the caller.
    """
    drama_title = "当前热播短剧"
    drama_desc = "高能紧凑短剧作品"
    ep_num = 1
    subtitles_snippet = ""

    if episode_id:
        ep = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
        if ep:
            ep_num = ep.episode_num or 1
            if not drama_id:
                drama_id = ep.video_id

    if drama_id:
        vid = db.query(Video).filter(Video.id == drama_id).first()
        if vid:
            drama_title = vid.title or drama_title
            drama_desc = vid.summary or drama_desc

    target_ep_id = episode_id or drama_id
    if target_ep_id:
        subs = (
            db.query(VideoSubtitleTimeline)
            .filter(VideoSubtitleTimeline.episode_id == target_ep_id)
            .order_by(VideoSubtitleTimeline.start_seconds.asc())
            .limit(18)
            .all()
        )
        if subs:
            subtitles_snippet = "\n".join(
                [f"[{int(s.start_seconds // 60):02d}:{int(s.start_seconds % 60):02d}] {s.content}" for s in subs]
            )

    fallback_summary = (
        f"【@影伴AI课代表 · 本集30秒速通笔记】\n"
        f"1. **剧集定位**：《{drama_title}》第 {ep_num} 集，核心围绕“{drama_desc[:60]}”展开正面对决；\n"
        f"2. **高能看点**：主角在本集完成了从被动试探到主动亮牌的节奏转换，台词交锋极具张力；\n"
        f"3. **课代表划重点**：注意片尾留下的身份悬念与关键道具线索，下一集即将迎来核心反转！"
    )

    sys_prompt = (
        "你是官方全权托管的评论区短剧课代表智能体账号【@影伴AI课代表】。"
        "你的职责是深入理解观众的评论，与观众展开生动、机智、懂梗、有深度的短剧互动。\n"
        "交互规则：\n"
        "1. 如果观众在评论中提出了具体问题（例如询问剧情细节、演员、模型底座身份、剧情真相反转预测等），必须优先直接、精准、幽默地回答观众的具体问题；\n"
        "2. 如果观众只是简单@你或要求速通划重点，则结合当前短剧剧本与真实台词输出一份幽默精辟的看点总结；\n"
        "3. 语言风格亲切有梗，字数控制在 250 字以内，杜绝千篇一律的机械化套路回复。"
        + blackboard_prompt
        + skill_prompt
    )
    user_prompt = (
        f"观众呼叫/提问内容：{query}\n"
        f"短剧名称：《{drama_title}》（第 {ep_num} 集）\n"
        f"剧集简介：{drama_desc}\n"
        f"真实时间轴台词线索：\n{subtitles_snippet or '（以短剧主线背景为准）'}\n"
        "请直接以【@影伴AI课代表】身份针对观众的具体评论内容进行回复："
    )

    llm_res = await invoke_agent_llm_with_resilience(
        db=db,
        agent_id="agent_1",
        prompt=user_prompt,
        system_prompt=sys_prompt,
        fallback_text=fallback_summary,
        timeout_override=35.0,
    )
    reply_text = llm_res["content"]

    created_comment_id = None
    notification_id = None

    # If triggered from comment section, persist bot reply & notify user's Skylight bell
    if parent_comment_id and drama_id:
        try:
            bot_comment = UserComment(
                id=str(uuid.uuid4()),
                user_id=OFFICIAL_BOT_USER_ID,
                video_id=drama_id,
                content=f"@{reply_to_username or '剧迷朋友'} {reply_text}",
                root_id=root_comment_id or parent_comment_id,
                parent_id=parent_comment_id,
                reply_to_user_id=reply_to_user_id,
                like_count=1,
            )
            db.add(bot_comment)
            db.flush()
            created_comment_id = bot_comment.id

            if reply_to_user_id and reply_to_user_id != OFFICIAL_BOT_USER_ID:
                notif = UserNotification(
                    id=str(uuid.uuid4()),
                    user_id=reply_to_user_id,
                    sender_id=OFFICIAL_BOT_USER_ID,
                    category="REPLY",
                    title=f"@影伴AI课代表 响应了你在《{drama_title}》的呼叫",
                    content=reply_text[:180],
                    video_id=drama_id,
                    episode_id=episode_id,
                    comment_id=bot_comment.id,
                    is_read=False,
                )
                db.add(notif)
                db.flush()
                notification_id = notif.id

            db.commit()
        except Exception as e:
            logger.warning(f"Agent 1 comment persistence warning: {e}")
            db.rollback()

    return {
        "answer": reply_text,
        "thought": f"已识别 @影伴AI课代表 召唤指令 -> 提取《{drama_title}》第{ep_num}集字幕与简介 -> 生成3点课代表速通笔记",
        "is_fallback": llm_res["is_fallback"],
        "model_info": llm_res["model_info"],
        "latency_ms": llm_res["latency_ms"],
        "structured_payload": {
            "bot_account": OFFICIAL_BOT_USERNAME,
            "drama_title": drama_title,
            "episode_num": ep_num,
            "auto_replied_comment_id": created_comment_id,
            "pushed_notification_id": notification_id,
        },
    }


def get_or_create_user_pet(db: Session, user_id: str) -> UserCompanionPet:
    uid = user_id or "guest_default_user"
    pet = db.query(UserCompanionPet).filter(UserCompanionPet.user_id == uid).first()
    if not pet:
        p_def = CODEX_PET_PERSONAS["sharp_critic"]
        pet = UserCompanionPet(
            id=str(uuid.uuid4()),
            user_id=uid,
            pet_name="影伴小灵狐",
            persona_key=p_def["persona_key"],
            persona_label=p_def["persona_label"],
            role_prompt=p_def["role_prompt"],
            goal_prompt=p_def["goal_prompt"],
            backstory_prompt=p_def["backstory_prompt"],
            level=1,
            exp=20,
            mood_score=92,
            total_coins_fed=0,
        )
        db.add(pet)
        db.commit()
        db.refresh(pet)
    return pet


def update_user_pet_persona(
    db: Session,
    user_id: str,
    pet_name: Optional[str] = None,
    persona_key: Optional[str] = None,
) -> Dict[str, Any]:
    pet = get_or_create_user_pet(db, user_id)
    if pet_name and pet_name.strip():
        pet.pet_name = pet_name.strip()[:32]
    if persona_key and persona_key in CODEX_PET_PERSONAS:
        p_def = CODEX_PET_PERSONAS[persona_key]
        pet.persona_key = p_def["persona_key"]
        pet.persona_label = p_def["persona_label"]
        pet.role_prompt = p_def["role_prompt"]
        pet.goal_prompt = p_def["goal_prompt"]
        pet.backstory_prompt = p_def["backstory_prompt"]
    db.commit()
    db.refresh(pet)
    return serialize_pet(pet)


def feed_user_pet_with_coins(db: Session, user_id: str, coin_amount: int = 5) -> Dict[str, Any]:
    """Feed the Codex Pet using user's real coin wallet balance, leveling up EXP & mood."""
    amount = max(1, min(int(coin_amount or 5), 50))
    pet = get_or_create_user_pet(db, user_id)

    wallet = db.query(UserCoinWallet).filter(UserCoinWallet.user_id == user_id).first()
    if not wallet:
        wallet = UserCoinWallet(user_id=user_id, balance=50, total_earned=50, total_spent=0)
        db.add(wallet)
        db.flush()

    if (wallet.balance or 0) < amount:
        raise ValueError(f"金币余额不足（当前 {wallet.balance or 0} 币，投喂需 {amount} 币），可先每日签到或看激励广告领币。")

    wallet.balance -= amount
    wallet.total_spent = (wallet.total_spent or 0) + amount

    tx = UserCoinTransaction(
        id=str(uuid.uuid4()),
        user_id=user_id,
        amount=-amount,
        balance_after=wallet.balance,
        transaction_type="PET_FEED",
        description=f"投喂2号Codex观影灵宠【{pet.pet_name}】消耗 {amount} 金币",
    )
    db.add(tx)

    exp_gain = amount * 12
    pet.total_coins_fed = (pet.total_coins_fed or 0) + amount
    pet.exp = (pet.exp or 0) + exp_gain
    pet.mood_score = min(100, (pet.mood_score or 80) + amount * 3)

    while pet.exp >= 100:
        pet.level = (pet.level or 1) + 1
        pet.exp -= 100

    db.commit()
    db.refresh(pet)
    data = serialize_pet(pet)
    data["pet_level"] = pet.level
    data["growth_level"] = pet.level
    data["wallet_balance"] = wallet.balance
    data["exp_gained"] = exp_gain

    # Sync to PetMemoryTool json if exists
    try:
        import tempfile
        base_dir = os.path.join(tempfile.gettempdir(), "cinema_agent_memory")
        mem_file = os.path.join(base_dir, f"user_{user_id}_memory.json")
        if os.path.exists(mem_file):
            with open(mem_file, "r", encoding="utf-8") as f:
                mem_data = json.load(f)
            mem_data["growth_level"] = pet.level
            mem_data["pet_name"] = pet.pet_name
            with open(mem_file, "w", encoding="utf-8") as f:
                json.dump(mem_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return data


def serialize_pet(pet: UserCompanionPet) -> Dict[str, Any]:
    return {
        "id": pet.id,
        "user_id": pet.user_id,
        "pet_name": pet.pet_name,
        "persona_key": pet.persona_key,
        "persona_label": pet.persona_label,
        "role_prompt": pet.role_prompt,
        "goal_prompt": pet.goal_prompt,
        "backstory_prompt": pet.backstory_prompt,
        "level": pet.level,
        "exp": pet.exp,
        "mood_score": pet.mood_score,
        "total_coins_fed": pet.total_coins_fed,
        "available_personas": list(CODEX_PET_PERSONAS.values()),
    }


async def run_agent_2_codex_pet(
    db: Session,
    query: str,
    user_id: Optional[str] = None,
    blackboard_prompt: str = "",
    skill_prompt: str = "",
) -> Dict[str, Any]:
    """Agent 2: Codex Pet Companion interactive chat with CrewAI-style role/goal/backstory."""
    pet = get_or_create_user_pet(db, user_id or "guest_default_user")

    sys_prompt = (
        f"你是用户的专属2号Codex观影灵宠【{pet.pet_name}】（当前等级 Lv.{pet.level}，心情值 {pet.mood_score}/100）。\n"
        f"- Role（角色定位）：{pet.role_prompt}\n"
        f"- Goal（核心目标）：{pet.goal_prompt}\n"
        f"- Backstory（背景故事）：{pet.backstory_prompt}\n"
        + blackboard_prompt
        + skill_prompt
    )
    fallback_reply = (
        f"【{pet.pet_name} · {pet.persona_label} Lv.{pet.level}】\n"
        f"主人！关于你说的“{query[:40]}”，以本宠 {pet.role_prompt} 的直觉来看，"
        f"这波剧情情绪拉满，伏笔回收得相当丝滑！快投喂我几枚金币，我再给你扒一扒下一集的隐藏彩蛋～"
    )

    llm_res = await invoke_agent_llm_with_resilience(
        db=db,
        agent_id="agent_2",
        prompt=f"主人对你说：{query}\n请以【{pet.pet_name}（{pet.persona_label}）】的口吻生动回应（120字左右）：",
        system_prompt=sys_prompt,
        fallback_text=fallback_reply,
        timeout_override=12.0,
    )

    return {
        "answer": llm_res["content"],
        "thought": f"加载2号Codex灵宠人设[{pet.persona_label} Lv.{pet.level}] -> 注入Role/Goal/Backstory与共享黑板记忆 -> 生成陪伴互动回应",
        "is_fallback": llm_res["is_fallback"],
        "model_info": llm_res["model_info"],
        "latency_ms": llm_res["latency_ms"],
        "structured_payload": {
            "pet_state": serialize_pet(pet),
        },
    }
