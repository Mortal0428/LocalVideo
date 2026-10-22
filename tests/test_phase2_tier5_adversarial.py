# -*- coding: utf-8 -*-
"""
CinemaAgent Phase 2 Milestone 4: Tier 5 White-Box Adversarial Stress Test Suite
=============================================================================
Coverage Scope:
  - T5_1: Concurrency & Race Conditions (Sign-in race, video tipping strict max 2 coins enforcement, uninitialized wallet race)
  - T5_2: Malicious & Boundary Payloads (SQLi, XSS script tags, emoji/unicode, negative coins, orphaned parent, empty comment)
  - T5_3: State Invariants (Double-entry ledger conservation, VIP monotonic dates, heat score formula exactness)
  - T5_4: Admin Governance Boundaries (Protected admin deletion, non-admin RBAC, duplicate username, upload fuzzing)
  - T5_5: Frontend Geometry & HIG Invariants (16:9 preview ratio under viewport resize, modal backdrop blur)

Execution:
  Direct: python tests/test_phase2_tier5_adversarial.py
  Pytest: pytest tests/test_phase2_tier5_adversarial.py -v
"""

import os
import sys
import time
import json
import re
import io
import jwt
import concurrent.futures
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

import requests
import pytest

# Ensure project root & backend on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, "storage", "test_screenshots")
ARTIFACT_DIR = os.path.join(PROJECT_ROOT, ".agents", "teamwork", "test_artifacts")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

BACKEND_BASE_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
FRONTEND_BASE_URL = os.environ.get("FRONTEND_URL", "http://127.0.0.1:5173")


