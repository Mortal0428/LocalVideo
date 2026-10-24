"""
Agent 4 专用解耦工具: 内容风控与安全审片
负责提供平台敏感词审查数据、违禁词拦截统计与人机中断审批单据
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.review import SensitiveWord
from app.models.agent_hub import ModerationInterruptQueue
from app.services.agent_fleet.tools.base_tool import BaseDecoupledTool


class ModerationStatsInput(BaseModel):
    include_pending: bool = Field(True, description="是否包含待处理审批队列")


class ModerationStatsTool(BaseDecoupledTool):
    name = "get_moderation_stats_tool"
    description = "查询平台敏感词库规模、拦截统计及人机回环挂起单据"
    args_schema = ModerationStatsInput
    category = "moderation"

    def execute(self, include_pending: bool = True) -> Dict[str, Any]:
        db: Session = SessionLocal()
        try:
            total_sensitive_words = db.query(SensitiveWord).count()
            pending_interrupts = db.query(ModerationInterruptQueue).filter(
                ModerationInterruptQueue.status == "PENDING"
            ).all()

            pending_list = [
                {
                    "interrupt_id": item.id,
                    "target_type": item.target_type,
                    "risk_score": item.risk_score,
                    "matched_words": item.matched_words,
                    "preview": (item.content_text or "")[:60],
                    "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else "",
                }
                for item in pending_interrupts[:8]
            ]

            return {
                "active_sensitive_lexicon_count": total_sensitive_words,
                "pending_interrupts_count": len(pending_interrupts),
                "pending_items": pending_list if include_pending else [],
                "risk_advice": "建议每周结合最新下沉短剧网络热梗更新违禁词库，保障台词与弹幕零合规风险。"
                if total_sensitive_words < 50
                else "当前词库规模健全，运行在平稳白名单防御状态。",
            }
        finally:
            db.close()
