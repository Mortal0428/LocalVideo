import os
import sys
import shutil
import asyncio
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BRAIN_ARTIFACT_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"
STORAGE_SCREENSHOTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage/test_screenshots"))

def save_and_copy_screenshot(src_path: str, filename: str):
    os.makedirs(STORAGE_SCREENSHOTS_DIR, exist_ok=True)
    if os.path.exists(BRAIN_ARTIFACT_DIR):
        brain_path = os.path.join(BRAIN_ARTIFACT_DIR, filename)
        shutil.copy2(src_path, brain_path)
        print(f"[SCREENSHOT SAVED] Brain artifact: {brain_path}")
    print(f"[SCREENSHOT SAVED] Local storage: {src_path}")

async def run_step9_e2e_verification():
    print("\n================================================================================")
    print(" [Playwright E2E] STEP 9: Bilibili Visual Polish & Model Engine Verification")
    print("================================================================================\n")

    os.makedirs(STORAGE_SCREENSHOTS_DIR, exist_ok=True)

    async with async_playwright() as p:
        print("[Playwright] Launching Chromium (msedge/chromium) in headless mode...")
        browser = await p.chromium.launch(headless=True, channel="msedge")
        context = await browser.new_context(viewport={"width": 1440, "height": 920})
        page = await context.new_page()

        page.on("console", lambda msg: print(f"  [CONSOLE] {msg.text}"))
        page.on("pageerror", lambda err: print(f"  [PAGE ERROR] {err}"))

        # ----------------------------------------------------------------------
        # 1. Test HomeView Portal (Bilibili Feed & Liquid Glass)
        # ----------------------------------------------------------------------
        print("\n[Step 1] Navigating to Home Portal at http://127.0.0.1:8000 ...")
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        await page.wait_for_selector("#apple-app-root", state="visible", timeout=10000)

        # Verify Header & Brand
        header = page.locator("#bili-global-header")
        await header.wait_for(state="visible")
        print("  [OK] Apple frosted glass global header visible.")

        # Verify Engine Settings Trigger Button
        engine_btn = page.locator("#btn-engine-settings")
        await engine_btn.wait_for(state="visible")
        print("  [OK] Engine settings button visible in header.")

        # Verify Category Filter Pills & Bilibili Pink highlight
        cat_pills = page.locator(".cat-pill-btn")
        cat_count = await cat_pills.count()
        assert cat_count >= 5, f"Expected at least 5 category pills, got {cat_count}"
        print(f"  [OK] Category pills rendered ({cat_count} pills).")

        # Verify Video Bento Grid & Cards
        cards = page.locator(".bento-card")
        await cards.first.wait_for(state="visible", timeout=6000)
        card_count = await cards.count()
        assert card_count >= 1, "Expected at least 1 video card rendered"
        print(f"  [OK] Video bento cards rendered ({card_count} cards).")

        # Save HomeView screenshot
        home_shot = os.path.join(STORAGE_SCREENSHOTS_DIR, "step9_bilibili_portal_home.png")
        await page.screenshot(path=home_shot, full_page=False)
        save_and_copy_screenshot(home_shot, "step9_bilibili_portal_home.png")

        # ----------------------------------------------------------------------
        # 2. Test Model Engine Settings Modal (Local Ollama + Xiaomi MiMo)
        # ----------------------------------------------------------------------
        print("\n[Step 2] Testing Engine Settings Modal...")
        await engine_btn.click()
        await page.wait_for_selector("#modal-engine-settings-backdrop", state="visible", timeout=6000)
        print("  [OK] Engine settings modal backdrop opened.")

        # Wait for model probe to complete (shows probed models)
        await page.wait_for_selector(".model-select-input", state="visible", timeout=6000)
        await asyncio.sleep(1.2)  # Allow options to populate from probe API

        # Click Connection Test Button
        test_conn_btn = page.locator("#btn-test-conn")
        if await test_conn_btn.is_visible():
            print("  [OK] Triggering model connectivity test...")
            await test_conn_btn.click()
            await page.wait_for_selector(".conn-status-msg", state="visible", timeout=8000)
            status_text = await page.locator(".conn-status-msg").inner_text()
            print(f"  [OK] Connectivity response: {status_text}")

        # Save Engine Modal screenshot
        modal_shot = os.path.join(STORAGE_SCREENSHOTS_DIR, "step9_engine_settings_modal.png")
        await page.screenshot(path=modal_shot, full_page=False)
        save_and_copy_screenshot(modal_shot, "step9_engine_settings_modal.png")

        # Close Modal
        close_modal_btn = page.locator("#btn-close-engine-modal")
        await close_modal_btn.click()
        await page.wait_for_selector("#modal-engine-settings-backdrop", state="hidden")
        print("  [OK] Engine settings modal closed cleanly.")
        await asyncio.sleep(0.6)

        # ----------------------------------------------------------------------
        # 3. Test Video Card Navigation & PlayerView (16:9 Cinema Mode)
        # ----------------------------------------------------------------------
        print("\n[Step 3] Entering PlayerView by clicking video card...")
        video_card = page.locator(".bento-card").first
        await video_card.scroll_into_view_if_needed()
        await video_card.click()
        await page.wait_for_selector("#cinema-backdrop", state="visible", timeout=8000)
        await page.wait_for_selector("#player-video", state="attached", timeout=8000)
        print("  [OK] PlayerView theater layout loaded.")

        # Verify Sidebar with 4 Tabs: 选集, 高能看点, 剧情伴读, 机审中台
        episodes_tab_btn = page.locator("#tab-btn-episodes")
        highlights_tab_btn = page.locator("#tab-btn-highlights")
        agent_tab_btn = page.locator("#tab-btn-agent")
        await episodes_tab_btn.wait_for(state="visible")
        await highlights_tab_btn.wait_for(state="visible")
        await agent_tab_btn.wait_for(state="visible")
        print("  [OK] Sidebar tabs (选集 / 高能看点 / 剧情伴读) visible.")

        # Take Landscape Cinema screenshot (Episodes tab default)
        landscape_episodes_shot = os.path.join(STORAGE_SCREENSHOTS_DIR, "step9_player_landscape_episodes.png")
        await page.screenshot(path=landscape_episodes_shot, full_page=False)
        save_and_copy_screenshot(landscape_episodes_shot, "step9_player_landscape_episodes.png")

        # ----------------------------------------------------------------------
        # 4. Test Highlights Tab & Seamless Timestamp Jump
        # ----------------------------------------------------------------------
        print("\n[Step 4] Testing High-Energy Highlights tab...")
        await highlights_tab_btn.click()
        await page.wait_for_selector("#panel-highlights", state="visible")
        highlight_cards = page.locator(".highlight-card-item")
        h_count = await highlight_cards.count()
        assert h_count >= 1, "Expected at least 1 high-energy highlight card"
        print(f"  [OK] Highlights list rendered with {h_count} scene cards.")

        # Save Landscape Highlights screenshot
        highlights_shot = os.path.join(STORAGE_SCREENSHOTS_DIR, "step9_player_landscape_highlights.png")
        await page.screenshot(path=highlights_shot, full_page=False)
        save_and_copy_screenshot(highlights_shot, "step9_player_landscape_highlights.png")

        # Click the 3rd highlight card (十万将士恭迎龙王, 01:15)
        print("  [OK] Clicking highlight bookmark to trigger seamless frame jump...")
        if h_count >= 3:
            await highlight_cards.nth(2).click()
        else:
            await highlight_cards.first.click()

        # Wait for Resume Toast notification
        toast = page.locator("#resume-toast-pill")
        await toast.wait_for(state="visible", timeout=4000)
        toast_text = await toast.inner_text()
        print(f"  [OK] Frame jump toast confirmed: '{toast_text}'")

        # ----------------------------------------------------------------------
        # 5. Test Dual-Mode Switcher: Switch to 9:16 Portrait Capsule Player
        # ----------------------------------------------------------------------
        print("\n[Step 5] Testing Seamless Switch to 9:16 Portrait Capsule...")
        portrait_btn = page.locator("#btn-mode-portrait")
        await portrait_btn.click()
        await page.wait_for_selector("#portrait-player-layout", state="visible")
        notch = page.locator(".mobile-notch-bar")
        await notch.wait_for(state="visible")
        print("  [OK] Successfully transformed into 9:16 Mobile Capsule Theater.")

        # Verify Video Element is still mounted (No reload!)
        video_el = page.locator("#player-video")
        assert await video_el.count() == 1, "Video element must remain persistently mounted!"
        print("  [OK] Video element instance safely preserved across mode transition.")

        # Save 9:16 Portrait screenshot
        portrait_shot = os.path.join(STORAGE_SCREENSHOTS_DIR, "step9_player_portrait_capsule.png")
        await page.screenshot(path=portrait_shot, full_page=False)
        save_and_copy_screenshot(portrait_shot, "step9_player_portrait_capsule.png")

        # ----------------------------------------------------------------------
        # 6. Test Danmaku Real-Time Flight on Screen
        # ----------------------------------------------------------------------
        print("\n[Step 6] Testing Danmaku sending and flight...")
        danmaku_input = page.locator("#input-danmaku")
        danmaku_btn = page.locator("#btn-send-danmaku")
        await danmaku_input.fill("恭迎十万将士与龙王归来！")
        await danmaku_btn.click()

        # Wait for flying danmaku to appear
        bullet = page.locator(".danmaku-flying-bullet").first
        await bullet.wait_for(state="visible", timeout=4000)
        bullet_text = await bullet.inner_text()
        print(f"  [OK] Flying danmaku launched on screen: '{bullet_text}'")

        # Save Danmaku flight screenshot
        danmaku_shot = os.path.join(STORAGE_SCREENSHOTS_DIR, "step9_player_danmaku_flight.png")
        await page.screenshot(path=danmaku_shot, full_page=False)
        save_and_copy_screenshot(danmaku_shot, "step9_player_danmaku_flight.png")

        await browser.close()
        print("\n================================================================================")
        print(" [Playwright E2E] STEP 9 ALL TESTS PASSED SUCCESSFULLY! ALL 6 SCREENSHOTS READY.")
        print("================================================================================\n")

if __name__ == "__main__":
    asyncio.run(run_step9_e2e_verification())