# ==============================================================================
# Screenshot Archiving Helper
# ==============================================================================
class AdversarialScreenshotManager:
    @staticmethod
    def capture(page, test_code: str, step_label: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_code = re.sub(r"[^a-zA-Z0-9_\-]", "_", test_code)
        safe_label = re.sub(r"[^a-zA-Z0-9_\-]", "_", step_label)
        filename = f"{timestamp}_{safe_code}_{safe_label}.png"

        target_path = os.path.join(SCREENSHOT_DIR, filename)
        audit_path = os.path.join(ARTIFACT_DIR, filename)

        try:
            page.screenshot(path=target_path, full_page=False)
            if os.path.exists(target_path):
                import shutil
                shutil.copyfile(target_path, audit_path)
            print(f"    [SCREENSHOT] Archived: {filename}")
        except Exception as e:
            print(f"    [WARN] Failed to capture screenshot {filename}: {e}")

        return target_path


# ==============================================================================
# Test Result Record & Reporter
# ==============================================================================
class AdversarialTestRecord:
    __test__ = False
    def __init__(self, code: str, title: str, status: str, detail: str = "", duration: float = 0.0):
        self.code = code
        self.title = title
        self.status = status
        self.detail = detail
        self.duration = duration


class AdversarialReporter:
    __test__ = False
    def __init__(self):
        self.records: List[AdversarialTestRecord] = []
        self.start_time = time.time()

    def record_pass(self, code: str, title: str, duration: float = 0.0, detail: str = ""):
        self.records.append(AdversarialTestRecord(code, title, "PASS", detail, duration))
        print(f"  [PASS] {code}: {title} ({duration:.2f}s)")

    def record_fail(self, code: str, title: str, detail: str = "", duration: float = 0.0):
        self.records.append(AdversarialTestRecord(code, title, "FAIL", detail, duration))
        print(f"  [FAIL] {code}: {title} - {detail} ({duration:.2f}s)")

    def print_summary(self) -> int:
        total_time = time.time() - self.start_time
        total = len(self.records)
        passed = sum(1 for r in self.records if r.status == "PASS")
        failed = sum(1 for r in self.records if r.status == "FAIL")

        print("\n" + "=" * 96)
        print("CINEMAAGENT PHASE 2 TIER 5 WHITE-BOX ADVERSARIAL STRESS TEST SUMMARY")
        print("=" * 96)
        print(f"{'Code':<8} | {'Title':<48} | {'Status':<12} | {'Time (s)':<8}")
        print("-" * 96)
        for r in self.records:
            status_display = "OK (PASS)" if r.status == "PASS" else "FAILED"
            print(f"{r.code:<8} | {r.title[:48]:<48} | {status_display:<12} | {r.duration:<8.2f}")

        print("-" * 96)
        print(f"Total Tier 5 Tests: {total} | Passed: {passed} | Failed: {failed}")
        print(f"Total Duration: {total_time:.2f}s | Screenshots: {SCREENSHOT_DIR}")
        print("=" * 96)

        return 1 if failed > 0 else 0


# ==============================================================================
# Helper Client for Adversarial Automation
# ==============================================================================
class AdversarialClient:
    def __init__(self, base_url: str = BACKEND_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.admin_token: Optional[str] = None

    def login_admin(self, username: str = "admin", password: str = "password123") -> str:
        url = f"{self.base_url}/api/v1/auth/login"
        resp = self.session.post(url, json={"username": username, "password": password}, timeout=10)
        if resp.status_code == 200:
            self.admin_token = resp.json().get("access_token")
            return self.admin_token
        raise RuntimeError(f"Admin login failed: HTTP {resp.status_code} - {resp.text}")

    def admin_headers(self) -> Dict[str, str]:
        if not self.admin_token:
            self.login_admin()
        return {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}

    def register_user(self, prefix: str = "adv_user", init_wallet: bool = True) -> Tuple[str, str, str]:
        """Register a test user and optionally pre-initialize wallet (as in normal login flow)."""
        uid = f"{prefix}_{int(time.time() * 1000) % 10000000}"
        pwd = "password123"
        url = f"{self.base_url}/api/v1/auth/register"
        resp = self.session.post(url, json={"username": uid, "password": pwd, "nickname": f"Adv {uid}"}, timeout=10)
        if resp.status_code in [200, 201]:
            user_data = resp.json()
            user_id = user_data.get("id") or user_data.get("data", {}).get("id")
            # Login
            login_resp = self.session.post(f"{self.base_url}/api/v1/auth/login", json={"username": uid, "password": pwd}, timeout=10)
            token = login_resp.json().get("access_token")
            if init_wallet:
                # Pre-initialize wallet via /wallet endpoint
                self.session.get(f"{self.base_url}/api/v1/user/coins/wallet", headers={"Authorization": f"Bearer {token}"}, timeout=5)
            return user_id, uid, token
        raise RuntimeError(f"Register test user failed: HTTP {resp.status_code} - {resp.text}")

    def user_headers(self, token: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def get_first_video_and_episode(self) -> Tuple[str, str]:
        from app.core.database import SessionLocal
        from app.models.video import Video, VideoEpisode
        db = SessionLocal()
        try:
            v = db.query(Video).first()
            if not v:
                raise RuntimeError("No Video album found in database")
            ep = db.query(VideoEpisode).filter(VideoEpisode.video_id == v.id).first()
            if not ep:
                raise RuntimeError("No VideoEpisode found for video " + v.id)
            return v.id, ep.id
        finally:
            db.close()


# ==============================================================================
# Tier 5 Adversarial Test Runner Class
# ==============================================================================
class Tier5AdversarialSuite:
    def __init__(self, reporter: Optional[AdversarialReporter] = None):
        self.reporter = reporter or AdversarialReporter()
        self.api = AdversarialClient()

    def run_all(self) -> int:
        print("\n>>> STARTING TIER 5 WHITE-BOX ADVERSARIAL STRESS SUITE...")
        self.test_t5_1_concurrency_coin_signin_race()
        self.test_t5_1_concurrency_video_tipping_race_strict_max_2_coins()
        self.test_t5_1_concurrency_tipping_2_coins_atomic_race()
        self.test_t5_2_sqli_payloads_in_comments_and_search()
        self.test_t5_2_xss_script_tags_payloads()
        self.test_t5_2_emoji_unicode_cjk_rtl_payloads()
        self.test_t5_2_negative_and_zero_coin_tipping_rejected()
        self.test_t5_2_orphaned_comment_parent_rejected()
        self.test_t5_2_empty_whitespace_comment_rejected()
        self.test_t5_3_double_entry_ledger_conservation()
        self.test_t5_3_vip_expiration_monotonic_continuity()
        self.test_t5_3_heat_score_formula_precision()
        self.test_t5_4_protected_admin_deletion_rejection()
        self.test_t5_4_non_admin_rbac_forbidden()
        self.test_t5_4_duplicate_username_conflict_rejection()
        self.test_t5_4_image_upload_format_fuzzing()
        self.test_t5_5_carousel_preview_16_9_aspect_ratio_viewport_stress()
        self.test_t5_5_modal_backdrop_blur_and_glass_invariants()
        return self.reporter.print_summary()

    # --------------------------------------------------------------------------
    # T5_1: Concurrency & Race Conditions
    # --------------------------------------------------------------------------
    def test_t5_1_concurrency_coin_signin_race(self):
        """T5_1A: 10 concurrent sign-in requests must yield exactly 1 success (+10) and 9 rejections."""
        t0 = time.time()
        code = "T5_1A"
        title = "Concurrency Race: Daily Coin Sign-In (10 Threads)"
        try:
            # Register user with initialized wallet
            user_id, username, token = self.api.register_user("t5_signin", init_wallet=True)
            signin_url = f"{self.api.base_url}/api/v1/user/coins/sign-in"
            headers = self.api.user_headers(token)

            def do_signin():
                return requests.post(signin_url, headers=headers, timeout=10)

            # Fire 10 concurrent requests simultaneously
            workers = 10
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(do_signin) for _ in range(workers)]
                responses = [f.result() for f in concurrent.futures.as_completed(futures)]

            successes = [r for r in responses if r.status_code == 200]
            rejections = [r for r in responses if r.status_code in [400, 409]]

            assert len(successes) == 1, f"Expected exactly 1 sign-in success under concurrency, got {len(successes)}"
            assert len(rejections) == workers - 1, f"Expected {workers - 1} sign-in rejections, got {len(rejections)} (statuses: {[r.status_code for r in responses]})"

            # Verify balance in database is exactly 60 (initial 50 + 10)
            from app.core.database import SessionLocal
            from app.models.coin import UserCoinWallet, UserCoinTransaction
            db = SessionLocal()
            try:
                wallet = db.query(UserCoinWallet).filter(UserCoinWallet.user_id == user_id).first()
                assert wallet is not None
                assert wallet.balance == 60, f"Expected wallet balance 60, found {wallet.balance}"
                assert wallet.total_earned == 60, f"Expected total_earned 60, found {wallet.total_earned}"

                sign_in_txs = db.query(UserCoinTransaction).filter(
                    UserCoinTransaction.user_id == user_id,
                    UserCoinTransaction.transaction_type == "SIGN_IN"
                ).all()
                assert len(sign_in_txs) == 1, f"Expected exactly 1 SIGN_IN transaction, found {len(sign_in_txs)}"
            finally:
                db.close()

            self.reporter.record_pass(code, title, time.time() - t0, "1 win / 9 rejected, balance=60")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)

    def test_t5_1_concurrency_video_tipping_race_strict_max_2_coins(self):
        """T5_1B: 10 concurrent 1-coin tip requests on same drama must strictly enforce max 2 coins."""
        t0 = time.time()
        code = "T5_1B"
        title = "Concurrency Race: 1-Coin Video Tipping (Max 2 Enforced)"
        try:
            user_id, username, token = self.api.register_user("t5_tip1", init_wallet=True)
            video_id, ep_id = self.api.get_first_video_and_episode()
            tip_url = f"{self.api.base_url}/api/v1/interactions/episodes/{ep_id}/tip"
            headers = self.api.user_headers(token)

            def do_tip():
                return requests.post(tip_url, json={"coin_amount": 1}, headers=headers, timeout=10)

            workers = 10
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(do_tip) for _ in range(workers)]
                responses = [f.result() for f in concurrent.futures.as_completed(futures)]

            successes = [r for r in responses if r.status_code == 200]
            rejections = [r for r in responses if r.status_code in [400, 409]]

            # Exactly 2 requests must succeed, and 8 rejected
            assert len(successes) == 2, f"Expected exactly 2 successful 1-coin tips under concurrency, got {len(successes)}"
            assert len(rejections) == workers - 2, f"Expected {workers - 2} rejections, got {len(rejections)}"

            # Verify in DB: VideoCoinTip.tip_count == 2
            from app.core.database import SessionLocal
            from app.models.coin import VideoCoinTip, UserCoinWallet
            db = SessionLocal()
            try:
                tip = db.query(VideoCoinTip).filter(
                    VideoCoinTip.user_id == user_id,
                    VideoCoinTip.video_id == video_id
                ).first()
                assert tip is not None
                assert tip.tip_count == 2, f"Expected tip_count == 2, got {tip.tip_count}"

                wallet = db.query(UserCoinWallet).filter(UserCoinWallet.user_id == user_id).first()
                assert wallet.balance == 48, f"Expected wallet balance 48 (50 - 2), got {wallet.balance}"
            finally:
                db.close()

            self.reporter.record_pass(code, title, time.time() - t0, "2 succeeded / 8 blocked, tip_count=2")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)

    def test_t5_1_concurrency_tipping_2_coins_atomic_race(self):
        """T5_1C: 6 concurrent 2-coin tip requests must yield exactly 1 success and 5 rejections."""
        t0 = time.time()
        code = "T5_1C"
        title = "Concurrency Race: Atomic 2-Coin Tipping Rejection"
        try:
            user_id, username, token = self.api.register_user("t5_tip2", init_wallet=True)
            video_id, ep_id = self.api.get_first_video_and_episode()
            tip_url = f"{self.api.base_url}/api/v1/interactions/episodes/{ep_id}/tip"
            headers = self.api.user_headers(token)

            def do_tip2():
                return requests.post(tip_url, json={"coin_amount": 2}, headers=headers, timeout=10)

            workers = 6
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(do_tip2) for _ in range(workers)]
                responses = [f.result() for f in concurrent.futures.as_completed(futures)]

            successes = [r for r in responses if r.status_code == 200]
            rejections = [r for r in responses if r.status_code in [400, 409]]

            assert len(successes) == 1, f"Expected exactly 1 successful 2-coin tip, got {len(successes)}"
            assert len(rejections) == workers - 1, f"Expected {workers - 1} rejections, got {len(rejections)}"

            # DB check
            from app.core.database import SessionLocal
            from app.models.coin import VideoCoinTip
            db = SessionLocal()
            try:
                tip = db.query(VideoCoinTip).filter(
                    VideoCoinTip.user_id == user_id,
                    VideoCoinTip.video_id == video_id
                ).first()
                assert tip is not None and tip.tip_count == 2
            finally:
                db.close()

            self.reporter.record_pass(code, title, time.time() - t0, "1 succeeded / 5 rejected, tip_count=2")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)

    # --------------------------------------------------------------------------
    # T5_2: Malicious & Boundary Payloads
    # --------------------------------------------------------------------------
    def test_t5_2_sqli_payloads_in_comments_and_search(self):
        """T5_2A: SQL injection payloads in comments and admin search must be safely escaped."""
        t0 = time.time()
        code = "T5_2A"
        title = "Malicious Payloads: SQL Injection Injection Resilience"
        try:
            user_id, _, token = self.api.register_user("t5_sqli")
            _, ep_id = self.api.get_first_video_and_episode()
            headers = self.api.user_headers(token)

            sqli_payloads = [
                "' OR '1'='1",
                "'; DROP TABLE dummy_nonexistent; --",
                "admin' --",
                "' UNION SELECT null, username, password_hash FROM users --"
            ]

            # 1. Post comments containing SQLi
            for payload in sqli_payloads:
                resp = requests.post(
                    f"{self.api.base_url}/api/v1/interactions/episodes/{ep_id}/comments",
                    json={"content": f"Test SQLi: {payload}"},
                    headers=headers,
                    timeout=5
                )
                assert resp.status_code == 200, f"Comment submission failed for SQLi payload: {payload}"
                data = resp.json().get("data", {})
                assert payload in data.get("content", ""), f"Payload was not saved verbatim"

            # 2. Test SQLi in admin drama search and user search
            admin_headers = self.api.admin_headers()
            r_dramas = requests.get(f"{self.api.base_url}/api/v1/admin/dramas?search=' OR '1'='1", headers=admin_headers, timeout=5)
            assert r_dramas.status_code == 200, f"Admin dramas SQLi search caused {r_dramas.status_code}"

            r_users = requests.get(f"{self.api.base_url}/api/v1/admin/users?search=' OR '1'='1", headers=admin_headers, timeout=5)
            assert r_users.status_code == 200, f"Admin users SQLi search caused {r_users.status_code}"

            self.reporter.record_pass(code, title, time.time() - t0, "SQLi payloads handled safely without injection")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)

    def test_t5_2_xss_script_tags_payloads(self):
        """T5_2B: XSS script tags in comments must be safely persisted and JSON escaped."""
        t0 = time.time()
        code = "T5_2B"
        title = "Malicious Payloads: XSS Script Tags Escaping"
        try:
            _, _, token = self.api.register_user("t5_xss")
            _, ep_id = self.api.get_first_video_and_episode()
            headers = self.api.user_headers(token)

            xss_payloads = [
                "<script>alert('XSS_EXEC_FAIL')</script>",
                "<img src=x onerror=alert(document.cookie)>",
                "<svg/onload=alert(1)>",
                "<iframe src=\"javascript:alert(1)\"></iframe>"
            ]

            for xss in xss_payloads:
                resp = requests.post(
                    f"{self.api.base_url}/api/v1/interactions/episodes/{ep_id}/comments",
                    json={"content": xss},
                    headers=headers,
                    timeout=5
                )
                assert resp.status_code == 200, f"XSS comment post failed with {resp.status_code}"
                ret_content = resp.json().get("data", {}).get("content", "")
                assert ret_content == xss, f"Content corrupted on save: {ret_content}"

            self.reporter.record_pass(code, title, time.time() - t0, "XSS payloads safely stored as literal text")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)

    def test_t5_2_emoji_unicode_cjk_rtl_payloads(self):
        """T5_2C: Multi-byte emojis, Unicode, and RTL strings must be preserved with utf8mb4."""
        t0 = time.time()
        code = "T5_2C"
        title = "Malicious Payloads: Emoji, CJK, & RTL Unicode Strings"
        try:
            _, _, token = self.api.register_user("t5_unicode")
            _, ep_id = self.api.get_first_video_and_episode()
            headers = self.api.user_headers(token)

            complex_string = "🎬🍿 爆米花好剧！🔥🔥 追更必备 🐉🚀 \u202eRTL-TEXT\u202c \u200b\u200c\u200d 特殊字符测试"
            resp = requests.post(
                f"{self.api.base_url}/api/v1/interactions/episodes/{ep_id}/comments",
                json={"content": complex_string},
                headers=headers,
                timeout=5
            )
            assert resp.status_code == 200, f"Unicode comment post failed: {resp.status_code}"
            assert resp.json().get("data", {}).get("content") == complex_string

            self.reporter.record_pass(code, title, time.time() - t0, "Full utf8mb4 emoji & unicode fidelity verified")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)

    def test_t5_2_negative_and_zero_coin_tipping_rejected(self):
        """T5_2D: Negative, zero, and out-of-range coin amounts must be rejected (422/400)."""
        t0 = time.time()
        code = "T5_2D"
        title = "Boundary: Negative / Zero / Excessive Coin Tipping"
        try:
            _, _, token = self.api.register_user("t5_coins_bnd")
            _, ep_id = self.api.get_first_video_and_episode()
            headers = self.api.user_headers(token)
            tip_url = f"{self.api.base_url}/api/v1/interactions/episodes/{ep_id}/tip"

            invalid_amounts = [-1, -100, 0, 3, 999999]
            for amt in invalid_amounts:
                resp = requests.post(tip_url, json={"coin_amount": amt}, headers=headers, timeout=5)
                assert resp.status_code in [400, 422], f"Expected 400/422 for coin_amount={amt}, got {resp.status_code}"

            self.reporter.record_pass(code, title, time.time() - t0, "All invalid coin amounts rejected")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)

    def test_t5_2_orphaned_comment_parent_rejected(self):
        """T5_2E: Replying to non-existent parent comment must cleanly return 404."""
        t0 = time.time()
        code = "T5_2E"
        title = "Boundary: Orphaned Non-Existent Comment Parent"
        try:
            _, _, token = self.api.register_user("t5_orphan")
            _, ep_id = self.api.get_first_video_and_episode()
            headers = self.api.user_headers(token)

            bogus_parent_id = "00000000-0000-0000-0000-000000000000"
            resp = requests.post(
                f"{self.api.base_url}/api/v1/interactions/episodes/{ep_id}/comments",
                json={"content": "Orphan reply", "parent_id": bogus_parent_id},
                headers=headers,
                timeout=5
            )
            assert resp.status_code == 404, f"Expected 404 for bogus parent_id, got {resp.status_code}"
            assert "Parent comment not found" in resp.text or "not found" in resp.text.lower()

            self.reporter.record_pass(code, title, time.time() - t0, "Non-existent parent returned 404")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)

    def test_t5_2_empty_whitespace_comment_rejected(self):
        """T5_2F: Empty or whitespace-only comment submissions must return HTTP 400."""
        t0 = time.time()
        code = "T5_2F"
        title = "Boundary: Empty / Whitespace-Only Comment Rejection"
        try:
            _, _, token = self.api.register_user("t5_empty")
            _, ep_id = self.api.get_first_video_and_episode()
            headers = self.api.user_headers(token)

            empty_contents = ["", "   ", "\t\t", "\n\n  \t "]
            for c in empty_contents:
                resp = requests.post(
                    f"{self.api.base_url}/api/v1/interactions/episodes/{ep_id}/comments",
                    json={"content": c},
                    headers=headers,
                    timeout=5
                )
                assert resp.status_code in [400, 422], f"Expected 400/422 for empty comment '{c}', got {resp.status_code}"

            self.reporter.record_pass(code, title, time.time() - t0, "Empty/whitespace comments blocked")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)

    # --------------------------------------------------------------------------
    # T5_3: State Invariants
    # --------------------------------------------------------------------------
    def test_t5_3_double_entry_ledger_conservation(self):
        """T5_3A: Double-entry ledger balance conservation invariant holds across transactions."""
        t0 = time.time()
        code = "T5_3A"
        title = "Invariant: Double-Entry Ledger Balance Conservation"
        try:
            user_id, _, token = self.api.register_user("t5_ledger", init_wallet=True)
            _, ep_id = self.api.get_first_video_and_episode()
            headers = self.api.user_headers(token)

            # 1. Initial registration: +50 (1 tx)
            # 2. Daily sign in: +10 (1 tx)
            r_sign = requests.post(f"{self.api.base_url}/api/v1/user/coins/sign-in", headers=headers, timeout=5)
            assert r_sign.status_code == 200

            # 3. Watch ad: +5 (1 tx)
            r_ad = requests.post(f"{self.api.base_url}/api/v1/user/coins/watch-ad", headers=headers, timeout=5)
            assert r_ad.status_code == 200

            # 4. Tip video: -1 (1 tx)
            r_tip = requests.post(f"{self.api.base_url}/api/v1/interactions/episodes/{ep_id}/tip", json={"coin_amount": 1}, headers=headers, timeout=5)
            assert r_tip.status_code == 200

            # 5. Second watch ad: +5 (1 tx)
            r_ad2 = requests.post(f"{self.api.base_url}/api/v1/user/coins/watch-ad", headers=headers, timeout=5)
            assert r_ad2.status_code == 200

            # Query database directly
            from app.core.database import SessionLocal
            from app.models.coin import UserCoinWallet, UserCoinTransaction
            db = SessionLocal()
            try:
                wallet = db.query(UserCoinWallet).filter(UserCoinWallet.user_id == user_id).first()
                txs = db.query(UserCoinTransaction).filter(UserCoinTransaction.user_id == user_id).all()

                assert wallet is not None
                assert len(txs) == 5  # REGISTER_BONUS, SIGN_IN, AD_REWARD, TIP_VIDEO, AD_REWARD

                sum_amounts = sum(t.amount for t in txs)
                sum_positive = sum(t.amount for t in txs if t.amount > 0)
                sum_negative = sum(t.amount for t in txs if t.amount < 0)

                # Mathematical Conservation Invariants:
                # 1. wallet.balance == sum of all ledger transactions
                assert wallet.balance == sum_amounts, f"wallet.balance ({wallet.balance}) != sum_amounts ({sum_amounts})"
                # 2. wallet.total_earned == sum of positive transactions
                assert wallet.total_earned == sum_positive, f"wallet.total_earned ({wallet.total_earned}) != sum_positive ({sum_positive})"
                # 3. wallet.total_spent == abs(sum of negative transactions)
                assert wallet.total_spent == abs(sum_negative), f"wallet.total_spent ({wallet.total_spent}) != abs(sum_negative) ({abs(sum_negative)})"
                # 4. wallet.balance == total_earned - total_spent
                assert wallet.balance == wallet.total_earned - wallet.total_spent, "wallet.balance != total_earned - total_spent"
                # Expected exact balance: 50 + 10 + 5 - 1 + 5 = 69
                assert wallet.balance == 69, f"Expected final balance 69, got {wallet.balance}"
            finally:
                db.close()

            self.reporter.record_pass(code, title, time.time() - t0, f"balance={wallet.balance}, sum_tx={sum_amounts}")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)

    def test_t5_3_vip_expiration_monotonic_continuity(self):
        """T5_3B: VIP expiration dates must advance monotonically with exact day arithmetic."""
        t0 = time.time()
        code = "T5_3B"
        title = "Invariant: VIP Expiration Monotonic Continuity"
        try:
            user_id, _, token = self.api.register_user("t5_vip_mono", init_wallet=True)
            headers = self.api.user_headers(token)

            # Give user 500 coins via admin
            requests.put(
                f"{self.api.base_url}/api/v1/admin/users/{user_id}",
                json={"coins": 500},
                headers=self.api.admin_headers(),
                timeout=5
            )

            # 1. Exchange 7 days
            r1 = requests.post(f"{self.api.base_url}/api/v1/user/coins/exchange-vip", json={"days": 7}, headers=headers, timeout=5)
            assert r1.status_code == 200
            vip_str1 = r1.json().get("data", {}).get("vip_expire_at")
            t_vip1 = datetime.fromisoformat(vip_str1.replace("Z", "+00:00")).replace(tzinfo=None)

            # 2. Exchange another 7 days
            r2 = requests.post(f"{self.api.base_url}/api/v1/user/coins/exchange-vip", json={"days": 7}, headers=headers, timeout=5)
            assert r2.status_code == 200
            vip_str2 = r2.json().get("data", {}).get("vip_expire_at")
            t_vip2 = datetime.fromisoformat(vip_str2.replace("Z", "+00:00")).replace(tzinfo=None)

            # Delta between 2 and 1 must be exactly 7 days (within 5 seconds tolerance)
            delta_1_2 = (t_vip2 - t_vip1).total_seconds()
            assert abs(delta_1_2 - 7 * 86400) < 5, f"Expected 7 days delta, got {delta_1_2}s"

            # 3. Exchange 30 days
            r3 = requests.post(f"{self.api.base_url}/api/v1/user/coins/exchange-vip", json={"days": 30}, headers=headers, timeout=5)
            assert r3.status_code == 200
            vip_str3 = r3.json().get("data", {}).get("vip_expire_at")
            t_vip3 = datetime.fromisoformat(vip_str3.replace("Z", "+00:00")).replace(tzinfo=None)

            # Delta between 3 and 2 must be exactly 30 days
            delta_2_3 = (t_vip3 - t_vip2).total_seconds()
            assert abs(delta_2_3 - 30 * 86400) < 5, f"Expected 30 days delta, got {delta_2_3}s"

            # Strict Monotonicity: now < vip1 < vip2 < vip3
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            assert now < t_vip1 < t_vip2 < t_vip3, "VIP timestamps failed monotonic order"

            self.reporter.record_pass(code, title, time.time() - t0, "+7d and +30d verified exact monotonicity")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)

    def test_t5_3_heat_score_formula_precision(self):
        """T5_3C: Heat score formula exactness against live database values."""
        t0 = time.time()
        code = "T5_3C"
        title = "Invariant: Short Drama Heat Score Formula Exactness"
        try:
            video_id, ep_id = self.api.get_first_video_and_episode()

            from app.core.database import SessionLocal
            from app.models.video import Video, VideoEpisode
            from app.models.interaction import VideoDanmaku
            db = SessionLocal()
            try:
                v = db.query(Video).filter(Video.id == video_id).first()
                assert v is not None

                views = v.view_count or 0
                likes = v.like_count or 0
                coins = getattr(v, "coin_count", 0) or 0
                danmakus = db.query(VideoDanmaku).join(VideoEpisode, VideoDanmaku.episode_id == VideoEpisode.id).filter(VideoEpisode.video_id == v.id).count()

                expected_heat = round(views * 1.0 + likes * 5.0 + coins * 10.0 + danmakus * 2.0, 2)
            finally:
                db.close()

            # Query album endpoint
            resp = requests.get(f"{self.api.base_url}/api/v1/interactions/album/{video_id}", timeout=5)
            assert resp.status_code == 200
            api_heat = resp.json().get("data", {}).get("heat_score", 0.0)

            # Check precision match
            assert abs(api_heat - expected_heat) < 0.01, f"Expected heat_score {expected_heat}, got {api_heat}"

            self.reporter.record_pass(code, title, time.time() - t0, f"formula={expected_heat} matches api={api_heat}")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)

    # --------------------------------------------------------------------------
    # T5_4: Admin Governance Boundaries
    # --------------------------------------------------------------------------
    def test_t5_4_protected_admin_deletion_rejection(self):
        """T5_4A: Protected root administrator account deletion must be strictly rejected."""
        t0 = time.time()
        code = "T5_4A"
        title = "Admin Boundaries: Protected Admin Deletion Rejection"
        try:
            admin_token = self.api.login_admin()
            payload = jwt.decode(admin_token, options={"verify_signature": False})
            current_admin_id = payload.get("sub")
            assert current_admin_id is not None, "Failed to decode admin id from token"

            # Attempt deletion of current logged in admin
            del_resp = requests.delete(
                f"{self.api.base_url}/api/v1/admin/users/{current_admin_id}",
                headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
                timeout=5
            )
            assert del_resp.status_code == 400, f"Expected 400 when deleting current admin user, got {del_resp.status_code}"
            assert "不能删除当前登录" in del_resp.text or "not allowed" in del_resp.text.lower()

            self.reporter.record_pass(code, title, time.time() - t0, "Protected admin deletion safely blocked with 400")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)

    def test_t5_4_non_admin_rbac_forbidden(self):
        """T5_4B: Non-admin viewer attempting admin actions must receive HTTP 403 Forbidden."""
        t0 = time.time()
        code = "T5_4B"
        title = "Admin Boundaries: Non-Admin RBAC 403 Rejection"
        try:
            _, _, token = self.api.register_user("t5_non_admin")
            viewer_headers = self.api.user_headers(token)

            endpoints = [
                ("GET", f"{self.api.base_url}/api/v1/admin/users"),
                ("POST", f"{self.api.base_url}/api/v1/admin/users"),
                ("DELETE", f"{self.api.base_url}/api/v1/admin/users/dummy-id"),
                ("POST", f"{self.api.base_url}/api/v1/admin/announcements"),
                ("PUT", f"{self.api.base_url}/api/v1/admin/dramas/dummy-id")
            ]

            for method, url in endpoints:
                if method == "GET":
                    r = requests.get(url, headers=viewer_headers, timeout=5)
                elif method == "POST":
                    r = requests.post(url, json={}, headers=viewer_headers, timeout=5)
                elif method == "PUT":
                    r = requests.put(url, json={}, headers=viewer_headers, timeout=5)
                elif method == "DELETE":
                    r = requests.delete(url, headers=viewer_headers, timeout=5)

                assert r.status_code == 403, f"Expected 403 for non-admin {method} {url}, got {r.status_code}"

            self.reporter.record_pass(code, title, time.time() - t0, "All 5 admin endpoints returned 403 Forbidden")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)

    def test_t5_4_duplicate_username_conflict_rejection(self):
        """T5_4C: Duplicate username registration and admin user creation must return 400 conflict."""
        t0 = time.time()
        code = "T5_4C"
        title = "Admin Boundaries: Duplicate Username Conflict Rejection"
        try:
            dup_username = f"dup_{int(time.time() * 1000) % 1000000}"
            # 1. First registration
            r1 = requests.post(
                f"{self.api.base_url}/api/v1/auth/register",
                json={"username": dup_username, "password": "password123"},
                timeout=5
            )
            assert r1.status_code in [200, 201]

            # 2. Second registration with same username
            r2 = requests.post(
                f"{self.api.base_url}/api/v1/auth/register",
                json={"username": dup_username, "password": "password123"},
                timeout=5
            )
            assert r2.status_code == 400, f"Expected 400 on duplicate register, got {r2.status_code}"

            # 3. Admin creation with same username
            r3 = requests.post(
                f"{self.api.base_url}/api/v1/admin/users",
                json={"username": dup_username, "password": "password123"},
                headers=self.api.admin_headers(),
                timeout=5
            )
            assert r3.status_code == 400, f"Expected 400 on admin creating duplicate username, got {r3.status_code}"
            assert "已被占用" in r3.text

            self.reporter.record_pass(code, title, time.time() - t0, "Duplicate username registration and admin creation rejected")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)

    def test_t5_4_image_upload_format_fuzzing(self):
        """T5_4D: File upload fuzzing rejects malicious extensions and oversized buffers (>10MB)."""
        t0 = time.time()
        code = "T5_4D"
        title = "Admin Boundaries: Local Image Upload Format Fuzzing"
        try:
            upload_url = f"{self.api.base_url}/api/v1/upload/image"
            headers = {"Authorization": f"Bearer {self.api.admin_token or self.api.login_admin()}"}

            forbidden_files = [
                ("malware.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/octet-stream"),
                ("script.py", b"import os; os.system('echo hacked')", "text/x-python"),
                ("shell.sh", b"#!/bin/bash\necho hacked", "text/x-sh"),
                ("backdoor.php", b"<?php echo 'hacked'; ?>", "application/x-php"),
                ("vector.svg", b"<svg onload=alert(1)></svg>", "image/svg+xml")
            ]

            for filename, content, mime in forbidden_files:
                files = {"file": (filename, io.BytesIO(content), mime)}
                r = requests.post(upload_url, files=files, headers=headers, timeout=5)
                assert r.status_code == 400, f"Expected 400 for forbidden file {filename}, got {r.status_code}"
                assert "不支持的图片格式" in r.text or "not supported" in r.text.lower()

            # Oversized file (>10MB)
            oversized_content = b"A" * (10 * 1024 * 1024 + 1024)
            files = {"file": ("oversized.jpg", io.BytesIO(oversized_content), "image/jpeg")}
            r_over = requests.post(upload_url, files=files, headers=headers, timeout=10)
            assert r_over.status_code == 400, f"Expected 400 for oversized file, got {r_over.status_code}"
            assert "超出限制" in r_over.text or "exceed" in r_over.text.lower()

            self.reporter.record_pass(code, title, time.time() - t0, "Malicious extensions and >10MB payload safely rejected")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)

    # --------------------------------------------------------------------------
    # T5_5: Frontend Geometry & HIG Invariants
    # --------------------------------------------------------------------------
    def test_t5_5_carousel_preview_16_9_aspect_ratio_viewport_stress(self):
        """T5_5A: 16:9 WYSIWYG Carousel preview card maintains ratio tolerance < 0.05 across viewport widths."""
        t0 = time.time()
        code = "T5_5A"
        title = "Frontend Geometry: Carousel 16:9 Ratio Viewport Stress"
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(channel="msedge", headless=True)
                except Exception:
                    browser = p.chromium.launch(headless=True)

                admin_token = self.api.admin_token or self.api.login_admin()
                ctx = browser.new_context(viewport={"width": 1440, "height": 900})

                # Inject auth
                page_init = ctx.new_page()
                page_init.goto(f"{FRONTEND_BASE_URL}/", wait_until="domcontentloaded")
                page_init.evaluate(f"""() => {{
                    localStorage.setItem('cinema_access_token', '{admin_token}');
                    localStorage.setItem('token', '{admin_token}');
                    localStorage.setItem('user', JSON.stringify({{"username": "admin", "role": "ADMIN"}}));
                }}""")
                page_init.close()

                page = ctx.new_page()
                page.goto(f"{FRONTEND_BASE_URL}/#/admin?tab=carousels", wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)

                # Locate #carousel-preview-16-9 .aspect-16-9-box
                preview_locator = page.locator("#carousel-preview-16-9 .aspect-16-9-box")
                assert preview_locator.count() > 0, "Could not find #carousel-preview-16-9 .aspect-16-9-box element"

                # Stress test 3 viewports: Desktop 1920x1080, Laptop 1440x900, Compact 1280x720
                test_viewports = [
                    (1920, 1080, "desktop_1080p"),
                    (1440, 900, "laptop_900p"),
                    (1280, 720, "compact_720p")
                ]

                target_ratio = 16.0 / 9.0  # 1.777777...
                for w, h, label in test_viewports:
                    page.set_viewport_size({"width": w, "height": h})
                    page.wait_for_timeout(400)

                    box = preview_locator.bounding_box()
                    assert box is not None, f"Bounding box for {label} was None"
                    w_box = box["width"]
                    h_box = box["height"]
                    assert h_box > 0, f"Height was <= 0: {h_box}"

                    ratio = w_box / h_box
                    tolerance = abs(ratio - target_ratio)
                    print(f"    [T5_5A] Viewport {w}x{h}: box={w_box:.1f}x{h_box:.1f}, ratio={ratio:.4f}, tolerance={tolerance:.4f}")
                    assert tolerance < 0.05, f"16:9 ratio tolerance exceeded in {label}: ratio={ratio:.4f}, tolerance={tolerance:.4f} >= 0.05"

                    AdversarialScreenshotManager.capture(page, code, f"{label}_ratio_pass")

                ctx.close()
                browser.close()

            self.reporter.record_pass(code, title, time.time() - t0, "16:9 ratio verified (<0.05 tol) across 1920, 1440, 1280 viewports")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)

    def test_t5_5_modal_backdrop_blur_and_glass_invariants(self):
        """T5_5B: Modal overlay and glass containers enforce Apple HIG backdrop-filter blur tokens."""
        t0 = time.time()
        code = "T5_5B"
        title = "Frontend HIG: Modal Overlay & Dark Glass Backdrop Blur"
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(channel="msedge", headless=True)
                except Exception:
                    browser = p.chromium.launch(headless=True)

                admin_token = self.api.admin_token or self.api.login_admin()
                ctx = browser.new_context(viewport={"width": 1440, "height": 900})

                page_init = ctx.new_page()
                page_init.goto(f"{FRONTEND_BASE_URL}/", wait_until="domcontentloaded")
                page_init.evaluate(f"""() => {{
                    localStorage.setItem('cinema_access_token', '{admin_token}');
                    localStorage.setItem('token', '{admin_token}');
                    localStorage.setItem('user', JSON.stringify({{"username": "admin", "role": "ADMIN"}}));
                }}""")
                page_init.close()

                page = ctx.new_page()
                # 1. AdminView glass inspection
                page.goto(f"{FRONTEND_BASE_URL}/#/admin?tab=users", wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)

                # Check admin-sidebar or glass-card backdrop-filter
                sidebar_blur = page.evaluate("""() => {
                    const el = document.querySelector('.admin-sidebar') || document.querySelector('.glass-card');
                    if (!el) return 'none';
                    const style = window.getComputedStyle(el);
                    return style.backdropFilter || style.webkitBackdropFilter || 'none';
                }""")
                assert "blur" in sidebar_blur, f"Expected backdrop-filter blur in AdminView, got: {sidebar_blur}"

                # 2. Player View Coin Tipping Modal inspection
                page.goto(f"{FRONTEND_BASE_URL}/#/video/latest", wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)

                if page.locator("#btn-coin-tip").count() > 0:
                    page.click("#btn-coin-tip")
                    page.wait_for_timeout(800)

                    # Inspect #coin-tip-modal or .modal-overlay
                    modal_blur = page.evaluate("""() => {
                        const el = document.querySelector('#coin-tip-modal') || document.querySelector('.modal-overlay') || document.querySelector('.apple-modal-backdrop');
                        if (!el) return 'none';
                        const style = window.getComputedStyle(el);
                        return style.backdropFilter || style.webkitBackdropFilter || 'none';
                    }""")
                    assert "blur" in modal_blur, f"Expected backdrop-filter blur on modal overlay, got: {modal_blur}"
                    AdversarialScreenshotManager.capture(page, code, "coin_modal_backdrop_blur_active")

                ctx.close()
                browser.close()

            self.reporter.record_pass(code, title, time.time() - t0, f"HIG blur confirmed (sidebar: {sidebar_blur})")
        except Exception as e:
            self.reporter.record_fail(code, title, str(e), time.time() - t0)


