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

        print("\n=== STEP 1: Login admin and verify BI Dashboard Light High Contrast ===")
        await page.goto("http://localhost:5173/#/login")
        await page.evaluate("localStorage.clear()")
        await page.reload()
        await page.wait_for_selector("#input-login-username", timeout=10000)
        await page.fill("#input-login-username", "admin")
        await page.fill("#input-login-password", "admin123")
        await page.click("#btn-submit-login")
        await page.wait_for_timeout(1000)

        # Go to Admin BI in light mode
        await page.goto("http://localhost:5173/#/admin?tab=bi")
        await page.evaluate("document.documentElement.setAttribute('data-theme', 'light'); localStorage.setItem('cinema_theme', 'light')")
        await page.wait_for_timeout(1200)

        # 1. Check KPI title color (should be dark ~#48484a)
        kpi_title_color = await page.locator(".kpi-title").first.evaluate("el => window.getComputedStyle(el).color")
        print(f"BI KPI title color: {kpi_title_color}")
        assert "72, 72, 74" in kpi_title_color or "29, 29, 31" in kpi_title_color, f"KPI title color failed: {kpi_title_color}"

        # 2. Check Legend pill text color (should be dark ~#48484a, not white)
        legend_color = await page.locator(".legend-pill").first.evaluate("el => window.getComputedStyle(el).color")
        print(f"BI Chart legend text color: {legend_color}")
        assert "72, 72, 74" in legend_color or "0, 0, 0" in legend_color or "29, 29, 31" in legend_color, f"Legend color failed: {legend_color}"

        # 3. Screenshot BI Dashboard in light theme
        bi_screen = os.path.join(SCREENSHOT_DIR, "verified_admin_bi_light_contrast.png")
        await page.screenshot(path=bi_screen, full_page=True)
        print("PASS: Admin BI Light Contrast verified.")

        print("\n=== STEP 2: Verify Dramas Catalog Title Column High Contrast (Figure 5 Fix) ===")
        await page.click("#admin-tab-dramas")
        await page.wait_for_timeout(1000)

        # Assert drama title has dark text color (#1d1d1f), not white #ffffff!
        drama_title_color = await page.locator(".drama-title-main").first.evaluate("el => window.getComputedStyle(el).color")
        print(f"Drama title color in catalog (must be dark #1d1d1f, NOT white): {drama_title_color}")
        assert "29, 29, 31" in drama_title_color or "0, 0, 0" in drama_title_color, f"Drama title is still white: {drama_title_color}"

        drama_synopsis_color = await page.locator(".drama-synopsis-sub").first.evaluate("el => window.getComputedStyle(el).color")
        print(f"Drama synopsis color: {drama_synopsis_color}")
        assert "110, 110, 115" in drama_synopsis_color, f"Synopsis color failed: {drama_synopsis_color}"

        # Screenshot Dramas catalog
        dramas_screen = os.path.join(SCREENSHOT_DIR, "verified_admin_dramas_name_light.png")
        await page.screenshot(path=dramas_screen)
        print("PASS: Dramas catalog title column verified.")

        print("\n=== STEP 3: Verify Applications Subtabs & Secondary Button (Figure 1 & 2 Fix) ===")
        await page.click("#admin-tab-applications")
        await page.wait_for_timeout(1000)

        # Assert subtab inactive text color is dark #48484a
        subtab_inactive_color = await page.locator("#subtab-reviewers").evaluate("el => window.getComputedStyle(el).color")
        print(f"Inactive application subtab text color: {subtab_inactive_color}")
        assert "72, 72, 74" in subtab_inactive_color, f"Subtab inactive text color failed: {subtab_inactive_color}"

        # Assert refresh button text color is dark #1d1d1f
        refresh_color = await page.locator("#btn-admin-refresh").evaluate("el => window.getComputedStyle(el).color")
        print(f"Refresh button text color: {refresh_color}")
        assert "29, 29, 31" in refresh_color or "0, 0, 0" in refresh_color, f"Refresh button color failed: {refresh_color}"

        # Screenshot Applications
        app_screen = os.path.join(SCREENSHOT_DIR, "verified_admin_applications_light.png")
        await page.screenshot(path=app_screen)
        print("PASS: Applications subtabs and buttons verified.")

        print("\n=== STEP 4: Verify Contents Risk Subtabs Contrast (Figure 4 Fix) ===")
        await page.click("#admin-tab-contents")
        await page.wait_for_timeout(1000)

        # Assert subtabs count and inactive colors
        danmaku_subtab_color = await page.locator("#subtab-danmakus").evaluate("el => window.getComputedStyle(el).color")
        print(f"Danmakus subtab inactive text color: {danmaku_subtab_color}")
        assert "72, 72, 74" in danmaku_subtab_color, f"Danmaku subtab color failed: {danmaku_subtab_color}"

        # Screenshot Contents
        content_screen = os.path.join(SCREENSHOT_DIR, "verified_admin_contents_subtabs_light.png")
        await page.screenshot(path=content_screen)
        print("PASS: Contents risk subtabs verified.")

        await browser.close()

        # Copy all screenshots to ARTIFACT_DIR
        for fn in [
            "verified_admin_bi_light_contrast.png",
            "verified_admin_dramas_name_light.png",
            "verified_admin_applications_light.png",
            "verified_admin_contents_subtabs_light.png"
        ]:
            src = os.path.join(SCREENSHOT_DIR, fn)
            if os.path.exists(src):
                shutil.copy(src, os.path.join(ARTIFACT_DIR, fn))

        print("\nALL SYSTEMATIC CONTRAST VERIFICATIONS PASSED (100% 4/4)!")

if __name__ == "__main__":
    asyncio.run(run_verification())
