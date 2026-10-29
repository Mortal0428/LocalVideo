"""
Adversarial Empirical Stress Test Suite for Milestone 3
Focus Areas:
1. Coin Tipping Limits (max 2/drama), Balance Integrity, Insufficient Coins, Concurrency Race Conditions
2. Daily Sign-In Idempotency, Repeated Clicks, Concurrent Bursts, Transaction Ledger Audit
3. Admin Full User CRUD Lifecycle, Password Reset Re-Auth, VIP Expiry, Cascade Deletion Integrity
4. Frontend DOM State Machine Verification via Playwright
"""

import os
import sys
import time
import uuid
import json
import concurrent.futures
from datetime import datetime, timedelta
import requests

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"

class AdversarialRunner:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.passed_tests = []
        self.failed_tests = []

    def log(self, msg: str):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def assert_test(self, condition: bool, test_name: str, detail: str = ""):
        if condition:
            self.log(f"[PASS] {test_name}")
            self.passed_tests.append(test_name)
        else:
            self.log(f"[FAIL] {test_name} - {detail}")
            self.failed_tests.append((test_name, detail))

    def login_admin(self) -> str:
        if self.admin_token:
            return self.admin_token
        resp = self.session.post(f"{BACKEND_URL}/api/v1/auth/login", json={"username": "admin", "password": "password123"}, timeout=5)
        if resp.status_code != 200:
            resp = self.session.post(f"{BACKEND_URL}/api/v1/auth/login", json={"username": "admin", "password": "adminpassword"}, timeout=5)
        assert resp.status_code == 200, f"Admin login failed: {resp.text}"
        self.admin_token = resp.json().get("access_token")
        return self.admin_token

    def register_user(self, prefix: str = "adv_user") -> tuple[str, str, str]:
        uname = f"{prefix}_{int(time.time()*1000)%10000000}_{uuid.uuid4().hex[:4]}"
        pwd = "TestPassword123!"
        resp = self.session.post(f"{BACKEND_URL}/api/v1/auth/register", json={
            "username": uname,
            "password": pwd,
            "nickname": f"Nick_{uname[:8]}"
        }, timeout=5)
        assert resp.status_code in [200, 201], f"Register failed: {resp.text}"
        reg_data = resp.json()
        user_id = reg_data.get("id")

        # Authenticate to obtain real access_token
        login_resp = self.session.post(f"{BACKEND_URL}/api/v1/auth/login", json={
            "username": uname,
            "password": pwd
        }, timeout=5)
        assert login_resp.status_code == 200, f"Login failed after register: {login_resp.text}"
        token = login_resp.json().get("access_token")
        return user_id, uname, token

    def get_first_video_and_episode(self) -> tuple[str, str]:
        adm_token = self.login_admin()
        headers = {"Authorization": f"Bearer {adm_token}"}
        try:
            resp = self.session.get(f"{BACKEND_URL}/api/v1/admin/dramas", headers=headers, timeout=5)
            if resp.status_code == 200:
                items = resp.json().get("data", {}).get("items", [])
                if items:
                    v_id = items[0].get("id")
                    ep_resp = self.session.get(f"{BACKEND_URL}/api/v1/creator/dramas/{v_id}/episodes", headers=headers, timeout=5)
                    if ep_resp.status_code == 200:
                        eps = ep_resp.json().get("data", [])
                        if isinstance(eps, list) and len(eps) > 0:
                            return v_id, eps[0].get("id")
        except Exception as e:
            self.log(f"API drama lookup failed: {e}")

        # Database fallback
        backend_path = os.path.abspath("backend")
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        from app.core.database import SessionLocal
        from app.models.video import Video, VideoEpisode
        db = SessionLocal()
        try:
            v = db.query(Video).first()
            if v:
                ep = db.query(VideoEpisode).filter(VideoEpisode.video_id == v.id).first()
                if ep:
                    return v.id, ep.id
        finally:
            db.close()
        raise RuntimeError("No available video and episode in database")

    # =========================================================================
    # SUITE 1: Coin Tipping Limits & Balance Integrity
    # =========================================================================
    def test_suite_1_coin_tipping_limits(self):
        self.log("\n=== SUITE 1: Coin Tipping Limits & Balance Integrity ===")
        vid, ep_id = self.get_first_video_and_episode()

        # 1.1 Fresh user initial state
        _, uname, token = self.register_user("tipper")
        headers = {"Authorization": f"Bearer {token}"}

        wallet_resp = self.session.get(f"{BACKEND_URL}/api/v1/user/coins/wallet", headers=headers, timeout=5)
        init_balance = wallet_resp.json().get("data", {}).get("balance", 0)
        self.assert_test(init_balance >= 50, "1.1 Initial User Wallet has registration bonus >= 50", f"balance={init_balance}")

        # Check initial tip status
        status_resp = self.session.get(f"{BACKEND_URL}/api/v1/interactions/episodes/{ep_id}/tip-status", headers=headers, timeout=5)
        initial_status = status_resp.json().get("data", {})
        init_tipped = initial_status.get("tipped_count", 0)
        init_heat = initial_status.get("heat_score", 0.0)
        init_coin_count = initial_status.get("video_coin_count", 0)
        self.assert_test(init_tipped == 0, "1.2 Initial Tipped Count for new user is 0", f"tipped_count={init_tipped}")

        # 1.3 Tip 1 coin
        tip1_resp = self.session.post(f"{BACKEND_URL}/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 1}, headers=headers, timeout=5)
        self.assert_test(tip1_resp.status_code == 200, "1.3 Tip 1 coin returns HTTP 200", f"status={tip1_resp.status_code}, body={tip1_resp.text}")
        tip1_data = tip1_resp.json().get("data", {})
        self.assert_test(tip1_data.get("tipped_count") == 1, "1.3.1 Tipped count incremented to 1", f"tipped_count={tip1_data.get('tipped_count')}")

        # Verify wallet balance decreased by exactly 1
        w1_resp = self.session.get(f"{BACKEND_URL}/api/v1/user/coins/wallet", headers=headers, timeout=5)
        w1_balance = w1_resp.json().get("data", {}).get("balance", 0)
        self.assert_test(w1_balance == init_balance - 1, "1.3.2 Wallet balance decreased by exactly 1", f"balance={w1_balance}, expected={init_balance - 1}")

        # Verify heat score increased by exactly 10.0
        new_heat = tip1_data.get("heat_score", 0.0)
        self.assert_test(abs(new_heat - (init_heat + 10.0)) < 0.01, "1.3.3 Heat score increased by exactly 10.0", f"new_heat={new_heat}, expected={init_heat + 10.0}")

        # 1.4 Tip second coin (1 coin)
        tip2_resp = self.session.post(f"{BACKEND_URL}/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 1}, headers=headers, timeout=5)
        self.assert_test(tip2_resp.status_code == 200, "1.4 Tip second coin returns HTTP 200", f"status={tip2_resp.status_code}")
        tip2_data = tip2_resp.json().get("data", {})
        self.assert_test(tip2_data.get("tipped_count") == 2, "1.4.1 Tipped count incremented to 2", f"tipped_count={tip2_data.get('tipped_count')}")

        w2_resp = self.session.get(f"{BACKEND_URL}/api/v1/user/coins/wallet", headers=headers, timeout=5)
        w2_balance = w2_resp.json().get("data", {}).get("balance", 0)
        self.assert_test(w2_balance == init_balance - 2, "1.4.2 Wallet balance decreased by exactly 2 total", f"balance={w2_balance}")

        # 1.5 Adversarial Test: Attempt 3rd coin (MUST FAIL WITH HTTP 400)
        tip3_resp = self.session.post(f"{BACKEND_URL}/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 1}, headers=headers, timeout=5)
        self.assert_test(tip3_resp.status_code == 400, "1.5 Attempting 3rd coin is rejected with HTTP 400", f"status={tip3_resp.status_code}, body={tip3_resp.text}")
        self.assert_test("最多" in tip3_resp.text or "上限" in tip3_resp.text or "2" in tip3_resp.text, "1.5.1 Error message clearly states 2-coin maximum limit", f"body={tip3_resp.text}")

        # Verify wallet balance is unchanged
        w3_resp = self.session.get(f"{BACKEND_URL}/api/v1/user/coins/wallet", headers=headers, timeout=5)
        w3_balance = w3_resp.json().get("data", {}).get("balance", 0)
        self.assert_test(w3_balance == w2_balance, "1.5.2 Wallet balance NOT deducted on rejected tip", f"balance={w3_balance}")

        # 1.6 Adversarial Test: Attempt 2 coins at once when user already tipped 2 (MUST FAIL WITH HTTP 400)
        tip4_resp = self.session.post(f"{BACKEND_URL}/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 2}, headers=headers, timeout=5)
        self.assert_test(tip4_resp.status_code == 400, "1.6 Attempting 2 coins when at limit is rejected with HTTP 400", f"status={tip4_resp.status_code}")

        # 1.7 Pydantic Schema Boundary Validation: Invalid coin amounts
        for invalid_amount in [0, 3, -1, 5, 100]:
            inv_resp = self.session.post(f"{BACKEND_URL}/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": invalid_amount}, headers=headers, timeout=5)
            self.assert_test(inv_resp.status_code in [400, 422], f"1.7 Invalid coin amount {invalid_amount} rejected with 400/422", f"status={inv_resp.status_code}")

        # 1.8 Insufficient Balance Testing
        poor_id, uname_poor, token_poor = self.register_user("poor_user")
        headers_poor = {"Authorization": f"Bearer {token_poor}"}

        admin_tok = self.login_admin()
        adm_headers = {"Authorization": f"Bearer {admin_tok}"}

        adjust_resp = self.session.put(f"{BACKEND_URL}/api/v1/admin/users/{poor_id}", json={"coins": 0}, headers=adm_headers, timeout=5)
        self.assert_test(adjust_resp.status_code == 200, "1.8 Admin successfully set poor user balance to 0", f"status={adjust_resp.status_code}")

        # Poor user attempts to tip 1 coin
        poor_tip1 = self.session.post(f"{BACKEND_URL}/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 1}, headers=headers_poor, timeout=5)
        self.assert_test(poor_tip1.status_code == 400, "1.8.1 Tipping with 0 balance rejected with HTTP 400", f"status={poor_tip1.status_code}, body={poor_tip1.text}")
        self.assert_test("余额不足" in poor_tip1.text or "insufficient" in poor_tip1.text.lower(), "1.8.2 Error message specifies insufficient coins", f"body={poor_tip1.text}")

        # Admin sets balance to 1, user attempts to tip 2 coins
        self.session.put(f"{BACKEND_URL}/api/v1/admin/users/{poor_id}", json={"coins": 1}, headers=adm_headers, timeout=5)
        poor_tip2 = self.session.post(f"{BACKEND_URL}/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 2}, headers=headers_poor, timeout=5)
        self.assert_test(poor_tip2.status_code == 400, "1.8.3 Tipping 2 coins with 1 coin balance rejected with HTTP 400", f"status={poor_tip2.status_code}")

        # 1.9 Concurrency Race Condition Test on Tipping Cap
        # Fresh user tries to send 10 concurrent requests of 1 coin each. ONLY 2 MUST SUCCEED!
        _, uname_race, token_race = self.register_user("race_tipper")
        headers_race = {"Authorization": f"Bearer {token_race}"}

        def make_tip_req():
            s = requests.Session()
            return s.post(f"{BACKEND_URL}/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 1}, headers=headers_race, timeout=10)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_tip_req) for _ in range(10)]
            results = [f.result() for f in futures]

        statuses = [r.status_code for r in results]
        self.log(f"Statuses from concurrent tipping: {statuses}")
        for idx, r in enumerate(results):
            if r.status_code != 200:
                self.log(f"Req {idx}: status={r.status_code}, body={r.text[:100]}")
        success_count = sum(1 for r in results if r.status_code == 200)
        fail_count = sum(1 for r in results if r.status_code in [400, 409])
        self.assert_test(success_count <= 2, f"1.9 Concurrency race condition: at most 2 tips can succeed", f"success={success_count}, fail={fail_count}")

        # Check tip status
        st_resp = self.session.get(f"{BACKEND_URL}/api/v1/interactions/episodes/{ep_id}/tip-status", headers=headers_race, timeout=5)
        tipped_cnt = st_resp.json().get("data", {}).get("tipped_count", 0)
        self.assert_test(tipped_cnt <= 2, f"1.9.1 DB tipped_count is strictly <= 2 (actual={tipped_cnt})")

        # Verify wallet balance reduced accordingly
        w_race_resp = self.session.get(f"{BACKEND_URL}/api/v1/user/coins/wallet", headers=headers_race, timeout=5)
        w_race_balance = w_race_resp.json().get("data", {}).get("balance", 0)
        self.assert_test(w_race_balance == 50 - tipped_cnt, f"1.9.2 Wallet balance deducted correctly by {tipped_cnt} (balance={w_race_balance})")

    # =========================================================================
    # SUITE 2: Daily Sign-In Idempotency
    # =========================================================================
    def test_suite_2_daily_signin_idempotency(self):
        self.log("\n=== SUITE 2: Daily Sign-In Idempotency ===")
        _, uname, token = self.register_user("signin_tester")
        headers = {"Authorization": f"Bearer {token}"}

        # 2.1 Initial wallet state
        w0_resp = self.session.get(f"{BACKEND_URL}/api/v1/user/coins/wallet", headers=headers, timeout=5)
        w0 = w0_resp.json().get("data", {})
        self.assert_test(w0.get("has_signed_today") is False, "2.1 Initial has_signed_today is False")
        self.assert_test(w0.get("balance") == 50, "2.1.1 Initial balance is 50")

        # 2.2 First Sign-In
        sign1_resp = self.session.post(f"{BACKEND_URL}/api/v1/user/coins/sign-in", headers=headers, timeout=5)
        self.assert_test(sign1_resp.status_code == 200, "2.2 First sign-in returns HTTP 200", f"status={sign1_resp.status_code}")
        sign1_data = sign1_resp.json().get("data", {})
        self.assert_test(sign1_data.get("reward") == 10, "2.2.1 First sign-in reward is 10 coins")
        self.assert_test(sign1_data.get("balance") == 60, "2.2.2 Balance updated to 60 coins")
        self.assert_test(sign1_data.get("has_signed_today") is True, "2.2.3 has_signed_today is True")

        # Verify wallet state after sign-in
        w1_resp = self.session.get(f"{BACKEND_URL}/api/v1/user/coins/wallet", headers=headers, timeout=5)
        w1 = w1_resp.json().get("data", {})
        self.assert_test(w1.get("has_signed_today") is True, "2.2.4 Wallet reports has_signed_today == True")
        self.assert_test(w1.get("balance") == 60, "2.2.5 Wallet reports balance == 60")

        # 2.3 Repeated Sign-In on Same Day (MUST FAIL WITH HTTP 400)
        sign2_resp = self.session.post(f"{BACKEND_URL}/api/v1/user/coins/sign-in", headers=headers, timeout=5)
        self.assert_test(sign2_resp.status_code == 400, "2.3 Duplicate sign-in rejected with HTTP 400", f"status={sign2_resp.status_code}, body={sign2_resp.text}")
        self.assert_test("已完成签到" in sign2_resp.text or "明天再来" in sign2_resp.text, "2.3.1 Friendly feedback for repeat sign-in", f"body={sign2_resp.text}")

        # Verify balance remains strictly 60
        w2_resp = self.session.get(f"{BACKEND_URL}/api/v1/user/coins/wallet", headers=headers, timeout=5)
        self.assert_test(w2_resp.json().get("data", {}).get("balance") == 60, "2.3.2 Balance strictly maintained at 60 after duplicate attempt")

        # 2.4 High-Concurrency Sign-In Burst
        # Try 10 concurrent requests to sign-in on this user who already signed in
        def make_signin_req():
            s = requests.Session()
            return s.post(f"{BACKEND_URL}/api/v1/user/coins/sign-in", headers=headers, timeout=5)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_signin_req) for _ in range(10)]
            burst_results = [f.result() for f in futures]

        burst_success = sum(1 for r in burst_results if r.status_code == 200)
        burst_rejected = sum(1 for r in burst_results if r.status_code == 400)
        self.assert_test(burst_success == 0 and burst_rejected == 10, "2.4 All 10 concurrent sign-in bursts rejected with HTTP 400", f"success={burst_success}, rejected={burst_rejected}")

        # 2.5 Fresh User Concurrent Sign-In Burst (Only 1 should EVER succeed)
        _, uname_fresh, token_fresh = self.register_user("fresh_signin")
        headers_fresh = {"Authorization": f"Bearer {token_fresh}"}

        def make_fresh_signin():
            s = requests.Session()
            return s.post(f"{BACKEND_URL}/api/v1/user/coins/sign-in", headers=headers_fresh, timeout=5)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_fresh_signin) for _ in range(10)]
            fresh_results = [f.result() for f in futures]

        fresh_statuses = [r.status_code for r in fresh_results]
        self.log(f"Statuses from concurrent fresh sign-in: {fresh_statuses}")
        for idx, r in enumerate(fresh_results):
            if r.status_code not in [200, 400]:
                self.log(f"Fresh sign-in Req {idx}: status={r.status_code}, body={r.text[:100]}")
        fresh_success = sum(1 for r in fresh_results if r.status_code == 200)
        self.assert_test(fresh_success == 1, "2.5 Concurrent sign-in on fresh user: strictly 1 succeeded and all others rejected", f"success={fresh_success}, statuses={fresh_statuses}")

        w_fresh_resp = self.session.get(f"{BACKEND_URL}/api/v1/user/coins/wallet", headers=headers_fresh, timeout=5)
        self.assert_test(w_fresh_resp.json().get("data", {}).get("balance") == 60, "2.5.1 Final balance is strictly 60 (initial 50 + 10)")

        # 2.6 Audit Ledger Verification
        tx_resp = self.session.get(f"{BACKEND_URL}/api/v1/user/coins/transactions", headers=headers_fresh, timeout=5)
        tx_data = tx_resp.json().get("data", {}).get("items", [])
        signin_txs = [t for t in tx_data if t.get("transaction_type") == "SIGN_IN"]
        self.assert_test(len(signin_txs) == 1, "2.6 Exactly ONE SIGN_IN transaction entry in audit ledger", f"count={len(signin_txs)}")

    # =========================================================================
    # SUITE 3: Admin Full User CRUD Lifecycle
    # =========================================================================
    def test_suite_3_admin_user_crud_lifecycle(self):
        self.log("\n=== SUITE 3: Admin User Full CRUD Lifecycle ===")
        admin_token = self.login_admin()
        adm_headers = {"Authorization": f"Bearer {admin_token}"}

        # 3.1 Create User via Admin API
        test_uname = f"crud_usr_{int(time.time()*1000)%10000000}"
        test_pwd = "InitialPassword123!"
        create_payload = {
            "username": test_uname,
            "password": test_pwd,
            "nickname": "初代测试员",
            "role": "USER",
            "coins": 88,
            "vip_days": 15
        }
        create_resp = self.session.post(f"{BACKEND_URL}/api/v1/admin/users", json=create_payload, headers=adm_headers, timeout=5)
        self.assert_test(create_resp.status_code == 200, "3.1 Admin create user returns HTTP 200", f"status={create_resp.status_code}, body={create_resp.text}")
        created_user = create_resp.json().get("data", {})
        user_id = created_user.get("id")
        self.assert_test(bool(user_id), "3.1.1 Created user returns valid user_id", f"user_id={user_id}")
        self.assert_test(created_user.get("coins") == 88, "3.1.2 Created user has initial 88 coins", f"coins={created_user.get('coins')}")
        self.assert_test(created_user.get("vip_expire_at") is not None, "3.1.3 Created user has VIP expiration set")

        # 3.2 Authenticate as newly created user
        login_resp = self.session.post(f"{BACKEND_URL}/api/v1/auth/login", json={"username": test_uname, "password": test_pwd}, timeout=5)
        self.assert_test(login_resp.status_code == 200, "3.2 New user can authenticate with initial password", f"status={login_resp.status_code}")
        usr_token = login_resp.json().get("access_token")
        usr_headers = {"Authorization": f"Bearer {usr_token}"}

        # Verify profile and wallet of newly created user
        prof_resp = self.session.get(f"{BACKEND_URL}/api/v1/user/profile", headers=usr_headers, timeout=5)
        prof_data = prof_resp.json().get("data", {})
        self.assert_test(prof_data.get("nickname") == "初代测试员", "3.2.1 User profile reflects nickname '初代测试员'", f"nickname={prof_data.get('nickname')}")
        self.assert_test(prof_data.get("role") == "USER", "3.2.2 User role is 'USER'")
        self.assert_test(prof_data.get("is_vip") is True, "3.2.3 User is_vip is True")

        w_resp = self.session.get(f"{BACKEND_URL}/api/v1/user/coins/wallet", headers=usr_headers, timeout=5)
        self.assert_test(w_resp.json().get("data", {}).get("balance") == 88, "3.2.4 User wallet balance matches 88")

        # 3.3 Edit User via Admin API
        new_pwd = "UpgradedPassword456!"
        update_payload = {
            "nickname": "升级版创作者",
            "password": new_pwd,
            "role": "CREATOR",
            "coins": 300,
            "vip_days": 10
        }
        update_resp = self.session.put(f"{BACKEND_URL}/api/v1/admin/users/{user_id}", json=update_payload, headers=adm_headers, timeout=5)
        self.assert_test(update_resp.status_code == 200, "3.3 Admin edit user returns HTTP 200", f"status={update_resp.status_code}")
        updated_data = update_resp.json().get("data", {})
        self.assert_test(updated_data.get("nickname") == "升级版创作者", "3.3.1 Updated nickname matches")
        self.assert_test(updated_data.get("role") == "CREATOR", "3.3.2 Updated role is 'CREATOR'")
        self.assert_test(updated_data.get("coins") == 300, "3.3.3 Updated coins is 300")

        # 3.4 Password Reset Re-Authentication Integrity
        old_login = self.session.post(f"{BACKEND_URL}/api/v1/auth/login", json={"username": test_uname, "password": test_pwd}, timeout=5)
        self.assert_test(old_login.status_code == 401, "3.4 Old password rejected with HTTP 401", f"status={old_login.status_code}")

        new_login = self.session.post(f"{BACKEND_URL}/api/v1/auth/login", json={"username": test_uname, "password": new_pwd}, timeout=5)
        self.assert_test(new_login.status_code == 200, "3.4.1 New password succeeds with HTTP 200", f"status={new_login.status_code}")
        new_usr_token = new_login.json().get("access_token")
        new_headers = {"Authorization": f"Bearer {new_usr_token}"}

        # Verify updated user wallet reflects 300 coins
        w_up_resp = self.session.get(f"{BACKEND_URL}/api/v1/user/coins/wallet", headers=new_headers, timeout=5)
        self.assert_test(w_up_resp.json().get("data", {}).get("balance") == 300, "3.4.2 User wallet balance updated to 300")

        # Verify audit ledger has ADMIN_ADJUST transaction
        tx_resp = self.session.get(f"{BACKEND_URL}/api/v1/user/coins/transactions", headers=new_headers, timeout=5)
        tx_items = tx_resp.json().get("data", {}).get("items", [])
        adm_adjust_txs = [t for t in tx_items if t.get("transaction_type") == "ADMIN_ADJUST"]
        self.assert_test(len(adm_adjust_txs) >= 1, "3.4.3 Admin adjustment recorded in transaction ledger")

        # 3.5 Delete User via Admin API
        del_resp = self.session.delete(f"{BACKEND_URL}/api/v1/admin/users/{user_id}", headers=adm_headers, timeout=5)
        self.assert_test(del_resp.status_code == 200, "3.5 Admin delete user returns HTTP 200", f"status={del_resp.status_code}")

        # 3.6 Subsequent Login and Auth Rejection
        deleted_login = self.session.post(f"{BACKEND_URL}/api/v1/auth/login", json={"username": test_uname, "password": new_pwd}, timeout=5)
        self.assert_test(deleted_login.status_code in [401, 404], "3.6 Deleted user login immediately rejected (401/404)", f"status={deleted_login.status_code}")

        # 3.7 Token Invalidation / User Nonexistence on Protected Route
        del_prof = self.session.get(f"{BACKEND_URL}/api/v1/user/profile", headers=new_headers, timeout=5)
        self.assert_test(del_prof.status_code in [401, 404], "3.7 Token for deleted user immediately rejected on protected endpoint", f"status={del_prof.status_code}")

        # 3.8 Prevent Admin Self-Deletion
        adm_prof = self.session.get(f"{BACKEND_URL}/api/v1/user/profile", headers=adm_headers, timeout=5)
        admin_id = adm_prof.json().get("data", {}).get("id")
        self_del = self.session.delete(f"{BACKEND_URL}/api/v1/admin/users/{admin_id}", headers=adm_headers, timeout=5)
        self.assert_test(self_del.status_code == 400, "3.8 Admin self-deletion prevented with HTTP 400", f"status={self_del.status_code}")

    # =========================================================================
    # SUITE 4: Playwright Frontend UI Empirical Inspection
    # =========================================================================
    def test_suite_4_playwright_frontend(self):
        self.log("\n=== SUITE 4: Playwright Frontend UI Empirical Inspection ===")
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(channel="msedge", headless=True)
            except Exception:
                browser = p.chromium.launch(headless=True)

            # 4.1 PlayerView Coin Tipping Modal & Disabled State Verification
            _, uname_p, token_p = self.register_user("pw_tipper")
            ctx_p = browser.new_context(viewport={"width": 1440, "height": 900})
            page_p = ctx_p.new_page()

            # Inject auth
            page_p.goto(f"{FRONTEND_URL}/", wait_until="domcontentloaded", timeout=15000)
            page_p.evaluate(f"""() => {{
                localStorage.setItem('cinema_access_token', '{token_p}');
                localStorage.setItem('token', '{token_p}');
                localStorage.setItem('user', JSON.stringify({json.dumps({"username": uname_p, "role": "USER"})}));
            }}""")

            page_p.goto(f"{FRONTEND_URL}/#/video/latest", wait_until="domcontentloaded", timeout=15000)
            page_p.wait_for_timeout(2000)

            # Check tip button
            has_tip_btn = page_p.locator("#btn-coin-tip").count() > 0
            self.assert_test(has_tip_btn, "4.1 PlayerView renders #btn-coin-tip action button")

            if has_tip_btn:
                page_p.click("#btn-coin-tip")
                page_p.wait_for_timeout(1000)

                # Check modal elements
                has_tip1 = page_p.locator("#btn-tip-1-coin").count() > 0
                has_tip2 = page_p.locator("#btn-tip-2-coins").count() > 0
                self.assert_test(has_tip1 and has_tip2, "4.1.1 Modal renders #btn-tip-1-coin and #btn-tip-2-coins")

                if has_tip2:
                    # Tip 2 coins
                    page_p.click("#btn-tip-2-coins")
                    page_p.wait_for_timeout(1500)

                    # Reopen modal if closed
                    if page_p.locator("#btn-tip-1-coin").count() == 0:
                        page_p.click("#btn-coin-tip")
                        page_p.wait_for_timeout(1000)

                    # Verify buttons become disabled after tipping 2 coins (max limit reached)
                    tip1_disabled = page_p.locator("#btn-tip-1-coin").is_disabled()
                    tip2_disabled = page_p.locator("#btn-tip-2-coins").is_disabled()
                    self.assert_test(tip1_disabled and tip2_disabled, "4.1.2 Both tip buttons become disabled when 2-coin cap reached")

                    # Check max-tip badge
                    max_badge_text = page_p.locator(".max-tip-badge").inner_text() if page_p.locator(".max-tip-badge").count() > 0 else ""
                    self.assert_test("已投满 2 枚金币" in max_badge_text, "4.1.3 UI displays '已投满 2 枚金币' badge", f"badge={max_badge_text}")

            ctx_p.close()

            # 4.2 UserProfileView Bento Cards & Sign-In Idempotency in Browser
            _, uname_u, token_u = self.register_user("pw_user_bento")
            ctx_u = browser.new_context(viewport={"width": 1440, "height": 900})
            page_u = ctx_u.new_page()

            page_u.goto(f"{FRONTEND_URL}/", wait_until="domcontentloaded", timeout=15000)
            page_u.evaluate(f"""() => {{
                localStorage.setItem('cinema_access_token', '{token_u}');
                localStorage.setItem('token', '{token_u}');
                localStorage.setItem('user', JSON.stringify({json.dumps({"username": uname_u, "role": "USER"})}));
            }}""")

            page_u.goto(f"{FRONTEND_URL}/#/user/space", wait_until="domcontentloaded", timeout=15000)
            page_u.wait_for_timeout(2000)

            has_wallet_card = page_u.locator("#user-wallet-card").count() > 0
            has_vip_card = page_u.locator("#user-vip-card").count() > 0
            self.assert_test(has_wallet_card and has_vip_card, "4.2 UserProfileView renders #user-wallet-card and #user-vip-card Bento cards")

            if has_wallet_card:
                signin_btn = page_u.locator("#btn-daily-signin")
                self.assert_test(signin_btn.count() > 0, "4.2.1 Wallet card contains #btn-daily-signin")

                # Click sign-in
                signin_btn.click()
                page_u.wait_for_timeout(1500)

                # Verify button changes to "今日已签到 ✓" and is disabled
                signin_text = signin_btn.inner_text()
                is_disabled = signin_btn.is_disabled()
                self.assert_test("已签到" in signin_text and is_disabled, "4.2.2 Sign-in button disabled and displays '今日已签到' after click", f"text={signin_text}, disabled={is_disabled}")

            ctx_u.close()

            # 4.3 AdminView User CRUD Table and Modals
            admin_tok = self.login_admin()
            ctx_adm = browser.new_context(viewport={"width": 1440, "height": 900})
            page_adm = ctx_adm.new_page()

            page_adm.goto(f"{FRONTEND_URL}/", wait_until="domcontentloaded", timeout=15000)
            page_adm.evaluate(f"""() => {{
                localStorage.setItem('cinema_access_token', '{admin_tok}');
                localStorage.setItem('token', '{admin_tok}');
                localStorage.setItem('user', JSON.stringify({json.dumps({"username": "admin", "role": "ADMIN"})}));
            }}""")

            page_adm.goto(f"{FRONTEND_URL}/#/admin?tab=users", wait_until="domcontentloaded", timeout=15000)
            page_adm.wait_for_timeout(2000)

            # Verify toolbar and add user button
            has_add_btn = page_adm.locator("#btn-admin-add-user").count() > 0
            self.assert_test(has_add_btn, "4.3 AdminView users tab renders #btn-admin-add-user")

            if has_add_btn:
                page_adm.click("#btn-admin-add-user")
                page_adm.wait_for_timeout(1000)

                has_modal = page_adm.locator("#modal-add-user").count() > 0
                has_uname_input = page_adm.locator("#input-add-username").count() > 0
                has_pwd_input = page_adm.locator("#input-add-password").count() > 0
                has_submit_btn = page_adm.locator("#btn-submit-add-user").count() > 0
                self.assert_test(has_modal and has_uname_input and has_pwd_input and has_submit_btn, "4.3.1 #modal-add-user dialog renders with required form fields and submit button")

            ctx_adm.close()
            browser.close()

    def run_all(self):
        self.log("Starting Adversarial Empirical Stress Testing Suite for Milestone 3...")
        t0 = time.time()
        self.test_suite_1_coin_tipping_limits()
        self.test_suite_2_daily_signin_idempotency()
        self.test_suite_3_admin_user_crud_lifecycle()
        self.test_suite_4_playwright_frontend()
        duration = time.time() - t0

        self.log("\n=======================================================")
        self.log(f"ADVERSARIAL STRESS TEST SUMMARY")
        self.log(f"Passed: {len(self.passed_tests)} | Failed: {len(self.failed_tests)} | Duration: {duration:.2f}s")
        self.log("=======================================================")

        if self.failed_tests:
            self.log("FAILED TESTS:")
            for name, detail in self.failed_tests:
                self.log(f"  - {name}: {detail}")
            return 1
        else:
            self.log("ALL ADVERSARIAL STRESS TESTS PASSED WITH 100% SUCCESS!")
            return 0


if __name__ == "__main__":
    runner = AdversarialRunner()
    sys.exit(runner.run_all())
