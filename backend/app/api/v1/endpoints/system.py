"""
==============================================================================
【模块名称】：system.py (系统运维监控与实时健康遥测接口)
【业务职能】：
  提供整个后端系统与大模型集群的脉搏遥测，实时输出当前服务可用性、底座响应延迟、
  断路器状态（正常/熔断）以及待处理工单数量，驱动中台顶栏呼吸灯。
【对应前端】：
  - 核心页面：frontend/src/components/AdminHeader.vue (中台顶栏右上角健康指示灯)
  - 管理大屏：frontend/src/views/AdminView.vue
  - 前端通信：frontend/src/api/admin.ts (getSystemTelemetry)
==============================================================================
"""
import time
import httpx
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.llm_gateway import llm_gateway

router = APIRouter()

@router.get("/telemetry")
async def get_system_telemetry(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    ==============================================================================
    【这个接口是做什么的】：
    系统实时健康与大模型运行探针，探测模型延迟、断路器熔断状态与待审工单数。
    对应 HTTP 端点：GET /telemetry
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：顶栏健康探针定时轮询
    - 调用链路：前端通过 admin.ts -> getSystemTelemetry() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    health = llm_gateway.get_health_status()
    cfg = llm_gateway.get_active_config()
    raw_cfg = llm_gateway.get_raw_config()

    # Measure latency to active provider endpoint (probe with short timeout)
    latency_ms = 1.0
    start_t = time.time()
    try:
        base_url = cfg.get("base_url", "http://localhost:11434")
        provider = cfg.get("provider", "ollama")
        api_key = raw_cfg.get("api_key", "")
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        async with httpx.AsyncClient(timeout=2.0) as client:
            if provider == "ollama":
                resp = await client.get(f"{base_url.rstrip('/')}/api/tags")
                if resp.status_code == 200:
                    latency_ms = round((time.time() - start_t) * 1000, 1)
            else:
                resp = await client.get(f"{base_url.rstrip('/')}/models", headers=headers)
                latency_ms = round((time.time() - start_t) * 1000, 1)
    except Exception:
        latency_ms = round((time.time() - start_t) * 1000, 1)

    # Query pending review tasks count
    pending_count = 0
    try:
        from app.models.review import ContentReview
        pending_count = db.query(ContentReview).filter(ContentReview.review_status == "PENDING").count()
    except Exception:
        pending_count = 0

    return {
        "status": health["status"],
        "circuit_state": health["circuit_state"],
        "active_provider": health["active_provider"],
        "active_model": health["active_model"],
        "latency_ms": latency_ms,
        "uptime_seconds": health["uptime_seconds"],
        "pending_reviews_count": pending_count,
        "consecutive_failures": health.get("consecutive_failures", 0),
        "recovery_countdown_seconds": health.get("recovery_countdown_seconds", 0.0)
    }
