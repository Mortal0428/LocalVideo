"""
Empirical Adversarial Stress Harness for Milestone 1 (M1: LLM Gateway & Resilience)

Adversarially challenges:
1. Circuit Breaker fail-fast latency (<5ms when OPEN, zero network hangs, P50/P95/P99/Max metrics)
2. Token Bucket high-concurrency burst throttling (strict capacity enforcement, replenishment math, dynamic re-rate)
3. Transparent system diagnostics under connection refused / timeout / open circuit, with zero canned/mock strings
4. Global codebase + database deep scanner for 11+ mock/canned text patterns
5. High-concurrency hot-reload stress test (simultaneous concurrent reads and writes)
6. Circuit Breaker HALF-OPEN recovery and revert transitions
7. Pipeline precedence evaluation: Token Bucket vs. Circuit Breaker interaction
"""

import os
import sys
import time
import json
import pytest
import asyncio
from typing import Dict, Any, List

# Ensure backend root is on sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.core.database import SessionLocal, init_db
from app.models.system_config import SystemConfig
from app.services.llm_gateway import (
    llm_gateway,
    TokenBucketLimiter,
    CircuitBreaker,
    DEFAULT_GATEWAY_CONFIG
)


# =========================================================================
# 1. Circuit Breaker Fail-Fast & Latency Distribution Under OPEN State
# =========================================================================

def test_adversarial_circuit_breaker_fail_fast_benchmark():
    """
    Stress-test Circuit Breaker fail-fast latency across 500 requests in OPEN state.
    Requirement: Fail-fast must be strictly < 5.0ms per request (target < 1ms),
    with zero network calls, zero hangs, and structured diagnostic output.
    """
    async def _run():
        cb = llm_gateway.circuit_breaker
        cb.reset()

        # Temporarily provide sufficient token bucket capacity to isolate Circuit Breaker timing
        orig_tokens = llm_gateway.rate_limiter.tokens
        orig_cap = llm_gateway.rate_limiter.capacity
        llm_gateway.rate_limiter.tokens = 5000.0
        llm_gateway.rate_limiter.capacity = 5000.0

        try:
            # Force 3 failures to trigger OPEN state
            for i in range(3):
                await cb.record_failure(f"Adversarial mock failure {i+1}")

            assert cb.state == CircuitBreaker.OPEN, "Circuit breaker must be OPEN after 3 failures"

            # Execute 500 serial requests and measure precise latency
            latencies_ms: List[float] = []
            diagnostics_collected = 0

            for _ in range(500):
                t0 = time.perf_counter()
                events = []
                async for evt in llm_gateway.stream_chat(prompt="Adversarial stress test prompt"):
                    events.append(evt)
                elapsed_ms = (time.perf_counter() - t0) * 1000
                latencies_ms.append(elapsed_ms)

                assert len(events) == 1, f"Expected exactly 1 diagnostic event, got {len(events)}"
                evt = events[0]
                assert evt.get("type") == "diagnostic"
                assert evt.get("status") == "CIRCUIT_BREAKER_OPEN"
                assert evt.get("circuit_state") == "OPEN"
                assert evt.get("recovery_countdown_seconds") > 0.0
                diagnostics_collected += 1

            sorted_lat = sorted(latencies_ms)
            p50 = sorted_lat[int(len(sorted_lat) * 0.50)]
            p95 = sorted_lat[int(len(sorted_lat) * 0.95)]
            p99 = sorted_lat[int(len(sorted_lat) * 0.99)]
            max_lat = sorted_lat[-1]
            avg_lat = sum(sorted_lat) / len(sorted_lat)

            print(f"\n[Circuit Breaker Fail-Fast Benchmark (500 requests)]")
            print(f"  Avg: {avg_lat:.3f}ms | P50: {p50:.3f}ms | P95: {p95:.3f}ms | P99: {p99:.3f}ms | Max: {max_lat:.3f}ms")

            assert p99 < 5.0, f"P99 latency ({p99:.3f}ms) exceeded 5.0ms threshold!"
            assert max_lat < 10.0, f"Max latency ({max_lat:.3f}ms) exceeded 10.0ms threshold!"
            assert diagnostics_collected == 500

        finally:
            llm_gateway.rate_limiter.tokens = orig_tokens
            llm_gateway.rate_limiter.capacity = orig_cap
            cb.reset()

    asyncio.run(_run())


