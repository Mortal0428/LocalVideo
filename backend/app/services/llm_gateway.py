# -*- coding: utf-8 -*-
"""
==============================================================================
【业务服务】：backend/app/services/llm_gateway.py
【业务定位】：全平台统一大模型高可用韧性网关（LLMGateway）
【核心功能】：
  1. 令牌桶限流保护（TokenBucketLimiter）：限制单客户端与全局并发突发，防止推理接口打爆；
  2. 断路器熔断降级（CircuitBreaker）：连续失败达阈值自动进入 OPEN 熔断状态，
     支持指数退避与半开探测（HALF_OPEN），遇到模型离线时输出透明诊断状态，绝不卡死线程；
  3. 多底座动态热重载：单例缓存 system_configs 表配置，支持在 Ollama、DeepSeek、
     OpenAI、小米 MiMo 之间毫秒级平滑切换，全平台所有用户共享最新配置；
  4. 统一调用门面（chat_completion / stream_chat）：抹平不同 AI 提供商的 API 差异。
【对应前端】：
  - 底座配置弹窗：frontend/src/components/EngineSettingsModal.vue
  - 顶栏健康呼吸灯：frontend/src/components/AdminHeader.vue
==============================================================================
"""

import time
import json
import asyncio
import threading
import logging
from typing import Optional, Dict, Any, AsyncGenerator, Tuple, List
import httpx
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.orm import Session
from app.core.config import settings
from langsmith import traceable

logger = logging.getLogger(__name__)

# 【网关默认种子配置】：当数据库 system_configs 中未配置时使用的初始兜底参数
DEFAULT_GATEWAY_CONFIG: Dict[str, Any] = {
    "provider": "ollama",
    "chat_model": "deepseek-r1:1.5b",
    "embedding_model": "qwen3-embedding:0.6b",
    "api_key": "",
    "base_url": "http://localhost:11434",
    "rate_limit_per_minute": 60,
    "timeout_seconds": 30.0,
    "temperature": 0.4,
    "version": 1
}

PROVIDER_DEFAULT_URLS = {
    "ollama": "http://localhost:11434",
    "deepseek": "https://api.deepseek.com",
    "mimo": "https://api.xiaomimimo.com/v1",
    "openai": "https://api.openai.com/v1"
}


