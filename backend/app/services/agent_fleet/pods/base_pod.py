"""
子智能体统一接口规范与基类 (BaseAgentPod)
规范各异构智能体的思考、工具调用、打字机流式输出与滑动窗口记忆治理
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.services.agent_fleet.core.memory_hub import global_memory_hub
from app.services.agent_fleet.core.resilience import execute_with_resilience
from app.services.agent_fleet.tools.base_tool import BaseDecoupledTool

logger = logging.getLogger("agent_fleet.pods")


class BaseAgentPod(ABC):
    """子智能体抽象基类"""

    agent_id: str
    agent_number: int
    name: str
    role_title: str
    system_prompt: str
    allowed_tools: List[BaseDecoupledTool] = []

    def get_isolated_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """从分层记忆中枢安全获取物理隔离的当前 Agent 专属滑动窗口历史"""
        return global_memory_hub.get_isolated_messages(self.agent_id, session_id, limit)

    def record_chat(
        self,
        session_id: str,
        role: str,
        content: str,
        thought: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None,
    ):
        """记录一条消息至本 Agent 的独立会话记忆池"""
        global_memory_hub.append_message(
            agent_id=self.agent_id,
            session_id=session_id,
            role=role,
            content=content,
            thought=thought,
            tool_calls=tool_calls,
            tool_results=tool_results,
            agent_name=self.name,
        )

    @abstractmethod
    async def run_step(
        self,
        session_id: str,
        user_message: str,
        attachment_path: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        db: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """异步执行单轮思考与真实工具调用及大模型推理"""
        pass
