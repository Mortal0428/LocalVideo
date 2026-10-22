"""
Empirical Challenger Suite: Milestone 1 Iteration 2 Gate
Agent: challenger_m1_iter2_2
Location: backend/tests/test_challenger_m1_iter2_empirical.py

Tasks:
1. Probe GET /api/v1/models/engine-settings with adversarial unauthenticated and unauthorized requests
   (anonymous, spoofed tokens, USER role, forged signature, expired token) to confirm zero API key leakage.
2. Stress-test concurrent hot-reload (_apply_config / reload_config) under heavy parallel reads
   (50+ readers, 10+ reloaders) to confirm zero torn reads or corrupted states.
3. Query MySQL database table video_subtitle_timelines directly to verify 0 residual fake subtitles.
"""

import os
import sys
import time
import json
import asyncio
import threading
import concurrent.futures
from typing import List, Dict, Any
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

# Ensure backend root is on sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.core.database import SessionLocal
from app.models.user import User
from app.models.video import VideoSubtitleTimeline
from app.models.system_config import SystemConfig
from app.core.security import create_access_token, SECRET_KEY
from app.core.config import settings
from app.services.llm_gateway import llm_gateway, DEFAULT_GATEWAY_CONFIG, PROVIDER_DEFAULT_URLS
from main import app

CANARY_SECRET = "sk-prod-challenger-canary-secret-xyz-9876543210"

FORBIDDEN_SUBTITLE_KEYWORDS = [
    "三年隐忍", "退婚", "黑卡", "龙王", "懦夫", "动我兄弟者", "至尊", "赘婿"
]


# ==============================================================================
# Challenge 1: Adversarial Probing of GET /engine-settings for Key Leakage & RBAC
# ==============================================================================

def test_task1_adversarial_engine_settings_unauthorized_probes():
    """
    Test 1: Probe GET /api/v1/models/engine-settings with multiple adversarial unauthorized
    requests to confirm zero API key leakage.
    """
    client = TestClient(app)

    # Setup canary secret in active gateway configuration
    with llm_gateway._config_lock:
        llm_gateway._config["api_key"] = CANARY_SECRET

    # Retrieve or create test users for different roles
    with SessionLocal() as db:
        user_obj = db.query(User).filter(User.role == "USER").first()
        if not user_obj:
            user_obj = User(id="challenger_user_sub", username="user_c", email="user_c@test.com", hashed_password="h", role="USER")
            db.add(user_obj); db.commit(); db.refresh(user_obj)
        user_jwt = create_access_token({"sub": user_obj.id})

        creator_obj = db.query(User).filter(User.role == "CREATOR").first()
        if not creator_obj:
            creator_obj = User(id="challenger_creator_sub", username="creator_c", email="creator_c@test.com", hashed_password="h", role="CREATOR")
            db.add(creator_obj); db.commit(); db.refresh(creator_obj)
        creator_jwt = create_access_token({"sub": creator_obj.id})

        admin_obj = db.query(User).filter(User.role == "ADMIN").first()
        if not admin_obj:
            admin_obj = User(id="challenger_admin_sub", username="admin_c", email="admin_c@test.com", hashed_password="h", role="ADMIN")
            db.add(admin_obj); db.commit(); db.refresh(admin_obj)
        admin_jwt = create_access_token({"sub": admin_obj.id})

    # Prepare adversarial probes
    forged_token = jwt.encode({"sub": admin_obj.id, "exp": int(time.time()) + 3600}, "completely_wrong_secret", algorithm="HS256")
    expired_token = jwt.encode({"sub": admin_obj.id, "exp": int(time.time()) - 3600}, SECRET_KEY, algorithm="HS256")

    probes = [
        ("Probe 1: Completely Anonymous (no header)", {}, 401),
        ("Probe 2: Empty Bearer token", {"Authorization": "Bearer "}, 401),
        ("Probe 3: Random garbage Bearer token", {"Authorization": "Bearer gibberish_token_12345"}, 401),
        ("Probe 4: Basic auth spoofing attempt", {"Authorization": "Basic YWRtaW46YWRtaW4="}, 401),
        ("Probe 5: Forged signature JWT (wrong HMAC secret)", {"Authorization": f"Bearer {forged_token}"}, 401),
        ("Probe 6: Expired Admin JWT token", {"Authorization": f"Bearer {expired_token}"}, 401),
        ("Probe 7: Valid USER role token", {"Authorization": f"Bearer {user_jwt}"}, 403),
        ("Probe 8: Valid CREATOR role token", {"Authorization": f"Bearer {creator_jwt}"}, 403),
    ]

    for label, headers, expected_code in probes:
        resp = client.get("/api/v1/models/engine-settings", headers=headers)
        assert resp.status_code == expected_code, (
            f"{label} failed: expected HTTP {expected_code}, got {resp.status_code}. Response: {resp.text}"
        )
        # CRITICAL ASSERTION: The canary secret MUST NEVER appear in ANY response text
        assert CANARY_SECRET not in resp.text, (
            f"{label} CRITICAL SECURITY LEAK: Canary secret leaked in response body! {resp.text}"
        )
        assert "9876543210" not in resp.text, (
            f"{label} CRITICAL SECURITY LEAK: Partial canary leaked in response body!"
        )

    # Valid ADMIN request must succeed BUT masked
    admin_resp = client.get("/api/v1/models/engine-settings", headers={"Authorization": f"Bearer {admin_jwt}"})
    assert admin_resp.status_code == 200, f"Admin request failed: {admin_resp.text}"
    admin_data = admin_resp.json().get("data", {})
    assert CANARY_SECRET not in admin_resp.text, "Admin response leaked raw unmasked canary secret!"
    assert admin_data.get("api_key") == admin_data.get("masked_api_key")
    assert admin_data.get("api_key").startswith("sk-p...")
    assert admin_data.get("api_key").endswith("3210")
    assert "challenger-canary-secret" not in admin_data.get("api_key")


