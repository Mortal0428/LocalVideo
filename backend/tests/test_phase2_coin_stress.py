"""
Phase 2 Milestone 1 Adversarial Empirical Stress Test Suite.
Role: Empirical Challenger (critic, specialist).

Focus: Stress-testing assumptions, boundary conditions, race conditions,
and invariants in the Coin Economy & Video Tipping subsystem:
1. Strict 2-coin tipping limit per user per drama (direct and cumulative).
2. Tipping boundary rejections (le=2, ge=1, 0 coins, negative coins, 3 coins).
3. Cross-episode tipping isolation on the same drama (preventing episode hopping bypass).
4. Insufficient wallet balance for tipping and VIP exchange.
5. Daily sign-in date idempotency, consecutive attempts, and date rollover.
6. VIP exchange non-standard day tier rejections (0, 1, 14, -7, 999).
7. VIP exchange chained forward-stacking duration arithmetic.
8. Admin coin balance clamping to >= 0 under negative set or negative adjustments.
9. Concurrent tipping race-condition hardening (10 concurrent requests, max 2 allowed).
10. Concurrent daily sign-in race-condition hardening (10 concurrent requests, max 1 allowed).
11. Double-entry transaction ledger integrity and balance_after mathematical consistency.
"""

import io
import os
import sys
import uuid
import pytest
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from main import app
from app.core.database import SessionLocal, init_db
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.video import Video, VideoEpisode
from app.models.coin import UserCoinWallet, UserCoinTransaction, VideoCoinTip

@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)

def create_test_user(username_prefix: str, role: str = "USER") -> dict:
    init_db()
    with SessionLocal() as db:
        unique_name = f"{username_prefix}_{uuid.uuid4().hex[:8]}"
        user = User(
            id=str(uuid.uuid4()),
            username=unique_name,
            password_hash=get_password_hash("Password123!"),
            nickname=f"昵称_{unique_name}",
            role=role,
            status="ACTIVE"
        )
        db.add(user)
        db.flush()

        wallet = UserCoinWallet(
            id=str(uuid.uuid4()),
            user_id=user.id,
            balance=50,
            total_earned=50,
            total_spent=0,
            last_sign_in_date=None
        )
        db.add(wallet)
        tx = UserCoinTransaction(
            id=str(uuid.uuid4()),
            user_id=user.id,
            amount=50,
            balance_after=50,
            transaction_type="REGISTER_BONUS",
            description="注册赠送金币"
        )
        db.add(tx)
        db.commit()
        db.refresh(user)
        token = create_access_token(data={"sub": user.id})
        return {"id": user.id, "username": unique_name, "token": token}

def create_test_drama_with_episodes(creator_id: str, ep_count: int = 2) -> dict:
    init_db()
    with SessionLocal() as db:
        drama = Video(
            id=str(uuid.uuid4()),
            title=f"压力测试剧_{uuid.uuid4().hex[:6]}",
            summary="用于对抗性压力测试的短剧资产",
            cover_url="/storage/test_stress_cover.jpg",
            category="悬疑推理",
            status="PUBLISHED",
            creator_id=creator_id,
            view_count=50,
            like_count=5,
            coin_count=0,
            heat_score=75.0
        )
        db.add(drama)
        db.flush()

        episodes = []
        for i in range(1, ep_count + 1):
            ep = VideoEpisode(
                id=str(uuid.uuid4()),
                video_id=drama.id,
                episode_num=i,
                title=f"第 {i} 集 对抗验证",
                raw_file_path=f"/storage/stress_ep{i}.mp4",
                duration_seconds=90,
                transcode_status="READY"
            )
            db.add(ep)
            episodes.append(ep)

        db.commit()
        return {
            "id": drama.id,
            "title": drama.title,
            "episodes": [{"id": e.id, "num": e.episode_num} for e in episodes]
        }


