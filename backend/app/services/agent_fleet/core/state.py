# -*- coding: utf-8 -*-
"""
==============================================================================
【模块名称】：CinemaAgent - 智能体状态定义 (AgentState)
【业务定位】：定义 LangGraph 状态图流转的核心 State 键值契约
==============================================================================
"""
"""
LangGraph 全局母体状态数据模型定义
支持异构多智能体协作、共享黑板工件传递、物理隔离会话记忆与人机中断恢复
"""

from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    role: str = Field(..., description="user / assistant / system / tool / observer")
    agent_id: Optional[str] = Field(None, description="发言智能体编号: agent_1 到 agent_9")
    agent_name: Optional[str] = Field(None, description="发言智能体名称")
    content: str = Field(..., description="消息正文")
    thought: Optional[str] = Field(None, description="思考过程/推理链")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="调用的工具列表")
    tool_results: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="工具返回数据")
    timestamp: Optional[str] = Field(None, description="生成时间戳")


class AgentGraphState(TypedDict, total=False):
    session_id: str                              # 唯一会话标识
    user_id: Optional[str]                      # 归属用户
    topic: Optional[str]                        # 当前讨论或任务主题
    active_agent_id: str                        # 当前正在执行思考/动作的智能体
    target_agent_id: Optional[str]              # 下一个被 @ 或交接的目标智能体
    messages: List[Dict[str, Any]]              # 当前会话消息列表 (受滑动窗口保护)
    blackboard_context: Dict[str, Any]          # 公共只读黑板契约 (存放各 Agent 交付的标准工件)
    scratchpad: Dict[str, Any]                  # 单轮临时草稿 (单步结束后销毁)
    current_tool_call: Optional[Dict[str, Any]] # 当前待执行或已执行的工具
    interrupt_payload: Optional[Dict[str, Any]] # 触发人机回环中断 (interrupt) 时的挂起单据
    round_count: int                            # 协同研讨轮次
    is_completed: bool                          # 是否已达成共识并完结
    telemetry: Dict[str, Any]                   # 耗时、Token 与审计遥测
