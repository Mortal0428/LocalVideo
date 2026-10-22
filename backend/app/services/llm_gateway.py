"""
LLM Gateway & Resilience Engine (CinemaAgent)
Unified singleton managing multi-provider LLM integrations (Ollama, DeepSeek-R1, MiMo, OpenAI)
with token bucket rate limiting, 3-state circuit breaker, Tenacity exponential backoff,
in-memory hot-reloading (<1ms), and transparent system diagnostics.
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

logger = logging.getLogger(__name__)

# Default seed configuration
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
    Token Bucket rate limiter for inference requests.
    Prevents concurrency overload with thread-safe lazy refill.
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
    3-State Circuit Breaker: CLOSED -> OPEN -> HALF-OPEN.
    - CLOSED: Normal operation. If consecutive failures >= threshold, switches to OPEN.
    - OPEN: Fail-fast (<1ms) without network calls. After recovery_timeout, switches to HALF-OPEN.
    - HALF-OPEN: Permits single probe call. Success -> CLOSED; Failure -> OPEN.
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

            # HALF-OPEN state: allow exactly 1 probe call; fail-fast block concurrent calls
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
                # If no record exists in DB, seed with default + env values
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
                    # Ignore masked api_key values from frontend forms
                    if k == "api_key" and isinstance(v, str) and ("..." in v or "***" in v):
                        continue
                    updated[k] = v

            # If base_url not specified, resolve provider default
            if not updated.get("base_url"):
                updated["base_url"] = PROVIDER_DEFAULT_URLS.get(updated.get("provider", "ollama"), "http://localhost:11434")

            # Atomic reference replacement (thread & coroutine safe pointer swap)
            self._config = updated

            # Sync back to settings for backward compatibility
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
        # Mask sensitive api_key if present
        if cfg.get("api_key"):
            k = str(cfg["api_key"])
            cfg["masked_api_key"] = f"{k[:4]}...{k[-4:]}" if len(k) > 8 else "***"
        else:
            cfg["masked_api_key"] = ""
        # Strictly ensure api_key is masked in the active config payload returned to callers
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
        """Generate embedding vector using the independently configured embedding engine."""
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
        """Return gateway status, telemetry and circuit metrics."""
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

    async def stream_chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream LLM inference response with token bucket rate limiting, circuit breaker,
        tenacity retries, and transparent diagnostics.
        Yields dicts with:
        - {"type": "thought", "content": "..."}
        - {"type": "token", "content": "..."}
        - {"type": "diagnostic", ...} on errors or circuit open
        """
        start_ts = time.time()
        active_provider = self._config.get("provider", "ollama")
        active_model = self._config.get("chat_model", "deepseek-r1:1.5b")
        base_url = self._config.get("base_url", PROVIDER_DEFAULT_URLS.get(active_provider, "http://localhost:11434"))
        api_key = self._config.get("api_key", "")
        timeout_sec = float(self._config.get("timeout_seconds", 30.0))
        temp = temperature if temperature is not None else float(self._config.get("temperature", 0.4))

        # 1. Rate Limiter Check (Token Bucket)
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

        # 2. Circuit Breaker Check (3-State)
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

        # 3. Stream Dispatch with Tenacity Retry
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
                # DeepSeek, MiMo, OpenAI: OpenAI Chat Completion SSE format
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

            # Record success on healthy stream completion
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
        """Stream from Ollama native /api/generate with tenacity retries."""
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

        # Retry with Tenacity on connect/timeout errors
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
        """Stream from DeepSeek, MiMo or OpenAI (/chat/completions) with tenacity retries."""
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

        # Build messages payload
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
                    # Check reasoning / thought (DeepSeek-R1 reasoning_content)
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


# Singleton instance
llm_gateway = LLMGateway()