def test_adversarial_circuit_breaker_concurrent_fail_fast():
    """
    Stress-test Circuit Breaker fail-fast under 100 concurrent tasks hitting OPEN circuit.
    """
    async def _run():
        cb = llm_gateway.circuit_breaker
        cb.reset()

        orig_tokens = llm_gateway.rate_limiter.tokens
        orig_cap = llm_gateway.rate_limiter.capacity
        llm_gateway.rate_limiter.tokens = 1000.0
        llm_gateway.rate_limiter.capacity = 1000.0

        try:
            for i in range(3):
                await cb.record_failure(f"Adversarial mock failure {i+1}")
            assert cb.state == CircuitBreaker.OPEN

            async def _call_once():
                t0 = time.perf_counter()
                events = []
                async for evt in llm_gateway.stream_chat(prompt="Concurrent probe"):
                    events.append(evt)
                return (time.perf_counter() - t0) * 1000, events

            # Launch 100 concurrent requests simultaneously
            results = await asyncio.gather(*[_call_once() for _ in range(100)])

            assert len(results) == 100
            for elapsed_ms, events in results:
                assert len(events) == 1
                assert events[0].get("status") == "CIRCUIT_BREAKER_OPEN"
                assert elapsed_ms < 10.0, f"Concurrent fail-fast call took {elapsed_ms:.2f}ms"
        finally:
            llm_gateway.rate_limiter.tokens = orig_tokens
            llm_gateway.rate_limiter.capacity = orig_cap
            cb.reset()

    asyncio.run(_run())


# =========================================================================
# 2. Token Bucket Burst Concurrency & Throttling
# =========================================================================

def test_adversarial_token_bucket_burst_concurrency():
    """
    Test Token Bucket under instantaneous burst:
    Capacity = 10, Rate = 60/min (1 token/sec).
    Simultaneously fire 50 concurrent requests.
    Exactly 10 must succeed, exactly 40 must be throttled with wait_sec > 0.
    """
    async def _run():
        limiter = TokenBucketLimiter(rate_limit_per_minute=60, capacity=10)

        # Fire 50 simultaneous acquire requests
        tasks = [limiter.acquire(1) for _ in range(50)]
        results = await asyncio.gather(*tasks)

        allowed_count = sum(1 for allowed, _ in results if allowed)
        throttled_count = sum(1 for allowed, _ in results if not allowed)

        assert allowed_count == 10, f"Expected exactly 10 requests allowed, got {allowed_count}"
        assert throttled_count == 40, f"Expected exactly 40 requests throttled, got {throttled_count}"

        # Verify wait_sec for throttled requests is strictly positive
        for allowed, wait_sec in results:
            if not allowed:
                assert wait_sec > 0.0, "Throttled requests must report positive wait_sec"

        # Replenishment test: Wait 1.1s -> should replenish ~1.1 tokens
        await asyncio.sleep(1.1)
        allowed, wait_sec = await limiter.acquire(1)
        assert allowed is True, "After 1.1s replenishment, 1 token must be acquired"

        # Next acquire immediately after must fail
        allowed, wait_sec = await limiter.acquire(1)
        assert allowed is False, "Immediate second acquire must fail"

    asyncio.run(_run())


def test_adversarial_token_bucket_dynamic_update():
    """
    Test dynamic re-configuration of token bucket during operation.
    """
    async def _run():
        limiter = TokenBucketLimiter(rate_limit_per_minute=60, capacity=5)
        
        # Drain 5 tokens
        for _ in range(5):
            ok, _ = await limiter.acquire(1)
            assert ok is True

        # 6th fails
        ok, _ = await limiter.acquire(1)
        assert ok is False

        # Update rate to 120/min (capacity becomes max(10, 60) = 60)
        limiter.update_rate(120)
        assert limiter.rate_per_sec == 2.0
        assert limiter.capacity == 60.0

        # Wait 0.6s -> replenishes ~1.2 tokens
        await asyncio.sleep(0.6)
        ok, _ = await limiter.acquire(1)
        assert ok is True

    asyncio.run(_run())


