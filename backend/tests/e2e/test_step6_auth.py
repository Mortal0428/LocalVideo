import os
import sys
import asyncio
import uvicorn
from multiprocessing import Process
from playwright.async_api import async_playwright

# Ensure backend root is on sys.path and configure UTF-8 output
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8006, log_level="warning")

async def test_step6_auth_and_roles():
    print("\n[Playwright E2E] Starting Phase 2: User Authentication & Role-Based Access Control Test...")
    
    server_process = Process(target=run_server, daemon=True)
    server_process.start()
    await asyncio.sleep(2.5)

    try:
        async with async_playwright() as p:
            print("[Playwright E2E] Launching Edge (Chromium) in Headless mode...")
            browser = await p.chromium.launch(headless=True, channel="msedge")
            context = await browser.new_context(viewport={"width": 1280, "height": 800})
            page = await context.new_page()

            print("[Playwright E2E] Navigating to http://127.0.0.1:8006 ...")
            await page.goto("http://127.0.0.1:8006", wait_until="networkidle")

            # 1. Verify Initial Guest State
            guest_badge = page.locator("#guest-badge")
            await guest_badge.wait_for(state="visible", timeout=5000)
            badge_text = await guest_badge.inner_text()
            print(f"[Playwright E2E] [OK] Initial status confirmed: '{badge_text}'")
            assert "游客" in badge_text

            # 2. Test Guest Interaction Interception (Smooth Pop-up without page reload)
            print("[Playwright E2E] Clicking Like button as Guest to trigger smooth auth modal...")
            like_btn = page.locator("#btn-like")
            await like_btn.click()

            # Verify Auth Modal appears
            auth_modal = page.locator("#modal-auth-card")
            await auth_modal.wait_for(state="visible", timeout=4000)
            notice_banner = page.locator("#auth-notice-banner")
            notice_text = await notice_banner.inner_text()
            print(f"[Playwright E2E] [OK] Auth modal popped up with notice: '{notice_text}'")
            assert "请先登录" in notice_text

            # 3. Test Registration Flow
            print("[Playwright E2E] Switching to '注册新账号' tab...")
            tab_register = page.locator("#tab-auth-register")
            await tab_register.click()
            await page.wait_for_timeout(300)

            unique_suffix = int(asyncio.get_event_loop().time() * 1000) % 10000
            test_username = f"e2e_user_{unique_suffix}"
            test_password = "password12345"
            test_nickname = f"特邀评剧官_{unique_suffix}"

            print(f"[Playwright E2E] Registering user: {test_username} / {test_nickname} ...")
            await page.fill("#auth-input-username", test_username)
            await page.fill("#auth-input-password", test_password)
            await page.fill("#auth-input-nickname", test_nickname)

            await page.click("#btn-submit-auth")
            await page.wait_for_timeout(1000)

            # 4. Verify Logged-In State
            user_display = page.locator("#user-display-name")
            await user_display.wait_for(state="visible", timeout=6000)
            name_text = await user_display.inner_text()
            print(f"[Playwright E2E] [OK] User logged in: '{name_text}'")
            assert test_nickname in name_text

            user_role_badge = page.locator("#user-role-badge")
            role_text = await user_role_badge.inner_text()
            print(f"[Playwright E2E] [OK] User role badge: '{role_text}'")
            assert "观众" in role_text

            # 5. Test Quick Role Switch in Top Nav
            print("[Playwright E2E] Testing quick role switch to 'CREATOR'...")
            btn_role_creator = page.locator("#btn-role-creator")
            await btn_role_creator.click()
            await page.wait_for_timeout(800)

            creator_role_text = await user_role_badge.inner_text()
            print(f"[Playwright E2E] [OK] Switched to Creator role: '{creator_role_text}'")
            assert "创作者" in creator_role_text

            print("[Playwright E2E] Testing quick role switch to 'REVIEWER'...")
            btn_role_reviewer = page.locator("#btn-role-reviewer")
            await btn_role_reviewer.click()
            await page.wait_for_timeout(800)

            reviewer_role_text = await user_role_badge.inner_text()
            print(f"[Playwright E2E] [OK] Switched to Reviewer role: '{reviewer_role_text}'")
            assert "审核员" in reviewer_role_text

            # 6. Test Logout
            print("[Playwright E2E] Testing logout...")
            btn_logout = page.locator("#btn-logout")
            await btn_logout.click()
            await page.wait_for_timeout(500)

            await guest_badge.wait_for(state="visible", timeout=4000)
            guest_text = await guest_badge.inner_text()
            print(f"[Playwright E2E] [OK] Logged out successfully, back to: '{guest_text}'")
            assert "游客" in guest_text

            await browser.close()
            print("\n==========================================================================")
            print("  [PLAYWRIGHT E2E PASSED] Phase 2: User Auth & Multi-Roles Passed 100%!")
            print("==========================================================================\n")

    finally:
        server_process.terminate()
        server_process.join()

if __name__ == "__main__":
    asyncio.run(test_step6_auth_and_roles())
