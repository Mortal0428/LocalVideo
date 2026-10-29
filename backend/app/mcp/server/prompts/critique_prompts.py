"""
CinemaAgent MCP 标准提示词模板仓库 (Prompts)
统一业务 Prompt 格式规范，免除客户端与各模型重复编写
"""


def critique_plot_twist_prompt(drama_title: str, character: str = "") -> str:
    """
    生成针对 1号 @影伴AI课代表 的剧情矛盾与反转深度透视提示词模板
    """
    char_clause = f"，重点聚焦角色【{character}】的情绪动机与隐藏伏笔" if character else ""
    return (
        f"你作为热播短剧《{drama_title}》的官方 AI 剧情课代表{char_clause}。\n"
        f"请从以下三维视角展开精辟、透彻、接地气的剧情拆解：\n"
        f"1. 【矛盾导火索】：表面冲突之下的真实利益争夺是什么？\n"
        f"2. 【高能反转点】：哪些台词和视听伏笔预示了后期的身份反转？\n"
        f"3. 【课代表划重点】：一句话总结这几集最爽的情绪钩子与金句提炼。"
    )


def moderation_audit_summary_prompt(date_str: str = "2026-10-27") -> str:
    """
    生成符合合规治理标准的弹幕风控审计综述报告模板
    """
    return (
        f"请根据【{date_str}】全站弹幕与评论巡检日志，输出一份工业级内容风控审计小结：\n"
        f"1. 今日高频违规关键词 Top 5 及变体形式分析；\n"
        f"2. 人机协同拦截率（机审拦截 vs 人工复核）；\n"
        f"3. 下一步风控词库自进化迭代建议（需要加入黑名单的高频谐音隐蔽词）。"
    )