def test_adversarial_pipeline_order_rate_limiter_precedes_circuit_breaker():
    """
    Adversarial verification of pipeline precedence:
    Token Bucket check precedes Circuit Breaker in stream_chat().
    When tokens are exhausted and Circuit is OPEN, requests receive RATE_LIMIT_EXCEEDED.
    """
    async def _run():
        cb = llm_gateway.circuit_breaker
        cb.reset()
        for i in range(3):
            await cb.record_failure(f"Failure {i+1}")
        assert cb.state == CircuitBreaker.OPEN

        # Drain token bucket and update last_refill
        llm_gateway.rate_limiter.tokens = 0.0
        llm_gateway.rate_limiter.last_refill = time.monotonic()

        events = []
        async for evt in llm_gateway.stream_chat(prompt="Precedence test"):
            events.append(evt)

        assert len(events) == 1
        assert events[0].get("status") == "RATE_LIMIT_EXCEEDED", (
            "Because RateLimiter is evaluated before CircuitBreaker, drained tokens trigger RATE_LIMIT_EXCEEDED."
        )

        cb.reset()
        llm_gateway.rate_limiter.tokens = float(llm_gateway.rate_limiter.capacity)

    asyncio.run(_run())


# =========================================================================
# 3. Transparent System Diagnostics & Zero Mock Strings
# =========================================================================

def test_adversarial_transparent_diagnostics_unreachable_endpoint():
    """
    Configure an unreachable base_url (port 59999).
    Verify gateway retries (Tenacity) and emits a structured diagnostic event.
    Verify ZERO canned fallback text in diagnostic output or generate() response.
    """
    async def _run():
        original_config = llm_gateway.get_active_config()
        cb = llm_gateway.circuit_breaker
        cb.reset()

        try:
            # Point to unreachable port
            llm_gateway._config["base_url"] = "http://127.0.0.1:59999"
            llm_gateway._config["timeout_seconds"] = 1.0

            t0 = time.perf_counter()
            res = await llm_gateway.generate(prompt="What is the meaning of life?")
            elapsed = time.perf_counter() - t0

            assert res["success"] is False, "Call to unreachable endpoint must fail"
            diag = res["diagnostic"]
            assert diag is not None
            assert diag["type"] == "diagnostic"
            assert diag["status"] == "MODEL_UNREACHABLE"
            assert "59999" in diag["base_url"]
            assert diag["retry_attempts"] >= 1
            assert "系统高可用网关诊断" in diag["diagnostic_message"]
            assert "ConnectError" in diag["error_type"] or "ConnectTimeout" in diag["error_type"] or "HTTP" in diag["error_type"]

            # Ensure content does not contain mock texts
            forbidden_canned = ["三年隐忍", "一纸退婚书", "至尊黑卡", "分析报告", "相遇在镜头"]
            for forbidden in forbidden_canned:
                assert forbidden not in res["content"]
                assert forbidden not in diag["diagnostic_message"]

        finally:
            # Restore configuration
            llm_gateway._apply_config(original_config)
            cb.reset()

    asyncio.run(_run())


