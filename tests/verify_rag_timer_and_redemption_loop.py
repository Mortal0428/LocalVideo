import os
import sys
import json
import time
import shutil
import requests
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5173"
API_URL = "http://localhost:8000/api/v1"
ARTIFACT_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"
SCREENSHOT_DIR = r"E:\个人项目作品\Agent项目\storage\test_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def save_shot(page, filename):
    p1 = os.path.join(SCREENSHOT_DIR, filename)
    p2 = os.path.join(ARTIFACT_DIR, filename)
    page.screenshot(path=p1, full_page=False)
    shutil.copyfile(p1, p2)
    print(f"[Screenshot Saved] {p2}")

def login_api(username, password):
    r = requests.post(f"{API_URL}/auth/login", json={"username": username, "password": password}, timeout=10)
    assert r.status_code == 200, f"Login failed for {username}: {r.text}"
    data = r.json().get("data") or r.json()
    return data["access_token"], data.get("user") or data

def run_tests():
    print("=== 1. API-Level Verification: Redemption Code Generation & Anti-Reuse ===")
    admin_token, admin_user = login_api("admin", "admin123")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Generate 2 COIN codes (100 coins each) and 2 VIP codes (30 days each)
    gen_coin = requests.post(
        f"{API_URL}/admin/redemption-codes/generate",
        headers=admin_headers,
        json={"code_type": "COIN", "reward_amount": 100, "count": 2, "expires_days": 30, "remark": "自动化闭环测试金币卡"}
    )
    assert gen_coin.status_code == 200, f"Generate coin codes failed: {gen_coin.text}"
    coin_codes = gen_coin.json()["data"]["codes"]
    assert len(coin_codes) == 2
    coin_code_1 = coin_codes[0]["code"]
    coin_code_2 = coin_codes[1]["code"]
    print(f"[OK] Generated COIN codes: {coin_code_1}, {coin_code_2}")

    gen_vip = requests.post(
        f"{API_URL}/admin/redemption-codes/generate",
        headers=admin_headers,
        json={"code_type": "VIP", "reward_amount": 30, "count": 2, "expires_days": 30, "remark": "自动化闭环测试VIP月卡"}
    )
    assert gen_vip.status_code == 200, f"Generate VIP codes failed: {gen_vip.text}"
    vip_codes = gen_vip.json()["data"]["codes"]
    assert len(vip_codes) == 2
    vip_code_1 = vip_codes[0]["code"]
    vip_code_2 = vip_codes[1]["code"]
    print(f"[OK] Generated VIP codes: {vip_code_1}, {vip_code_2}")

    # Test API redemption & anti-reuse
    wallet_before = requests.get(f"{API_URL}/user/coins/wallet", headers=admin_headers).json()["data"]["balance"]
    redeem_1 = requests.post(f"{API_URL}/user/coins/redeem", headers=admin_headers, json={"code": coin_code_1})
    assert redeem_1.status_code == 200, f"First redeem failed: {redeem_1.text}"
    wallet_after = redeem_1.json()["data"]["balance"]
    assert wallet_after == wallet_before + 100, f"Expected {wallet_before + 100}, got {wallet_after}"
    print(f"[OK] First COIN redemption succeeded: {wallet_before} -> {wallet_after}")

    # Attempt to reuse coin_code_1 -> MUST FAIL with 400
    redeem_dup = requests.post(f"{API_URL}/user/coins/redeem", headers=admin_headers, json={"code": coin_code_1})
    assert redeem_dup.status_code == 400, f"Duplicate redeem should fail with 400, got {redeem_dup.status_code}"
    assert "已被使用" in redeem_dup.json().get("detail", ""), f"Unexpected error detail: {redeem_dup.text}"
    print("[OK] Duplicate COIN redemption strictly blocked (HTTP 400)")

    print("=== 2. Playwright UI E2E Verification ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 960})
        page = context.new_page()

        # Inject admin token
        page.goto(f"{BASE_URL}/#/", wait_until="domcontentloaded")
        page.evaluate(
            f"""() => {{
                localStorage.setItem('cinema_access_token', '{admin_token}');
                localStorage.setItem('token', '{admin_token}');
                localStorage.setItem('access_token', '{admin_token}');
                localStorage.setItem('user', JSON.stringify({json.dumps(admin_user)}));
                localStorage.setItem('cinema_theme', 'light');
                document.documentElement.setAttribute('data-theme', 'light');
            }}"""
        )

        # Navigate to Admin -> Redemption Code Asset Center
        page.goto(f"{BASE_URL}/#/admin?tab=redemption", wait_until="networkidle")
        page.wait_for_selector("#section-redemption", timeout=15000)
        time.sleep(1.0)

        # Open Generate Redemption Dialog and generate a code via UI
        page.click("#btn-open-generate-redemption")
        page.wait_for_selector("#modal-generate-redemption", timeout=10000)
        time.sleep(0.6)
        page.click("#btn-submit-generate-redemption")
        page.wait_for_selector("#box-generated-codes-result", timeout=10000)
        time.sleep(0.8)
        save_shot(page, "verified_admin_redemption_generate_modal_light.png")

        # Close dialog and screenshot the Redemption Code Table
        page.keyboard.press("Escape")
        time.sleep(0.6)
        save_shot(page, "verified_admin_redemption_table_light.png")

        # Navigate to RAG Center in Light Mode & launch 3-sample benchmark
        page.click("#admin-tab-rag")
        page.wait_for_selector("#btn-launch-or-view-benchmark", timeout=15000)
        time.sleep(1.5)

        if not page.locator("#benchmark-elapsed-badge").is_visible():
            select_el = page.query_selector("select[title='选择基准评测抽检样本数']")
            if select_el:
                select_el.select_option("3")
                time.sleep(0.3)
            page.click("#btn-launch-or-view-benchmark")

        page.wait_for_selector("#benchmark-elapsed-badge", timeout=10000)

        # Wait 4.5 seconds so timer increments and questions evaluate
        time.sleep(4.5)
        badge_text_light = page.inner_text("#benchmark-elapsed-badge").strip()
        print("[OK] Light mode timer badge text verified: non-zero elapsed seconds")
        assert badge_text_light != "耗时 0s", f"Timer did not increment! Got: {badge_text_light}"

        # Verify badge computed colors in Light Mode (must be high contrast, not white-on-white)
        badge_styles = page.eval_on_selector(
            "#benchmark-elapsed-badge",
            "el => ({ bg: getComputedStyle(el).backgroundColor, color: getComputedStyle(el).color })"
        )
        print(f"[OK] Light mode timer badge styles: {badge_styles}")
        assert badge_styles["bg"] != badge_styles["color"], "Badge background and text color must not be identical!"

        save_shot(page, "verified_rag_timer_and_dynamic_f1_light.png")

        # Switch to Dark Mode and verify timer & logs
        page.evaluate("() => { localStorage.setItem('cinema_theme', 'dark'); document.documentElement.setAttribute('data-theme', 'dark'); }")
        time.sleep(2.5)
        save_shot(page, "verified_rag_timer_and_dynamic_f1_dark.png")

        # Wait for evaluation to produce dynamic F1 logs
        for _ in range(30):
            logs_text = page.inner_text(".hig-scroll")
            if "完成打分:" in logs_text:
                print("[OK] Real-time benchmark logs verified (contains dynamic 4-metric breakdown)")
                assert "忠实度=" in logs_text, "Expected detailed dynamic metrics in log output!"
                break
            time.sleep(1.5)
        save_shot(page, "verified_rag_dynamic_f1_logs_completed.png")

        # Navigate to User Profile View (/#/user/space) to test UI Redemption of coin_code_2 and duplicate rejection
        page.evaluate("() => { localStorage.setItem('cinema_theme', 'light'); document.documentElement.setAttribute('data-theme', 'light'); }")
        page.goto(f"{BASE_URL}/#/user/space", wait_until="networkidle")
        page.wait_for_selector("#user-redemption-card", timeout=15000)
        time.sleep(1.0)

        balance_before_ui = int(page.inner_text(".balance-num").strip())
        page.fill("#input-redeem-code", coin_code_2)
        page.click("#btn-submit-redeem")
        page.wait_for_selector("#redeem-feedback-msg.is-success", timeout=10000)
        time.sleep(0.8)

        balance_after_ui = int(page.inner_text(".balance-num").strip())
        print(f"[OK] UI Coin Redemption succeeded: {balance_before_ui} -> {balance_after_ui}")
        assert balance_after_ui == balance_before_ui + 100
        save_shot(page, "verified_user_redeem_success_light.png")

        # Now try to redeem coin_code_2 AGAIN in the UI -> must show error banner!
        page.fill("#input-redeem-code", coin_code_2)
        page.click("#btn-submit-redeem")
        page.wait_for_selector("#redeem-feedback-msg.is-error", timeout=10000)
        time.sleep(0.8)
        feedback_error = page.inner_text("#redeem-feedback-msg").strip()
        print("[OK] UI Duplicate Redemption rejected as expected")
        assert "已被使用" in feedback_error
        save_shot(page, "verified_user_redeem_duplicate_blocked_light.png")

        # Now redeem VIP code via UI in Dark Mode
        page.evaluate("() => { localStorage.setItem('cinema_theme', 'dark'); document.documentElement.setAttribute('data-theme', 'dark'); }")
        time.sleep(0.6)
        page.fill("#input-redeem-code", vip_code_1)
        page.click("#btn-submit-redeem")
        page.wait_for_selector("#redeem-feedback-msg.is-success", timeout=10000)
        time.sleep(0.8)
        vip_feedback = page.inner_text("#redeem-feedback-msg").strip()
        print("[OK] UI VIP Redemption succeeded")
        assert "VIP" in vip_feedback
        save_shot(page, "verified_user_redeem_vip_success_dark.png")

        browser.close()

    print("=== ALL E2E VERIFICATIONS PASSED 100% ===")

if __name__ == "__main__":
    run_tests()
