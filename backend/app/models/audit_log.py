# -*- coding: utf-8 -*-
"""
==============================================================================
【模型文件】：backend/app/models/audit_log.py
【业务定位】：全链路操作审计追踪流水模型（SystemAuditLog）
【对应表名】：system_audit_logs
【核心功能】：
  记录全平台所有角色（用户、创作者、管理员、后台智能体系统）的关键行为轨迹。
  涵盖登录登出、剧集播放、RAG 知识检索、多智能体圆桌推演、金币变动、封禁解封等。
  为系统安全防御、故障溯源与运营 BI 提供铁证级可审计日志。
【对应前端】：
  - 审计日志大屏：frontend/src/views/AdminView.vue (审计流 Tab)
==============================================================================
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, func
from app.core.database import Base

class SystemAuditLog(Base):
    """
    【系统全链路操作审计追踪实体】
    记录任何有价值的系统事件，支持高并发轻量写入与多维复合搜索。
    """
    __tablename__ = "system_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), default=datetime.utcnow, index=True)
    
    # 操作人基本档案（支持未登录访客 IP 记录）
    user_id = Column(Integer, nullable=True, index=True)
    username = Column(String(64), nullable=True, index=True)
    user_role = Column(String(32), default="visitor", index=True)  # admin, creator, user, system, visitor
    ip_address = Column(String(64), nullable=True, default="127.0.0.1")
    
    # 业务作用域
    module = Column(String(64), nullable=False, index=True)  # auth, player, rag, agent_roundtable, admin_bi, pet, user_center, coin
    action = Column(String(64), nullable=False, index=True)  # login, stream_play, rag_query, agent_dispatch, pet_mode_switch 等
    target_id = Column(String(128), nullable=True)           # 例如被操作的 video_id, session_id, user_id
    
    # 执行状态与技术性能指标
    status = Column(String(32), default="SUCCESS", index=True)  # SUCCESS, FAILED, WARNING, BLOCKED
    exec_time_ms = Column(Integer, default=0)                  # 该次操作耗时毫秒数
    summary = Column(Text, nullable=False)                     # 人类可读简明摘要（如：“管理员张三审核通过了短剧《战神回归》”）
    detail_json = Column(JSON, nullable=True)                  # 结构化扩展上下文字典（入参、出参或错误栈）

    def to_dict(self):
        """将审计日志转化为前台规范的 JSON 字典"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user_id": self.user_id,
            "username": self.username,
            "user_role": self.user_role,
            "ip_address": self.ip_address,
            "module": self.module,
            "action": self.action,
            "target_id": self.target_id,
            "status": self.status,
            "exec_time_ms": self.exec_time_ms,
            "summary": self.summary,
            "detail_json": self.detail_json,
        }