# ==============================================================================
# Challenge 2: Heavy Concurrency Stress Test on Hot-Reload (_apply_config)
# ==============================================================================

def test_task2_concurrent_hot_reload_under_heavy_parallel_reads():
    """
    Test 2: Stress-test concurrent hot-reload (_apply_config) under heavy parallel reads
    with 60 concurrent reader threads and 15 reloader threads performing hundreds of
    interleaved operations.
    Verifies:
    - Zero torn reads (snapshots are always 100% internally consistent).
    - Zero unhandled exceptions.
    - Zero corrupted states in rate limiter, circuit breaker, or config dict.
    """
    num_readers = 60
    num_reloaders = 15
    duration_seconds = 4.0

    stop_event = threading.Event()
    read_snapshots: List[Dict[str, Any]] = []
    errors: List[str] = []
    read_count = 0
    reload_count = 0
    stats_lock = threading.Lock()

    configurations_pool = [
        {
            "provider": "ollama",
            "chat_model": "deepseek-r1:1.5b",
            "embedding_model": "qwen3-embedding:0.6b",
            "base_url": "http://localhost:11434",
            "rate_limit_per_minute": 60,
            "timeout_seconds": 30.0,
            "temperature": 0.4,
            "version": 100
        },
        {
            "provider": "deepseek",
            "chat_model": "deepseek-chat",
            "embedding_model": "deepseek-embed",
            "base_url": "https://api.deepseek.com",
            "rate_limit_per_minute": 120,
            "timeout_seconds": 45.0,
            "temperature": 0.7,
            "version": 101
        },
        {
            "provider": "mimo",
            "chat_model": "mimo-v1",
            "embedding_model": "mimo-embed-v1",
            "base_url": "https://api.xiaomimimo.com/v1",
            "rate_limit_per_minute": 30,
            "timeout_seconds": 20.0,
            "temperature": 0.2,
            "version": 102
        },
        {
            "provider": "openai",
            "chat_model": "gpt-4o-mini",
            "embedding_model": "text-embedding-3-small",
            "base_url": "https://api.openai.com/v1",
            "rate_limit_per_minute": 150,
            "timeout_seconds": 60.0,
            "temperature": 0.5,
            "version": 103
        }
    ]

    def reader_worker(worker_id: int):
        nonlocal read_count
        local_reads = 0
        while not stop_event.is_set():
            try:
                # 1. Read active config
                cfg = llm_gateway.get_active_config()
                # 2. Read health status
                health = llm_gateway.get_health_status()
                # 3. Read rate limiter rate
                limiter_rate = llm_gateway.rate_limiter.rate_per_sec

                # Invariant checks for consistency
                provider = cfg.get("provider")
                base_url = cfg.get("base_url")
                expected_url = PROVIDER_DEFAULT_URLS.get(provider)
                if expected_url and base_url != expected_url:
                    errors.append(f"Torn read detected by reader {worker_id}: provider={provider} but base_url={base_url} (expected {expected_url})")

                if limiter_rate <= 0:
                    errors.append(f"Invalid rate limiter rate {limiter_rate} read by reader {worker_id}")

                if health.get("circuit_state") not in ["CLOSED", "OPEN", "HALF-OPEN"]:
                    errors.append(f"Corrupted circuit state {health.get('circuit_state')} read by reader {worker_id}")

                local_reads += 1
                time.sleep(0.001)  # small yield to maximize thread interleaving
            except Exception as e:
                errors.append(f"Reader {worker_id} crashed with exception: {type(e).__name__}: {e}")

        with stats_lock:
            read_count += local_reads

    def reloader_worker(worker_id: int):
        nonlocal reload_count
        local_reloads = 0
        idx = 0
        while not stop_event.is_set():
            try:
                new_cfg = configurations_pool[idx % len(configurations_pool)]
                llm_gateway.reload_config(new_config=new_cfg)
                local_reloads += 1
                idx += 1
                time.sleep(0.005)  # rapid reloads every 5ms
            except Exception as e:
                errors.append(f"Reloader {worker_id} crashed with exception: {type(e).__name__}: {e}")

        with stats_lock:
            reload_count += local_reloads

    threads: List[threading.Thread] = []
    # Spawn 60 reader threads
    for i in range(num_readers):
        t = threading.Thread(target=reader_worker, args=(i,))
        threads.append(t)
    # Spawn 15 reloader threads
    for j in range(num_reloaders):
        t = threading.Thread(target=reloader_worker, args=(j,))
        threads.append(t)

    # Start all threads simultaneously
    for t in threads:
        t.start()

    # Let them race under heavy load
    time.sleep(duration_seconds)
    stop_event.set()

    for t in threads:
        t.join(timeout=2.0)

    # Assertions
    print(f"\n[Stress Test Concurrency Metrics]")
    print(f"Total concurrent parallel reads completed: {read_count}")
    print(f"Total concurrent hot-reloads completed: {reload_count}")
    print(f"Total concurrency errors/torn reads detected: {len(errors)}")

    assert len(errors) == 0, f"Concurrency stress test failed with errors:\n" + "\n".join(errors[:10])
    assert read_count >= 1000, f"Expected at least 1000 parallel reads, but achieved {read_count}"
    assert reload_count >= 100, f"Expected at least 100 parallel reloads, but achieved {reload_count}"

    # Final post-stress health verification of LLMGateway
    final_cfg = llm_gateway.get_active_config()
    final_health = llm_gateway.get_health_status()
    assert final_health["status"] in ["healthy", "degraded"], f"Unhealthy status after stress: {final_health}"
    assert llm_gateway.rate_limiter.rate_per_sec > 0
    assert final_cfg["provider"] in ["ollama", "deepseek", "mimo", "openai"]

    # Restore default config
    llm_gateway.reload_config(new_config=DEFAULT_GATEWAY_CONFIG)


