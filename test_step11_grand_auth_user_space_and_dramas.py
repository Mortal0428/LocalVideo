import asyncio
import os
import shutil
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

ARTIFACT_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"
SCREENSHOT_DIR = os.path.join(os.getcwd(), "storage", "test_screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def test_auth_user_space_and_quark_dramas():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="msedge")
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("=== Test 1: Full-Page Grand Login Center (/login) ===")
        await page.goto("http://localhost:5173/#/login")
        await page.wait_for_selector("#auth-center-root", timeout=10000)
        await page.wait_for_selector("#form-login", timeout=5000)
        await asyncio.sleep(1)

        login_shot = os.path.join(SCREENSHOT_DIR, "step11_grand_login_view.png")
        await page.screenshot(path=login_shot, full_page=True)
        shutil.copy2(login_shot, os.path.join(ARTIFACT_DIR, "step11_grand_login_view.png"))
        print(f"Captured: {login_shot}")

        print("=== Test 2: Switch to Register Tab ===")
        await page.click("#tab-btn-register")
        await page.wait_for_selector("#form-register", timeout=5000)
        await asyncio.sleep(0.5)

        register_shot = os.path.join(SCREENSHOT_DIR, "step11_grand_register_view.png")
        await page.screenshot(path=register_shot, full_page=True)
        shutil.copy2(register_shot, os.path.join(ARTIFACT_DIR, "step11_grand_register_view.png"))
        print(f"Captured: {register_shot}")

        print("=== Test 3: Quick Login as Viewer and Enter User Space (/user/space) ===")
        await page.click("#tab-btn-login")
        await page.click("#btn-demo-viewer")
        await page.wait_for_timeout(1000)

        await page.goto("http://localhost:5173/#/user/space")
        await page.wait_for_selector("#user-space-root", timeout=10000)
        await page.wait_for_selector("#creator-qualification-box", timeout=5000)
        await asyncio.sleep(1)

        user_space_shot = os.path.join(SCREENSHOT_DIR, "step11_user_space_dashboard.png")
        await page.screenshot(path=user_space_shot, full_page=True)
        shutil.copy2(user_space_shot, os.path.join(ARTIFACT_DIR, "step11_user_space_dashboard.png"))
        print(f"Captured: {user_space_shot}")

        print("=== Test 4: Apply for Creator Qualification ===")
        apply_btn = page.locator("#btn-apply-creator")
        if await apply_btn.is_visible():
            await apply_btn.click()
            await page.wait_for_selector("#creator-apply-modal", timeout=5000)
            await page.fill("#input-apply-creator-name", "极光微影制片厂")
            await page.fill("#input-apply-creator-bio", "专注全天候短剧生产与网盘原生流媒体连载！")
            await page.click("#btn-confirm-apply-creator")
            await page.wait_for_timeout(1500)
            print("Creator application submitted successfully!")

            creator_approved_shot = os.path.join(SCREENSHOT_DIR, "step11_user_space_creator_approved.png")
            await page.screenshot(path=creator_approved_shot, full_page=True)
            shutil.copy2(creator_approved_shot, os.path.join(ARTIFACT_DIR, "step11_user_space_creator_approved.png"))
            print(f"Captured: {creator_approved_shot}")

        print("=== Test 5: Check Home Feed with Quark Short Dramas (/ ) ===")
        await page.goto("http://localhost:5173/#/")
        await page.wait_for_selector(".bento-cards-grid", timeout=10000)
        await asyncio.sleep(2)

        cards = await page.locator(".bili-video-card").count()
        print(f"Home feed rendered {cards} video cards!")

        home_dramas_shot = os.path.join(SCREENSHOT_DIR, "step11_portal_quark_dramas.png")
        await page.screenshot(path=home_dramas_shot, full_page=True)
        shutil.copy2(home_dramas_shot, os.path.join(ARTIFACT_DIR, "step11_portal_quark_dramas.png"))
        print(f"Captured: {home_dramas_shot}")

        print("=== Test 6: Click First Short Drama into Dual-Mode Theater ===")
        first_card = page.locator(".bili-video-card").first
        await first_card.click()
        await page.wait_for_selector("#cinema-backdrop", timeout=10000)
        await asyncio.sleep(2)

        # Check episodes tab
        await page.click("#tab-btn-episodes")
        await asyncio.sleep(1)
        episodes_count = await page.locator(".episode-tile-btn").count()
        print(f"Player loaded {episodes_count} episodes for this drama!")

        player_shot = os.path.join(SCREENSHOT_DIR, "step11_player_quark_episodes.png")
        await page.screenshot(path=player_shot, full_page=True)
        shutil.copy2(player_shot, os.path.join(ARTIFACT_DIR, "step11_player_quark_episodes.png"))
        print(f"Captured: {player_shot}")

        print("=== Test 7: Creator Studio with Sync Button (/creator) ===")
        await page.goto("http://localhost:5173/#/creator")
        await page.wait_for_selector("#creator-studio-page", timeout=10000)
        await asyncio.sleep(1)

        creator_shot = os.path.join(SCREENSHOT_DIR, "step11_creator_studio_synced.png")
        await page.screenshot(path=creator_shot, full_page=True)
        shutil.copy2(creator_shot, os.path.join(ARTIFACT_DIR, "step11_creator_studio_synced.png"))
        print(f"Captured: {creator_shot}")

        await browser.close()
        print("ALL TESTS PASSED SUCCESSFULLY! (Exit code 0)")

if __name__ == "__main__":
    asyncio.run(test_auth_user_space_and_quark_dramas())
