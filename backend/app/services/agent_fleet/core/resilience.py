"""
工程韧性与动态可调超时断路器 (Resilience & Circuit Breaker)
- 单步工具超时: 默认 30.0s (支持前端滑块动态配置)
- 单轮思考超时: 默认 60.0s (支持前端滑块动态配置)
- 降级与兜底策略: 超时触发时自动平滑切入 Fallback 备选模型或友好兜底，消除线程卡死
"""

import json
import time
import logging
import asyncio
from typing import Callable, Any, Dict, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.system_config import SystemConfig

logger = logging.getLogger("agent_fleet.resilience")

# 全局内存缓存的动态运行时治理配置
_ACTIVE_RUNTIME_CONFIG: Dict[str, Any] = {
    "tool_timeout_seconds": 30.0,
    "thought_timeout_seconds": 60.0,
    "sliding_window_rounds": 10,
    "max_retries": 2,
    "enable_circuit_breaker": True,
}


def load_runtime_governance_config() -> Dict[str, Any]:
    """从数据库 system_configs 动态读取运行时治理配置，实现免重启毫秒级热生效"""
    global _ACTIVE_RUNTIME_CONFIG
    try:
        db: Session = SessionLocal()
        try:
            cfg = db.query(SystemConfig).filter(SystemConfig.config_key == "agent_runtime_governance").first()
            if cfg and cfg.config_value:
                parsed = json.loads(cfg.config_value)
                if isinstance(parsed, dict):
                    _ACTIVE_RUNTIME_CONFIG.update(parsed)
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Could not load agent_runtime_governance from DB: {e}")
    return _ACTIVE_RUNTIME_CONFIG


def update_runtime_governance_config(new_config: Dict[str, Any]) -> Dict[str, Any]:
    """前端滑块更新运行时治理配置并持久化落库"""
    global _ACTIVE_RUNTIME_CONFIG
    _ACTIVE_RUNTIME_CONFIG.update(new_config)

    try:
        db: Session = SessionLocal()
        try:
            cfg = db.query(SystemConfig).filter(SystemConfig.config_key == "agent_runtime_governance").first()
            if not cfg:
                cfg = SystemConfig(
                    config_key="agent_runtime_governance",
                    config_value=json.dumps(_ACTIVE_RUNTIME_CONFIG, ensure_ascii=False),
                    description="智能体生态运行时治理配置(超时断路/滑动窗口)",
                )
                db.add(cfg)
            else:
                cfg.config_value = json.dumps(_ACTIVE_RUNTIME_CONFIG, ensure_ascii=False)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to save agent_runtime_governance to DB: {e}")

    return _ACTIVE_RUNTIME_CONFIG


def get_tool_timeout() -> float:
    """获取当前动态生效的单工具超时时长 (秒)"""
    return float(_ACTIVE_RUNTIME_CONFIG.get("tool_timeout_seconds", 30.0))


def get_thought_timeout() -> float:
    """获取当前动态生效的单轮思考超时时长 (秒)"""
    return float(_ACTIVE_RUNTIME_CONFIG.get("thought_timeout_seconds", 60.0))


async def execute_with_resilience(
    func: Callable[..., Any],
    *args,
    timeout_sec: Optional[float] = None,
    fallback_result: Optional[Any] = None,
    task_name: str = "agent_task",
    **kwargs,
) -> Any:
    """
    异步任务超时断路与降级执行器
    执行指定协程，超时自动触发断路熔断并返回优雅兜底结构，绝不卡死主线程
    """
    actual_timeout = timeout_sec or get_thought_timeout()
    t0 = time.time()
    try:
        if asyncio.iscoroutinefunction(func):
            return await asyncio.wait_for(func(*args, **kwargs), timeout=actual_timeout)
        else:
            # 同步函数包装进线程池异步执行
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, lambda: func(*args, **kwargs)),
                timeout=actual_timeout,
            )
    except asyncio.TimeoutError:
        elapsed = time.time() - t0
        logger.error(f"[CircuitBreaker] Task '{task_name}' timed out after {elapsed:.2f}s (limit: {actual_timeout}s)")
        if fallback_result is not None:
            return fallback_result
        return {
            "status": "TIMEOUT_FALLBACK",
            "message": f"任务执行已达到保护上限({actual_timeout}s)，系统已启动工程熔断保护，请稍后重试或简化输入。",
            "elapsed_seconds": elapsed,
        }
    except Exception as e:
        logger.error(f"[CircuitBreaker] Task '{task_name}' failed with error: {e}")
        if fallback_result is not None:
            return fallback_result
        raise e


# 初始化加载
load_runtime_governance_config()
