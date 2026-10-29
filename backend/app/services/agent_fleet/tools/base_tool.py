# -*- coding: utf-8 -*-
"""
==============================================================================
【模块名称】：CinemaAgent 智能体专属工具 - 智能体工具抽象基类 (base_tool.py)
【业务定位】：定义 Agent 可调用的 Tool 规范、入参 schema 与执行抽象方法
==============================================================================
"""
"""
解耦独立工具矩阵抽象基类 (BaseDecoupledTool)
支持强类型 Pydantic 输入输出 Schema、动态超时保护与错误断路器
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Type, Optional
from pydantic import BaseModel
from app.services.agent_fleet.core.resilience import get_tool_timeout

logger = logging.getLogger("agent_fleet.tools")


class BaseDecoupledTool(ABC):
    """解耦工具抽象基类"""

    name: str
    description: str
    args_schema: Type[BaseModel]
    category: str = "general"

    def get_timeout_seconds(self) -> float:
        """从全局动态韧性中枢获取当前工具超时时间"""
        return get_tool_timeout()

    def run(self, **kwargs) -> Dict[str, Any]:
        """带入参验证、耗时统计与异常拦截的执行入口"""
        t0 = time.time()
        try:
            # Pydantic 校验入参
            validated = self.args_schema(**kwargs)
            result = self.execute(**validated.model_dump())
            elapsed = time.time() - t0
            return {
                "success": True,
                "tool_name": self.name,
                "data": result,
                "elapsed_seconds": round(elapsed, 3),
            }
        except Exception as e:
            elapsed = time.time() - t0
            logger.error(f"Tool '{self.name}' execution failed: {e}")
            return {
                "success": False,
                "tool_name": self.name,
                "error": str(e),
                "elapsed_seconds": round(elapsed, 3),
            }

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """具体工具业务逻辑，由各独立子类实现"""
        pass
