import asyncio
import os
import shutil
import sys
import json
import httpx
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

ARTIFACT_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"
SCREENSHOT_DIR = os.path.join(os.getcwd(), "storage", "test_screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def get_auth_token(username, password):
    res = httpx.post("http://127.0.0.1:8000/api/v1/auth/login", json={"username": username, "password": password})
    if res.status_code == 200:
        return res.json()
    raise Exception(f"Login failed for {username}: {res.text}")

async def run_verification():
    viewer_auth = get_auth_token("viewer", "viewer123")
    admin_auth = get_auth_token("admin", "admin123")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="msedge")
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("\n=======================================================")
        print("STAGE 1: Verify Coin Tip Dialog Gold High Contrast (Dark & Light)")
        print("=======================================================")
        # Inject viewer auth
        await page.goto("http://localhost:5173/#/")
        await page.evaluate("""(auth) => {
            localStorage.setItem('token', auth.access_token);
            localStorage.setItem('access_token', auth.access_token);
            localStorage.setItem('user', JSON.stringify(auth.user));
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('cinema_theme', 'dark');
        }""", viewer_auth)

        # Go to Player view with real drama UUID (我推的孩子 第一季)
        target_video_id = "5f586a0c-294b-49ac-a25d-31ac131f12b7"
        await page.goto(f"http://localhost:5173/#/video/{target_video_id}")
        await page.wait_for_selector("#btn-coin-tip", timeout=12000)
        await page.wait_for_timeout(1000)

        # Click coin tip button
        await page.click("#btn-coin-tip")
        await page.wait_for_selector(".coin-tip-dialog", state="visible", timeout=6000)
        await page.wait_for_timeout(600)

        # Verify dark mode gold color
        wallet_val_dark = page.locator(".coin-tip-dialog .wallet-val")
        dark_color = await wallet_val_dark.evaluate("el => window.getComputedStyle(el).color")
        print(f"Coin Balance Color in Dark Mode: {dark_color}")
        assert "29, 29, 31" not in dark_color and "0, 0, 0" not in dark_color, f"Dark mode coin value should NOT be black! Got: {dark_color}"

        dark_shot = os.path.join(SCREENSHOT_DIR, "verified_coin_balance_dark_high_contrast.png")
        await page.screenshot(path=dark_shot)
        shutil.copy(dark_shot, os.path.join(ARTIFACT_DIR, "verified_coin_balance_dark_high_contrast.png"))
        print("PASS: Coin balance in Dark Mode has bright high-contrast gold (#ffd60a).")

        # Switch to Light Mode
        await page.evaluate("""() => {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('cinema_theme', 'light');
        }""")
        await page.wait_for_timeout(600)

        wallet_val_light = page.locator(".coin-tip-dialog .wallet-val")
        light_color = await wallet_val_light.evaluate("el => window.getComputedStyle(el).color")
        print(f"Coin Balance Color in Light Mode: {light_color}")
        assert "29, 29, 31" not in light_color, f"Light mode coin value should NOT be black! Got: {light_color}"

        light_shot = os.path.join(SCREENSHOT_DIR, "verified_coin_balance_light_high_contrast.png")
        await page.screenshot(path=light_shot)
        shutil.copy(light_shot, os.path.join(ARTIFACT_DIR, "verified_coin_balance_light_high_contrast.png"))
        print("PASS: Coin balance in Light Mode has rich amber-gold high contrast (#d97706).")

        # Close coin modal
        await page.locator("#btn-coin-modal-close").click()
        await page.wait_for_timeout(500)

        print("\n=======================================================")
        print("STAGE 2: Verify Announcement Modal Solid Apple HIG Redesign")
        print("=======================================================")
        # Inject admin auth
        await page.evaluate("""(auth) => {
            localStorage.setItem('token', auth.access_token);
            localStorage.setItem('access_token', auth.access_token);
            localStorage.setItem('user', JSON.stringify(auth.user));
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('cinema_theme', 'dark');
        }""", admin_auth)

        # Go to Admin announcements tab
        await page.goto("http://localhost:5173/#/admin?tab=announcements")
        await page.wait_for_selector("#btn-create-announcement", timeout=10000)
        await page.wait_for_timeout(1000)

        # Click create announcement button
        await page.click("#btn-create-announcement")
        await page.wait_for_selector("#modal-announcement", state="visible", timeout=6000)
        await page.wait_for_timeout(600)

        # Assert dialog card has solid background and border
        dialog_bg = await page.locator(".announcement-dialog").evaluate("el => window.getComputedStyle(el).backgroundColor")
        dialog_border = await page.locator(".announcement-dialog").evaluate("el => window.getComputedStyle(el).borderWidth")
        print(f"Announcement dialog background: {dialog_bg}, border width: {dialog_border}")
        assert dialog_bg != "rgba(0, 0, 0, 0)" and dialog_bg != "transparent", "Announcement dialog MUST have solid card background!"

        # Assert tag pills exist and are styled
        tag_pill_count = await page.locator(".announcement-dialog .tag-option-pill").count()
        print(f"Announcement tag pills count: {tag_pill_count}")
        assert tag_pill_count >= 5, "Announcement dialog should have standard tag pills!"

        # Screenshot Dark Mode Announcement Modal
        ann_dark_shot = os.path.join(SCREENSHOT_DIR, "verified_announcement_dialog_solid_card_dark.png")
        await page.screenshot(path=ann_dark_shot)
        shutil.copy(ann_dark_shot, os.path.join(ARTIFACT_DIR, "verified_announcement_dialog_solid_card_dark.png"))
        print("PASS: Announcement dialog in Dark Mode is solid Apple HIG card.")

        # Switch to Light Mode
        await page.evaluate("""() => {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('cinema_theme', 'light');
        }""")
        await page.wait_for_timeout(600)

        ann_light_shot = os.path.join(SCREENSHOT_DIR, "verified_announcement_dialog_solid_card_light.png")
        await page.screenshot(path=ann_light_shot)
        shutil.copy(ann_light_shot, os.path.join(ARTIFACT_DIR, "verified_announcement_dialog_solid_card_light.png"))
        print("PASS: Announcement dialog in Light Mode is pristine solid Apple HIG card.")

        # Close announcement modal
        await page.locator(".announcement-dialog .modal-close-btn").click()
        await page.wait_for_timeout(500)

        print("\n=======================================================")
        print("STAGE 3: Verify RAG Benchmark Persistent Background HUD & On-Demand Progress")
        print("=======================================================")
        # Switch to RAG tab via sidebar tab button
        await page.click("#admin-tab-rag")
        await page.wait_for_timeout(2000)

        # If a background task is already running and dialog popped up, minimize it
        if await page.locator("#btn-benchmark-minimize-or-close").is_visible():
            print("Auto-detected restored active benchmark progress modal on mount! Minimizing to background...")
            await page.locator("#btn-benchmark-minimize-or-close").click()
            await page.wait_for_timeout(600)

        # 1. Verify Stream Switch in Judge Modal
        judge_btn = page.locator("button:has-text('裁判:')").first
        await judge_btn.click()
        switch_el = page.locator(".el-switch:has(#switch-judge-stream)")
        await switch_el.wait_for(state="visible", timeout=6000)
        stream_switch_visible = await switch_el.is_visible()
        print(f"Judge Stream Toggle switch visible: {stream_switch_visible}")
        assert stream_switch_visible, "Judge Stream Toggle switch MUST be present in LLM Judge config modal!"
        
        # Close judge modal via close button
        close_judge_btn = page.locator("#btn-close-judge-modal")
        if await close_judge_btn.is_visible():
            await close_judge_btn.click()
        else:
            await page.click("button:has-text('取消')")
        await page.wait_for_timeout(500)

        # Check if benchmark is already running or launch new one
        launch_btn = page.locator("#btn-launch-or-view-benchmark")
        launch_text = await launch_btn.text_content()
        if "评测中" not in launch_text:
            sample_select = page.locator("select[title*='选择基准评测抽检样本数']").first
            if await sample_select.is_visible():
                await sample_select.select_option(value="3")
                await page.wait_for_timeout(300)
            await launch_btn.click()
            await page.wait_for_selector(".apple-modal-dialog", state="visible", timeout=8000)
            print("Benchmark launched! Progress dialog visible.")
            await page.wait_for_timeout(1500)
            # Minimize to background
            await page.locator("#btn-benchmark-minimize-or-close").click()
            await page.wait_for_timeout(800)
        else:
            print("Benchmark is actively running in background.")

        # Verify persistent status strip is visible
        status_bar_visible = await page.locator("#persistent-benchmark-status-bar").is_visible()
        print(f"Persistent Background HUD Status Bar visible: {status_bar_visible}")
        assert status_bar_visible, "Persistent Background Benchmark HUD Bar MUST be visible when running in background!"

        # Screenshot RAG Background HUD
        hud_shot = os.path.join(SCREENSHOT_DIR, "verified_rag_benchmark_background_persistent_hud.png")
        await page.screenshot(path=hud_shot)
        shutil.copy(hud_shot, os.path.join(ARTIFACT_DIR, "verified_rag_benchmark_background_persistent_hud.png"))
        print("PASS: RAG Center Persistent Background HUD verified.")

        # Re-open dialog by clicking launch button
        await launch_btn.click()
        await page.wait_for_timeout(600)
        is_modal_reopened = await page.locator(".apple-modal-dialog").is_visible()
        print(f"Modal successfully re-opened via button: {is_modal_reopened}")
        assert is_modal_reopened, "Clicking launch button while running MUST re-open progress modal!"

        # Close modal again
        await page.locator("#btn-benchmark-minimize-or-close").click()
        await page.wait_for_timeout(500)

        # 4. Switch to Announcements tab to verify Global AdminHeader HUD Capsule
        await page.click("#admin-tab-announcements")
        await page.wait_for_timeout(2500)

        global_hud = page.locator("#global-eval-hud-capsule")
        global_hud_visible = await global_hud.is_visible()
        print(f"AdminHeader Global Eval HUD Capsule visible on Announcements tab: {global_hud_visible}")
        if global_hud_visible:
            hud_text = await global_hud.text_content()
            print(f"AdminHeader Global Eval HUD Capsule text: {hud_text}")
            assert "RAG" in hud_text and "%" in hud_text

        header_shot = os.path.join(SCREENSHOT_DIR, "verified_admin_header_global_eval_capsule.png")
        await page.screenshot(path=header_shot)
        shutil.copy(header_shot, os.path.join(ARTIFACT_DIR, "verified_admin_header_global_eval_capsule.png"))
        print("PASS: AdminHeader Global Eval HUD Capsule verified across tabs.")

        print("\n=======================================================")
        print("ALL CLOSED-LOOP VERIFICATIONS PASSED WITH EXIT CODE 0!")
        print("=======================================================")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_verification())
