# -*- coding: utf-8 -*-
"""
==============================================================================
【业务服务】：backend/app/services/audit_service.py
【业务定位】：全链路安全审计日志流录入与多维检索聚合服务（AuditService）
【前端链路对接】：
  1. 页面来源：frontend/src/views/AdminView.vue（管理中台 -> 审计日志 Tab 与 BI 监控看板）
  2. 触发与路由链路：
     - 日志表格拉取：AdminView.vue 挂载时触发 GET /api/v1/admin/audit/logs（进入 admin.py）；
       -> 路由调用 audit_service.get_logs()，返回分页日志列表与总数；
     - 审计统计拉取：AdminView.vue 触发 GET /api/v1/admin/audit/stats；
       -> 路由调用 audit_service.get_stats()，返回模块分布饼图、角色分布、平均响应耗时与24小时流量；
     - 业务落库打点：用户登录、短剧播放、RAG 检索、智能体调度、敏感词拦截等关键业务发生时，
       后端各模块异步调用 audit_service.log_action(...) 将审计快照写入 system_audit_logs 表。
【核心功能】：
  1. 轻量异步落库（log_action）：记录操作人、用户角色、IP 地址、耗时、执行状态与详细 Payload；
  2. 复合条件分页检索（get_logs）：支持按模块、动作、状态、角色与模糊关键字快速查询；
  3. 模块热度与耗时统计（get_stats）：统计系统高频调用瓶颈、成功率与慢请求分布；
  4. 首次启动基线日志补齐（seed_baseline_logs_if_empty）：当新环境数据库为空时自动灌入标准基线数据。
==============================================================================
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func

from app.models.audit_log import SystemAuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """
    【系统审计日志服务类】
    统一管理全平台的安全审计日志流，支持日志落库、复合过滤检索、BI 聚合分析与基线数据填充。
    """

    @staticmethod
    def log_action(
        db: Session,
        module: str,
        action: str,
        summary: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        user_role: str = "visitor",
        ip_address: str = "127.0.0.1",
        target_id: Optional[str] = None,
        status: str = "SUCCESS",
        exec_time_ms: int = 0,
        detail_json: Optional[Dict[str, Any]] = None,
    ) -> Optional[SystemAuditLog]:
        """
        向数据库 `system_audit_logs` 表记录单条操作审计日志。
        
        【参数大白话详解】：
        - db (Session): 数据库会话连接。
        - module (str): 业务模块标识（例如："auth" 认证、"player" 播放器、"rag" 剧情检索、"agent" 智能体、"moderation" 内容风控）。
        - action (str): 执行的具体动作名（例如："login" 登录、"hybrid_search" 混合检索、"dispatch" 智能体调度）。
        - summary (str): 人类可读的大白话摘要说明（例如："用户张三成功登录系统，签发 JWT 令牌"）。
        - user_id (Optional[int]): 当前操作人的用户主键 ID，未登录时为 None。
        - username (Optional[str]): 操作人账号名（如 "admin" 或 "viewer_alice"）。
        - user_role (str, 默认 "visitor"): 操作人角色（"admin" 管理员、"creator" 创作者、"user" 普通观众、"visitor" 访客）。
        - ip_address (str, 默认 "127.0.0.1"): 客户端发起请求的 IP 地址。
        - target_id (Optional[str]): 被操作的目标实体主键 ID（如短剧 ID、分集 ID 或工单单号）。
        - status (str, 默认 "SUCCESS"): 最终执行状态（"SUCCESS" 成功、"FAILED" 失败、"WARNING" 告警拦截）。
        - exec_time_ms (int, 默认 0): 该操作在后端执行的实际耗时毫秒数。
        - detail_json (Optional[Dict[str, Any]]): 扩展上下文字典（如请求参数、模型用量等），在数据库中存为 JSON 格式。
        
        【返回值说明】：
        - Optional[SystemAuditLog]: 持久化后的审计日志实体对象；若写入失败则回滚并返回 None，杜绝影响主业务。
        """
        try:
            log_item = SystemAuditLog(
                user_id=user_id,
                username=username,
                user_role=user_role,
                ip_address=ip_address,
                module=module,
                action=action,
                target_id=str(target_id) if target_id is not None else None,
                status=status,
                exec_time_ms=exec_time_ms,
                summary=summary,
                detail_json=detail_json or {},
            )
            db.add(log_item)
            db.commit()
            db.refresh(log_item)
            return log_item
        except Exception as e:
            db.rollback()
            logger.error(f"写入系统审计日志失败: {e}")
            return None

    @staticmethod
    def get_logs(
        db: Session,
        page: int = 1,
        page_size: int = 15,
        module: Optional[str] = None,
        action: Optional[str] = None,
        status: Optional[str] = None,
        user_role: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        支持多维复合条件筛选的审计日志分页查询。
        
        【参数说明】：
        - db (Session): 数据库会话。
        - page (int, 默认 1): 当前查询第几页。
        - page_size (int, 默认 15): 每页展示的记录条数。
        - module (Optional[str]): 模块过滤条件（如 "rag"）。
        - action (Optional[str]): 动作过滤条件（如 "hybrid_search"）。
        - status (Optional[str]): 状态过滤条件（"SUCCESS" / "FAILED" / "WARNING"）。
        - user_role (Optional[str]): 用户角色过滤条件（"admin" / "creator" / "user"）。
        - keyword (Optional[str]): 模糊搜索词，同时匹配 summary、username、target_id 和 ip_address。
        
        【返回值字典结构详解】：
        {
            "total": int,      # 符合条件的日志总记录数（用于前端分页器展示总页数）
            "page": int,       # 当前页码
            "page_size": int,  # 每页条数
            "items": list      # 序列化后的日志列表，每个元素包含 id, module, action, summary, status 等
        }
        """
        query = db.query(SystemAuditLog)

        if module and module.strip():
            query = query.filter(SystemAuditLog.module == module.strip())

        if action and action.strip():
            query = query.filter(SystemAuditLog.action == action.strip())

        if status and status.strip():
            query = query.filter(SystemAuditLog.status == status.strip())

        if user_role and user_role.strip():
            query = query.filter(SystemAuditLog.user_role == user_role.strip())

        if keyword and keyword.strip():
            kw = f"%{keyword.strip()}%"
            query = query.filter(
                or_(
                    SystemAuditLog.summary.ilike(kw),
                    SystemAuditLog.username.ilike(kw),
                    SystemAuditLog.target_id.ilike(kw),
                    SystemAuditLog.ip_address.ilike(kw),
                )
            )

        total = query.count()
        logs = (
            query.order_by(desc(SystemAuditLog.id))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [item.to_dict() for item in logs],
        }

    @staticmethod
    def get_stats(db: Session) -> Dict[str, Any]:
        """
        聚合全站安全审计核心指标，为管理中台 BI 大屏与驾驶舱提供图表数据。
        
        【返回值字典结构详解】：
        {
            "total_logs": int,            # 审计日志累计总量
            "success_count": int,         # 成功状态操作总次数
            "failed_count": int,          # 失败状态操作总次数
            "warning_count": int,         # 告警/拦截状态操作总次数
            "success_rate": float,        # 全站接口调用综合成功率（百分比，如 99.4）
            "recent_24h_count": int,      # 过去 24 小时内发生的请求总数（反映全站活跃热度）
            "avg_latency_ms": float,      # 全站业务平均执行耗时（毫秒数，反映响应性能）
            "module_distribution": list,  # 各业务模块调用频次分布列表（ECharts 饼图渲染）
            "role_distribution": list     # 各类操作角色频次分布列表
        }
        """
        total_logs = db.query(SystemAuditLog).count()
        success_count = db.query(SystemAuditLog).filter(SystemAuditLog.status == "SUCCESS").count()
        failed_count = db.query(SystemAuditLog).filter(SystemAuditLog.status == "FAILED").count()
        warning_count = db.query(SystemAuditLog).filter(SystemAuditLog.status == "WARNING").count()

        # 统计各业务模块调用占比分布
        module_groups = (
            db.query(SystemAuditLog.module, func.count(SystemAuditLog.id))
            .group_by(SystemAuditLog.module)
            .all()
        )
        module_dist = [{"module": m[0], "count": m[1]} for m in module_groups]

        # 统计各操作角色分布
        role_groups = (
            db.query(SystemAuditLog.user_role, func.count(SystemAuditLog.id))
            .group_by(SystemAuditLog.user_role)
            .all()
        )
        role_dist = [{"role": r[0], "count": r[1]} for r in role_groups]

        # 统计过去 24 小时新增日志总数
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        recent_24h_count = (
            db.query(SystemAuditLog)
            .filter(SystemAuditLog.created_at >= twenty_four_hours_ago)
            .count()
        )

        # 统计平均请求耗时
        avg_latency = (
            db.query(func.avg(SystemAuditLog.exec_time_ms))
            .filter(SystemAuditLog.exec_time_ms > 0)
            .scalar()
            or 38
        )

        return {
            "total_logs": total_logs,
            "success_count": success_count,
            "failed_count": failed_count,
            "warning_count": warning_count,
            "success_rate": round((success_count / total_logs * 100), 2) if total_logs > 0 else 100.0,
            "recent_24h_count": recent_24h_count,
            "avg_latency_ms": round(float(avg_latency), 1),
            "module_distribution": module_dist,
            "role_distribution": role_dist,
        }

    @staticmethod
    def seed_baseline_logs_if_empty(db: Session):
        """
        当审计日志表为空或记录较少时，自动注入覆盖全模块的标准基线审计日志，
        确保初次部署或开发测试环境下管理中台各 BI 图表不会出现白屏或空数据。
        """
        count = db.query(SystemAuditLog).count()
        if count >= 8:
            return

        baseline_data = [
            {
                "user_id": 1,
                "username": "admin",
                "user_role": "admin",
                "ip_address": "127.0.0.1",
                "module": "auth",
                "action": "login",
                "target_id": "sys_auth_token",
                "status": "SUCCESS",
                "exec_time_ms": 42,
                "summary": "管理员 admin 成功通过账号密码认证登录系统，签发 JWT 令牌",
                "detail_json": {"auth_type": "password", "scopes": ["admin", "creator", "user"], "client": "Chrome/124.0"},
            },
            {
                "user_id": 1,
                "username": "admin",
                "user_role": "admin",
                "ip_address": "127.0.0.1",
                "module": "admin_bi",
                "action": "view_cockpit",
                "target_id": "bi_dashboard",
                "status": "SUCCESS",
                "exec_time_ms": 68,
                "summary": "管理员调取 BI 智能驾驶舱全链路时序数据与 Agent 集群负载概览",
                "detail_json": {"chart": "holt_winters_forecast", "time_range": "14d_history_7d_forecast"},
            },
            {
                "user_id": 2,
                "username": "viewer_alice",
                "user_role": "user",
                "ip_address": "192.168.1.105",
                "module": "player",
                "action": "stream_play",
                "target_id": "video_1_ep_1",
                "status": "SUCCESS",
                "exec_time_ms": 19,
                "summary": "用户开始播放短剧《战神归来》第 1 集，自动挂载预加载流缓冲",
                "detail_json": {"preload": "metadata", "autoplay_delay_sec": 3, "quality": "1080P"},
            },
            {
                "user_id": 2,
                "username": "viewer_alice",
                "user_role": "user",
                "ip_address": "192.168.1.105",
                "module": "rag",
                "action": "hybrid_search",
                "target_id": "drama_rag_corpus_1",
                "status": "SUCCESS",
                "exec_time_ms": 115,
                "summary": "触发多模态 RAG 剧情伴侣问答：三路混合检索（向量 + BM25 + Neo4j 图谱）",
                "detail_json": {
                    "query": "叶天帝在青云宗最后的结局是什么？",
                    "retrieval_chunks": 5,
                    "reranker_score": 0.892,
                    "anti_spoiler_gate": "PASSED",
                },
            },
            {
                "user_id": 1,
                "username": "admin",
                "user_role": "admin",
                "ip_address": "127.0.0.1",
                "module": "agent_roundtable",
                "action": "collaborative_dispatch",
                "target_id": "session_roundtable_prod",
                "status": "SUCCESS",
                "exec_time_ms": 284,
                "summary": "九大智能体圆桌会话协同：编剧与导演专家完成分镜交付物持久化",
                "detail_json": {
                    "session_id": "roundtable_prod_master",
                    "artifacts_updated": ["STORYBOARD_SPEC", "MARKETING_KIT"],
                    "blackboard_keys": ["storyboard", "marketing_kit", "review_verdict"],
                },
            },
            {
                "user_id": 2,
                "username": "viewer_alice",
                "user_role": "user",
                "ip_address": "192.168.1.105",
                "module": "pet",
                "action": "switch_mode",
                "target_id": "companion_pet_xiaoqian",
                "status": "SUCCESS",
                "exec_time_ms": 12,
                "summary": "用户将桌面伴侣小茜切换为超清静态贴纸模式，并锁定安全视口坐标",
                "detail_json": {"mode": "static_poster", "rate": 1.0, "pos_x": 1120, "pos_y": 640},
            },
            {
                "user_id": 3,
                "username": "creator_bob",
                "user_role": "creator",
                "ip_address": "192.168.1.118",
                "module": "creator_studio",
                "action": "upload_script",
                "target_id": "drama_script_302",
                "status": "SUCCESS",
                "exec_time_ms": 94,
                "summary": "创作者提交分集剧本切片，触发后台 OCR 与多模态文本索引自动构建",
                "detail_json": {"chunks_created": 32, "embedding_model": "text-embedding-v3"},
            },
            {
                "user_id": None,
                "username": "anonymous",
                "user_role": "visitor",
                "ip_address": "203.0.113.45",
                "module": "auth",
                "action": "login_attempt",
                "target_id": "sys_auth_token",
                "status": "WARNING",
                "exec_time_ms": 55,
                "summary": "检测到未知客户端凭证错误，已触发频次安全监控与防爆破拦截",
                "detail_json": {"reason": "invalid_credentials", "attempt_count": 1},
            },
        ]

        for item in baseline_data:
            log_obj = SystemAuditLog(
                user_id=item["user_id"],
                username=item["username"],
                user_role=item["user_role"],
                ip_address=item["ip_address"],
                module=item["module"],
                action=item["action"],
                target_id=item["target_id"],
                status=item["status"],
                exec_time_ms=item["exec_time_ms"],
                summary=item["summary"],
                detail_json=item["detail_json"],
            )
            db.add(log_obj)

        try:
            db.commit()
            logger.info("成功初始化写入系统基线审计日志数据")
        except Exception as e:
            db.rollback()
            logger.error(f"写入基线审计日志异常: {e}")


# 全局单例审计服务实例
audit_service = AuditService()
