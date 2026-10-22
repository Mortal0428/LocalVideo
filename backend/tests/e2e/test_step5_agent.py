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
    uvicorn.run(app, host="127.0.0.1", port=8005, log_level="warning")

async def test_step5_video_agent_companion():
    print("\n[Playwright E2E] Starting Step 5 Video Knowledge RAG & Companion Agent E2E Test...")
    
    server_process = Process(target=run_server, daemon=True)
    server_process.start()
    await asyncio.sleep(2.0)

    try:
        async with async_playwright() as p:
            print("[Playwright E2E] Launching Edge (Chromium) in Headless mode...")
            browser = await p.chromium.launch(headless=True, channel="msedge")
            context = await browser.new_context(viewport={"width": 1280, "height": 800})
            page = await context.new_page()

            print("[Playwright E2E] Navigating to Cinema Player at http://127.0.0.1:8005 ...")
            await page.goto("http://127.0.0.1:8005", wait_until="networkidle")

            # 1. Switch to AI Companion Panel
            print("[Playwright E2E] Opening '✨ 剧情伴读' AI Agent tab...")
            tab_agent = page.locator("#tab-agent")
            await tab_agent.click()
            await page.wait_for_timeout(500)

            agent_panel = page.locator("#panel-agent")
            await agent_panel.wait_for(state="visible")
            print("[Playwright E2E] [OK] AI Companion Agent panel is visible.")

            # 2. Check Quick Prompt Pills
            qp_first = page.locator("#qp-pill-0")
            await qp_first.wait_for(state="visible")
            qp_text = await qp_first.inner_text()
            print(f"[Playwright E2E] Found Quick Prompt Pill: '{qp_text}'")

            # 3. Test Question A: Click Quick Prompt Pill
            print(f"[Playwright E2E] Clicking quick prompt: '{qp_text}' ...")
            await qp_first.click()

            # Wait for Agent response row to appear
            agent_reply = page.locator(".agent-msg-row.agent").last
            await agent_reply.wait_for(state="visible", timeout=8000)
            reply_text = await agent_reply.inner_text()
            print(f"[Playwright E2E] [OK] Agent responded: {reply_text[:100]}...")
            assert "相遇" in reply_text or "镜头" in reply_text or "00:00" in reply_text

            # 4. Test In-Player Video Seek Jump Trigger
            jump_btn = agent_reply.locator(".jump-timestamp-btn")
            await jump_btn.wait_for(state="visible")
            jump_label = await jump_btn.inner_text()
            print(f"[Playwright E2E] Found Jump Button: '{jump_label}', clicking to jump video frame...")
            await jump_btn.click()
            await page.wait_for_timeout(1000)

            # Assert Toast feedback appears
            toast = page.locator(".resume-toast")
            await toast.wait_for(state="visible", timeout=4000)
            toast_text = await toast.inner_text()
            print(f"[Playwright E2E] [OK] Video jump confirmed with Toast: '{toast_text}'")
            assert "精准定位" in toast_text or "00:00" in toast_text

            # 5. Test Question B: Custom Text Question in Input Area
            custom_question = "这一集最甜的高能看点在哪里？"
            print(f"[Playwright E2E] Asking custom question: '{custom_question}' ...")
            input_agent = page.locator("#input-agent")
            await input_agent.fill(custom_question)
            
            send_btn = page.locator("#btn-send-agent")
            await send_btn.click()

            # Wait for new agent reply
            await page.wait_for_timeout(1500)
            new_agent_reply = page.locator(".agent-msg-row.agent").last
            await new_agent_reply.wait_for(state="visible", timeout=8000)
            new_reply_text = await new_agent_reply.inner_text()
            print(f"[Playwright E2E] [OK] Agent responded to custom question: {new_reply_text[:100]}...")
            assert "高能" in new_reply_text or "合唱" in new_reply_text or "跳转" in new_reply_text or "名场面" in new_reply_text

            await browser.close()
            print("\n==========================================================================")
            print("  [PLAYWRIGHT E2E PASSED] Step 5: Multi-Modal Video Agent Passed!")
            print("==========================================================================\n")

    finally:
        server_process.terminate()
        server_process.join()

if __name__ == "__main__":
    asyncio.run(test_step5_video_agent_companion())
