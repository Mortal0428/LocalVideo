"""
Milestone 1 (M1: LLM Gateway & Resilience) Adversarial Challenge Test Suite
Empirical challenger instance: challenger_m1_2

Adversarial testing covers:
1. Multi-client concurrent requests against LLMGateway and TokenBucketLimiter.
2. Input validation and boundary probing on PUT /api/v1/models/engine-settings
   (non-existent providers, malformed types, negative numbers, RBAC permissions).
3. Circuit breaker state machine and recovery:
   CLOSED -> OPEN (fail-fast) -> HALF-OPEN (recovery probe) -> OPEN (probe fail) -> HALF-OPEN -> CLOSED (probe pass).
4. Truthful diagnostics and 100% elimination of canned fallback answers across all service disruption scenarios.
"""

import os
import sys
import time
import json
import asyncio
import pytest
from typing import List, Dict, Any

# Ensure backend root is on sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.core.database import SessionLocal, init_db
from app.models.user import User
from app.models.system_config import SystemConfig
from app.core.security import create_access_token
from app.services.llm_gateway import (
    llm_gateway,
    TokenBucketLimiter,
    CircuitBreaker,
    DEFAULT_GATEWAY_CONFIG
)
from app.services.agent_service import agent_service
from app.services.video_rag_service import video_rag_service
from fastapi.testclient import TestClient
from main import app

FORBIDDEN_SNIPPETS = [
    "三年隐忍，我低调归来",
    "一纸退婚书就是你的下场",
    "最高至尊黑卡",
    "本地模型离线兜底输出",
    "根据设定的行业规则与知识库切片，生成了符合商业标准的初版分析报告",
    "两位主角的初次登场相遇在镜头 [00:00 跳转]",
    "【视觉画面快照】在当前时间点",
    "【视觉感知辅助】画面特写聚集于核心冲突人物神情",
    "根据时间轴台词解构分析：本集冲突转折点位于 [00:25 跳转]，主角在此处低调隐忍",
    "已为您检索分集时间轴：主角在 [00:25 跳转] 现身",
    "十万将士恭迎龙王"
]


# ==============================================================================
# Challenge 1: Multi-Client Concurrent Requests & Token Bucket Limiter
# ==============================================================================

def test_challenge_token_bucket_high_concurrency_burst():
    """
    Stress-test TokenBucketLimiter under rapid high-concurrency burst.
    Verifies lock safety, exact token accounting, and lack of race conditions.
    """
    async def _run():
        capacity = 10
        limiter = TokenBucketLimiter(rate_limit_per_minute=60, capacity=capacity)
        
        # 50 concurrent tasks all trying to acquire 1 token at the exact same instant
        async def worker(task_id: int):
            allowed, wait_sec = await limiter.acquire(1)
            return {"id": task_id, "allowed": allowed, "wait_sec": wait_sec}

        tasks = [worker(i) for i in range(50)]
        results = await asyncio.gather(*tasks)

        allowed_results = [r for r in results if r["allowed"] is True]
        rejected_results = [r for r in results if r["allowed"] is False]

        # Exactly capacity (10) requests must succeed; remainder must be rate-limited
        assert len(allowed_results) == capacity, (
            f"Expected exactly {capacity} allowed tokens, but got {len(allowed_results)}"
        )
        assert len(rejected_results) == 40, (
            f"Expected exactly 40 rejected tokens, but got {len(rejected_results)}"
        )
        # Every rejected request must report a positive wait time
        for r in rejected_results:
            assert r["wait_sec"] > 0.0, f"Wait time should be positive, got {r['wait_sec']}"

    asyncio.run(_run())


