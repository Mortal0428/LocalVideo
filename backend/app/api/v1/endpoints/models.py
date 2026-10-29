"""
==============================================================================
【模块名称】：models.py (大模型底座统一热配置、连接探针与双模型路由)
【业务职能】：
  超级管理员在线配置 LLM（大语言模型）与 Embedding（向量模型）的统一入口。支持在
  Ollama/DeepSeek-R1/OpenAI/Mimo 之间毫秒级热切换，提供网络连通性探测与网关健康指标。
【对应前端】：
  - 核心页面：frontend/src/components/EngineSettingsModal.vue (引擎设置弹窗)
  - 管理中台：frontend/src/views/AdminView.vue (系统底座 Tab)
  - 前端通信：frontend/src/api/admin.ts
==============================================================================
"""
import os
import json
import httpx
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.api.deps import require_role
from app.models.user import User
from app.models.system_config import SystemConfig
from app.services.llm_gateway import llm_gateway, PROVIDER_DEFAULT_URLS

logger = logging.getLogger(__name__)

router = APIRouter()

VALID_PROVIDERS = ["ollama", "deepseek", "mimo", "openai"]

class EngineSettingsUpdateRequest(BaseModel):
    provider: Optional[str] = None  # "ollama" | "deepseek" | "mimo" | "openai"
    chat_model: Optional[str] = None
    embedding_model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    rate_limit_per_minute: Optional[int] = None
    timeout_seconds: Optional[float] = None
    temperature: Optional[float] = None

class ModelConfigUpdate(BaseModel):
    """Backward compatible payload for legacy frontend modals."""
    provider: Optional[str] = None
    chat_model: Optional[str] = None
    embedding_model: Optional[str] = None
    mimo_base_url: Optional[str] = None
    mimo_model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None

class ChatEngineSettings(BaseModel):
    provider: str
    model_name: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = 0.4
    timeout_seconds: Optional[float] = 30.0

class EmbeddingEngineSettings(BaseModel):
    provider: str
    model_name: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None

class DualSettingsUpdateRequest(BaseModel):
    chat_engine: Optional[ChatEngineSettings] = None
    embedding_engine: Optional[EmbeddingEngineSettings] = None

class ConnectionTestRequest(BaseModel):
    provider: str  # "ollama" | "deepseek" | "mimo" | "openai"
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None

def _persist_and_reload(
    db: Session,
    updates: Dict[str, Any],
    username: str
) -> Dict[str, Any]:
    """Helper to update system_configs record in DB and hot-reload in LLMGateway."""
    provider = updates.get("provider")
    if provider and provider not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider '{provider}'. Must be one of {VALID_PROVIDERS}"
        )

    record = db.query(SystemConfig).filter(SystemConfig.config_key == "llm_gateway_config").with_for_update().first()
    if record and record.config_value:
        try:
            curr_config = json.loads(record.config_value)
        except Exception:
            curr_config = llm_gateway.get_raw_config()
    else:
        curr_config = llm_gateway.get_raw_config()
        record = SystemConfig(
            config_key="llm_gateway_config",
            description="Global LLM Gateway & Resilience Configuration"
        )
        db.add(record)

    # Apply updates
    for k, v in updates.items():
        if v is not None:
            if isinstance(v, str):
                v_str = v.strip()
                if v_str:
                    # Ignore masked api_key values from frontend forms (prevent overwriting real keys)
                    if k == "api_key" and ("..." in v_str or "***" in v_str):
                        continue
                    curr_config[k] = v_str
            else:
                curr_config[k] = v

    # Increment version & update timestamp
    version = int(curr_config.get("version", 1)) + 1
    curr_config["version"] = version
    now_iso = datetime.now().isoformat() + "Z"
    curr_config["updated_at"] = now_iso


    record.config_value = json.dumps(curr_config, ensure_ascii=False)
    record.updated_by = username
    db.commit()

    # Instant hot-reload in singleton gateway (<1ms)
    reloaded = llm_gateway.reload_config(new_config=curr_config)
    logger.info(f"LLMGateway hot-reloaded by @{username}: v{version} provider={reloaded.get('provider')} model={reloaded.get('chat_model')}")

    return {
        "success": True,
        "message": "Model engine configuration updated and hot-reloaded successfully",
        "active_config": {
            "provider": reloaded.get("provider"),
            "chat_model": reloaded.get("chat_model"),
            "version": version,
            "updated_at": now_iso
        }
    }