def test_adversarial_deep_scan_database_for_fake_subtitles():
    """
    Adversarially scan MySQL database tables (video_subtitle_timelines, system_configs)
    to confirm zero fake text relics remain in the database.
    """
    from sqlalchemy import text
    with SessionLocal() as db:
        # Check video_subtitle_timelines (must exist and contain ZERO fake subtitles)
        rows = db.execute(text("SELECT id, content FROM video_subtitle_timelines")).fetchall()
        assert len(rows) == 0, f"Expected 0 residual subtitle rows in video_subtitle_timelines, found {len(rows)}"
        for row in rows:
            content = str(row[1]) if row[1] else ""
            assert "三年隐忍" not in content, f"DB Violation in video_subtitle_timelines id={row[0]}: {content}"
            assert "一纸退婚书" not in content, f"DB Violation in video_subtitle_timelines id={row[0]}: {content}"
            assert "至尊黑卡" not in content, f"DB Violation in video_subtitle_timelines id={row[0]}: {content}"
            assert "十万将士" not in content, f"DB Violation in video_subtitle_timelines id={row[0]}: {content}"
            assert "懦夫" not in content, f"DB Violation in video_subtitle_timelines id={row[0]}: {content}"
            assert "动我兄弟者" not in content, f"DB Violation in video_subtitle_timelines id={row[0]}: {content}"

        # Check system_configs
        configs = db.query(SystemConfig).all()
        for cfg in configs:
            val = str(cfg.config_value)
            assert "三年隐忍" not in val
            assert "至尊黑卡" not in val
            assert "一纸退婚书" not in val


# =========================================================================
# 4. High-Concurrency Hot-Reload Stress Test
# =========================================================================

def test_adversarial_concurrent_hot_reload_safety():
    """
    Stress-test thread/coroutine safety of hot-reload:
    - 50 reader tasks continuously calling get_active_config(), get_health_status()
    - 10 updater tasks continuously calling reload_config() with new values
    Verify zero crashes, zero KeyError/AttributeError, and final consistency.
    """
    async def _run():
        stop_event = asyncio.Event()
        read_counts = 0
        update_counts = 0
        errors: List[str] = []

        async def _reader():
            nonlocal read_counts
            while not stop_event.is_set():
                try:
                    cfg = llm_gateway.get_active_config()
                    assert "provider" in cfg
                    assert "chat_model" in cfg
                    health = llm_gateway.get_health_status()
                    assert "status" in health
                    assert "circuit_state" in health
                    read_counts += 1
                    await asyncio.sleep(0.001)
                except Exception as e:
                    errors.append(f"Reader error: {e}")

        async def _updater(idx: int):
            nonlocal update_counts
            models = ["deepseek-r1:1.5b", "qwen3.5:2b", "llama3.2:3b", "mistral:7b"]
            for i in range(20):
                try:
                    new_cfg = {
                        "provider": "ollama",
                        "chat_model": models[(idx + i) % len(models)],
                        "rate_limit_per_minute": 60 + i,
                        "version": 100 + idx * 20 + i
                    }
                    llm_gateway.reload_config(new_config=new_cfg)
                    update_counts += 1
                    await asyncio.sleep(0.002)
                except Exception as e:
                    errors.append(f"Updater error: {e}")

        # Launch 50 readers and 10 updaters
        readers = [asyncio.create_task(_reader()) for _ in range(50)]
        updaters = [asyncio.create_task(_updater(i)) for i in range(10)]

        await asyncio.gather(*updaters)
        stop_event.set()
        await asyncio.gather(*readers)

        assert len(errors) == 0, f"Concurrent hot-reload produced errors: {errors}"
        assert read_counts > 500, f"Expected >500 concurrent reads, got {read_counts}"
        assert update_counts == 200, f"Expected 200 updates, got {update_counts}"

        # Reset configuration to valid default
        llm_gateway.reload_config(new_config=DEFAULT_GATEWAY_CONFIG)

    asyncio.run(_run())


# =========================================================================
# 5. Circuit Breaker HALF-OPEN Recovery & Revert Transitions
# =========================================================================

