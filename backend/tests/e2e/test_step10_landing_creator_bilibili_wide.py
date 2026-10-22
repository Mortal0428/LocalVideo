import os
import sys
import asyncio
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

SCREENSHOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "storage", "test_screenshots"))
BRAIN_ARTIFACT_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(BRAIN_ARTIFACT_DIR, exist_ok=True)

async def run_step10_test():
    print(">>> [Playwright E2E] Starting Step 10: Landing Showcase, Creator Studio & Bilibili Fluid Layout Test...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="msedge")
        # Use wide 1720x980 viewport to verify relaxed wide Bilibili layout
        context = await browser.new_context(viewport={"width": 1720, "height": 980})
        page = await context.new_page()

        # -------------------------------------------------------------
        # 1. Test Landing Page Showcase
        # -------------------------------------------------------------
        print("\n--- 1. Testing Landing Page Showcase (/landing) ---")
        await page.goto("http://localhost:5173/#/landing", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        headline = await page.locator(".landing-headline").inner_text()
        print(f"Landing Headline: {headline[:30]}...")
        assert "短剧" in headline or "CinemaAgent" in headline

        # Verify 3 feature cards
        features_count = await page.locator(".feature-glass-card").count()
        print(f"Found {features_count} landing feature cards.")
        assert features_count >= 3

        # Capture landing screenshot
        shot_landing = os.path.join(SCREENSHOT_DIR, "step10_landing_showcase.png")
        shot_landing_brain = os.path.join(BRAIN_ARTIFACT_DIR, "step10_landing_showcase.png")
        await page.screenshot(path=shot_landing, full_page=False)
        await page.screenshot(path=shot_landing_brain, full_page=False)
        print("Captured Landing Showcase Screenshot.")

        # Click CTA to enter Portal
        print("Clicking '进入视听大厅' CTA button...")
        await page.locator("#btn-enter-portal").click()
        await page.wait_for_timeout(1000)
        assert page.url.endswith("#/") or page.url.endswith("/")

        # -------------------------------------------------------------
        # 2. Test Bilibili Wide Fluid Layout & De-AI Clean Cards
        # -------------------------------------------------------------
        print("\n--- 2. Testing Bilibili Wide Fluid Layout & Clean Cards ---")
        main_box = await page.locator(".portal-main-wrap").bounding_box()
        assert main_box is not None
        print(f"Main portal container width on 1720px viewport: {main_box['width']}px")
        # Ensure it has expanded beyond the old cramped 1120px
        assert main_box["width"] > 1400, f"Expected width > 1400px, got {main_box['width']}px"

        # Verify all squircle emoji badges are removed from cards
        squircle_count = await page.locator(".bento-card .card-icon-squircle").count()
        print(f"Squircle emoji icons count in cards: {squircle_count} (Must be 0)")
        assert squircle_count == 0, "Card emoji squircle icons should be completely removed"

        # Verify 16:9 thumbnail is at top
        await page.wait_for_selector(".bili-video-card", timeout=8000)
        card = page.locator(".bili-video-card").first
        assert await card.is_visible()
        thumb = card.locator(".card-thumbnail-box")
        assert await thumb.is_visible()

        # Capture Bilibili Wide Portal screenshot
        shot_bili = os.path.join(SCREENSHOT_DIR, "step10_bilibili_wide_portal.png")
        shot_bili_brain = os.path.join(BRAIN_ARTIFACT_DIR, "step10_bilibili_wide_portal.png")
        await page.screenshot(path=shot_bili, full_page=False)
        await page.screenshot(path=shot_bili_brain, full_page=False)
        print("Captured Bilibili Wide Portal Screenshot.")

        # -------------------------------------------------------------
        # 3. Test Creator Studio & Cloud Disk Tree
        # -------------------------------------------------------------
        print("\n--- 3. Testing Creator Studio & Quark Cloud Disk ---")
        # First ensure creator role via quick switch
        await page.locator("#btn-role-creator").click()
        await page.wait_for_selector("#btn-role-creator.active", timeout=5000)
        await page.wait_for_timeout(500)

        await page.goto("http://localhost:5173/#/creator", wait_until="networkidle")
        await page.wait_for_selector(".studio-page-title", timeout=5000)

        title = await page.locator(".studio-page-title").inner_text()
        print(f"Creator Studio Title: {title}")
        assert "创作者中心" in title or "Creator" in title or "工作室" in title

        # Verify cloud path label
        cloud_path_elem = page.locator("#current-cloud-path")
        if await cloud_path_elem.is_visible():
            cloud_path = await cloud_path_elem.inner_text()
            print(f"Current Quark Cloud Disk Path: {cloud_path}")
            assert "/kuake" in cloud_path

        # Verify tab switching
        await page.wait_for_selector("#tab-video-upload", timeout=5000)
        await page.locator("#tab-video-upload").click()
        await page.wait_for_timeout(500)
        assert await page.locator("#panel-video-upload").is_visible()
        print("Video upload panel verified.")

        await page.locator("#tab-my-dramas").click()
        await page.wait_for_timeout(500)
        assert await page.locator("#panel-my-dramas").is_visible()
        print("My dramas panel verified.")

        # Return to disk tab
        await page.locator("#tab-pan-tree").click()
        await page.wait_for_timeout(500)

        # Capture Creator Studio screenshot
        shot_creator = os.path.join(SCREENSHOT_DIR, "step10_creator_studio_pan.png")
        shot_creator_brain = os.path.join(BRAIN_ARTIFACT_DIR, "step10_creator_studio_pan.png")
        await page.screenshot(path=shot_creator, full_page=False)
        await page.screenshot(path=shot_creator_brain, full_page=False)
        print("Captured Creator Studio Screenshot.")

        # -------------------------------------------------------------
        # 4. Test Admin Console & RBAC Moderation
        # -------------------------------------------------------------
        print("\n--- 4. Testing Admin Console & RBAC Moderation ---")
        # Switch to Admin role
        await page.locator("#btn-role-admin").click()
        await page.wait_for_selector("#btn-role-admin.active", timeout=5000)
        await page.wait_for_timeout(500)

        await page.goto("http://localhost:5173/#/admin", wait_until="networkidle")
        await page.wait_for_timeout(1500)

        admin_title = await page.locator(".admin-page-title").inner_text()
        print(f"Admin Page Title: {admin_title}")
        assert "管理员控制台" in admin_title

        # Check metrics grid
        metrics_count = await page.locator(".metric-glass-card").count()
        print(f"Found {metrics_count} admin metrics cards.")
        assert metrics_count >= 4

        # Check users table
        rows_count = await page.locator(".admin-data-table tbody tr").count()
        print(f"Found {rows_count} user rows in admin table.")
        assert rows_count > 0

        # Capture Admin Console screenshot
        shot_admin = os.path.join(SCREENSHOT_DIR, "step10_admin_console_rbac.png")
        shot_admin_brain = os.path.join(BRAIN_ARTIFACT_DIR, "step10_admin_console_rbac.png")
        await page.screenshot(path=shot_admin, full_page=False)
        await page.screenshot(path=shot_admin_brain, full_page=False)
        print("Captured Admin Console Screenshot.")

        await browser.close()
        print("\n[SUCCESS] [Playwright E2E] All Step 10 assertions passed with 100% success!")

if __name__ == "__main__":
    asyncio.run(run_step10_test())
