import os
import time
import asyncio
from playwright.async_api import async_playwright

SCREENSHOT_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"
BASE_URL = "http://127.0.0.1:8000"

async def run_e2e():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("[E2E] Step 1: Login as Administrator...")
        await page.goto(f"{BASE_URL}/#/login")
        await page.wait_for_selector("#btn-submit-login", timeout=10000)
        await page.fill("#input-login-username", "admin")
        await page.fill("#input-login-password", "password123")
        await page.click("#btn-submit-login")
        await page.wait_for_timeout(1500)

        print("[E2E] Step 2: Navigate to Admin Console -> Content Moderation & DFA...")
        await page.goto(f"{BASE_URL}/#/admin?tab=contents")
        await page.wait_for_selector("#section-contents", timeout=10000)
        await page.wait_for_timeout(1000)

        # 1. Check Review Queue subtab
        await page.click("#subtab-review-queue")
        await page.wait_for_timeout(600)
        assert await page.is_visible("#card-review-queue")
        print("[E2E] Subtab 1: Review Queue verified.")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step16_admin_review_queue_and_moderation.png"))

        # 2. Check DFA Sensitive Lexicon subtab
        print("[E2E] Subtab 2: DFA Sensitive Lexicon & Sandbox...")
        await page.click("#subtab-sensitive-lexicon")
        await page.wait_for_selector("#card-sensitive-lexicon", timeout=5000)
        await page.wait_for_timeout(800)

        # Open Add Sensitive Word Modal
        await page.click("#btn-add-sensitive-word")
        await page.wait_for_timeout(500)
        assert await page.is_visible("#input-modal-new-word")
        await page.fill("#input-modal-new-word", "高危违禁词条测试")
        await page.select_option("#select-modal-new-word-category", "暴恐")
        await page.select_option("#select-modal-new-word-level", "HIGH")
        await page.click("#btn-confirm-add-word")
        try:
            await page.wait_for_selector(".el-overlay", state="hidden", timeout=5000)
        except Exception:
            await page.wait_for_timeout(1000)
        print("[E2E] Sensitive word '高危违禁词条测试' added and DFA hot-reloaded.")

        # Test DFA Sandbox
        await page.fill("#textarea-dfa-test", "紧急通知：检测到一段含有高危违禁词条测试的发言，请即刻审查")
        await page.click("#btn-run-dfa-test")
        await page.wait_for_selector("#dfa-test-result-box", timeout=5000)
        result_text = await page.inner_text("#dfa-test-result-box")
        assert "命中违禁词" in result_text
        assert "高危违禁词条测试" in result_text
        print("[E2E] DFA Sandbox detected violation and returned sanitized text.")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step16_admin_dfa_sensitive_lexicon.png"))

        # 3. Creator Studio: Manage Dramas and Episodes
        print("[E2E] Step 3: Navigate to Creator Studio...")
        await page.goto(f"{BASE_URL}/#/creator")
        await page.wait_for_timeout(2000)
        
        # If user is not yet recognized as creator in local session, click apply
        if await page.is_visible("#btn-submit-creator-apply"):
            print("[E2E] Unlocking creator privileges on page...")
            await page.click("#btn-submit-creator-apply")
            await page.wait_for_timeout(1500)

        await page.wait_for_selector("#tab-my-dramas", timeout=15000)
        await page.click("#tab-my-dramas")
        await page.wait_for_selector("#panel-my-dramas", timeout=8000)
        await page.wait_for_timeout(1000)

        # Wait for drama cards and action buttons
        await page.wait_for_selector("button[id^='btn-episodes-']", timeout=10000)
        first_episodes_btn = page.locator("button[id^='btn-episodes-']").first
        first_edit_btn = page.locator("button[id^='btn-edit-drama-']").first
        assert await first_episodes_btn.is_visible()
        assert await first_edit_btn.is_visible()

        # Open Edit Drama Modal
        await first_edit_btn.click()
        await page.wait_for_selector("#modal-edit-drama", timeout=5000)
        await page.wait_for_timeout(600)
        print("[E2E] Drama Edit modal opened successfully.")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step16_creator_studio_drama_edit_modal.png"))
        await page.click("#modal-edit-drama button:has-text('取消')")
        await page.wait_for_timeout(500)

        # Open Episodes Management Drawer
        await first_episodes_btn.click()
        await page.wait_for_selector("#modal-manage-episodes", timeout=8000)
        await page.wait_for_timeout(1000)
        assert await page.is_visible("table.creator-table")
        print("[E2E] Creator Episodes Management Drawer opened successfully.")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step16_creator_studio_episodes_drawer.png"))
        await page.click("button:has-text('完成分集编排')")
        await page.wait_for_timeout(500)

        # 4. User Space Reviewer Direct Link
        print("[E2E] Step 4: Check User Space Reviewer Link...")
        await page.goto(f"{BASE_URL}/#/user/space")
        await page.wait_for_selector("#btn-enter-reviewer-space", timeout=8000)
        reviewer_href = await page.get_attribute("#btn-enter-reviewer-space", "href")
        print(f"[E2E] Reviewer space direct link: {reviewer_href}")
        assert "#/admin?tab=contents" in reviewer_href
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step16_user_space_reviewer_direct_link.png"))

        await browser.close()
        print("[E2E] All Playwright End-to-End tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(run_e2e())
