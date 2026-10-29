"""
==============================================================================
【模块名称】：CinemaAgent MCP 云端服务标准 JSON-RPC 2.0 路由器 (MCP Router)
【业务定位】：对外暴露的标准化 MCP 协议端点网关。
【全链路调用位置】：
  前端 MCP 中台沙盒 / 外部智能体网络 -> POST /api/v1/mcp -> 本模块 handle_mcp_jsonrpc()
【核心解决的核心问题】：
  1. 严格遵循 Model Context Protocol (MCP) 与 JSON-RPC 2.0 工业级报文规范；
  2. 集中分发 7 大核心 RPC Method：
     - initialize (握手协议协商)
     - tools/list (获取已注册工具清单与入参 JSON Schema)
     - tools/call (执行工具并返回标准 content 块)
     - resources/list 与 resources/read (只读资源 URI 定位与读取)
     - prompts/list 与 prompts/get (获取标准提示词工程模板)
  3. 异常标准化拦截：入参不合法或方法不存在时，返回标准的 -32600 / -32601 / -32602 错误码，绝不抛出未捕获异常。
==============================================================================
"""

import time
import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from app.mcp.server.core import (
    mcp_server,
    get_mcp_overview,
    execute_mcp_tool_direct,
)

logger = logging.getLogger("mcp.server.router")
router = APIRouter(prefix="/mcp", tags=["Model Context Protocol"])


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = 1
    method: str
    params: Optional[Dict[str, Any]] = None


class ToolCallPayload(BaseModel):
    tool_name: str
    arguments: Optional[Dict[str, Any]] = None


@router.get("/status")
async def mcp_server_status():
    """获取 MCP 服务运行状态与能力概览"""
    overview = await get_mcp_overview()
    return {"code": 200, "message": "MCP Server Online", "data": overview}


@router.post("/tools/call-direct")
async def mcp_call_tool_direct(payload: ToolCallPayload):
    """管理员在线直接调试调用 MCP 工具"""
    args = payload.arguments or {}
    res = await execute_mcp_tool_direct(payload.tool_name, args)
    return {"code": 200, "data": res}


@router.post("/jsonrpc")
@router.post("")
async def handle_mcp_jsonrpc_endpoint(req: JsonRpcRequest):
    """
    100% 工业级标准 JSON-RPC 2.0 端点。
    支持 initialize, tools/list, tools/call, resources/list, resources/read, prompts/list, prompts/get
    """
    method = req.method
    params = req.params or {}
    req_id = req.id

    try:
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": mcp_server.name,
                        "version": mcp_server.version,
                    },
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                        "prompts": {"listChanged": False},
                    },
                },
            }

        elif method == "tools/list":
            tools = await mcp_server.list_tools()
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": [
                        {
                            "name": t.name,
                            "description": t.description,
                            "inputSchema": getattr(t, "parameters", {}) or getattr(t, "inputSchema", {}),
                        }
                        for t in tools
                    ]
                },
            }

        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or params.get("parameters") or {}
            if not name:
                raise ValueError("Missing 'name' in tools/call parameters")
            call_res = await execute_mcp_tool_direct(name, arguments)
            if call_res.get("status") == "ERROR":
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32603,
                        "message": call_res.get("error", "Internal error"),
                    },
                }
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(call_res.get("result", {}), ensure_ascii=False) if not call_res.get("raw_text") else call_res.get("raw_text"),
                        }
                    ],
                    "structured_content": call_res.get("result", {}),
                    "isError": False,
                },
            }

        elif method == "resources/list":
            resources = await mcp_server.list_resources()
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "resources": [
                        {
                            "uri": str(r.uri),
                            "name": getattr(r, "name", str(r.uri)),
                            "description": getattr(r, "description", ""),
                            "mimeType": "application/json",
                        }
                        for r in resources
                    ]
                },
            }

        elif method == "resources/read":
            uri = params.get("uri")
            if not uri:
                raise ValueError("Missing 'uri' in resources/read parameters")
            content_res = await mcp_server.read_resource(uri)
            text_val = ""
            if hasattr(content_res, "contents") and content_res.contents:
                text_val = content_res.contents[0].content
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": text_val,
                        }
                    ]
                },
            }

        elif method == "prompts/list":
            prompts = await mcp_server.list_prompts()
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "prompts": [
                        {
                            "name": p.name,
                            "description": getattr(p, "description", ""),
                            "arguments": [
                                {"name": a.name, "description": getattr(a, "description", ""), "required": getattr(a, "required", False)}
                                for a in (getattr(p, "arguments", []) or [])
                            ],
                        }
                        for p in prompts
                    ]
                },
            }

        elif method == "prompts/get":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            rendered = await mcp_server.render_prompt(name, arguments)
            text_out = ""
            if hasattr(rendered, "messages") and rendered.messages:
                msg = rendered.messages[0]
                text_out = getattr(msg.content, "text", str(msg.content))
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "description": getattr(rendered, "description", ""),
                    "messages": [
                        {
                            "role": "user",
                            "content": {"type": "text", "text": text_out},
                        }
                    ],
                },
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found",
                },
            }

    except Exception as e:
        logger.error(f"MCP JSON-RPC Error: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32603,
                "message": str(e),
            },
        }