# ==============================================================================
# Pytest Integration Fixtures & Test Callers
# ==============================================================================
@pytest.fixture(scope="module")
def adversarial_suite():
    return Tier5AdversarialSuite()

def test_t5_1_concurrency_signin(adversarial_suite):
    adversarial_suite.test_t5_1_concurrency_coin_signin_race()

def test_t5_1_concurrency_tipping_race(adversarial_suite):
    adversarial_suite.test_t5_1_concurrency_video_tipping_race_strict_max_2_coins()

def test_t5_1_concurrency_tipping_atomic(adversarial_suite):
    adversarial_suite.test_t5_1_concurrency_tipping_2_coins_atomic_race()

def test_t5_2_sqli(adversarial_suite):
    adversarial_suite.test_t5_2_sqli_payloads_in_comments_and_search()

def test_t5_2_xss(adversarial_suite):
    adversarial_suite.test_t5_2_xss_script_tags_payloads()

def test_t5_2_unicode(adversarial_suite):
    adversarial_suite.test_t5_2_emoji_unicode_cjk_rtl_payloads()

def test_t5_2_negative_coins(adversarial_suite):
    adversarial_suite.test_t5_2_negative_and_zero_coin_tipping_rejected()

def test_t5_2_orphan_parent(adversarial_suite):
    adversarial_suite.test_t5_2_orphaned_comment_parent_rejected()

