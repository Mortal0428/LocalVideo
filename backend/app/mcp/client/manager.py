"""
CinemaAgent MCP 客户端管理器 (Client Adapter)
负责连接本地与远程 MCP 节点，并将 MCP Tools 转化为 LangChain 标准 Tool
"""

import httpx
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, create_model

logger = logging.getLogger("mcp.client.manager")


class MCPClientManager:
    """
    通用 MCP 客户端单例：
    管理多个 MCP Server 连接，提供工具发现与即插即用动态装配能力。
    """
    _instance: Optional["MCPClientManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._servers: Dict[str, str] = {
                "local_cinema": "http://127.0.0.1:8000/api/v1/mcp"
            }
            cls._cached_tools: Dict[str, List[Any]] = {}
        return cls._instance

    def register_server(self, server_name: str, url: str) -> None:
        """注册或更新远程 MCP 节点地址"""
        self._servers[server_name] = url.rstrip("/")
        logger.info(f"Registered MCP Server: {server_name} -> {url}")

    def list_servers(self) -> Dict[str, str]:
        """返回已注册的全部 MCP 节点"""
        return dict(self._servers)

    async def fetch_tools_from_server(self, server_name: str = "local_cinema") -> List[Dict[str, Any]]:
        """从指定 MCP 节点获取全部可用工具列表"""
        url = self._servers.get(server_name)
        if not url:
            raise ValueError(f"Server '{server_name}' not registered")

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                url,
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("result", {}).get("tools", [])
            else:
                logger.warning(f"Failed to fetch tools from {server_name}: HTTP {resp.status_code}")
                return []

    async def call_remote_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """通过 JSON-RPC 2.0 协议远程执行工具"""
        url = self._servers.get(server_name)
        if not url:
            raise ValueError(f"Server '{server_name}' not registered")

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                if "error" in data:
                    raise RuntimeError(f"MCP Tool Error: {data['error'].get('message')}")
                return data.get("result", {})
            raise RuntimeError(f"MCP Server HTTP {resp.status_code}")

    async def get_langchain_tools(self, server_name: str = "local_cinema") -> List[StructuredTool]:
        """
        将指定 MCP 节点暴露的所有工具动态桥接为 LangChain StructuredTool，
        使 9 大智能体可无感通过 Function Calling 或 Agent 流程调用。
        """
        raw_tools = await self.fetch_tools_from_server(server_name)
        lc_tools: List[StructuredTool] = []

        for rt in raw_tools:
            name = rt.get("name")
            desc = rt.get("description", "")
            
            # 创建动态执行闭包
            def _make_tool_func(s_name: str, t_name: str):
                async def _async_exec(**kwargs):
                    res = await self.call_remote_tool(s_name, t_name, kwargs)
                    return res.get("structured_content") or res.get("content", [{}])[0].get("text", "")
                return _async_exec

            tool_func = _make_tool_func(server_name, name)
            tool_obj = StructuredTool.from_function(
                coroutine=tool_func,
                name=name,
                description=desc,
            )
            lc_tools.append(tool_obj)

        return lc_tools


# 单例实例
mcp_client_manager = MCPClientManager()
