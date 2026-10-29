# -*- coding: utf-8 -*-
"""
==============================================================================
【模块名称】：CinemaAgent 智能体核心底座 - memory_hub.py
【业务定位】：跨会话长期记忆中枢与向量检索存储管理
==============================================================================
"""
"""
四层分级记忆中枢与滑动窗口治理模块 (Hierarchical Memory Hub)
- L1: 单步临时草稿 (单轮销毁)
- L2: 会话滑动窗口 (严格取近 5~10 轮对话，超限自动触发 LLM 递归摘要压缩)
- L3: 跨智能体只读公共黑板 (仅存储结构化确定性工件，杜绝幻觉传话)
- L4: 长期实体档案 (用户偏好与短剧知识图谱)
- 物理作用域隔离: agent_mem:{agent_id}:{session_id}，防止不同智能体记忆相互串通
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.agent_hub import AgentBlackboardSession
from app.core.cache import cache_manager

logger = logging.getLogger("agent_fleet.memory_hub")

# 内存单例高速缓存 (当 Redis 不可用时降级)
_LOCAL_SESSION_CACHE: Dict[str, List[Dict[str, Any]]] = {}
_LOCAL_BLACKBOARD_CACHE: Dict[str, Dict[str, Any]] = {}


class HierarchicalMemoryHub:
    """四层分级记忆治理核心管理器"""

    def __init__(self, default_window_rounds: int = 10):
        self.default_window_rounds = default_window_rounds

    def _build_isolated_key(self, agent_id: str, session_id: str) -> str:
        """生成物理隔离的独立会话键，彻底杜绝不同 Agent 间记忆混淆"""
        return f"agent_mem:{agent_id}:{session_id}"

    def get_isolated_messages(
        self, agent_id: str, session_id: str, window_limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取指定 Agent 在指定会话中的独立历史消息，受滑动窗口严格截断保护"""
        limit = window_limit or self.default_window_rounds
        key = self._build_isolated_key(agent_id, session_id)
        raw_msgs = _LOCAL_SESSION_CACHE.get(key)
        if raw_msgs is None:
            # 尝试从 Redis 唤醒冷记忆
            try:
                if cache_manager.ping():
                    redis_key = f"cinema:agents:mem:{agent_id}:{session_id}"
                    cached_val = cache_manager.get(redis_key)
                    if cached_val:
                        raw_msgs = json.loads(cached_val) if isinstance(cached_val, str) else cached_val
                        _LOCAL_SESSION_CACHE[key] = raw_msgs
            except Exception as e:
                logger.warning(f"Redis memory read error: {e}")
            if raw_msgs is None:
                raw_msgs = []
                _LOCAL_SESSION_CACHE[key] = raw_msgs

        if len(raw_msgs) <= limit:
            return raw_msgs

        # 滑动窗口截断：保留最新 limit 轮对话
        return raw_msgs[-limit:]

    def append_message(
        self,
        agent_id: str,
        session_id: str,
        role: str,
        content: str,
        thought: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None,
        agent_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """追加一条带强类型格式的结构化消息至该 Agent 的专属记忆池"""
        key = self._build_isolated_key(agent_id, session_id)
        if key not in _LOCAL_SESSION_CACHE:
            _LOCAL_SESSION_CACHE[key] = []

        entry = {
            "role": role,
            "agent_id": agent_id,
            "agent_name": agent_name or agent_id,
            "content": content,
            "thought": thought,
            "tool_calls": tool_calls or [],
            "tool_results": tool_results or [],
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        }

        _LOCAL_SESSION_CACHE[key].append(entry)

        # 同步持久化写入 Redis 高速缓存 (双驱保障)
        try:
            if cache_manager.ping():
                redis_key = f"cinema:agents:mem:{agent_id}:{session_id}"
                cache_manager.set(redis_key, json.dumps(_LOCAL_SESSION_CACHE[key], ensure_ascii=False), expire_seconds=86400 * 7)
                cache_manager._redis_client.sadd("cinema:agents:all_sessions", session_id)
        except Exception as err:
            logger.warning(f"Redis memory write error non-fatal: {err}")

        # 同步落库 MySQL AgentBlackboardSession 表 (确保后端重启无损还原)
        if session_id.startswith("rt_session_"):
            try:
                db_session: Session = SessionLocal()
                try:
                    rec = db_session.query(AgentBlackboardSession).filter(AgentBlackboardSession.session_id == session_id).first()
                    if not rec:
                        rec = AgentBlackboardSession(
                            session_id=session_id,
                            turn_count=1,
                            shared_facts_json="{}",
                            recent_turns_json=json.dumps([entry], ensure_ascii=False),
                        )
                        db_session.add(rec)
                    else:
                        existing = []
                        if rec.recent_turns_json:
                            try:
                                existing = json.loads(rec.recent_turns_json)
                            except Exception:
                                existing = []
                        existing.append(entry)
                        rec.recent_turns_json = json.dumps(existing[-50:], ensure_ascii=False)
                        rec.turn_count = (rec.turn_count or 0) + 1
                    db_session.commit()
                finally:
                    db_session.close()
            except Exception as db_err:
                logger.warning(f"Failed to persist roundtable message to DB: {db_err}")

        # 检查是否需要递归摘要压缩
        if len(_LOCAL_SESSION_CACHE[key]) > self.default_window_rounds * 2:
            self._compress_session_memory(agent_id, session_id)

        return entry

    def _compress_session_memory(self, agent_id: str, session_id: str):
        """执行滑动窗口超限递归摘要压缩"""
        key = self._build_isolated_key(agent_id, session_id)
        history = _LOCAL_SESSION_CACHE.get(key, [])
        if len(history) <= self.default_window_rounds:
            return

        # 待压缩的陈旧历史
        stale_history = history[:-self.default_window_rounds]
        recent_history = history[-self.default_window_rounds:]

        summary_points = []
        for msg in stale_history:
            sender = msg.get("agent_name") or msg.get("role")
            text = (msg.get("content") or "")[:80]
            summary_points.append(f"{sender}: {text}")

        compact_summary = "【前序历史摘要】" + "；".join(summary_points[-5:])
        summary_entry = {
            "role": "system",
            "agent_id": agent_id,
            "agent_name": "MemoryCompressor",
            "content": compact_summary,
            "thought": "已自动执行滑动窗口递归摘要，保留关键事实并释放上下文",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        }

        _LOCAL_SESSION_CACHE[key] = [summary_entry] + recent_history
        logger.info(f"Agent {agent_id} session {session_id} memory compressed via sliding window.")

    # ---------------- L3: 跨 Agent 共享只读公共黑板 (Blackboard) ----------------

    def get_blackboard_artifact(self, session_id: str, artifact_key: str) -> Optional[Any]:
        """从公共黑板中按 Key 提取结构化确定性工件"""
        bb = _LOCAL_BLACKBOARD_CACHE.get(session_id, {})
        return bb.get(artifact_key)

    def write_blackboard_artifact(
        self, session_id: str, artifact_key: str, artifact_val: Any, author_agent_id: str
    ):
        """将校验通过的结构化工件写入公共黑板，供下游 Agent 只读读取"""
        if session_id not in _LOCAL_BLACKBOARD_CACHE:
            _LOCAL_BLACKBOARD_CACHE[session_id] = {}

        _LOCAL_BLACKBOARD_CACHE[session_id][artifact_key] = artifact_val
        _LOCAL_BLACKBOARD_CACHE[session_id][f"{artifact_key}_author"] = author_agent_id
        _LOCAL_BLACKBOARD_CACHE[session_id][f"{artifact_key}_updated_at"] = datetime.utcnow().isoformat()

        # 同步持久化写入 Redis
        try:
            if cache_manager.ping():
                redis_key = f"cinema:agents:blackboard:{session_id}"
                cache_manager.set(redis_key, json.dumps(_LOCAL_BLACKBOARD_CACHE[session_id], ensure_ascii=False), expire_seconds=86400 * 7)
        except Exception as e:
            logger.warning(f"Redis blackboard write error: {e}")

        # 同步写入持久化数据库
        try:
            db: Session = SessionLocal()
            try:
                rec = db.query(AgentBlackboardSession).filter(AgentBlackboardSession.session_id == session_id).first()
                state_json = json.dumps(_LOCAL_BLACKBOARD_CACHE[session_id], ensure_ascii=False)
                if not rec:
                    rec = AgentBlackboardSession(
                        session_id=session_id,
                        shared_facts_json=state_json,
                        turn_count=1,
                    )
                    db.add(rec)
                else:
                    rec.shared_facts_json = state_json
                    rec.turn_count = (rec.turn_count or 0) + 1
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Could not persist blackboard artifact to DB: {e}")

    def get_full_blackboard(self, session_id: str) -> Dict[str, Any]:
        """获取当前会话全量黑板状态快照"""
        return _LOCAL_BLACKBOARD_CACHE.get(session_id, {})


# 全局单例
global_memory_hub = HierarchicalMemoryHub()