def test_challenge_llm_gateway_concurrent_stream_rate_limit_rejection():
    """
    Verify that concurrent calls to LLMGateway.stream_chat() gracefully reject
    excess calls with structured RATE_LIMIT_EXCEEDED diagnostics and zero hanging.
    """
    async def _run():
        # Configure low capacity rate limiter: 3 tokens capacity, 0.1 tokens/sec refill
        llm_gateway.rate_limiter = TokenBucketLimiter(rate_limit_per_minute=6, capacity=3)
        llm_gateway.circuit_breaker.reset()

        async def call_gateway(idx: int):
            t0 = time.perf_counter()
            events = []
            async for ev in llm_gateway.stream_chat(prompt=f"concurrency test {idx}"):
                events.append(ev)
                break  # Evaluate initial admission/rejection event
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return {"id": idx, "events": events, "elapsed_ms": elapsed_ms}

        # Fire 10 concurrent requests
        tasks = [call_gateway(i) for i in range(10)]
        responses = await asyncio.gather(*tasks)

        rate_limited_count = 0
        allowed_count = 0
        for resp in responses:
            events = resp["events"]
            assert len(events) >= 1, "Gateway must emit at least one event per stream"
            first_event = events[0]
            if first_event.get("type") == "diagnostic" and first_event.get("status") == "RATE_LIMIT_EXCEEDED":
                rate_limited_count += 1
                # Rate limited requests must fail fast (< 50ms)
                assert resp["elapsed_ms"] < 50.0, f"Rate limited call should fail fast, took {resp['elapsed_ms']}ms"
                # Verify diagnostic content
                assert "令牌桶保护机制" in first_event.get("diagnostic_message", "")
                assert first_event.get("recovery_countdown_seconds", 0) > 0.0
            else:
                allowed_count += 1

        # Exactly 3 allowed (capacity), 7 rejected
        assert allowed_count == 3, f"Expected exactly 3 allowed calls, got {allowed_count}"
        assert rate_limited_count == 7, f"Expected exactly 7 rate limited calls, got {rate_limited_count}"

        # Reset limiter to normal defaults
        llm_gateway.rate_limiter = TokenBucketLimiter(rate_limit_per_minute=60)

    asyncio.run(_run())


def test_challenge_token_bucket_refill_accuracy():
    """
    Verify that token bucket refills accurately after sleep.
    """
    async def _run():
        # 60 tokens/min = 1 token/sec, capacity = 2
        limiter = TokenBucketLimiter(rate_limit_per_minute=60, capacity=2)
        # Drain 2 tokens
        assert (await limiter.acquire(1))[0] is True
        assert (await limiter.acquire(1))[0] is True
        assert (await limiter.acquire(1))[0] is False  # Empty

        # Sleep for 1.1 seconds -> refills ~1 token
        await asyncio.sleep(1.1)
        allowed, _ = await limiter.acquire(1)
        assert allowed is True, "Token bucket should have refilled 1 token after 1.1s"

        # Second immediate acquire should fail
        allowed, _ = await limiter.acquire(1)
        assert allowed is False, "Second immediate acquire should fail after single token consumed"

    asyncio.run(_run())


# ==============================================================================
# Challenge 2: Probing Input Validation on PUT /api/v1/models/engine-settings
# ==============================================================================

def test_challenge_engine_settings_nonexistent_provider():
    """
    Probe PUT /api/v1/models/engine-settings with invalid/nonexistent providers.
    Must return HTTP 400 Bad Request with strict rejection.
    """
    client = TestClient(app)
    with SessionLocal() as db:
        admin_user = db.query(User).filter(User.role == "ADMIN").first()
        token = create_access_token({"sub": admin_user.id})

    invalid_providers = ["anthropic", "baidu", "claude_v3", "custom_hack", "unknown_llm"]
    for prov in invalid_providers:
        resp = client.put(
            "/api/v1/models/engine-settings",
            headers={"Authorization": f"Bearer {token}"},
            json={"provider": prov}
        )
        assert resp.status_code == 400, f"Provider '{prov}' should return 400, got {resp.status_code}"
        assert "Invalid provider" in resp.json().get("detail", "")


def test_challenge_engine_settings_malformed_types():
    """
    Probe PUT /api/v1/models/engine-settings with malformed datatypes.
    FastAPI Pydantic must reject with HTTP 422 Unprocessable Content.
    """
    client = TestClient(app)
    with SessionLocal() as db:
        admin_user = db.query(User).filter(User.role == "ADMIN").first()
        token = create_access_token({"sub": admin_user.id})

    # String passed to integer field
    resp1 = client.put(
        "/api/v1/models/engine-settings",
        headers={"Authorization": f"Bearer {token}"},
        json={"rate_limit_per_minute": "unlimited"}
    )
    assert resp1.status_code == 422, f"Expected 422, got {resp1.status_code}"

    # Object passed to float field
    resp2 = client.put(
        "/api/v1/models/engine-settings",
        headers={"Authorization": f"Bearer {token}"},
        json={"timeout_seconds": {"invalid": "object"}}
    )
    assert resp2.status_code == 422, f"Expected 422, got {resp2.status_code}"


