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
    uvicorn.run(app, host="127.0.0.1", port=8007, log_level="warning")

async def test_step7_bilibili_portal_and_dual_mode_player():
    print("\n[Playwright E2E] Starting Step 7: Bilibili-Style Portal & Dual-Mode Player Test...")
    
    server_process = Process(target=run_server, daemon=True)
    server_process.start()
    await asyncio.sleep(2.5)

    try:
        async with async_playwright() as p:
            print("[Playwright E2E] Launching Edge (Chromium) in Headless mode...")
            browser = await p.chromium.launch(headless=True, channel="msedge")
            context = await browser.new_context(viewport={"width": 1440, "height": 900})
            page = await context.new_page()

            # 1. Visit Portal Home Page
            print("[Playwright E2E] Navigating to Portal Home at http://127.0.0.1:8007 ...")
            await page.goto("http://127.0.0.1:8007", wait_until="networkidle")

            # Verify Bilibili portal structure
            portal_page = page.locator("#bili-portal-page")
            await portal_page.wait_for(state="visible", timeout=5000)
            print("[Playwright E2E] [OK] Bilibili portal container loaded.")

            header = page.locator("#bili-global-header")
            await header.wait_for(state="visible")
            print("[Playwright E2E] [OK] Top global header is visible.")

            banner = page.locator("#bili-banner-hero")
            await banner.wait_for(state="visible")
            print("[Playwright E2E] [OK] Top illustrated scenic banner is visible.")

            channel_bar = page.locator("#channel-bar")
            await channel_bar.wait_for(state="visible")
            print("[Playwright E2E] [OK] Category channels bar is visible.")

            carousel = page.locator("#carousel-banner-box")
            await carousel.wait_for(state="visible")
            print("[Playwright E2E] [OK] 16:9 Hero carousel is visible.")

            # 2. Check Video Cards Grid
            cards = page.locator(".bili-video-card")
            card_count = await cards.count()
            print(f"[Playwright E2E] [OK] Found {card_count} video cards in Bilibili grid.")
            assert card_count >= 4

            # 3. Test Search Functionality
            print("[Playwright E2E] Testing search bar with keyword '乘风' ...")
            search_input = page.locator("#home-search-input")
            await search_input.fill("乘风")
            await page.click("#btn-search")
            await page.wait_for_timeout(500)

            filtered_cards = page.locator(".bili-video-card")
            filtered_count = await filtered_cards.count()
            print(f"[Playwright E2E] [OK] Search returned {filtered_count} matched cards.")
            assert filtered_count >= 1

            # Reset search
            await page.click(".clear-search-btn")
            await page.wait_for_timeout(500)

            # 4. Click Video Card to Enter Dual-Mode Player
            first_card = page.locator(".bili-video-card").first
            card_title = await first_card.locator(".card-title").inner_text()
            print(f"[Playwright E2E] Clicking video card: '{card_title}' to enter player...")
            await first_card.click()
            await page.wait_for_timeout(1000)

            # Assert URL navigated to /video/
            current_url = page.url
            print(f"[Playwright E2E] [OK] Current URL: {current_url}")
            assert "/video/" in current_url

            # 5. Verify Mode A: 16:9 Landscape Widescreen Player
            landscape_layout = page.locator("#landscape-player-layout")
            await landscape_layout.wait_for(state="visible", timeout=6000)
            print("[Playwright E2E] [OK] 16:9 Landscape widescreen cinema layout loaded successfully!")

            video_elem = page.locator("#player-video")
            await video_elem.wait_for(state="visible")
            print("[Playwright E2E] [OK] Video element is mounted and ready.")

            danmaku_box = page.locator(".danmaku-send-box")
            await danmaku_box.wait_for(state="visible")
            print("[Playwright E2E] [OK] In-player danmaku controller is visible.")

            # 6. Test Mode Switcher: Toggle to 9:16 Portrait Capsule
            print("[Playwright E2E] Testing mode switch to '📱 竖屏胶囊 (9:16)'...")
            btn_portrait = page.locator("#btn-mode-portrait")
            await btn_portrait.click()
            await page.wait_for_timeout(600)

            portrait_layout = page.locator("#portrait-player-layout")
            await portrait_layout.wait_for(state="visible", timeout=4000)
            print("[Playwright E2E] [OK] Successfully switched to 9:16 Portrait Mobile Capsule Mode!")

            # 7. Test Mode Switcher: Toggle back to 16:9 Landscape Widescreen
            print("[Playwright E2E] Testing mode switch back to '🖥️ 横屏宽屏 (16:9)'...")
            btn_landscape = page.locator("#btn-mode-landscape")
            await btn_landscape.click()
            await page.wait_for_timeout(600)

            await landscape_layout.wait_for(state="visible", timeout=4000)
            print("[Playwright E2E] [OK] Successfully returned to 16:9 Landscape Cinema Mode!")

            # 8. Test Navigation Back to Home Portal
            print("[Playwright E2E] Clicking '← 首页大厅' button to return home...")
            btn_back = page.locator("#btn-back-home")
            await btn_back.click()
            await page.wait_for_timeout(800)

            await portal_page.wait_for(state="visible", timeout=5000)
            print("[Playwright E2E] [OK] Successfully returned to Bilibili Home Portal!")

            await browser.close()
            print("\n==========================================================================")
            print("  [PLAYWRIGHT E2E PASSED] Step 7: Bilibili Portal & Dual-Mode Player Passed!")
            print("==========================================================================\n")

    finally:
        server_process.terminate()
        server_process.join()

if __name__ == "__main__":
    asyncio.run(test_step7_bilibili_portal_and_dual_mode_player())
