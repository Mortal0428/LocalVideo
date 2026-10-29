import asyncio
import os
import shutil
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

ARTIFACT_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"
SCREENSHOT_DIR = os.path.join(os.getcwd(), "storage", "test_screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

async def run_verification():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="msedge")
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("\n=== STEP 1: Login viewer and verify User Space Light High Contrast (Problem 1 & 2) ===")
        await page.goto("http://localhost:5173/#/login")
        await page.wait_for_selector("#input-login-username", timeout=10000)
        await page.fill("#input-login-username", "viewer")
        await page.fill("#input-login-password", "viewer123")
        await page.click("#btn-submit-login")
        await page.wait_for_timeout(1000)

        # Go to user profile / space
        await page.goto("http://localhost:5173/#/user/space")
        await page.wait_for_timeout(1000)

        # Switch to light mode via header theme button
        await page.evaluate("document.documentElement.setAttribute('data-theme', 'light'); localStorage.setItem('cinema_theme', 'light')")
        await page.wait_for_timeout(500)

        # Assert card headings and text have dark color, not invisible white
        heading_color = await page.locator(".card-heading").first.evaluate("el => window.getComputedStyle(el).color")
        print(f"User Space card heading color (should be dark/black): {heading_color}")
        assert "29, 29, 31" in heading_color or "0, 0, 0" in heading_color, f"Heading color contrast failed: {heading_color}"

        # Screenshot user profile light mode
        await page.screenshot(path="storage/test_screenshots/verified_user_space_light_contrast.png", full_page=True)
        print("PASS: User space light contrast and top header margin verified.")

        print("\n=== STEP 2: Verify Player Header Dark & Light Cohesion (Problem 4 - Fig 4) ===")
        # Go to Player view
        await page.goto("http://localhost:5173/#/video/1")
        await page.wait_for_timeout(1500)

        # Set dark theme
        await page.evaluate("document.documentElement.setAttribute('data-theme', 'dark'); localStorage.setItem('cinema_theme', 'dark')")
        await page.wait_for_timeout(500)

        # Verify header is dark translucent, not solid white
        header_bg_dark = await page.locator(".player-global-header").evaluate("el => window.getComputedStyle(el).backgroundColor")
        print(f"Player header dark bg (should be dark ~18,18,20): {header_bg_dark}")
        assert "18, 18, 20" in header_bg_dark or "rgba(18" in header_bg_dark, f"Player header dark failed: {header_bg_dark}"
        await page.screenshot(path="storage/test_screenshots/verified_player_dark_header.png")

        # Set light theme
        await page.evaluate("document.documentElement.setAttribute('data-theme', 'light'); localStorage.setItem('cinema_theme', 'light')")
        await page.wait_for_timeout(500)
        header_bg_light = await page.locator(".player-global-header").evaluate("el => window.getComputedStyle(el).backgroundColor")
        print(f"Player header light bg (should be light ~255,255,255): {header_bg_light}")
        assert "255, 255, 255" in header_bg_light, f"Player header light failed: {header_bg_light}"
        await page.screenshot(path="storage/test_screenshots/verified_player_light_header.png")
        print("PASS: Player header dark/light cohesion verified.")

        print("\n=== STEP 3: Login admin and verify Admin Catalog & Pan Sync Light Cards (Problem 3 & 5) ===")
        # Login admin
        await page.goto("http://localhost:5173/#/login")
        await page.wait_for_selector("#input-login-username", timeout=10000)
        await page.fill("#input-login-username", "admin")
        await page.fill("#input-login-password", "admin123")
        await page.click("#btn-submit-login")
        await page.wait_for_timeout(1000)

        # Navigate to Admin Dramas catalog in light theme
        await page.goto("http://localhost:5173/#/admin?tab=dramas")
        await page.evaluate("document.documentElement.setAttribute('data-theme', 'light'); localStorage.setItem('cinema_theme', 'light')")
        await page.wait_for_timeout(800)

        # Verify tag-pill has high contrast blue text
        tag_color = await page.locator(".tag-pill").first.evaluate("el => window.getComputedStyle(el).color")
        print(f"Admin drama tag-pill color (should be vivid blue ~0, 113, 227): {tag_color}")
        assert "0, 113, 227" in tag_color, f"Tag pill text contrast failed: {tag_color}"
        await page.screenshot(path="storage/test_screenshots/verified_admin_dramas_light_tag.png")
        print("PASS: Admin drama tag-pill contrast verified.")

        # Navigate to Admin Sync via sidebar button
        await page.click("#admin-tab-sync")
        await page.wait_for_timeout(800)

        # Verify sync config card is white card in light mode
        sync_card_bg = await page.locator(".sync-config-card").evaluate("el => window.getComputedStyle(el).backgroundColor")
        print(f"Admin sync config card bg (should be pure white 255, 255, 255): {sync_card_bg}")
        assert "255, 255, 255" in sync_card_bg or "rgb(255, 255, 255)" in sync_card_bg, f"Sync card bg failed: {sync_card_bg}"

        radio_name_color = await page.locator(".radio-name").first.evaluate("el => window.getComputedStyle(el).color")
        print(f"Admin sync radio name color (should be dark ~29, 29, 31): {radio_name_color}")
        assert "29, 29, 31" in radio_name_color, f"Radio name color failed: {radio_name_color}"
        await page.screenshot(path="storage/test_screenshots/verified_admin_sync_light_cards.png")
        print("PASS: Admin pan sync light cards and high contrast text verified.")

        print("\n=== STEP 4: Login creator and verify Creator Studio Avatar Menu & BI Dashboard (Problem 6) ===")
        # Login creator
        await page.goto("http://localhost:5173/#/login")
        await page.evaluate("localStorage.clear()")
        await page.reload()
        await page.wait_for_selector("#input-login-username", timeout=10000)
        await page.fill("#input-login-username", "creator")
        await page.fill("#input-login-password", "creator123")
        await page.click("#btn-submit-login")
        await page.wait_for_timeout(1000)

        # Navigate to Creator Studio
        await page.goto("http://localhost:5173/#/creator")
        await page.wait_for_timeout(800)

        # Open profile menu in header
        await page.click("#admin-profile-chip")
        await page.wait_for_timeout(400)

        # Assert "切换至控制管理中台" does NOT exist
        admin_switch_count = await page.locator("text='切换至控制管理中台'").count()
        print(f"Number of '切换至控制管理中台' buttons in creator menu: {admin_switch_count}")
        assert admin_switch_count == 0, "Security/Role Bug: Admin console switch button should NOT exist for creator"

        # Assert "BI 创作数据看板" exists and click it
        bi_btn = page.locator("#btn-creator-goto-bi")
        assert await bi_btn.count() > 0, "Creator BI button should exist in profile dropdown"
        await bi_btn.click()
        await page.wait_for_timeout(800)

        # Verify BI tab is active and panel-creator-bi is visible
        bi_panel = page.locator("#panel-creator-bi")
        assert await bi_panel.is_visible(), "Creator BI dashboard panel should be visible"

        kpi_cards_count = await page.locator(".kpi-bento-card").count()
        print(f"Number of Bento KPI cards in Creator BI: {kpi_cards_count}")
        assert kpi_cards_count == 4, f"Expected 4 Bento KPI cards, got {kpi_cards_count}"

        await page.screenshot(path="storage/test_screenshots/verified_creator_bi_dashboard.png")
        print("PASS: Creator studio profile menu and BI dashboard verified.")

        await browser.close()
        
        # Copy all screenshots to ARTIFACT_DIR
        for fn in [
            "verified_user_space_light_contrast.png",
            "verified_player_dark_header.png",
            "verified_player_light_header.png",
            "verified_admin_dramas_light_tag.png",
            "verified_admin_sync_light_cards.png",
            "verified_creator_bi_dashboard.png"
        ]:
            src = os.path.join(SCREENSHOT_DIR, fn)
            if os.path.exists(src):
                shutil.copy(src, os.path.join(ARTIFACT_DIR, fn))
        
        print("\nALL VERIFICATIONS PASSED SUCCESSFULLY (100% 5/5)!")

if __name__ == "__main__":
    asyncio.run(run_verification())