def test_challenge_engine_settings_negative_values_and_internal_defense():
    """
    Probe boundary inputs like negative rate limits and negative timeouts.
    Examines API boundary behavior and verifies LLMGateway's internal defensive clamping.
    """
    client = TestClient(app)
    with SessionLocal() as db:
        admin_user = db.query(User).filter(User.role == "ADMIN").first()
        token = create_access_token({"sub": admin_user.id})

    # Probing negative rate limit
    resp = client.put(
        "/api/v1/models/engine-settings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "provider": "ollama",
            "rate_limit_per_minute": -100
        }
    )
    # Check gateway internal defense: even if accepted or clamped,
    # TokenBucketLimiter must NOT produce a negative rate or NaN
    assert llm_gateway.rate_limiter.rate_per_sec >= 0.1
    assert llm_gateway.rate_limiter.capacity >= 10.0

    # Restore healthy settings
    client.put(
        "/api/v1/models/engine-settings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "provider": "ollama",
            "chat_model": "deepseek-r1:1.5b",
            "rate_limit_per_minute": 60,
            "timeout_seconds": 30.0,
            "temperature": 0.4
        }
    )


def test_challenge_engine_settings_rbac_permissions():
    """
    Verify RBAC security: only ADMIN role can update engine settings.
    Anonymous -> 401, USER role -> 403.
    """
    client = TestClient(app)
    
    # 1. Anonymous request
    r_anon = client.put(
        "/api/v1/models/engine-settings",
        json={"provider": "ollama"}
    )
    assert r_anon.status_code in [401, 403], f"Anonymous should be 401/403, got {r_anon.status_code}"

    # 2. Regular user request
    with SessionLocal() as db:
        normal_user = db.query(User).filter(User.role == "USER").first()
        if not normal_user:
            normal_user = User(
                id="challenger_normal_user_test",
                username="test_user_challenger",
                email="test_user_challenger@test.com",
                hashed_password="hash",
                role="USER"
            )
            db.add(normal_user)
            db.commit()
            db.refresh(normal_user)
        user_token = create_access_token({"sub": normal_user.id})

    r_user = client.put(
        "/api/v1/models/engine-settings",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"provider": "ollama"}
    )
    assert r_user.status_code == 403, f"Regular USER must be 403 Forbidden, got {r_user.status_code}"


# ==============================================================================
# Challenge 3: Circuit Breaker HALF-OPEN State Transitions & Recovery
# ==============================================================================