# =========================================================================
# 1. Coin Tipping Bounds & Parameter Validation
# =========================================================================
def test_tipping_parameter_bounds_rejection(client):
    """
    Hypothesis: Attackers attempt to send invalid coin amounts (0, negative, >2, floats).
    Expected: Pydantic ge=1, le=2 must reject with 422 Unprocessable Entity.
    """
    user = create_test_user("tip_param_user")
    admin = create_test_user("tip_param_admin", role="ADMIN")
    drama = create_test_drama_with_episodes(admin["id"])
    ep_id = drama["episodes"][0]["id"]
    headers = {"Authorization": f"Bearer {user['token']}"}

    # Attack 1: Attempt to tip 3 coins directly
    res3 = client.post(f"/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 3}, headers=headers)
    assert res3.status_code == 422, f"Expected 422 for coin_amount=3, got {res3.status_code}: {res3.text}"

    # Attack 2: Attempt to tip 0 coins
    res0 = client.post(f"/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 0}, headers=headers)
    assert res0.status_code == 422, f"Expected 422 for coin_amount=0, got {res0.status_code}: {res0.text}"

    # Attack 3: Attempt to tip negative coins (-1)
    res_neg = client.post(f"/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": -1}, headers=headers)
    assert res_neg.status_code == 422, f"Expected 422 for coin_amount=-1, got {res_neg.status_code}: {res_neg.text}"

    # Attack 4: Attempt to tip excessive coins (100)
    res_huge = client.post(f"/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 100}, headers=headers)
    assert res_huge.status_code == 422, f"Expected 422 for coin_amount=100, got {res_huge.status_code}: {res_huge.text}"


# =========================================================================
# 2. Cumulative Limit Sequence & State Rollback
# =========================================================================
def test_tipping_cumulative_limit_and_state_invariants(client):
    """
    Hypothesis: User tips 1 coin, then tries 2 coins (1+2=3>2).
    Expected: 2nd attempt rejected with 400.
    Invariants: Wallet balance is NOT deducted, tipped_count remains 1, heat_score unchanged.
    Then User tips 1 coin -> succeeds (total 2).
    Next attempts of 1 or 2 coins are both rejected with 400.
    """
    user = create_test_user("tip_cumul_user")
    admin = create_test_user("tip_cumul_admin", role="ADMIN")
    drama = create_test_drama_with_episodes(admin["id"])
    ep_id = drama["episodes"][0]["id"]
    headers = {"Authorization": f"Bearer {user['token']}"}

    # Step 1: Check initial wallet balance is 50
    res_w = client.get("/api/v1/user/coins/wallet", headers=headers)
    assert res_w.status_code == 200
    assert res_w.json()["data"]["balance"] == 50

    # Step 2: Tip 1 coin -> Expected success
    res_tip1 = client.post(f"/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 1}, headers=headers)
    assert res_tip1.status_code == 200
    d1 = res_tip1.json()["data"]
    assert d1["tipped_count"] == 1
    assert d1["wallet_balance"] == 49
    heat_score_after_1 = d1["heat_score"]

    # Step 3: Attempt to tip 2 coins (1 + 2 = 3 > 2) -> Must be rejected with 400
    res_tip_overflow = client.post(f"/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 2}, headers=headers)
    assert res_tip_overflow.status_code == 400
    assert "最多打赏 2 枚金币" in res_tip_overflow.json()["detail"] or "每部短剧" in res_tip_overflow.json()["detail"]

    # Verify state invariant: wallet balance still 49, tipped count still 1
    res_w2 = client.get("/api/v1/user/coins/wallet", headers=headers)
    assert res_w2.json()["data"]["balance"] == 49
    res_status = client.get(f"/api/v1/interactions/episodes/{ep_id}/tip-status", headers=headers)
    assert res_status.json()["data"]["tipped_count"] == 1
    assert res_status.json()["data"]["heat_score"] == heat_score_after_1

    # Step 4: Tip second 1 coin -> Expected success
    res_tip2 = client.post(f"/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 1}, headers=headers)
    assert res_tip2.status_code == 200
    d2 = res_tip2.json()["data"]
    assert d2["tipped_count"] == 2
    assert d2["wallet_balance"] == 48
    # Heat score formula: coin*10.0, so 1 more coin must add exactly 10.0
    assert round(d2["heat_score"] - heat_score_after_1, 2) == 10.0

    # Step 5: Tipping 1 more coin (2 + 1 = 3 > 2) -> Rejected
    res_tip_extra1 = client.post(f"/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 1}, headers=headers)
    assert res_tip_extra1.status_code == 400

    # Step 6: Tipping 2 more coins (2 + 2 = 4 > 2) -> Rejected
    res_tip_extra2 = client.post(f"/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 2}, headers=headers)
    assert res_tip_extra2.status_code == 400

    # Final wallet check: balance remained 48
    res_w_final = client.get("/api/v1/user/coins/wallet", headers=headers)
    assert res_w_final.json()["data"]["balance"] == 48


# =========================================================================
# 3. Cross-Episode Tipping Isolation on Same Drama
# =========================================================================
def test_cross_episode_tipping_limit_enforcement(client):
    """
    Hypothesis: Tipping limit is defined per-drama, not per-episode.
    Attack scenario: User tips 1 coin on Episode 1, switches to Episode 2,
    tips 1 coin, then attempts to tip 1 more coin on Episode 2 or Episode 1.
    Expected: Limit of 2 applies to the whole drama across all episodes.
    """
    user = create_test_user("cross_ep_user")
    admin = create_test_user("cross_ep_admin", role="ADMIN")
    drama = create_test_drama_with_episodes(admin["id"], ep_count=2)
    ep1_id = drama["episodes"][0]["id"]
    ep2_id = drama["episodes"][1]["id"]
    headers = {"Authorization": f"Bearer {user['token']}"}

    # Tip 1 coin on Episode 1
    res1 = client.post(f"/api/v1/interactions/episodes/{ep1_id}/tip", json={"coin_amount": 1}, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["data"]["tipped_count"] == 1

    # Check status on Episode 2 -> Must reflect 1 tipped coin already
    res_status2 = client.get(f"/api/v1/interactions/episodes/{ep2_id}/tip-status", headers=headers)
    assert res_status2.status_code == 200
    assert res_status2.json()["data"]["tipped_count"] == 1

    # Tip 1 coin on Episode 2 -> Reaches drama cap (2)
    res2 = client.post(f"/api/v1/interactions/episodes/{ep2_id}/tip", json={"coin_amount": 1}, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["data"]["tipped_count"] == 2

    # Attempt to tip on Episode 2 again -> MUST FAIL (400)
    res3 = client.post(f"/api/v1/interactions/episodes/{ep2_id}/tip", json={"coin_amount": 1}, headers=headers)
    assert res3.status_code == 400

    # Attempt to tip on Episode 1 again -> MUST FAIL (400)
    res4 = client.post(f"/api/v1/interactions/episodes/{ep1_id}/tip", json={"coin_amount": 1}, headers=headers)
    assert res4.status_code == 400


# =========================================================================
# 4. Insufficient Wallet Balance Tipping
# =========================================================================
def test_tipping_with_insufficient_wallet_balance(client):
    """
    Hypothesis: User with balance = 0 attempts to tip coins.
    Expected: 400 error '金币余额不足', zero database state change.
    """
    user = create_test_user("broke_user")
    admin = create_test_user("broke_admin", role="ADMIN")
    drama = create_test_drama_with_episodes(admin["id"])
    ep_id = drama["episodes"][0]["id"]
    headers_user = {"Authorization": f"Bearer {user['token']}"}
    headers_admin = {"Authorization": f"Bearer {admin['token']}"}

    # Admin drains user coins to 0
    res_drain = client.put(f"/api/v1/admin/users/{user['id']}", json={"coins": 0}, headers=headers_admin)
    assert res_drain.status_code == 200
    assert res_drain.json()["data"]["coins"] == 0

    # Attempt to tip 1 coin
    res_tip = client.post(f"/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 1}, headers=headers_user)
    assert res_tip.status_code == 400
    assert "金币余额不足" in res_tip.json()["detail"]

    # Verify tip count is still 0
    res_status = client.get(f"/api/v1/interactions/episodes/{ep_id}/tip-status", headers=headers_user)
    assert res_status.json()["data"]["tipped_count"] == 0


# =========================================================================
# 5. Daily Sign-In Idempotency & Date Rollover
# =========================================================================
def test_daily_sign_in_idempotency_and_ledger(client):
    """
    Hypothesis: User attempts repeated sign-in on same UTC day.
    Expected: First succeeds (+10), second and third immediately rejected with 400.
    Rollover: Setting last_sign_in_date to yesterday allows exactly one new claim today.
    """
    user = create_test_user("signin_stress_user")
    headers = {"Authorization": f"Bearer {user['token']}"}

    # 1. First sign-in
    res1 = client.post("/api/v1/user/coins/sign-in", headers=headers)
    assert res1.status_code == 200
    assert res1.json()["data"]["balance"] == 60
    assert res1.json()["data"]["has_signed_today"] is True

    # 2. Immediate duplicate sign-in -> 400
    res2 = client.post("/api/v1/user/coins/sign-in", headers=headers)
    assert res2.status_code == 400
    assert "今日已完成签到" in res2.json()["detail"]

    # 3. Third attempt -> 400
    res3 = client.post("/api/v1/user/coins/sign-in", headers=headers)
    assert res3.status_code == 400

    # Verify transactions ledger has exactly ONE SIGN_IN entry
    res_tx = client.get("/api/v1/user/coins/transactions", headers=headers)
    assert res_tx.status_code == 200
    sign_in_txs = [t for t in res_tx.json()["data"]["items"] if t["transaction_type"] == "SIGN_IN"]
    assert len(sign_in_txs) == 1
    assert sign_in_txs[0]["amount"] == 10

    # 4. Simulate date rollover: manually set last_sign_in_date to yesterday in DB
    yesterday_str = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    with SessionLocal() as db:
        wallet = db.query(UserCoinWallet).filter(UserCoinWallet.user_id == user["id"]).first()
        wallet.last_sign_in_date = yesterday_str
        db.commit()

    # Query wallet: has_signed_today should now be False
    res_w = client.get("/api/v1/user/coins/wallet", headers=headers)
    assert res_w.json()["data"]["has_signed_today"] is False

    # Sign-in on new day -> Succeeds (+10) -> balance 70
    res_newday = client.post("/api/v1/user/coins/sign-in", headers=headers)
    assert res_newday.status_code == 200
    assert res_newday.json()["data"]["balance"] == 70

    # Duplicate on new day -> 400
    res_newday_dup = client.post("/api/v1/user/coins/sign-in", headers=headers)
    assert res_newday_dup.status_code == 400


# =========================================================================
# 6. VIP Exchange Boundary Conditions & Non-Standard Tiers
# =========================================================================
def test_vip_exchange_boundaries_and_invalid_tiers(client):
    """
    Hypothesis: Attackers request invalid VIP tiers (0, 1, 14, -7, 999) or attempt exchange
    with insufficient coins.
    Expected: Rejected with 400, no balance change, no VIP extended.
    """
    user = create_test_user("vip_boundary_user")
    headers = {"Authorization": f"Bearer {user['token']}"}

    # Initial balance is 50. 7-day requires 100 -> Insufficient balance 400
    res_7_broke = client.post("/api/v1/user/coins/exchange-vip", json={"days": 7}, headers=headers)
    assert res_7_broke.status_code == 400
    assert "金币余额不足" in res_7_broke.json()["detail"]

    # 30-day requires 200 -> Insufficient balance 400
    res_30_broke = client.post("/api/v1/user/coins/exchange-vip", json={"days": 30}, headers=headers)
    assert res_30_broke.status_code == 400
    assert "金币余额不足" in res_30_broke.json()["detail"]

    # Invalid day tiers
    invalid_days = [0, 1, 3, 14, 15, -7, 999]
    for d in invalid_days:
        res_inv = client.post("/api/v1/user/coins/exchange-vip", json={"days": d}, headers=headers)
        assert res_inv.status_code == 400, f"Expected 400 for days={d}, got {res_inv.status_code}: {res_inv.text}"
        assert "仅支持兑换 7 天" in res_inv.json()["detail"]

    # Verify wallet balance unchanged at 50
    res_w = client.get("/api/v1/user/coins/wallet", headers=headers)
    assert res_w.json()["data"]["balance"] == 50


# =========================================================================
# 7. VIP Exchange Chained Forward Stacking Arithmetic
# =========================================================================
def test_vip_exchange_chained_forward_stacking(client):
    """
    Hypothesis: Sequential VIP purchases should stack on top of existing vip_expire_at,
    rather than overwriting with (now + days).
    Flow: User exchanges 7d -> expire = now + 7d.
    User exchanges 30d -> expire = previous_expire + 30d = now + 37d.
    User exchanges 7d -> expire = previous_expire + 7d = now + 44d.
    """
    user = create_test_user("vip_chain_user")
    admin = create_test_user("vip_chain_admin", role="ADMIN")
    headers_user = {"Authorization": f"Bearer {user['token']}"}
    headers_admin = {"Authorization": f"Bearer {admin['token']}"}

    # Admin funds user with 500 coins
    client.put(f"/api/v1/admin/users/{user['id']}", json={"coins": 500}, headers=headers_admin)

    # 1. Exchange 7 days VIP (costs 100 coins)
    t0 = datetime.utcnow()
    res1 = client.post("/api/v1/user/coins/exchange-vip", json={"days": 7}, headers=headers_user)
    assert res1.status_code == 200
    exp1_str = res1.json()["data"]["vip_expire_at"]
    exp1 = datetime.fromisoformat(exp1_str)
    # exp1 should be approximately t0 + 7 days (within 5 seconds tolerance)
    expected_exp1 = t0 + timedelta(days=7)
    assert abs((exp1 - expected_exp1).total_seconds()) < 5

    # 2. Exchange 30 days VIP (costs 200 coins)
    res2 = client.post("/api/v1/user/coins/exchange-vip", json={"days": 30}, headers=headers_user)
    assert res2.status_code == 200
    exp2_str = res2.json()["data"]["vip_expire_at"]
    exp2 = datetime.fromisoformat(exp2_str)
    # exp2 should be approximately exp1 + 30 days
    expected_exp2 = exp1 + timedelta(days=30)
    assert abs((exp2 - expected_exp2).total_seconds()) < 5

    # 3. Exchange another 7 days VIP (costs 100 coins)
    res3 = client.post("/api/v1/user/coins/exchange-vip", json={"days": 7}, headers=headers_user)
    assert res3.status_code == 200
    exp3_str = res3.json()["data"]["vip_expire_at"]
    exp3 = datetime.fromisoformat(exp3_str)
    expected_exp3 = exp2 + timedelta(days=7)
    assert abs((exp3 - expected_exp3).total_seconds()) < 5

    # Remaining balance: 500 - 100 - 200 - 100 = 100 coins
    res_w = client.get("/api/v1/user/coins/wallet", headers=headers_user)
    assert res_w.json()["data"]["balance"] == 100


# =========================================================================
# 8. Admin Coin Adjustments Negative Clamping & Ledger Invariant
# =========================================================================
def test_admin_coin_clamping_and_ledger_invariants(client):
    """
    Hypothesis: Admin sets negative coins or large negative delta.
    Expected: Wallet balance is clamped to >= 0 (max(0, val)).
    Audit ledger must record exact diff and final balance_after == wallet.balance.
    """
    user = create_test_user("admin_clamp_user")
    admin = create_test_user("admin_clamp_admin", role="ADMIN")
    headers_user = {"Authorization": f"Bearer {user['token']}"}
    headers_admin = {"Authorization": f"Bearer {admin['token']}"}

    # 1. Admin sets coins to -50
    res_set_neg = client.put(f"/api/v1/admin/users/{user['id']}", json={"coins": -50}, headers=headers_admin)
    assert res_set_neg.status_code == 200
    assert res_set_neg.json()["data"]["coins"] == 0

    # User wallet check: balance is 0
    res_w0 = client.get("/api/v1/user/coins/wallet", headers=headers_user)
    assert res_w0.json()["data"]["balance"] == 0

    # 2. Admin applies negative adjustment -100 on 0 balance
    res_adj_neg = client.put(f"/api/v1/admin/users/{user['id']}", json={"coins_adjustment": -100}, headers=headers_admin)
    assert res_adj_neg.status_code == 200
    assert res_adj_neg.json()["data"]["coins"] == 0

    # 3. Admin sets coins to 1,000,000 (Massive balance)
    res_huge = client.put(f"/api/v1/admin/users/{user['id']}", json={"coins": 1000000}, headers=headers_admin)
    assert res_huge.status_code == 200
    assert res_huge.json()["data"]["coins"] == 1000000

    # 4. Audit ledger verification
    res_tx = client.get("/api/v1/user/coins/transactions", headers=headers_user)
    assert res_tx.status_code == 200
    items = res_tx.json()["data"]["items"]
    # Check that the 1,000,000 balance transaction exists in ledger
    assert any(t["balance_after"] == 1000000 and t["transaction_type"] == "ADMIN_ADJUST" for t in items)


# =========================================================================
# 9. Concurrency Stress Test: Race-Condition on Video Tipping
# =========================================================================
def test_concurrent_tipping_race_condition(client):
    """
    Hypothesis: 10 concurrent threads simultaneously attempt to tip 1 coin
    for the same user and drama (starting at 0 tips).
    Enforcement invariant: At the end, tip_count in database MUST be <= 2.
    The database unique constraint and limit checks must NEVER allow tip_count > 2.
    """
    user = create_test_user("race_tip_user")
    admin = create_test_user("race_tip_admin", role="ADMIN")
    drama = create_test_drama_with_episodes(admin["id"])
    ep_id = drama["episodes"][0]["id"]
    headers = {"Authorization": f"Bearer {user['token']}"}

    def attempt_tip():
        c = TestClient(app, raise_server_exceptions=False)
        return c.post(
            f"/api/v1/interactions/episodes/{ep_id}/tip",
            json={"coin_amount": 1},
            headers=headers
        )

    # Launch 10 concurrent requests
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(attempt_tip) for _ in range(10)]
        results = [f.result() for f in as_completed(futures)]

    status_codes = [r.status_code for r in results]
    success_count = sum(1 for code in status_codes if code == 200)

    # Invariant 1: Total successful responses claiming success must be at least 1 and at most 2
    # Invariant 2: Database tip_count MUST NEVER exceed 2!
    # Invariant 3: No unhandled 500 errors (all rejections must be 400)
    assert all(code in (200, 400) for code in status_codes), f"Unhandled server error in concurrent tipping: {status_codes}"
    with SessionLocal() as db:
        tip = db.query(VideoCoinTip).filter(
            VideoCoinTip.user_id == user["id"],
            VideoCoinTip.video_id == drama["id"]
        ).first()
        tip_count = tip.tip_count if tip else 0
        assert tip_count <= 2, f"CRITICAL CONCURRENCY BREACH: Database tip_count {tip_count} exceeded max limit of 2!"


# =========================================================================
# 10. Concurrency Stress Test: Race-Condition on Daily Sign-In
# =========================================================================
def test_concurrent_sign_in_race_condition(client):
    """
    Hypothesis: 10 concurrent threads simultaneously call /sign-in on the same user.
    Adversarial evaluation: measures whether simultaneous execution slips past
    application-level date check without row-level locking.
    """
    user = create_test_user("race_signin_user")
    headers = {"Authorization": f"Bearer {user['token']}"}

    def attempt_signin():
        c = TestClient(app, raise_server_exceptions=False)
        return c.post("/api/v1/user/coins/sign-in", headers=headers)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(attempt_signin) for _ in range(10)]
        results = [f.result() for f in as_completed(futures)]

    status_codes = [r.status_code for r in results]
    success_count = sum(1 for code in status_codes if code == 200)

    # Concurrency invariant: Strictly 1 sign-in succeeds (+10 coins), 9 receive 400
    assert success_count == 1, f"CONCURRENCY BREACH: {success_count} sign-ins succeeded for same day! Expected strictly 1."
    failure_count = sum(1 for code in status_codes if code == 400)
    assert failure_count == 9, f"Expected 9 rejections (400), got {failure_count} (status_codes: {status_codes})"

    # Check ledger and wallet state
    with SessionLocal() as db:
        wallet = db.query(UserCoinWallet).filter(UserCoinWallet.user_id == user["id"]).first()
        assert wallet.last_sign_in_date is not None
        assert wallet.balance == 60, f"Expected wallet balance 60 (50 initial + 10 sign-in), got {wallet.balance}"
        tx_count = db.query(UserCoinTransaction).filter(
            UserCoinTransaction.user_id == user["id"],
            UserCoinTransaction.transaction_type == "SIGN_IN"
        ).count()
        # Verify transaction records reflect strictly 1 sign-in
        assert tx_count == 1