def test_adversarial_circuit_breaker_half_open_lifecycle():
    """
    Verify complete transition cycle:
    CLOSED -> (3 failures) -> OPEN -> (recovery timeout) -> HALF-OPEN -> (failure) -> OPEN
    -> (recovery timeout) -> HALF-OPEN -> (success) -> CLOSED
    """
    async def _run():
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.15)
        assert cb.state == CircuitBreaker.CLOSED

        # 1. Trigger OPEN
        await cb.record_failure("Err 1")
        await cb.record_failure("Err 2")
        await cb.record_failure("Err 3")
        assert cb.state == CircuitBreaker.OPEN

        # 2. Check rejection in OPEN
        can, state, countdown = await cb.can_execute()
        assert can is False
        assert state == CircuitBreaker.OPEN
        assert countdown > 0

        # 3. Wait for recovery timeout (0.15s) -> transitions to HALF-OPEN on next can_execute
        await asyncio.sleep(0.18)
        can, state, countdown = await cb.can_execute()
        assert can is True
        assert state == CircuitBreaker.HALF_OPEN

        # 4. Probe fails in HALF-OPEN -> immediately reverts to OPEN
        await cb.record_failure("Probe failed")
        assert cb.state == CircuitBreaker.OPEN

        # 5. Wait for recovery timeout again
        await asyncio.sleep(0.18)
        can, state, countdown = await cb.can_execute()
        assert can is True
        assert state == CircuitBreaker.HALF_OPEN

        # 6. Probe succeeds in HALF-OPEN -> restores CLOSED
        await cb.record_success()
        assert cb.state == CircuitBreaker.CLOSED
        assert cb.consecutive_failures == 0

    asyncio.run(_run())


def test_adversarial_circuit_breaker_half_open_thundering_herd_guard():
    """
    Verify Circuit Breaker prevents thundering herd in HALF-OPEN state:
    When 20 concurrent coroutines hit HALF-OPEN, exactly 1 is allowed as probe,
    and 19 are fail-fast rejected.
    """
    async def _run():
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)
        await cb.record_failure("Failure 1")
        await cb.record_failure("Failure 2")
        assert cb.state == CircuitBreaker.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.06)

        # Launch 20 concurrent requests
        tasks = [cb.can_execute() for _ in range(20)]
        results = await asyncio.gather(*tasks)

        allowed_count = sum(1 for allowed, state, countdown in results if allowed)
        blocked_count = sum(1 for allowed, state, countdown in results if not allowed)

        assert allowed_count == 1, f"Expected exactly 1 probe allowed in HALF-OPEN, got {allowed_count}"
        assert blocked_count == 19, f"Expected exactly 19 blocked in HALF-OPEN, got {blocked_count}"

        # Complete probe with success
        await cb.record_success()
        assert cb.state == CircuitBreaker.CLOSED
        assert cb._probe_inflight is False

    asyncio.run(_run())


def test_adversarial_engine_settings_rbac_and_key_masking():
    """
    Verify security hole fix:
    - GET /api/v1/models/engine-settings requires ADMIN role (401 anonymous, 403 user, 200 admin).
    - Returned api_key is masked and never leaks raw key.
    """
    from fastapi.testclient import TestClient
    from main import app
    from app.models.user import User
    from app.core.security import create_access_token

    client = TestClient(app)

    # 1. Anonymous -> 401
    resp_anon = client.get("/api/v1/models/engine-settings")
    assert resp_anon.status_code == 401, f"Anonymous request must return 401, got {resp_anon.status_code}"

    # 2. Regular user -> 403
    with SessionLocal() as db:
        normal_user = db.query(User).filter(User.role == "USER").first()
        assert normal_user is not None
        user_token = create_access_token({"sub": normal_user.id})

        admin_user = db.query(User).filter(User.role == "ADMIN").first()
        assert admin_user is not None
        admin_token = create_access_token({"sub": admin_user.id})

    resp_user = client.get(
        "/api/v1/models/engine-settings",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert resp_user.status_code == 403, f"Regular USER must return 403, got {resp_user.status_code}"

    # 3. Admin user -> 200 with masked key
    resp_admin = client.get(
        "/api/v1/models/engine-settings",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp_admin.status_code == 200
    data = resp_admin.json()["data"]
    assert "api_key" in data
    assert "masked_api_key" in data
    assert data["api_key"] == data["masked_api_key"]
    # Check that it doesn't leak cleartext sk- prefix without masking
    if data["api_key"]:
        assert "..." in data["api_key"] or "***" in data["api_key"]