def test_challenge_circuit_breaker_full_lifecycle_and_half_open_probe():
    """
    Adversarial verification of the full 3-state CircuitBreaker lifecycle:
    1. CLOSED: Normal operation
    2. Consecutive failures threshold reached -> OPEN (fail-fast active)
    3. Recovery timeout expires -> transitions to HALF-OPEN on first call
    4. Probe fails in HALF-OPEN -> reverts back to OPEN with fresh timeout
    5. Recovery timeout expires again -> transitions to HALF-OPEN
    6. Probe succeeds in HALF-OPEN -> transitions to CLOSED and resets consecutive_failures to 0
    """
    async def _run():
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.3)
        cb.reset()
        assert cb.state == CircuitBreaker.CLOSED

        # Phase 1: CLOSED normal
        can_exec, state, _ = await cb.can_execute()
        assert can_exec is True and state == CircuitBreaker.CLOSED

        # Phase 2: Trigger OPEN
        await cb.record_failure("Err 1")
        assert cb.state == CircuitBreaker.CLOSED
        await cb.record_failure("Err 2")
        assert cb.state == CircuitBreaker.CLOSED
        await cb.record_failure("Err 3")
        assert cb.state == CircuitBreaker.OPEN
        assert cb.consecutive_failures == 3

        # Fast-fail check in OPEN
        t0 = time.perf_counter()
        can_exec, state, countdown = await cb.can_execute()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        assert can_exec is False
        assert state == CircuitBreaker.OPEN
        assert countdown > 0.0
        assert elapsed_ms < 1.0, f"Fail-fast in OPEN state must be <1ms, took {elapsed_ms:.3f}ms"

        # Phase 3: Wait recovery timeout (0.3s) -> HALF-OPEN
        await asyncio.sleep(0.35)
        can_exec, state, _ = await cb.can_execute()
        assert can_exec is True, "In HALF-OPEN, probe call should be allowed"
        assert state == CircuitBreaker.HALF_OPEN, f"Expected HALF-OPEN state, got {state}"
        assert cb.state == CircuitBreaker.HALF_OPEN

        # Phase 4: Probe FAILS in HALF-OPEN -> Must revert immediately to OPEN
        await cb.record_failure("Probe failed in HALF-OPEN")
        assert cb.state == CircuitBreaker.OPEN, "Failure in HALF-OPEN must revert state back to OPEN"
        can_exec, state, countdown = await cb.can_execute()
        assert can_exec is False
        assert state == CircuitBreaker.OPEN

        # Phase 5: Wait recovery timeout again -> transitions to HALF-OPEN again
        await asyncio.sleep(0.35)
        can_exec, state, _ = await cb.can_execute()
        assert can_exec is True
        assert state == CircuitBreaker.HALF_OPEN

        # Phase 6: Probe SUCCEEDS in HALF-OPEN -> Must transition to CLOSED
        await cb.record_success()
        assert cb.state == CircuitBreaker.CLOSED, "Success in HALF-OPEN must restore state to CLOSED"
        assert cb.consecutive_failures == 0

        # Normal requests proceed
        can_exec, state, _ = await cb.can_execute()
        assert can_exec is True
        assert state == CircuitBreaker.CLOSED

    asyncio.run(_run())


def test_challenge_circuit_breaker_telemetry_reporting():
    """
    Verify get_health_status() reports correct status during each circuit state:
    CLOSED -> healthy
    OPEN -> down
    HALF-OPEN -> degraded
    """
    async def _run():
        cb = llm_gateway.circuit_breaker
        cb.reset()

        # 1. CLOSED
        h1 = llm_gateway.get_health_status()
        assert h1["status"] == "healthy"
        assert h1["circuit_state"] == "CLOSED"

        # 2. OPEN
        await cb.record_failure("test 1")
        await cb.record_failure("test 2")
        await cb.record_failure("test 3")
        assert cb.state == CircuitBreaker.OPEN
        h2 = llm_gateway.get_health_status()
        assert h2["status"] == "down"
        assert h2["circuit_state"] == "OPEN"
        assert h2["recovery_countdown_seconds"] > 0

        # 3. Simulate transition to HALF-OPEN
        cb.state = CircuitBreaker.HALF_OPEN
        h3 = llm_gateway.get_health_status()
        assert h3["status"] == "degraded"
        assert h3["circuit_state"] == "HALF-OPEN"

        # Reset
        cb.reset()

    asyncio.run(_run())


# ==============================================================================
# Challenge 4: Rigorous Zero Fake Canned Answers Across All Disruption Paths
# ==============================================================================

