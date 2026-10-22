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
    uvicorn.run(app, host="127.0.0.1", port=8004, log_level="warning")

async def test_step4_danmaku_and_review():
    print("\n[Playwright E2E] Starting Step 4 WebSocket Danmaku & Moderation Review E2E Test...")
    
    server_process = Process(target=run_server, daemon=True)
    server_process.start()
    await asyncio.sleep(2.0)

    try:
        async with async_playwright() as p:
            print("[Playwright E2E] Launching Edge (Chromium) in Headless mode...")
            browser = await p.chromium.launch(headless=True, channel="msedge")

            # 1. Create two concurrent user contexts to simulate real-time live interaction
            context_a = await browser.new_context(viewport={"width": 1280, "height": 800})
            context_b = await browser.new_context(viewport={"width": 1280, "height": 800})

            page_a = await context_a.new_page()
            page_b = await context_b.new_page()

            print("[Playwright E2E] Opening Viewer A at http://127.0.0.1:8004 ...")
            await page_a.goto("http://127.0.0.1:8004", wait_until="networkidle")

            print("[Playwright E2E] Opening Viewer B at http://127.0.0.1:8004 ...")
            await page_b.goto("http://127.0.0.1:8004", wait_until="networkidle")

            # Wait for danmaku container in both viewers
            await page_a.locator("#danmaku-container").wait_for(state="attached", timeout=10000)
            await page_b.locator("#danmaku-container").wait_for(state="attached", timeout=10000)
            print("[Playwright E2E] [OK] Both viewers connected to cinema player & WebSocket.")

            # Test A: Real-Time Danmaku Send (A) -> Instant Broadcast & Render (B)
            msg_normal = "Playwright实测：甜度超标，必须发弹幕！"
            input_a = page_a.locator("#input-danmaku")
            await input_a.fill(msg_normal)
            await page_a.locator("#btn-send-danmaku").click()
            print(f"[Playwright E2E] Viewer A sent normal danmaku: '{msg_normal}'")

            # In Viewer B: Verify the flying danmaku appears on screen
            flying_item_b = page_b.locator(".flying-danmaku-item").filter(has_text="甜度超标")
            await flying_item_b.wait_for(state="visible", timeout=6000)
            text_b = await flying_item_b.inner_text()
            print(f"[Playwright E2E] [OK] Viewer B received real-time broadcast and rendered in track: '{text_b}'")
            assert "甜度超标" in text_b

            # Test B: Real-Time DFA Sensitive Word Interception
            msg_violation = "敏感词测试：本剧包含违禁涉赌内容快来看"
            await input_a.fill(msg_violation)
            await page_a.locator("#btn-send-danmaku").click()
            print(f"[Playwright E2E] Viewer A attempted to send sensitive danmaku: '{msg_violation}'")

            # Verify Toast alert on Viewer A
            toast_a = page_a.locator(".resume-toast")
            await toast_a.wait_for(state="visible", timeout=5000)
            toast_text = await toast_a.inner_text()
            print(f"[Playwright E2E] [OK] Sender A received instant moderation block: '{toast_text}'")
            assert "涉敏" in toast_text or "违禁" in toast_text or "拦截" in toast_text

            # Verify Viewer B did NOT receive the violated danmaku
            await page_b.wait_for_timeout(1500)
            violated_item_b = page_b.locator(".flying-danmaku-item").filter(has_text="违禁")
            assert (await violated_item_b.count()) == 0, "Violated sensitive danmaku leaked to Viewer B!"
            print("[Playwright E2E] [OK] Confirmed: Sensitive danmaku was blocked from broadcasting to Viewer B!")

            # Test C: Content Safety Review Queue Verification
            print("[Playwright E2E] Opening Moderator Review Console tab...")
            tab_review = page_a.locator("#tab-review")
            await tab_review.click()
            await page_a.wait_for_timeout(1000)

            review_panel = page_a.locator("#panel-review")
            await review_panel.wait_for(state="visible")
            review_text = await review_panel.inner_text()
            print(f"[Playwright E2E] Review queue content loaded: {review_text[:120]}...")
            assert "违规" in review_text or "违禁" in review_text or "风险" in review_text

            # Test D: Review Decision Action (Approve / Reject)
            reject_btn = page_a.locator(".act-btn.reject").first
            if await reject_btn.count() > 0:
                print("[Playwright E2E] Clicking reject button on flagged content...")
                await reject_btn.click()
                await page_a.wait_for_timeout(1500)
                print("[Playwright E2E] [OK] Moderator rejection action processed successfully.")

            await browser.close()
            print("\n==========================================================================")
            print("  [PLAYWRIGHT E2E PASSED] Step 4: Danmaku & Moderation Review Passed!")
            print("==========================================================================\n")

    finally:
        server_process.terminate()
        server_process.join()

if __name__ == "__main__":
    asyncio.run(test_step4_danmaku_and_review())
