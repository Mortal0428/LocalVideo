"""
==============================================================================
【工具名称】：全域弹幕与评论内容风控安全审查工具 (moderation_safety_tools)
【工具标识】：moderation_inspect_content
【全链路调用位置】：
  1. 用户在前端发送弹幕/发表评论时被风控拦截管道调用；
  2. 管理员在 MCP 云端中台在线沙盒调试时被触发执行；
  3. 4 号合规守卫智能体 (ModerationGatekeeperPod) 执行自动巡检时调用。
【核心处理逻辑】：
  1. 扫描文本是否命中敏感违规词库 (政治敏感、暴恐、涉黄、恶意辱骂)；
  2. 计算综合风险分 (0~100)；
  3. 给出判定裁决 (SAFE 安全放行 / BLOCK 直接拦截违规 / REVIEW 进入人工复核队列)。
==============================================================================
"""

import re
from typing import Dict, Any, List, Optional
from app.core.database import SessionLocal
from app.models.review import SensitiveWord


async def mcp_inspect_danmaku_safety(
    content: str,
    target_type: str = "danmaku",
    risk_threshold: int = 60
) -> Dict[str, Any]:
    """
    对弹幕或评论文本执行深度合规安全扫描。

    Args:
        content: 待检测的弹幕或评论文本
        target_type: 检测对象类型 ('danmaku' | 'comment')
        risk_threshold: 触发阻断的风险分阈值 (0~100)
    """
    if not content or not content.strip():
        return {
            "verdict": "SAFE",
            "risk_score": 0,
            "matched_keywords": [],
            "suggested_action": "PASS",
            "reason": "内容为空"
        }

    clean_content = content.strip()
    db = SessionLocal()
    matched_words = []
    max_risk = 0

    try:
        # 查询系统违规敏感词表
        sensitive_words = db.query(SensitiveWord).all()
        for sw in sensitive_words:
            w = sw.word.strip() if sw.word else ""
            if w and w in clean_content:
                matched_words.append({
                    "word": w,
                    "level": sw.level or "MEDIUM",
                    "category": sw.category or "通用违规"
                })
                lvl = (sw.level or "MEDIUM").upper()
                if lvl == "HIGH":
                    max_risk = max(max_risk, 90)
                elif lvl == "MEDIUM":
                    max_risk = max(max_risk, 65)
                else:
                    max_risk = max(max_risk, 40)

        # 检查高危攻击性模式
        vulgar_pattern = r"(傻逼|操你|死全家|垃圾|脑残|滚粗)"
        if re.search(vulgar_pattern, clean_content):
            matched_words.append({
                "word": "攻击性污秽言论",
                "level": "HIGH",
                "category": "侮辱谩骂"
            })
            max_risk = max(max_risk, 95)

        verdict = "SAFE"
        suggested_action = "PASS"
        if max_risk >= risk_threshold:
            verdict = "VIOLATION" if max_risk >= 80 else "SUSPICIOUS"
            suggested_action = "DELETE" if max_risk >= 80 else "PENDING_HITL"

        return {
            "verdict": verdict,
            "risk_score": max_risk,
            "matched_count": len(matched_words),
            "matched_keywords": matched_words,
            "suggested_action": suggested_action,
            "target_type": target_type,
            "inspected_content": clean_content[:100]
        }
    finally:
        db.close()