def test_challenge_zero_canned_answers_under_all_disruptions():
    """
    Adversarial audit verifying absolute ZERO canned answers and ZERO fake plot lines
    under all possible simulated disruptions:
    - Path A: Circuit Breaker OPEN
    - Path B: Rate Limit Exceeded
    - Path C: Remote connection refused / offline server
    - Path D: Cloud provider missing API Key
    - Path E: Agent companion streaming under offline disruption
    - Path F: Video RAG service under offline disruption
    """
    async def _run():
        cb = llm_gateway.circuit_breaker

        # Path A: Circuit Breaker OPEN
        cb.reset()
        await cb.record_failure("Err 1")
        await cb.record_failure("Err 2")
        await cb.record_failure("Err 3")
        assert cb.state == CircuitBreaker.OPEN

        events_cb = []
        async for ev in llm_gateway.stream_chat(prompt="剧情解读分析"):
            events_cb.append(ev)

        for ev in events_cb:
            content_str = str(ev)
            for forbidden in FORBIDDEN_SNIPPETS:
                assert forbidden not in content_str, (
                    f"Disruption Path A violation: Found forbidden text '{forbidden}' in circuit OPEN response!"
                )
        assert events_cb[0]["type"] == "diagnostic"
        assert events_cb[0]["status"] == "CIRCUIT_BREAKER_OPEN"

        # Path B: Rate Limit Exceeded
        cb.reset()
        limiter = TokenBucketLimiter(rate_limit_per_minute=60, capacity=1)
        await limiter.acquire(1)  # Drain bucket
        llm_gateway.rate_limiter = limiter

        events_rl = []
        async for ev in llm_gateway.stream_chat(prompt="测试令牌桶限流"):
            events_rl.append(ev)

        for ev in events_rl:
            content_str = str(ev)
            for forbidden in FORBIDDEN_SNIPPETS:
                assert forbidden not in content_str, (
                    f"Disruption Path B violation: Found forbidden text '{forbidden}' in rate limit response!"
                )
        assert events_rl[0]["type"] == "diagnostic"
        assert events_rl[0]["status"] == "RATE_LIMIT_EXCEEDED"

        # Reset limiter
        llm_gateway.rate_limiter = TokenBucketLimiter(rate_limit_per_minute=60)

        # Path C: Remote connection refused / offline server
        cb.reset()
        llm_gateway._config["base_url"] = "http://127.0.0.1:59999"  # Non-existent port
        events_conn = []
        async for ev in llm_gateway.stream_chat(prompt="短剧高能解说"):
            events_conn.append(ev)

        for ev in events_conn:
            content_str = str(ev)
            for forbidden in FORBIDDEN_SNIPPETS:
                assert forbidden not in content_str, (
                    f"Disruption Path C violation: Found forbidden text '{forbidden}' in connection error response!"
                )
        assert any(ev.get("type") == "diagnostic" for ev in events_conn)

        # Path D: Cloud provider missing API Key
        cb.reset()
        llm_gateway._config["provider"] = "deepseek"
        llm_gateway._config["chat_model"] = "deepseek-chat"
        llm_gateway._config["api_key"] = ""
        events_key = []
        async for ev in llm_gateway.stream_chat(prompt="测试缺失密钥"):
            events_key.append(ev)

        for ev in events_key:
            content_str = str(ev)
            for forbidden in FORBIDDEN_SNIPPETS:
                assert forbidden not in content_str, (
                    f"Disruption Path D violation: Found forbidden text '{forbidden}' in missing key response!"
                )
        assert any(ev.get("type") == "diagnostic" for ev in events_key)

        # Restore default config
        llm_gateway._config["provider"] = "ollama"
        llm_gateway._config["chat_model"] = "deepseek-r1:1.5b"
        llm_gateway._config["base_url"] = "http://localhost:11434"
        cb.reset()

        # Path E: agent_service.chat_stream() under offline disruption
        cb.reset()
        await cb.record_failure("Simulated offline 1")
        await cb.record_failure("Simulated offline 2")
        await cb.record_failure("Simulated offline 3")
        assert cb.state == CircuitBreaker.OPEN

        with SessionLocal() as db:
            agent_sse_events = []
            async for sse_chunk in agent_service.chat_stream(
                db=db,
                episode_id="default",
                question="男主角什么时候出现？",
                current_video_time=10.0
            ):
                agent_sse_events.append(sse_chunk)

        full_agent_stream = "".join(agent_sse_events)
        for forbidden in FORBIDDEN_SNIPPETS:
            assert forbidden not in full_agent_stream, (
                f"Disruption Path E violation: Found forbidden text '{forbidden}' in agent_service stream!"
            )
        # Must contain transparent diagnostic information
        assert "系统高可用网关诊断" in full_agent_stream or "CIRCUIT_BREAKER_OPEN" in full_agent_stream

        # Path F: video_rag_service.generate_companion_answer() under offline disruption
        rag_result = await video_rag_service.generate_companion_answer(
            episode_id="default",
            question="这一集最精彩的高潮在哪里？",
            current_video_time=12.0
        )
        answer_text = rag_result.get("answer", "")
        for forbidden in FORBIDDEN_SNIPPETS:
            assert forbidden not in answer_text, (
                f"Disruption Path F violation: Found forbidden text '{forbidden}' in video_rag_service answer!"
            )
        # In offline state, video_rag_service should carry the diagnostic text, not fake answers
        assert "系统高可用网关诊断" in answer_text or "熔断保护" in answer_text

        # Final cleanup: reset circuit breaker
        cb.reset()

    asyncio.run(_run())