class TokenBucketLimiter:
    """
    【令牌桶限流保护器 (TokenBucketLimiter)】
    
    【核心现实作用】：
    用于限制用户或系统对大模型推理接口的瞬时并发请求频率。
    大模型推理（尤其是本地部署的 Ollama 或高成本云端 DeepSeek）非常消耗 GPU 和显存，
    如果观众疯狂狂点【发送】或脚本恶意刷接口，很容易导致显卡打满崩溃（OOM）。
    本令牌桶算法以恒定速率往桶里注入令牌，请求到达时必须消耗令牌才能执行推理，
    当桶内令牌耗尽时立即拦截，返回明确等待倒计时，防止推理集群被打爆。
    
    【内部关键字段大白话】：
    - rate_per_sec (float): 每秒自动注入桶内的令牌数量（例如 60次/分 -> 1.0 个/秒）。
    - capacity (float): 令牌桶最大容量（容许的瞬时突发并发数，超出部分直接拦截）。
    - tokens (float): 当前桶内剩余可用的令牌数量。
    - last_refill (float): 上一次计算并补充令牌的时间戳（利用惰性补充算法，无需后台定时器占用 CPU）。
    """
    def __init__(self, rate_limit_per_minute: int = 60, capacity: Optional[int] = None):
        self.rate_per_sec = max(0.1, rate_limit_per_minute / 60.0)
        self.capacity = float(capacity or max(10, rate_limit_per_minute // 2))
        self.tokens = self.capacity
        self.last_refill = time.monotonic()
        self._lock = None
        self._lock_loop = None

    @property
    def lock(self) -> asyncio.Lock:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if self._lock is None or self._lock_loop != loop:
            self._lock = asyncio.Lock()
            self._lock_loop = loop
        return self._lock

    def update_rate(self, rate_limit_per_minute: int):
        self.rate_per_sec = max(0.1, rate_limit_per_minute / 60.0)
        self.capacity = float(max(10, rate_limit_per_minute // 2))
        self.tokens = min(self.tokens, self.capacity)

    async def acquire(self, required_tokens: int = 1) -> Tuple[bool, float]:
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.last_refill = now
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate_per_sec)

            if self.tokens >= required_tokens:
                self.tokens -= required_tokens
                return True, 0.0
            else:
                deficit = required_tokens - self.tokens
                wait_sec = deficit / self.rate_per_sec
                return False, wait_sec


class CircuitBreaker:
    """
    【三态工程高可用熔断器 (CircuitBreaker)】
    
    【核心现实作用】：
    就像家里的电闸保险丝。当云端大模型 API 欠费、挂掉、网络中断或本地 Ollama 服务没有启动时，
    如果没有熔断器，后端每个请求都会傻傻卡死等待 30 秒超时，最终导致所有工作线程耗尽、整站瘫痪崩溃。
    断路器能够在连续发生故障时果断“跳闸”，直接在毫秒级快速返回诊断状态，绝不卡顿，并支持自动试探恢复。
    
    【三态转换逻辑大白话】：
    1. CLOSED (合闸正常态)：平时正常放行所有大模型请求。一旦连续失败达到阈值（如连续 3 次报错），立刻跳闸转为 OPEN！
    2. OPEN (跳闸熔断态)：所有请求在 1 毫秒内立即快速失败，不再发起真实网络请求，并向前端返回倒计时提示（如“15秒后重试”）。
    3. HALF-OPEN (半开试探态)：熔断冷却时间过后，允许且只允许单次探针请求去试探大模型。若成功则恢复 CLOSED，若仍失败则继续跳回 OPEN。
    
    【内部关键字段大白话】：
    - failure_threshold (int): 触发熔断的连续失败次数阈值（默认 3 次）。
    - recovery_timeout (float): 触发熔断后的冷却观察期（秒，默认 15.0 秒）。
    - consecutive_failures (int): 当前连续失败的计数器，一旦调用成功会立刻清零。
    - state (str): 当前断路器所处的状态 ("CLOSED" / "OPEN" / "HALF-OPEN")。
    """
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF-OPEN"

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 15.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = self.CLOSED
        self.consecutive_failures = 0
        self.total_requests = 0
        self.total_failures = 0
        self.last_state_change = time.time()
        self.last_failure_reason = ""
        self._probe_inflight = False
        self._lock = None
        self._lock_loop = None

    @property
    def lock(self) -> asyncio.Lock:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if self._lock is None or self._lock_loop != loop:
            self._lock = asyncio.Lock()
            self._lock_loop = loop
        return self._lock

    async def can_execute(self) -> Tuple[bool, str, float]:
        async with self.lock:
            self.total_requests += 1
            now = time.time()
            if self.state == self.CLOSED:
                return True, self.CLOSED, 0.0

            if self.state == self.OPEN:
                elapsed = now - self.last_state_change
                if elapsed >= self.recovery_timeout:
                    self.state = self.HALF_OPEN
                    self.last_state_change = now
                    self._probe_inflight = True
                    logger.info("Circuit breaker switched from OPEN to HALF-OPEN trial probe.")
                    return True, self.HALF_OPEN, 0.0
                countdown = max(0.0, self.recovery_timeout - elapsed)
                return False, self.OPEN, countdown

            # 半开试探态 (HALF-OPEN)：严格仅允许单次探针请求通行；其余并发请求一律快速熔断拦截
            if self.state == self.HALF_OPEN:
                if not self._probe_inflight:
                    self._probe_inflight = True
                    return True, self.HALF_OPEN, 0.0
                else:
                    countdown = max(0.0, self.recovery_timeout - (now - self.last_state_change))
                    return False, self.HALF_OPEN, countdown

            return False, self.state, 0.0

    async def record_success(self):
        async with self.lock:
            if self.state in [self.HALF_OPEN, self.OPEN]:
                logger.info(f"Circuit breaker recovered: switched from {self.state} to CLOSED.")
            self.state = self.CLOSED
            self.consecutive_failures = 0
            self._probe_inflight = False

    async def record_failure(self, reason: str):
        async with self.lock:
            self.consecutive_failures += 1
            self.total_failures += 1
            self.last_failure_reason = reason
            self._probe_inflight = False
            now = time.time()

            if self.state == self.HALF_OPEN:
                self.state = self.OPEN
                self.last_state_change = now
                logger.warning(f"Circuit breaker probe failed in HALF-OPEN. Reverted to OPEN: {reason}")
            elif self.state == self.CLOSED and self.consecutive_failures >= self.failure_threshold:
                self.state = self.OPEN
                self.last_state_change = now
                logger.warning(
                    f"Circuit breaker triggered OPEN after {self.consecutive_failures} consecutive failures. "
                    f"Fail-fast active for {self.recovery_timeout}s. Reason: {reason}"
                )

    def reset(self):
        self.state = self.CLOSED
        self.consecutive_failures = 0
        self.last_state_change = time.time()
        self.last_failure_reason = ""
        self._probe_inflight = False

    def get_status(self) -> Dict[str, Any]:
        countdown = 0.0
        if self.state == self.OPEN:
            elapsed = time.time() - self.last_state_change
            countdown = max(0.0, self.recovery_timeout - elapsed)
        return {
            "state": self.state,
            "consecutive_failures": self.consecutive_failures,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "last_failure_reason": self.last_failure_reason,
            "recovery_countdown_seconds": round(countdown, 1)
        }


class LLMGateway:
    """
    Unified High-Availability LLM Gateway Singleton.
    """
    _instance: Optional["LLMGateway"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._config = dict(DEFAULT_GATEWAY_CONFIG)
        self._config_lock = threading.Lock()
        self.rate_limiter = TokenBucketLimiter(
            rate_limit_per_minute=self._config["rate_limit_per_minute"]
        )
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=15.0)
        self._start_time = time.time()
        self._init_from_db_or_env()

    def _init_from_db_or_env(self):
        """Initial bootstrap of configuration from database or env settings."""
        try:
            from app.core.database import SessionLocal
            from app.models.system_config import SystemConfig
            with SessionLocal() as db:
                record = db.query(SystemConfig).filter(SystemConfig.config_key == "llm_gateway_config").first()
                if record and record.config_value:
                    loaded = json.loads(record.config_value)
                    self._apply_config(loaded, is_initial=True)
                    logger.info(f"LLMGateway initialized from DB: provider={self._config['provider']}, model={self._config['chat_model']}")
                    return
                # 若数据库中尚无配置记录，使用系统默认值与环境变量完成首次种子初始化
                initial = dict(DEFAULT_GATEWAY_CONFIG)
                if settings.ACTIVE_PROVIDER in PROVIDER_DEFAULT_URLS:
                    initial["provider"] = settings.ACTIVE_PROVIDER
                if settings.DEFAULT_LLM_MODEL:
                    initial["chat_model"] = settings.DEFAULT_LLM_MODEL
                if settings.DEFAULT_EMBEDDING_MODEL:
                    initial["embedding_model"] = settings.DEFAULT_EMBEDDING_MODEL
                if settings.OLLAMA_BASE_URL:
                    initial["base_url"] = settings.OLLAMA_BASE_URL
                if settings.MIMO_API_KEY:
                    initial["api_key"] = settings.MIMO_API_KEY

                new_record = SystemConfig(
                    config_key="llm_gateway_config",
                    config_value=json.dumps(initial, ensure_ascii=False),
                    description="Global LLM Gateway & Resilience Configuration",
                    updated_by="SYSTEM"
                )
                db.add(new_record)
                db.commit()
                self._apply_config(initial, is_initial=True)
                logger.info(f"LLMGateway seeded new configuration into DB: {initial['provider']}:{initial['chat_model']}")
        except Exception as e:
            logger.warning(f"Could not load initial LLM Gateway config from DB: {e}. Using runtime defaults.")
            self._apply_config(DEFAULT_GATEWAY_CONFIG, is_initial=True)

    def _apply_config(self, new_cfg: Dict[str, Any], is_initial: bool = False):
        """Atomically apply new config in memory and refresh sub-components."""
        with self._config_lock:
            updated = dict(self._config)
            for k, v in new_cfg.items():
                if v is not None:
                    # 忽略前端表单传回的带掩码 *** 或 ... 的脱敏密钥，防止覆盖真实密钥
                    if k == "api_key" and isinstance(v, str) and ("..." in v or "***" in v):
                        continue
                    updated[k] = v

            # 若未指定基地址 base_url，则自动解析对应提供商的默认地址
            if not updated.get("base_url"):
                updated["base_url"] = PROVIDER_DEFAULT_URLS.get(updated.get("provider", "ollama"), "http://localhost:11434")

            # 原子指针替换（线程安全与协程安全的配置热重载更新）
            self._config = updated

            # 同步刷新至全局 settings 对象，确保历史兼容性
            try:
                settings.ACTIVE_PROVIDER = self._config.get("provider", "ollama")
                settings.DEFAULT_LLM_MODEL = self._config.get("chat_model", "deepseek-r1:1.5b")
                settings.DEFAULT_EMBEDDING_MODEL = self._config.get("embedding_model", "qwen3-embedding:0.6b")
            except Exception:
                pass

            self.rate_limiter.update_rate(int(self._config.get("rate_limit_per_minute", 60)))
            if not is_initial:
                # On admin update, reset circuit breaker so new model isn't blocked by previous failures
                self.circuit_breaker.reset()

    def reload_config(self, db: Optional[Session] = None, new_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Hot-reload LLM Gateway configuration in <1ms without server restart.
        """
        if new_config:
            self._apply_config(new_config)
            return self.get_active_config()

        if db is not None:
            from app.models.system_config import SystemConfig
            record = db.query(SystemConfig).filter(SystemConfig.config_key == "llm_gateway_config").first()
            if record and record.config_value:
                loaded = json.loads(record.config_value)
                self._apply_config(loaded)
        return self.get_active_config()

    def get_active_config(self) -> Dict[str, Any]:
        """Return shallow copy of active in-memory configuration with masked credentials."""
        cfg = dict(self._config)
        # 若存在 API 密钥，进行安全脱敏打码处理（只露首尾各4位）
        if cfg.get("api_key"):
            k = str(cfg["api_key"])
            cfg["masked_api_key"] = f"{k[:4]}...{k[-4:]}" if len(k) > 8 else "***"
        else:
            cfg["masked_api_key"] = ""
        # 严格确保向调用方返回当前生效配置时，API 密钥处于脱敏掩码状态
        cfg["api_key"] = cfg["masked_api_key"]
        return cfg

    def get_raw_config(self) -> Dict[str, Any]:
        """Return copy of active in-memory configuration with unmasked credentials (internal use only)."""
        return dict(self._config)

    def get_dual_config(self) -> Dict[str, Any]:
        """Return decoupled Chat Engine and Embedding Engine configurations."""
        cfg = self.get_active_config()
        chat_prov = cfg.get("provider", "ollama")
        chat_url = cfg.get("base_url") or PROVIDER_DEFAULT_URLS.get(chat_prov, "http://localhost:11434")
        
        emb_prov = cfg.get("embedding_provider") or "ollama"
        emb_url = cfg.get("embedding_base_url") or PROVIDER_DEFAULT_URLS.get(emb_prov, "http://localhost:11434")
        emb_model = cfg.get("embedding_model") or "qwen3-embedding:0.6b"
        
        emb_key = cfg.get("embedding_api_key", "")
        masked_emb_key = f"{emb_key[:4]}...{emb_key[-4:]}" if len(emb_key) > 8 else ("***" if emb_key else "")

        return {
            "chat_engine": {
                "provider": chat_prov,
                "model_name": cfg.get("chat_model", "deepseek-r1:1.5b"),
                "base_url": chat_url,
                "api_key": cfg.get("masked_api_key", ""),
                "temperature": cfg.get("temperature", 0.4),
                "timeout_seconds": cfg.get("timeout_seconds", 30.0)
            },
            "embedding_engine": {
                "provider": emb_prov,
                "model_name": emb_model,
                "base_url": emb_url,
                "api_key": masked_emb_key
            },
            "version": cfg.get("version", 1),
            "updated_at": cfg.get("updated_at", "")
        }

    async def generate_embedding(self, text: str) -> List[float]:
        """使用独立配置的 Embedding 引擎生成高维文本向量特征（支持 Ollama 与云端 OpenAI 格式）。"""
        cfg = dict(self._config)
        prov = cfg.get("embedding_provider", "ollama")
        base_url = cfg.get("embedding_base_url") or PROVIDER_DEFAULT_URLS.get(prov, "http://localhost:11434")
        model = cfg.get("embedding_model", "qwen3-embedding:0.6b")
        api_key = cfg.get("embedding_api_key", "")

        if prov == "ollama":
            url = f"{base_url.rstrip('/')}/api/embeddings"
            payload = {"model": model, "prompt": text}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json().get("embedding", [])
                raise RuntimeError(f"Ollama embedding failed with HTTP {resp.status_code}")
        else:
            url = f"{base_url.rstrip('/')}/v1/embeddings" if not base_url.endswith("/embeddings") else base_url
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            payload = {"model": model, "input": text}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("data", [{}])[0].get("embedding", [])
                raise RuntimeError(f"Cloud embedding failed with HTTP {resp.status_code}")

    def get_health_status(self) -> Dict[str, Any]:
        """返回网关健康指标、遥测数据与断路器当前状态（供管理中台顶栏呼吸灯与大屏展示）。"""
        cb_status = self.circuit_breaker.get_status()
        state = cb_status["state"]
        if state == CircuitBreaker.CLOSED:
            overall_status = "healthy"
        elif state == CircuitBreaker.HALF_OPEN:
            overall_status = "degraded"
        else:
            overall_status = "down"

        return {
            "status": overall_status,
            "circuit_state": state,
            "active_provider": self._config.get("provider", "ollama"),
            "active_model": self._config.get("chat_model", "deepseek-r1:1.5b"),
            "base_url": self._config.get("base_url", "http://localhost:11434"),
            "consecutive_failures": cb_status["consecutive_failures"],
            "recovery_countdown_seconds": cb_status["recovery_countdown_seconds"],
            "uptime_seconds": int(time.time() - self._start_time)
        }

    @traceable(
        name="CinemaAgent-LLMGateway-StreamChat",
        run_type="llm",
        metadata={"platform": "CinemaAgent", "engine": "Dual-LLM-Mesh"}
    )
    async def stream_chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        全平台统一大模型流式推理调度总入口 (SSE 格式生成流)。
        
        【调用来源（从前端一路追踪到此）】：
        1. 前端 PlayerView.vue 伴聊 -> POST /api/v1/agent/chat-stream -> agent_service.chat_stream()
        2. RAG 在线调度流水线 -> rag_pipeline.query_stream()
        3. 最终统一进入本方法发起大模型流式调用。
        
        【入参大白话详解】：
        - prompt (str): 组装完毕的完整提示词（包含当前剧情切片、台词时间戳、防剧透指示与用户提问）。
        - system_prompt (Optional[str]): 角色设定与系统人设（如：“你是短剧伴读 Agent...”）。
        - messages (Optional[List[Dict[str, str]]]): 历史会话上下文列表（多轮对话记录）。
        - temperature (Optional[float]): 采样温度（0.0~1.0），越低回答越严谨保守，越高越有创意。
        
        【Yields 生成事件大白话详解（前端按帧接收）】：
        1. {"type": "thought", "content": "..."}: 深度推理思维链（如 DeepSeek-R1 思考内容，前端折叠展示）；
        2. {"type": "token", "content": "..."}: 正文打字机增量字词，前端实时拼接到气泡中；
        3. {"type": "diagnostic", ...}: 熔断或网络异常时的透明诊断报告，前端直接友好提示。
        """
        start_ts = time.time()
        active_provider = self._config.get("provider", "ollama")
        active_model = self._config.get("chat_model", "deepseek-r1:1.5b")
        base_url = self._config.get("base_url", PROVIDER_DEFAULT_URLS.get(active_provider, "http://localhost:11434"))
        api_key = self._config.get("api_key", "")
        timeout_sec = float(self._config.get("timeout_seconds", 30.0))
        temp = temperature if temperature is not None else float(self._config.get("temperature", 0.4))

        # 步骤 1：令牌桶限流检查（防止用户高频连续点击打爆推理显存）
        allowed, wait_sec = await self.rate_limiter.acquire(1)
        if not allowed:
            diag = {
                "type": "diagnostic",
                "status": "RATE_LIMIT_EXCEEDED",
                "circuit_state": self.circuit_breaker.state,
                "provider": active_provider,
                "model": active_model,
                "base_url": base_url,
                "elapsed_ms": round((time.time() - start_ts) * 1000, 2),
                "retry_attempts": 0,
                "error_type": "RateLimitExceeded",
                "error_detail": f"Inference rate limit exceeded. Retry in {round(wait_sec, 1)}s.",
                "diagnostic_message": f"【系统高可用网关诊断】请求频率超过限制，已触发令牌桶保护机制，请在 {round(wait_sec, 1)} 秒后重试。",
                "recovery_countdown_seconds": round(wait_sec, 1)
            }
            yield diag
            return

        # 步骤 2：断路器状态核验（检查大模型是否处于跳闸熔断冷却期）
        can_run, cb_state, countdown = await self.circuit_breaker.can_execute()
        if not can_run:
            diag = {
                "type": "diagnostic",
                "status": "CIRCUIT_BREAKER_OPEN",
                "circuit_state": cb_state,
                "provider": active_provider,
                "model": active_model,
                "base_url": base_url,
                "elapsed_ms": round((time.time() - start_ts) * 1000, 2),
                "retry_attempts": 0,
                "error_type": "CircuitBreakerOpen",
                "error_detail": f"Circuit breaker OPEN due to consecutive failures: {self.circuit_breaker.last_failure_reason}",
                "diagnostic_message": (
                    f"【系统高可用网关诊断】大模型引擎 [{active_provider}: {active_model}] 连续异常，"
                    f"断路器已触发熔断保护 (Circuit State: OPEN)。"
                    f"系统将在 {round(countdown, 1)} 秒后尝试半开恢复。请检查模型服务或在管理后台切换引擎。"
                ),
                "recovery_countdown_seconds": round(countdown, 1)
            }
            yield diag
            return

        # 步骤 3：根据当前配置的提供商分发流式请求（结合 Tenacity 指数退避重试）
        attempts = 0
        try:
            if active_provider == "ollama":
                async for item in self._stream_ollama(
                    base_url=base_url,
                    model=active_model,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temp,
                    timeout_sec=timeout_sec
                ):
                    attempts = 1
                    yield item
            else:
                # 针对 DeepSeek、MiMo 与 OpenAI：采用兼容 OpenAI 标准的 Chat Completion SSE 流式格式
                async for item in self._stream_openai_compatible(
                    provider=active_provider,
                    base_url=base_url,
                    model=active_model,
                    api_key=api_key,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    messages=messages,
                    temperature=temp,
                    timeout_sec=timeout_sec
                ):
                    attempts = 1
                    yield item

            # 流式生成顺利完成，通知断路器记录一次成功（恢复正常合闸态）
            await self.circuit_breaker.record_success()

        except Exception as e:
            err_type = type(e).__name__
            err_msg = str(e)
            elapsed_ms = round((time.time() - start_ts) * 1000, 2)
            await self.circuit_breaker.record_failure(f"{err_type}: {err_msg}")

            diag = {
                "type": "diagnostic",
                "status": "MODEL_UNREACHABLE",
                "circuit_state": self.circuit_breaker.state,
                "provider": active_provider,
                "model": active_model,
                "base_url": base_url,
                "elapsed_ms": elapsed_ms,
                "retry_attempts": max(1, attempts),
                "error_type": err_type,
                "error_detail": err_msg,
                "diagnostic_message": (
                    f"【系统高可用网关诊断】调用大模型引擎 [{active_provider}: {active_model}] 失败 ({err_type})。"
                    f"断路器当前状态: {self.circuit_breaker.state}。请检查服务地址 {base_url} 或鉴权密钥。"
                ),
                "recovery_countdown_seconds": self.circuit_breaker.recovery_timeout
            }
            yield diag

    async def _stream_ollama(
        self,
        base_url: str,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        timeout_sec: float
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """通过 Ollama 原生 /api/generate 接口建立流式长连接，并配置指数退避重试机制。"""
        url = f"{base_url.rstrip('/')}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": 1024
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        timeout_cfg = httpx.Timeout(connect=min(5.0, timeout_sec), read=timeout_sec, write=10.0, pool=10.0)

        # 针对网络连接中断与超时异常使用 Tenacity 执行指数退避重试
        retrying = AsyncRetrying(
            stop=stop_after_attempt(2),
            wait=wait_exponential(multiplier=0.3, min=0.3, max=1.5),
            retry=retry_if_exception_type((httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.RemoteProtocolError)),
            reraise=True
        )

        async def _open_stream():
            async for attempt in retrying:
                with attempt:
                    client = httpx.AsyncClient(timeout=timeout_cfg)
                    req = client.build_request("POST", url, json=payload)
                    resp = await client.send(req, stream=True)
                    if resp.status_code != 200:
                        body = await resp.aread()
                        await client.aclose()
                        raise httpx.HTTPStatusError(f"HTTP {resp.status_code}: {body.decode(errors='ignore')[:200]}", request=req, response=resp)
                    return client, resp

        client, resp = await _open_stream()
        try:
            async for raw_line in resp.aiter_lines():
                if not raw_line:
                    continue
                try:
                    data = json.loads(raw_line)
                    th = data.get("thinking", "")
                    tok = data.get("response", "")
                    if th:
                        yield {"type": "thought", "content": th}
                    if tok:
                        yield {"type": "token", "content": tok}
                    if data.get("done", False):
                        break
                except Exception:
                    continue
        finally:
            await resp.aclose()
            await client.aclose()

    async def _stream_openai_compatible(
        self,
        provider: str,
        base_url: str,
        model: str,
        api_key: str,
        prompt: str,
        system_prompt: Optional[str],
        messages: Optional[List[Dict[str, str]]],
        temperature: float,
        timeout_sec: float
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """通过兼容 OpenAI 的标准 /chat/completions 接口建立流式长连接（支持 DeepSeek-R1 思考链与小米 MiMo）。"""
        url = base_url.rstrip("/")
        if not url.endswith("/chat/completions"):
            if not url.endswith("/v1"):
                url = f"{url}/v1"
            url = f"{url}/chat/completions"

        headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        elif provider in ["deepseek", "openai"]:
            raise ValueError(f"Provider '{provider}' requires an API Key, but none was configured.")

        # 构造符合 OpenAI 标准的 messages 列表结构
        payload_messages: List[Dict[str, str]] = []
        if messages:
            payload_messages = list(messages)
        else:
            if system_prompt:
                payload_messages.append({"role": "system", "content": system_prompt})
            payload_messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": payload_messages,
            "temperature": temperature,
            "stream": True
        }

        timeout_cfg = httpx.Timeout(connect=min(5.0, timeout_sec), read=timeout_sec, write=10.0, pool=10.0)

        retrying = AsyncRetrying(
            stop=stop_after_attempt(2),
            wait=wait_exponential(multiplier=0.3, min=0.3, max=1.5),
            retry=retry_if_exception_type((httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.RemoteProtocolError)),
            reraise=True
        )

        async def _open_stream():
            async for attempt in retrying:
                with attempt:
                    client = httpx.AsyncClient(timeout=timeout_cfg)
                    req = client.build_request("POST", url, headers=headers, json=payload)
                    resp = await client.send(req, stream=True)
                    if resp.status_code not in [200, 201]:
                        body = await resp.aread()
                        await client.aclose()
                        raise httpx.HTTPStatusError(f"HTTP {resp.status_code}: {body.decode(errors='ignore')[:200]}", request=req, response=resp)
                    return client, resp

        client, resp = await _open_stream()
        try:
            async for raw_line in resp.aiter_lines():
                if not raw_line or not raw_line.startswith("data:"):
                    continue
                line_data = raw_line[5:].strip()
                if line_data == "[DONE]":
                    break
                try:
                    data = json.loads(line_data)
                    choice = data.get("choices", [{}])[0]
                    delta = choice.get("delta", {})
                    # 解析深度推理思考链（针对 DeepSeek-R1 的 reasoning_content 字段）
                    thought = delta.get("reasoning_content") or delta.get("thought", "")
                    token = delta.get("content", "")
                    if thought:
                        yield {"type": "thought", "content": thought}
                    if token:
                        yield {"type": "token", "content": token}
                except Exception:
                    continue
        finally:
            await resp.aclose()
            await client.aclose()

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Non-streaming single call.
        Returns:
            {
                "success": bool,
                "content": str,
                "thought": str,
                "diagnostic": Optional[dict]
            }
        """
        tokens: List[str] = []
        thoughts: List[str] = []
        diagnostic: Optional[Dict[str, Any]] = None

        async for item in self.stream_chat(prompt=prompt, system_prompt=system_prompt):
            itype = item.get("type")
            if itype == "token":
                tokens.append(item.get("content", ""))
            elif itype == "thought":
                thoughts.append(item.get("content", ""))
            elif itype == "diagnostic":
                diagnostic = item

        full_content = "".join(tokens)
        full_thought = "".join(thoughts)
        if diagnostic:
            return {
                "success": False,
                "content": diagnostic.get("diagnostic_message", "LLM inference unavailable"),
                "thought": full_thought,
                "diagnostic": diagnostic
            }

        return {
            "success": True,
            "content": full_content,
            "thought": full_thought,
            "diagnostic": None
        }


# 全局单例网关实例，供全站各模块直接导入使用
llm_gateway = LLMGateway()