# ==============================================================================
# Challenge 3: Direct MySQL Database Clean State Audit
# ==============================================================================

def test_task3_mysql_video_subtitle_timelines_zero_fake_rows():
    """
    Test 3: Query MySQL database table video_subtitle_timelines directly to confirm 0 fake rows.
    Verifies:
    1. Table video_subtitle_timelines row count is exactly 0.
    2. Raw SQL SELECT query confirms row count is 0.
    3. Zero forbidden fake subtitle phrases exist in the database.
    """
    with SessionLocal() as db:
        # 1. ORM level count
        orm_count = db.query(VideoSubtitleTimeline).count()

        # 2. Raw SQL count
        raw_sql_result = db.execute(text("SELECT COUNT(*) FROM video_subtitle_timelines")).scalar()

        # 3. Fetch all rows if any
        rows = db.query(VideoSubtitleTimeline).all()

        # Check against all known fake phrases
        violation_records = []
        for r in rows:
            content = r.content or ""
            for kw in FORBIDDEN_SUBTITLE_KEYWORDS:
                if kw in content:
                    violation_records.append({"id": r.id, "keyword": kw, "content": content})

    print(f"\n[MySQL DB Audit Metrics]")
    print(f"ORM video_subtitle_timelines row count: {orm_count}")
    print(f"Raw SQL video_subtitle_timelines count: {raw_sql_result}")
    print(f"Forbidden subtitle violations detected: {len(violation_records)}")

    assert orm_count == 0, f"Database contamination: expected 0 rows in video_subtitle_timelines, found {orm_count}"
    assert raw_sql_result == 0, f"Database contamination: raw SQL found {raw_sql_result} rows"
    assert len(violation_records) == 0, f"Found forbidden fake phrases in database: {violation_records}"
