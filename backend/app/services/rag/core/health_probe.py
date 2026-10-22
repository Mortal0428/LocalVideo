"""
CinemaAgent 工业级基础设施独立心跳探测模块 (Health Probes)
提供对 Neo4j 图数据库、大模型底座（Ollama/DeepSeek/OpenAI）、向量库的即测即验（Ping/Status）API，
配备严格的超时熔断保护，杜绝前端遭遇 504 错误。
"""

import time
import asyncio
import logging
from typing import Dict, Any, Optional

import httpx
from app.services.rag.core.neo4j_client import graph_service

logger = logging.getLogger(__name__)


async def probe_neo4j_service(
    uri: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    timeout_sec: float = 2.5
) -> Dict[str, Any]:
    """
    异步实时探测 Neo4j 连通性、连接延迟与节点/关系拓扑统计。
    超时自动降级并返回结构化诊断信息，绝不阻塞事件循环。
    """
    start_t = time.perf_counter()
    
    def _sync_ping():
        # 尝试通过已有的 graph_service 或新建轻量驱动探测
        is_live = graph_service.check_connectivity()
        status = graph_service.get_status()
        return is_live, status

    try:
        is_live, status = await asyncio.wait_for(
            asyncio.to_thread(_sync_ping),
            timeout=timeout_sec
        )
        latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
        return {
            "is_connected": is_live,
            "latency_ms": latency_ms,
            "backend": status.get("backend", "embedded_fallback"),
            "uri": status.get("uri", "bolt://localhost:7687"),
            "user": status.get("user", "neo4j"),
            "total_nodes": status.get("total_nodes", 0),
            "total_edges": status.get("total_edges", 0),
            "message": "Neo4j 图数据库连通正常，服务就绪" if is_live else "Neo4j 未连通，当前由嵌入式图存储降级保护"
        }
    except asyncio.TimeoutError:
        latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
        return {
            "is_connected": False,
            "latency_ms": latency_ms,
            "backend": "embedded_fallback",
            "uri": uri or "bolt://localhost:7687",
            "user": user or "neo4j",
            "total_nodes": 0,
            "total_edges": 0,
            "message": f"探测 Neo4j 超时 ({timeout_sec}s)，自动降级至本地嵌入式图存储"
        }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
        return {
            "is_connected": False,
            "latency_ms": latency_ms,
            "backend": "embedded_fallback",
            "uri": uri or "bolt://localhost:7687",
            "user": user or "neo4j",
            "total_nodes": 0,
            "total_edges": 0,
            "message": f"探测 Neo4j 异常: {str(e)}"
        }


async def probe_llm_service(
    provider: str,
    model_name: str,
    base_url: str,
    api_key: str = "",
    timeout_sec: float = 4.0
) -> Dict[str, Any]:
    """
    异步即时探测指定大模型底座的 HTTP 连通性与首字延迟。
    支持 Ollama、DeepSeek、OpenAI、Mimo 等标准 API 格式。
    """
    start_t = time.perf_counter()
    clean_base = (base_url or "").rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            if provider.lower() == "ollama":
                # Ollama 探测 tags 或版本
                url = f"{clean_base}/api/tags" if "/api" not in clean_base else f"{clean_base}/tags"
                resp = await client.get(url)
                latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
                if resp.status_code == 200:
                    models = [m.get("name") for m in resp.json().get("models", [])]
                    matched = any(model_name in m for m in models) if model_name else True
                    return {
                        "is_connected": True,
                        "latency_ms": latency_ms,
                        "provider": provider,
                        "model_name": model_name,
                        "available_models": models[:6],
                        "model_ready": matched,
                        "message": "Ollama 服务在线且模型匹配" if matched else f"Ollama 在线，但模型 {model_name} 未在本地拉取"
                    }
                else:
                    return {
                        "is_connected": False,
                        "latency_ms": latency_ms,
                        "provider": provider,
                        "model_name": model_name,
                        "message": f"Ollama 返回 HTTP {resp.status_code}"
                    }
            else:
                # OpenAI / DeepSeek / Compatible 格式
                url = f"{clean_base}/chat/completions" if "/v1" in clean_base or "api." in clean_base else f"{clean_base}/v1/chat/completions"
                headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1
                }
                resp = await client.post(url, headers=headers, json=payload)
                latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
                if resp.status_code == 200:
                    return {
                        "is_connected": True,
                        "latency_ms": latency_ms,
                        "provider": provider,
                        "model_name": model_name,
                        "message": "大模型在线，首字握手成功"
                    }
                else:
                    return {
                        "is_connected": False,
                        "latency_ms": latency_ms,
                        "provider": provider,
                        "model_name": model_name,
                        "message": f"大模型服务返回 HTTP {resp.status_code}: {resp.text[:120]}"
                    }
    except asyncio.TimeoutError:
        latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
        return {
            "is_connected": False,
            "latency_ms": latency_ms,
            "provider": provider,
            "model_name": model_name,
            "message": f"探测大模型超时 ({timeout_sec}s)"
        }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
        return {
            "is_connected": False,
            "latency_ms": latency_ms,
            "provider": provider,
            "model_name": model_name,
            "message": f"探测大模型失败: {str(e)}"
        }