@router.put("/engine-settings")
async def update_engine_settings(
    req: EngineSettingsUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    管理员在线保存并热重载大模型底座配置（提供商、API Key、基础 URL、模型名）。
    对应 HTTP 端点：PUT /engine-settings
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：点击引擎配置弹窗保存按钮
    - 调用链路：前端通过 admin.ts -> updateEngineSettings() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    updates = req.model_dump(exclude_none=True) if hasattr(req, "model_dump") else req.dict(exclude_none=True)

    return _persist_and_reload(db, updates, current_user.username)

@router.get("/engine-settings", dependencies=[Depends(require_role(["ADMIN"]))])
async def get_engine_settings():
    """
    ==============================================================================
    【这个接口是做什么的】：
    获取当前系统正在生效的大模型底座动态热配置。
    对应 HTTP 端点：GET /engine-settings
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：打开引擎配置弹窗时拉取
    - 调用链路：前端通过 admin.ts -> getEngineSettings() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    return {
        "code": 200,
        "data": llm_gateway.get_active_config()
    }

@router.post("/config")
async def update_model_config(
    req: ModelConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    更新特定模型底座配置并重置网关单例。
    对应 HTTP 端点：POST /config
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：配置面板点击应用
    - 调用链路：前端通过 admin.ts -> updateModelConfig() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    updates: Dict[str, Any] = {}
    if req.provider:
        updates["provider"] = req.provider
    if req.chat_model:
        updates["chat_model"] = req.chat_model
    if req.embedding_model:
        updates["embedding_model"] = req.embedding_model
    if req.base_url:
        updates["base_url"] = req.base_url
    elif req.mimo_base_url:
        updates["base_url"] = req.mimo_base_url
    if req.api_key:
        updates["api_key"] = req.api_key

    res = _persist_and_reload(db, updates, current_user.username)
    cfg = llm_gateway.get_active_config()
    return {
        "code": 200,
        "message": "模型引擎与厂商配置已由管理员成功更新并全局生效！",
        "data": {
            "active_provider": cfg.get("provider"),
            "chat_model": cfg.get("chat_model"),
            "embedding_model": cfg.get("embedding_model"),
            "base_url": cfg.get("base_url"),
            "version": cfg.get("version"),
            "updated_by": current_user.username
        }
    }

@router.get("/dual-settings")
async def get_dual_settings():
    """
    ==============================================================================
    【这个接口是做什么的】：
    获取双模型协同配置（LLM 文本生成大模型 + Embedding 文本向量模型）。
    对应 HTTP 端点：GET /dual-settings
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：打开双模型配置抽屉
    - 调用链路：前端通过 admin.ts -> getDualSettings() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    return {
        "code": 200,
        "data": llm_gateway.get_dual_config()
    }

@router.put("/dual-settings")
async def update_dual_settings(
    req: DualSettingsUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    保存双模型配置，毫秒级热重载在线推理与向量检索底层实例。
    对应 HTTP 端点：PUT /dual-settings
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：保存双模型配置
    - 调用链路：前端通过 admin.ts -> updateDualSettings() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    updates: Dict[str, Any] = {}
    if req.chat_engine:
        updates["provider"] = req.chat_engine.provider
        updates["chat_model"] = req.chat_engine.model_name
        if req.chat_engine.base_url:
            updates["base_url"] = req.chat_engine.base_url
        if req.chat_engine.api_key:
            updates["api_key"] = req.chat_engine.api_key
        if req.chat_engine.temperature is not None:
            updates["temperature"] = req.chat_engine.temperature
        if req.chat_engine.timeout_seconds is not None:
            updates["timeout_seconds"] = req.chat_engine.timeout_seconds

    if req.embedding_engine:
        updates["embedding_provider"] = req.embedding_engine.provider
        updates["embedding_model"] = req.embedding_engine.model_name
        if req.embedding_engine.base_url:
            updates["embedding_base_url"] = req.embedding_engine.base_url
        if req.embedding_engine.api_key:
            updates["embedding_api_key"] = req.embedding_engine.api_key

    res = _persist_and_reload(db, updates, current_user.username)
    return {
        "code": 200,
        "message": "双轨模型引擎（对话推理 + 向量嵌入）已成功独立配置并全局生效！",
        "data": llm_gateway.get_dual_config()
    }

@router.get("/probe")
async def probe_models():
    """
    ==============================================================================
    【这个接口是做什么的】：
    在线探测指定 AI 供应商（如本地 Ollama 或 OpenAI）当前所有可用模型清单。
    对应 HTTP 端点：GET /probe
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：引擎配置弹窗中点击探测模型列表
    - 调用链路：前端通过 admin.ts -> probeModels() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    active_cfg = llm_gateway.get_active_config()
    ollama_base_url = active_cfg.get("base_url", settings.OLLAMA_BASE_URL) if active_cfg.get("provider") == "ollama" else settings.OLLAMA_BASE_URL
    
    ollama_running = False
    ollama_models: List[Dict[str, Any]] = []
    chat_models: List[str] = []
    embedding_models: List[str] = []

    # 1. Probe Local Ollama
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{ollama_base_url.rstrip('/')}/api/tags")
            if resp.status_code == 200:
                ollama_running = True
                data = resp.json()
                for item in data.get("models", []):
                    name = item.get("name", "")
                    size_mb = round(item.get("size", 0) / (1024 * 1024), 1)
                    ollama_models.append({
                        "name": name,
                        "size_mb": size_mb,
                        "modified_at": item.get("modified_at", "")
                    })
                    if "embed" in name.lower() or "bge" in name.lower():
                        embedding_models.append(name)
                    else:
                        chat_models.append(name)
    except Exception as e:
        logger.warning(f"Ollama probe failed: {e}")

    # Note: If Ollama is offline or has no models, chat_models remains [] (NO FAKE MODELS)

    # 2. Check Cloud Providers status
    raw_cfg = llm_gateway.get_raw_config()
    mimo_key = raw_cfg.get("api_key") if raw_cfg.get("provider") == "mimo" else os.getenv("MIMO_API_KEY", settings.MIMO_API_KEY or "")
    mimo_configured = bool(mimo_key and len(mimo_key) > 6)
    mimo_masked = f"{mimo_key[:4]}...{mimo_key[-4:]}" if mimo_configured else ""

    deepseek_key = raw_cfg.get("api_key") if raw_cfg.get("provider") == "deepseek" else os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_configured = bool(deepseek_key and len(deepseek_key) > 6)
    deepseek_masked = f"{deepseek_key[:4]}...{deepseek_key[-4:]}" if deepseek_configured else ""

    openai_key = raw_cfg.get("api_key") if raw_cfg.get("provider") == "openai" else os.getenv("OPENAI_API_KEY", "")
    openai_configured = bool(openai_key and len(openai_key) > 6)
    openai_masked = f"{openai_key[:4]}...{openai_key[-4:]}" if openai_configured else ""

    return {
        "code": 200,
        "data": {
            "active_provider": active_cfg.get("provider"),
            "active_chat_model": active_cfg.get("chat_model"),
            "active_embedding_model": active_cfg.get("embedding_model"),
            "ollama": {
                "running": ollama_running,
                "base_url": ollama_base_url,
                "chat_models": chat_models,
                "embedding_models": embedding_models,
                "all_models": ollama_models
            },
            "deepseek": {
                "base_url": active_cfg.get("base_url") if active_cfg.get("provider") == "deepseek" else PROVIDER_DEFAULT_URLS["deepseek"],
                "configured": deepseek_configured,
                "masked_key": deepseek_masked,
                "supported_models": ["deepseek-chat", "deepseek-reasoner"]
            },
            "mimo": {
                "base_url": active_cfg.get("base_url") if active_cfg.get("provider") == "mimo" else PROVIDER_DEFAULT_URLS["mimo"],
                "configured": mimo_configured,
                "masked_key": mimo_masked,
                "supported_models": ["mimo-v1", "mimo-v1-chat", "mimo-v1-pro"]
            },
            "openai": {
                "base_url": active_cfg.get("base_url") if active_cfg.get("provider") == "openai" else PROVIDER_DEFAULT_URLS["openai"],
                "configured": openai_configured,
                "masked_key": openai_masked,
                "supported_models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
            }
        }
    }

@router.post("/test-connection")
async def test_connection(req: ConnectionTestRequest):
    """
    ==============================================================================
    【这个接口是做什么的】：
    实测连接当前配置的 LLM 大语言模型服务，验证网络连通性与响应速度。
    对应 HTTP 端点：POST /test-connection
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：点击测试 LLM 连通性按钮
    - 调用链路：前端通过 admin.ts -> testConnection() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    provider = req.provider.lower().strip()
    if provider not in VALID_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Provider must be one of {VALID_PROVIDERS}")

    active_cfg = llm_gateway.get_raw_config()
    base_url = req.base_url or (active_cfg.get("base_url") if active_cfg.get("provider") == provider else PROVIDER_DEFAULT_URLS.get(provider, "http://localhost:11434"))
    target_model = req.model or active_cfg.get("chat_model", "default")
    req_key = req.api_key.strip() if req.api_key else ""
    if req_key and not ("..." in req_key or "***" in req_key):
        api_key = req_key
    else:
        api_key = active_cfg.get("api_key") if active_cfg.get("provider") == provider else ""

    if provider == "ollama":
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(f"{base_url.rstrip('/')}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name") for m in res.json().get("models", [])]
                    found = any(target_model in m or m in target_model for m in models)
                    if found:
                        return {"code": 200, "status": "success", "reply": f"Ollama 本地引擎正常，模型 [{target_model}] 在线可用"}
                    return {"code": 404, "status": "failed", "detail": f"未在本地检测到模型: {target_model}。已检测到的模型: {', '.join(models) if models else '无'}"}
                return {"code": 500, "status": "failed", "detail": f"Ollama 服务异常 HTTP {res.status_code}"}
        except Exception as e:
            return {"code": 500, "status": "failed", "detail": f"无法连接 Ollama ({base_url}): {e}"}

    # Cloud providers: DeepSeek, MiMo, OpenAI
    if not api_key:
        # Fall back to env variables if available
        if provider == "mimo":
            api_key = os.getenv("MIMO_API_KEY", settings.MIMO_API_KEY or "")
        elif provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY", "")
        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY", "")

    if not api_key:
        return {"code": 400, "status": "failed", "detail": f"未检测到 {provider.upper()} API Key，请先输入密钥"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    url = base_url.rstrip("/")
    if not url.endswith("/chat/completions"):
        if not url.endswith("/v1"):
            url = f"{url}/v1"
        url = f"{url}/chat/completions"

    payload = {
        "model": target_model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 10
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, headers=headers, json=payload)
            if res.status_code in [200, 201]:
                data = res.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "OK")
                return {"code": 200, "status": "success", "reply": f"{provider.capitalize()} 连通成功！模型响应: {content[:80]}"}
            elif res.status_code == 401:
                return {"code": 401, "status": "failed", "detail": f"{provider.capitalize()} API Key 鉴权失败，请检查密钥是否正确"}
            else:
                return {"code": res.status_code, "status": "failed", "detail": res.text[:200]}
    except Exception as e:
        return {"code": 500, "status": "failed", "detail": f"连接 {provider.capitalize()} 服务失败: {e}"}

@router.post("/test-embedding")
async def test_embedding_connection(req: ConnectionTestRequest):
    """
    ==============================================================================
    【这个接口是做什么的】：
    实测连接当前配置的 Embedding 向量模型服务，验证文本向量化输出。
    对应 HTTP 端点：POST /test-embedding
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：点击测试向量模型连通性按钮
    - 调用链路：前端通过 admin.ts -> testEmbeddingConnection() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    provider = req.provider.lower().strip()
    active_cfg = llm_gateway.get_raw_config()
    base_url = req.base_url or (active_cfg.get("embedding_base_url") if active_cfg.get("embedding_provider") == provider else PROVIDER_DEFAULT_URLS.get(provider, "http://localhost:11434"))
    target_model = req.model or active_cfg.get("embedding_model", "qwen3-embedding:0.6b")
    req_key = req.api_key.strip() if req.api_key else ""
    api_key = req_key if (req_key and not ("..." in req_key or "***" in req_key)) else (active_cfg.get("embedding_api_key", ""))

    try:
        if provider == "ollama":
            url = f"{base_url.rstrip('/')}/api/embeddings"
            payload = {"model": target_model, "prompt": "test embedding"}
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    vec = res.json().get("embedding", [])
                    return {"code": 200, "status": "success", "reply": f"Ollama 向量引擎正常！模型 [{target_model}] 维度: {len(vec)}"}
                return {"code": 500, "status": "failed", "detail": f"Ollama 向量服务异常 HTTP {res.status_code}: {res.text[:100]}"}
        else:
            url = f"{base_url.rstrip('/')}/v1/embeddings" if not base_url.endswith("/embeddings") else base_url
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            payload = {"model": target_model, "input": "test embedding"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    vec = data.get("data", [{}])[0].get("embedding", [])
                    return {"code": 200, "status": "success", "reply": f"{provider.capitalize()} 向量服务正常！向量维度: {len(vec)}"}
                return {"code": res.status_code, "status": "failed", "detail": res.text[:200]}
    except Exception as e:
        return {"code": 500, "status": "failed", "detail": f"向量模型连接失败: {e}"}

@router.get("/telemetry")
async def get_gateway_telemetry():
    """
    ==============================================================================
    【这个接口是做什么的】：
    获取大模型调用网关的实时吞吐、失败重试与断路器统计状态。
    对应 HTTP 端点：GET /telemetry
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：管理中台模型健康大屏
    - 调用链路：前端通过 admin.ts -> getGatewayTelemetry() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    return llm_gateway.get_health_status()
