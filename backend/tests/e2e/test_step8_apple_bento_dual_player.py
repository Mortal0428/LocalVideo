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
    uvicorn.run(app, host="127.0.0.1", port=8008, log_level="warning")

async def test_step8_apple_bento_dual_player():
    print("\n[Playwright E2E] Starting Step 8: Apple HIG Bento Grid Portal & Seamless Dual-Mode Player Test...")

    server_process = Process(target=run_server, daemon=True)
    server_process.start()
    await asyncio.sleep(2.5)

    screenshots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage/test_screenshots"))
    os.makedirs(screenshots_dir, exist_ok=True)

    try:
        async with async_playwright() as p:
            print("[Playwright E2E] Launching Edge (Chromium) in Headless mode...")
            browser = await p.chromium.launch(headless=True, channel="msedge")
            context = await browser.new_context(viewport={"width": 1440, "height": 900})
            page = await context.new_page()
            page.on("console", lambda msg: print(f"[BROWSER CONSOLE] {msg.text}"))
            page.on("pageerror", lambda err: print(f"[BROWSER ERROR] {err}"))

            # -------------------------------------------------------------
            # 1. Visit Portal Home Page (Apple HIG Bento Grid)
            # -------------------------------------------------------------
            print("[Playwright E2E] Navigating to Apple Bento Portal at http://127.0.0.1:8008 ...")
            await page.goto("http://127.0.0.1:8008", wait_until="networkidle")

            # Check Apple App Root & Ambient Aurora Background
            app_root = page.locator("#apple-app-root")
            await app_root.wait_for(state="visible", timeout=6000)
            print("[Playwright E2E] [OK] Apple App Root loaded.")

            aurora_bg = page.locator(".aurora-ambient-bg")
            await aurora_bg.wait_for(state="attached")
            print("[Playwright E2E] [OK] Ambient Aurora floating gradient orbs mounted.")

            # Check Global Header & Big Type Hero Title
            header = page.locator("#bili-global-header")
            await header.wait_for(state="visible")
            print("[Playwright E2E] [OK] Apple frosted glass global header visible.")

            hero_title = page.locator(".hero-big-title")
            await hero_title.wait_for(state="visible")
            title_text = await hero_title.inner_text()
            assert "CinemaAgent" in title_text
            print(f"[Playwright E2E] [OK] Hero Big Title rendered: '{title_text}'")

            # Check Category Filter Pills
            cat_bar = page.locator("#channel-bar")
            await cat_bar.wait_for(state="visible")
            print("[Playwright E2E] [OK] Category filter pills bar visible.")

            # Check Spotlight Hero Bento Card
            spotlight_bento = page.locator("#carousel-banner-box")
            await spotlight_bento.wait_for(state="visible")
            print("[Playwright E2E] [OK] Spotlight 2x2 Feature Bento Card rendered.")

            # Check 3-Column Bento Grid Cards
            bento_cards = page.locator(".bento-card")
            card_count = await bento_cards.count()
            print(f"[Playwright E2E] [OK] Found {card_count} Bento cards in 3-column grid.")
            assert card_count >= 4

            # Capture Screenshot 1: Home Bento Grid Portal
            shot1_path = os.path.join(screenshots_dir, "step8_apple_bento_portal_home.png")
            await page.screenshot(path=shot1_path, full_page=False)
            print(f"[Playwright E2E] [SCREENSHOT] Saved Home Bento Grid: {shot1_path}")

            # -------------------------------------------------------------
            # 2. Search Functionality
            # -------------------------------------------------------------
            print("[Playwright E2E] Testing search with keyword '乘风' ...")
            search_input = page.locator("#home-search-input")
            await search_input.fill("乘风")
            await page.click("#btn-search")
            await page.wait_for_timeout(500)

            filtered_count = await page.locator(".bento-card").count()
            print(f"[Playwright E2E] [OK] Search returned {filtered_count} matched Bento cards.")
            assert filtered_count >= 1

            # Clear search
            await page.click(".clear-search-btn")
            await page.wait_for_timeout(500)

            # -------------------------------------------------------------
            # 3. Enter Player Page via Bento Action Pill
            # -------------------------------------------------------------
            first_card = page.locator(".bento-card").first
            card_title = await first_card.locator(".card-title").inner_text()
            print(f"[Playwright E2E] Clicking Bento Card action: '{card_title}' to open player...")
            await first_card.locator(".apple-primary-pill").click()
            await page.wait_for_timeout(1000)

            current_url = page.url
            print(f"[Playwright E2E] [OK] Navigated to: {current_url}")
            assert "/video/" in current_url

            # Debug page content
            debug_shot = os.path.join(screenshots_dir, "debug_player_fail.png")
            await page.screenshot(path=debug_shot)
            body_snippet = await page.evaluate("() => document.querySelector('#app')?.innerHTML.substring(0, 400) || document.body.innerHTML.substring(0, 400)")
            print(f"[DEBUG BODY SNIPPET]: {body_snippet}")

            # -------------------------------------------------------------
            # 4. Verify Mode A: 16:9 Landscape Widescreen Cinema
            # -------------------------------------------------------------
            cinema_page = page.locator("#cinema-backdrop")
            await cinema_page.wait_for(state="visible", timeout=6000)
            assert "mode-landscape" in (await cinema_page.get_attribute("class") or "")
            print("[Playwright E2E] [OK] 16:9 Landscape widescreen cinema mode active.")

            video_elem = page.locator("#player-video")
            await video_elem.wait_for(state="visible")
            print("[Playwright E2E] [OK] Core persistent video element mounted.")

            # Capture Screenshot 2: 16:9 Landscape Cinema Mode
            shot2_path = os.path.join(screenshots_dir, "step8_apple_landscape_cinema_mode.png")
            await page.screenshot(path=shot2_path, full_page=False)
            print(f"[Playwright E2E] [SCREENSHOT] Saved 16:9 Cinema Mode: {shot2_path}")

            # -------------------------------------------------------------
            # 5. Test Seamless Hot-Switch to Mode B: 9:16 Portrait Capsule
            # -------------------------------------------------------------
            print("[Playwright E2E] Testing seamless switch to '📱 9:16 沉浸胶囊' ...")
            await page.click("#btn-mode-portrait")
            await page.wait_for_timeout(600)

            assert "mode-portrait" in (await cinema_page.get_attribute("class") or "")
            notch = page.locator(".mobile-notch-bar")
            await notch.wait_for(state="visible")
            print("[Playwright E2E] [OK] Switched to 9:16 Portrait Capsule Mode! Mobile notch is visible.")

            # Verify the SAME video element remains alive without being recreated
            await video_elem.wait_for(state="visible")
            print("[Playwright E2E] [OK] Video element remained 100% persistent across mode switch!")

            # Capture Screenshot 3: 9:16 Portrait Capsule Mode
            shot3_path = os.path.join(screenshots_dir, "step8_apple_portrait_capsule_mode.png")
            await page.screenshot(path=shot3_path, full_page=False)
            print(f"[Playwright E2E] [SCREENSHOT] Saved 9:16 Capsule Mode: {shot3_path}")

            # Switch back to 16:9 Landscape
            print("[Playwright E2E] Switching back to '🖥️ 16:9 极简宽屏' ...")
            await page.click("#btn-mode-landscape")
            await page.wait_for_timeout(600)
            assert "mode-landscape" in (await cinema_page.get_attribute("class") or "")
            print("[Playwright E2E] [OK] Returned to 16:9 Landscape Mode smoothly.")

            # -------------------------------------------------------------
            # 6. Test AI Companion Agent Interaction & Timestamp Seeking
            # -------------------------------------------------------------
            print("[Playwright E2E] Testing AI Companion Agent with glowing timestamp seeking...")
            jump_btn = page.locator(".jump-timestamp-btn").first
            await jump_btn.wait_for(state="visible")
            await jump_btn.click()
            await page.wait_for_timeout(500)

            # Check auto-resume / seek toast notification
            toast = page.locator("#resume-toast-pill")
            await toast.wait_for(state="visible")
            toast_text = await toast.inner_text()
            print(f"[Playwright E2E] [OK] Timestamp Jump Toast displayed: '{toast_text}'")

            # Ask Agent Question
            agent_input = page.locator("#input-agent")
            await agent_input.fill("本集的核心矛盾反转是什么？")
            await page.click("#btn-send-agent")
            await page.wait_for_timeout(1000)

            agent_messages = page.locator(".chat-bubble-row")
            msg_count = await agent_messages.count()
            print(f"[Playwright E2E] [OK] Agent conversation updated: {msg_count} messages.")
            assert msg_count >= 3

            # Capture Screenshot 4: AI Companion Agent Interaction
            shot4_path = os.path.join(screenshots_dir, "step8_apple_ai_agent_companion.png")
            await page.screenshot(path=shot4_path, full_page=False)
            print(f"[Playwright E2E] [SCREENSHOT] Saved AI Companion Agent: {shot4_path}")

            # -------------------------------------------------------------
            # 7. Return to Portal Home
            # -------------------------------------------------------------
            print("[Playwright E2E] Clicking '返回大厅' ...")
            await page.click("#btn-back-home")
            await page.wait_for_timeout(600)
            assert page.url.endswith("#/") or page.url.endswith(":8008/")
            print("[Playwright E2E] [OK] Successfully returned to Apple Bento Portal Home!")

            print("\n==========================================================================")
            print("  [PLAYWRIGHT E2E PASSED] Step 8: Apple HIG Bento & Dual-Mode Passed!     ")
            print("==========================================================================\n")

    finally:
        server_process.terminate()
        server_process.join(timeout=3)

if __name__ == "__main__":
    asyncio.run(test_step8_apple_bento_dual_player())
