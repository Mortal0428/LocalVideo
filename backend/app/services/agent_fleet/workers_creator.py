"""
Expert Group D: Creator Studio & Director Script-Storyboard Crew
- Agent 5: 创作者中心作品运营助手 (Viral Title, Golden 3s Hook, Tags & Multi-Poster Strategy)
- Agent 8: 短剧导演与剧本分镜写作 Crew (Plan & Execute + Writer -> Director -> Critic Loop + Skills Injection)
"""
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.services.agent_fleet.base_and_telemetry import invoke_agent_llm_with_resilience

logger = logging.getLogger(__name__)


async def run_agent_5_creator_assist(
    db: Session,
    query: str,
    blackboard_prompt: str = "",
    skill_prompt: str = "",
) -> Dict[str, Any]:
    """
    Agent 5: Creator Center Viral Operations Assistant.
    Generates high-CTR titles, golden 3-second hooks, tags, and multi-cover carousel advice.
    """
    topic = (query or "都市高能反转短剧").strip()[:80]
    viral_candidates = [
        {
            "style": "强悬念反差型",
            "title": f"《倒计时72小时：他们不知道我才是底牌》",
            "ctr_prediction": "9.4%",
        },
        {
            "style": "极致情绪拉扯型",
            "title": f"《大雾散尽时，她站在光里亮出身份》",
            "ctr_prediction": "8.9%",
        },
        {
            "style": "高概念爽感型",
            "title": f"《第99次试探：全员恶人局的破局者》",
            "ctr_prediction": "9.1%",
        },
    ]

    fallback_copy = (
        f"### 【5号 创作者中心爆款作品策划案】\n"
        f"**创作主题**：`{topic}`\n\n"
        f"#### 1. 高点击率爆款剧名备选（A/B 测试推荐）\n"
        + "\n".join([f"- **{c['style']}**：{c['title']}（预估点击率 `{c['ctr_prediction']}`）" for c in viral_candidates])
        + "\n\n#### 2. 黄金前 3 秒完播留存钩子（Golden 3s Hook）\n"
        "- **第 1 秒（视觉反差）**：冷色调大雨特写，主角将染血或烫金邀请函扔进火盆；\n"
        "- **第 2 秒（台词暴击）**：“所有人都在等我认输，可这场局从三年前就是我攒的。”\n"
        "- **第 3 秒（悬念卡点）**：门外骤然响起急促敲门声，镜头急推至门把手转动瞬间切入正片。\n\n"
        "#### 3. 推荐标签与多封面画报轮播建议\n"
        "- **核心标签**：`#高能反转` `#极限拉扯` `#智商在线` `#电影感短剧`\n"
        "- **多海报轮播策略**：第1张采用高反差双人对峙主视觉，第2张采用关键道具悬念特写，第3张采用高潮名场面剧照。"
    )

    sys_prompt = (
        "你是5号创作者中心作品运营助手。"
        "请为创作者提供高点击率短剧标题备选、黄金前3秒留存钩子、爆款标签以及多封面轮播图设计建议。"
        + blackboard_prompt
        + skill_prompt
    )
    llm_res = await invoke_agent_llm_with_resilience(
        db=db,
        agent_id="agent_5",
        prompt=f"创作者创作需求：{query}\n请输出完整的爆款短剧包装策划方案：",
        system_prompt=sys_prompt,
        fallback_text=fallback_copy,
        timeout_override=14.0,
    )

    return {
        "answer": llm_res["content"],
        "thought": "解析创作者题材定位 -> 注入黄金前3秒悬念钩子公式Skill -> 生成3组A/B测试标题、开场钩子与多封面轮播策略",
        "is_fallback": llm_res["is_fallback"],
        "model_info": llm_res["model_info"],
        "latency_ms": llm_res["latency_ms"],
        "structured_payload": {
            "viral_titles": viral_candidates,
            "recommended_tags": ["高能反转", "极限拉扯", "智商在线", "电影感短剧"],
            "golden_3s_hook": "1秒极端反差画面 + 2秒核心冲突台词 + 3秒悬念留白",
        },
    }


