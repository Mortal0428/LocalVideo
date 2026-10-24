"""
Blackboard Shared State & Sliding-Window Auto-Summarization Memory Integrator.
Allows all 9 specialized agents to share context seamlessly and prevents
context window explosion via automatic rolling summarization.
"""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models.agent_hub import AgentBlackboardSession

logger = logging.getLogger(__name__)

SLIDING_WINDOW_MAX_TURNS = 6
KEEP_RECENT_TURNS = 3


class BlackboardMemoryIntegrator:
    """
    Manages cross-agent shared Blackboard state and sliding-window summarization.
    """

    @staticmethod
    def get_or_create_session(
        db: Session,
        session_id: str,
        user_id: Optional[str] = None,
        drama_id: Optional[str] = None,
        episode_id: Optional[str] = None,
    ) -> AgentBlackboardSession:
        sid = (session_id or "global_shared_session").strip()
        rec = db.query(AgentBlackboardSession).filter(AgentBlackboardSession.session_id == sid).first()
        if not rec:
            initial_facts = {
                "active_drama_id": drama_id or "",
                "active_episode_id": episode_id or "",
                "user_taste_tags": ["高能反转", "快节奏悬疑", "细腻情感"],
                "last_invoked_agent": "agent_9",
                "shared_notes": [],
            }
            rec = AgentBlackboardSession(
                session_id=sid,
                user_id=user_id,
                drama_id=drama_id,
                episode_id=episode_id,
                shared_facts_json=json.dumps(initial_facts, ensure_ascii=False),
                rolling_summary="会话已初始化，全局黑板记忆池正在跨智能体同步上下文。",
                recent_turns_json="[]",
                turn_count=0,
                compression_count=0,
            )
            db.add(rec)
            db.commit()
            db.refresh(rec)
        return rec

    @staticmethod
    def build_context_prompt(rec: AgentBlackboardSession) -> str:
        try:
            facts = json.loads(rec.shared_facts_json or "{}")
        except Exception:
            facts = {}
        try:
            turns = json.loads(rec.recent_turns_json or "[]")
        except Exception:
            turns = []

        turns_str = "\n".join(
            [f"- [{t.get('agent_id', 'agent')}] 用户: {t.get('q', '')} -> 响应: {t.get('a', '')[:120]}" for t in turns[-4:]]
        )
        return (
            f"\n【全局共享黑板 (Blackboard) 上下文】\n"
            f"- 历史滚动摘要：{rec.rolling_summary or '暂无历史摘要'}\n"
            f"- 跨智能体共享事实锚点：{json.dumps(facts, ensure_ascii=False)}\n"
            f"- 最近对话滑窗：\n{turns_str or '（当前为首轮对话）'}\n"
        )

    @classmethod
    def append_turn_and_auto_compress(
        cls,
        db: Session,
        session_id: str,
        agent_id: str,
        query: str,
        answer: str,
        new_facts: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        drama_id: Optional[str] = None,
        episode_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        rec = cls.get_or_create_session(db, session_id, user_id, drama_id, episode_id)
        try:
            facts = json.loads(rec.shared_facts_json or "{}")
        except Exception:
            facts = {}

        facts["last_invoked_agent"] = agent_id
        facts["last_active_at"] = datetime.utcnow().isoformat() + "Z"
        if drama_id:
            facts["active_drama_id"] = drama_id
        if episode_id:
            facts["active_episode_id"] = episode_id
        if new_facts:
            facts.update(new_facts)

        try:
            turns: List[Dict[str, Any]] = json.loads(rec.recent_turns_json or "[]")
        except Exception:
            turns = []

        turns.append(
            {
                "agent_id": agent_id,
                "q": (query or "")[:160],
                "a": (answer or "")[:240],
                "ts": datetime.utcnow().strftime("%H:%M:%S"),
            }
        )
        rec.turn_count = (rec.turn_count or 0) + 1

        # Auto-compress if turns exceed SLIDING_WINDOW_MAX_TURNS
        if len(turns) >= SLIDING_WINDOW_MAX_TURNS:
            evicted = turns[:-KEEP_RECENT_TURNS]
            turns = turns[-KEEP_RECENT_TURNS:]
            evicted_digest = "；".join(
                [f"[{e.get('agent_id')}]问'{e.get('q', '')[:30]}'答'{e.get('a', '')[:45]}'" for e in evicted]
            )
            prev_summary = rec.rolling_summary or ""
            rec.rolling_summary = (
                f"{prev_summary[:220]} | [第{(rec.compression_count or 0) + 1}次自动摘要]：{evicted_digest}"
            ).strip(" |")
            rec.compression_count = (rec.compression_count or 0) + 1

        rec.shared_facts_json = json.dumps(facts, ensure_ascii=False)
        rec.recent_turns_json = json.dumps(turns, ensure_ascii=False)
        db.commit()
        return cls.to_snapshot(rec)

    @classmethod
    def force_compress_session(cls, db: Session, session_id: str) -> Dict[str, Any]:
        """Explicitly triggered by Admin Integrator to compress memory window immediately."""
        rec = cls.get_or_create_session(db, session_id)
        try:
            turns: List[Dict[str, Any]] = json.loads(rec.recent_turns_json or "[]")
        except Exception:
            turns = []

        if turns:
            digest = "；".join(
                [f"[{t.get('agent_id')}] {t.get('q', '')[:30]}->{t.get('a', '')[:45]}" for t in turns]
            )
            rec.rolling_summary = f"【整合器深度压缩摘要 #{ (rec.compression_count or 0) + 1 }】{digest}"
            rec.recent_turns_json = json.dumps(turns[-1:], ensure_ascii=False)
        else:
            rec.rolling_summary = (
                f"【整合器深度压缩摘要 #{ (rec.compression_count or 0) + 1 }】"
                f"已归档当前跨智能体共享状态与历史上下文，释放冗余 Token 空间。"
            )
        rec.compression_count = (rec.compression_count or 0) + 1
        db.commit()
        return cls.to_snapshot(rec)

    @staticmethod
    def to_snapshot(rec: AgentBlackboardSession) -> Dict[str, Any]:
        try:
            facts = json.loads(rec.shared_facts_json or "{}")
        except Exception:
            facts = {}
        try:
            turns = json.loads(rec.recent_turns_json or "[]")
        except Exception:
            turns = []
        return {
            "session_id": rec.session_id,
            "user_id": rec.user_id,
            "drama_id": rec.drama_id,
            "episode_id": rec.episode_id,
            "shared_facts": facts,
            "rolling_summary": rec.rolling_summary,
            "recent_turns": turns,
            "turn_count": rec.turn_count,
            "compression_count": rec.compression_count,
            "updated_at": rec.updated_at.isoformat() if rec.updated_at else "",
        }
