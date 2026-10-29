"""
==============================================================================
【模块名称】：CinemaAgent FastMCP 服务端核心引擎容器 (FastMCP Server Core)
【业务定位】：全平台所有 MCP 工具、只读资源与提示词模板的单例注册中心。
【全链路调用位置】：
  由 mcp/server/router.py 转发调用，或在后端初始化时注册工具
【核心解决的核心问题】：
  1. 统一管理 4 大核心工具 (短剧搜索、分集切片台词、Neo4j人物关系图谱、弹幕内容风控)；
  2. 统一管理 2 大只读资源 (全站Trending Top5、短剧知识图谱Ontology结构)；
  3. 统一管理 2 大标准Prompt模板 (剧情反转剧评模板、弹幕安全合规汇报模板)；
  4. 为智能体与外部生态提供零侵入式工具调用容器。
==============================================================================
"""

import time
import json
import logging
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP

from app.mcp.server.tools.cinema_media_tools import (
    mcp_search_dramas,
    mcp_get_episode_transcript,
)
from app.mcp.server.tools.graph_rag_tools import (
    mcp_query_character_relations,
)
from app.mcp.server.tools.moderation_safety_tools import (
    mcp_inspect_danmaku_safety,
)
from app.mcp.server.resources.drama_resources import (
    get_trending_dramas_resource,
    get_graph_ontology_resource,
)
from app.mcp.server.prompts.critique_prompts import (
    critique_plot_twist_prompt,
    moderation_audit_summary_prompt,
)

logger = logging.getLogger("mcp.server.core")

# 初始化 FastMCP 单例服务
mcp_server = FastMCP(
    name="CinemaAgent-MCP",
    instructions="CinemaAgent 全场景短剧流媒体与创作平台工业级云端 MCP 工具中台",
    version="1.0.0",
)

# ================= 注册 Tools 工具能力 =================
@mcp_server.tool(name="cinema_search_dramas", description="多维检索平台在架短剧真实媒资数据")
async def tool_search_dramas(
    keyword: str = "",
    category: Optional[str] = None,
    min_heat: Optional[int] = None,
    limit: int = 5,
) -> Dict[str, Any]:
    return await mcp_search_dramas(keyword=keyword, category=category, min_heat=min_heat, limit=limit)


@mcp_server.tool(name="cinema_get_episode_transcript", description="按分集与秒级时间轴提取短剧台词字幕与事实切片")
async def tool_get_episode_transcript(
    video_id: str,
    episode_num: int = 1,
    start_sec: float = 0.0,
    end_sec: float = 300.0,
) -> Dict[str, Any]:
    return await mcp_get_episode_transcript(video_id=video_id, episode_num=episode_num, start_sec=start_sec, end_sec=end_sec)


@mcp_server.tool(name="graph_query_character_relations", description="遍历 Neo4j 知识图谱查询短剧人物三元组关系路径与高能冲突")
async def tool_query_character_relations(
    character_name: str,
    drama_title: Optional[str] = None,
    depth: int = 2,
) -> Dict[str, Any]:
    return await mcp_query_character_relations(character_name=character_name, drama_title=drama_title, depth=depth)


@mcp_server.tool(name="moderation_inspect_content", description="基于站内违规敏感词库与多级风控规则审查弹幕/评论安全性")
async def tool_inspect_content(
    content: str,
    target_type: str = "danmaku",
    risk_threshold: int = 60,
) -> Dict[str, Any]:
    return await mcp_inspect_danmaku_safety(content=content, target_type=target_type, risk_threshold=risk_threshold)


# ================= 注册 Resources 只读上下文能力 =================
@mcp_server.resource("cinema://dramas/trending-top5")
def res_trending_dramas() -> str:
    """全站热播短剧 Top 5 实时只读数据源"""
    return get_trending_dramas_resource()


@mcp_server.resource("graph://schema/ontology")
def res_graph_ontology() -> str:
    """短剧人物与情感关系本体结构定义"""
    return get_graph_ontology_resource()


# ================= 注册 Prompts 提示词模板能力 =================
@mcp_server.prompt(name="critique_plot_twist")
def prompt_critique(drama_title: str, character: str = "") -> str:
    """1号课代表剧情矛盾与高能反转拆解标准模板"""
    return critique_plot_twist_prompt(drama_title=drama_title, character=character)


@mcp_server.prompt(name="moderation_audit_summary")
def prompt_moderation_summary(date_str: str = "2026-10-27") -> str:
    """弹幕合规治理审计综述报告标准模板"""
    return moderation_audit_summary_prompt(date_str=date_str)


# ================= 统一对外查询方法 =================
async def get_mcp_overview() -> Dict[str, Any]:
    """获取 MCP 服务端实时运行状态与能力大厅元数据"""
    tools = await mcp_server.list_tools()
    resources = await mcp_server.list_resources()
    prompts = await mcp_server.list_prompts()

    return {
        "server_name": mcp_server.name,
        "instructions": mcp_server.instructions,
        "version": mcp_server.version,
        "protocol": "Model Context Protocol (JSON-RPC 2.0)",
        "status": "ONLINE",
        "transport": "streamable-http & asgi-mount",
        "counts": {
            "tools": len(tools),
            "resources": len(resources),
            "prompts": len(prompts),
        },
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "parameters": getattr(t, "parameters", {}) or getattr(t, "inputSchema", {}),
            }
            for t in tools
        ],
        "resources": [
            {
                "uri": str(r.uri),
                "name": getattr(r, "name", str(r.uri)),
                "description": getattr(r, "description", ""),
            }
            for r in resources
        ],
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
        ],
    }


async def execute_mcp_tool_direct(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    直接执行 MCP 工具并返回执行耗时与结构化数据
    """
    t0 = time.time()
    try:
        res = await mcp_server.call_tool(tool_name, arguments)
        latency_ms = round((time.time() - t0) * 1000.0, 2)
        
        # 兼容 FastMCP 返回的 content 与 structured_content
        text_out = ""
        structured = {}
        if hasattr(res, "content") and res.content:
            text_out = "\n".join([getattr(c, "text", str(c)) for c in res.content])
        if hasattr(res, "structured_content") and res.structured_content:
            structured = res.structured_content
        elif text_out:
            try:
                structured = json.loads(text_out)
            except Exception:
                structured = {"raw": text_out}

        return {
            "status": "SUCCESS",
            "tool_name": tool_name,
            "latency_ms": latency_ms,
            "result": structured,
            "raw_text": text_out,
        }
    except Exception as e:
        latency_ms = round((time.time() - t0) * 1000.0, 2)
        return {
            "status": "ERROR",
            "tool_name": tool_name,
            "latency_ms": latency_ms,
            "error": str(e),
        }