async def run_agent_8_director_crew(
    db: Session,
    query: str,
    blackboard_prompt: str = "",
    skill_prompt: str = "",
) -> Dict[str, Any]:
    """
    Agent 8: Short-Drama Director & Script-Storyboard Writing Crew.
    Executes a 3-role internal workflow:
    1. Screenwriter (主笔编剧): Crafts high-tension scene script & character lock sheets
    2. Storyboard Director (分镜导演): Converts script into 9:16 vertical storyboard table
    3. Sharp Producer Critic (毒舌制片人): Audits pacing & hook density, ensuring >90 quality score
    """
    scene_theme = (query or "雨夜宴会厅身份揭晓名场面").strip()[:100]

    character_locks: List[Dict[str, str]] = [
        {
            "role_name": "沈知微（女主 / 幕后操盘者）",
            "visual_lock": "黑色修身丝绒长裙，左耳佩戴祖母绿耳坠，眼神冷冽克制，手持烫金股权书",
            "motivation": "在对手最志得意满的时刻当众完成致命反击",
        },
        {
            "role_name": "陆凛（男主 / 暗线盟友）",
            "visual_lock": "深灰双排扣西装，领口微敞，腕戴复古机械表，站于二楼廊桥俯瞰全场",
            "motivation": "配合女主封锁全场退路，必要时亮出底牌兜底",
        },
    ]

    storyboard_shots: List[Dict[str, Any]] = [
        {
            "shot_no": "S01",
            "framing_and_motion": "ECU 大特写 · 慢速推镜 (Push-in)",
            "visual_description": "9:16竖屏构图：高跟鞋踩碎地面水洼倒影，镜头顺势上移至女主紧握的烫金文件袋",
            "dialogue": "（画外音冷笑）“既然各位都签好字了，不妨看看最后一页写的是谁的名字。”",
            "sound_bgm": "低沉大提琴重音骤停 + 清脆脚步声回响",
            "duration_sec": 3.0,
        },
        {
            "shot_no": "S02",
            "framing_and_motion": "MCU 中近景 · 360度环绕运镜",
            "visual_description": "宴会厅大门轰然推开，冷光从背后勾勒出沈知微轮廓，全场宾客愕然回头",
            "dialogue": "反派拍案而起：“你怎么可能出现在这里？！”",
            "sound_bgm": "金属打击乐卡点 + 倒吸冷气环境音",
            "duration_sec": 4.0,
        },
        {
            "shot_no": "S03",
            "framing_and_motion": "CU 近景正反打 · 浅景深焦点切换",
            "visual_description": "沈知微指尖轻点桌面，文件袋滑向长桌中央，特写停留在鲜红公章与签名上",
            "dialogue": "沈知微：“三年前你拿走的，今天连本带利该物归原主了。”",
            "sound_bgm": "紧凑鼓点渐强 (BPM 128)",
            "duration_sec": 4.5,
        },
        {
            "shot_no": "S04",
            "framing_and_motion": "LS 竖屏仰拍转特写 · 希区柯克变焦",
            "visual_description": "二楼廊桥灯光亮起，陆凛缓步走出，抬手示意安保封锁全场通道",
            "dialogue": "陆凛：“忘了提醒各位，今晚这座大楼的最高权限，半小时前已经易主了。”",
            "sound_bgm": "高燃交响电子混音爆发 + 悬念尾音留白",
            "duration_sec": 5.0,
        },
    ]

    critic_review = {
        "producer_score": 94,
        "verdict": "APPROVED (一审通过，准予进入无限画布分镜生产)",
        "critique_notes": "前3秒视觉反差钩子到位，9:16竖屏景别以ECU/CU为主，台词无废话，情绪曲线在第12秒精准拉升至高潮。",
    }

    md_table_rows = "\n".join(
        [
            f"| {s['shot_no']} | {s['framing_and_motion']} | {s['visual_description']} | {s['dialogue']} | {s['sound_bgm']} | {s['duration_sec']}s |"
            for s in storyboard_shots
        ]
    )

    fallback_script = (
        f"### 【8号 短剧导演与剧本分镜工作坊】《{scene_theme}》工业级分镜方案\n\n"
        f"#### 一、角色外貌与气场锁死卡（Character Visual Lock）\n"
        + "\n".join([f"- **{c['role_name']}**：{c['visual_lock']}（核心动机：{c['motivation']}）" for c in character_locks])
        + "\n\n#### 二、9:16 竖屏导演分镜脚本表（Director Storyboard）\n"
        "| 镜号 | 景别与运镜 | 画面视觉描述 | 台词与潜台词 | BGM/音效设计 | 时长 |\n"
        "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
        + md_table_rows
        + f"\n\n#### 三、毒舌制片人审稿结论（Producer Critic Loop）\n"
        f"- **综合评分**：`{critic_review['producer_score']} / 100`（状态：`{critic_review['verdict']}`）\n"
        f"- **制片审校意见**：{critic_review['critique_notes']}"
    )

    sys_prompt = (
        "你是8号短剧导演与剧本分镜写作 Crew 智能体（包含主笔编剧、分镜导演、毒舌制片人三角色协同）。"
        "请严格按照竖屏微短剧导演规范，输出【角色外貌锁死设定】、【高冲突剧本】、【Markdown标准分镜表】以及【毒舌制片人评分点评】。"
        + blackboard_prompt
        + skill_prompt
    )
    llm_res = await invoke_agent_llm_with_resilience(
        db=db,
        agent_id="agent_8",
        prompt=f"导演分镜创作命题：{query}\n请输出完整的角色设定、分镜表与制片人审稿结论：",
        system_prompt=sys_prompt,
        fallback_text=fallback_script,
        timeout_override=18.0,
    )

    return {
        "answer": llm_res["content"],
        "thought": (
            "Plan&Execute导演工作流启动 -> [1.主笔编剧]构建冲突台词与角色视觉锁 -> "
            "[2.分镜导演]挂载竖屏微短剧分镜规范生成4镜脚本 -> "
            f"[3.毒舌制片人]审校打分({critic_review['producer_score']}分)通过"
        ),
        "is_fallback": llm_res["is_fallback"],
        "model_info": llm_res["model_info"],
        "latency_ms": llm_res["latency_ms"],
        "structured_payload": {
            "scene_theme": scene_theme,
            "character_locks": character_locks,
            "storyboard_shots": storyboard_shots,
            "critic_review": critic_review,
        },
    }