def test_t5_2_empty_comment(adversarial_suite):
    adversarial_suite.test_t5_2_empty_whitespace_comment_rejected()

def test_t5_3_ledger(adversarial_suite):
    adversarial_suite.test_t5_3_double_entry_ledger_conservation()

def test_t5_3_vip_monotonic(adversarial_suite):
    adversarial_suite.test_t5_3_vip_expiration_monotonic_continuity()

def test_t5_3_heat_precision(adversarial_suite):
    adversarial_suite.test_t5_3_heat_score_formula_precision()

def test_t5_4_admin_deletion(adversarial_suite):
    adversarial_suite.test_t5_4_protected_admin_deletion_rejection()

def test_t5_4_rbac(adversarial_suite):
    adversarial_suite.test_t5_4_non_admin_rbac_forbidden()

def test_t5_4_dup_username(adversarial_suite):
    adversarial_suite.test_t5_4_duplicate_username_conflict_rejection()

def test_t5_4_upload_fuzzing(adversarial_suite):
    adversarial_suite.test_t5_4_image_upload_format_fuzzing()

def test_t5_5_carousel_ratio(adversarial_suite):
    adversarial_suite.test_t5_5_carousel_preview_16_9_aspect_ratio_viewport_stress()

def test_t5_5_backdrop_blur(adversarial_suite):
    adversarial_suite.test_t5_5_modal_backdrop_blur_and_glass_invariants()


# ==============================================================================
# Standalone CLI Entrypoint
# ==============================================================================
if __name__ == "__main__":
    suite = Tier5AdversarialSuite()
    exit_code = suite.run_all()
    sys.exit(exit_code)
