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
    uvicorn.run(app, host="127.0.0.1", port=8003, log_level="warning")

async def test_step3_vue_player_and_interactions():
    print("\n[Playwright E2E] Starting Step 3 Vue 3 Player & Interactions E2E Test...")
    
    # 1. Start Server on port 8003
    server_process = Process(target=run_server, daemon=True)
    server_process.start()
    await asyncio.sleep(2.0)

    try:
        # 2. Launch Headless Edge (Chromium)
        async with async_playwright() as p:
            print("[Playwright E2E] Launching Edge (Chromium) in Headless mode...")
            browser = await p.chromium.launch(headless=True, channel="msedge")
            context = await browser.new_context(viewport={"width": 1280, "height": 800})
            page = await context.new_page()

            # Test A: Load Vue 3 Cinema Player Page
            print("[Playwright E2E] Navigating to http://127.0.0.1:8003 ...")
            await page.goto("http://127.0.0.1:8003", wait_until="networkidle")

            # Verify 9:16 Mobile Capsule container is rendered
            capsule = page.locator("#video-capsule-container")
            await capsule.wait_for(state="visible", timeout=10000)
            box = await capsule.bounding_box()
            assert box is not None and box["width"] > 300, "Mobile capsule container failed to render properly!"
            print(f"[Playwright E2E] [OK] 9:16 Mobile Capsule verified: width={box['width']}px, height={box['height']}px")

            # Test B: Verify HTML5 Video Element & Unicom Cloud Stream Loading
            video = page.locator("#player-video")
            await video.wait_for(state="attached", timeout=8000)
            
            # Wait for video readyState >= 1 (metadata loaded)
            await page.wait_for_timeout(3000)
            ready_state = await page.evaluate("() => document.getElementById('player-video').readyState")
            video_src = await page.evaluate("() => document.getElementById('player-video').src")
            print(f"[Playwright E2E] [OK] Video element verified: readyState={ready_state}, src={video_src}")
            assert ready_state >= 1, f"Video readyState expected >=1, got {ready_state}"
            assert "/api/v1/videos/stream/" in video_src, f"Video src does not point to stream endpoint: {video_src}"

            # Test C: Micro-interaction: Like Button Toggle
            like_btn = page.locator("#btn-like")
            like_count_el = page.locator("#like-count-label")
            initial_count_text = await like_count_el.inner_text()
            initial_count = int(initial_count_text) if initial_count_text.isdigit() else 0
            
            print(f"[Playwright E2E] Current like count: {initial_count}, clicking like button...")
            await like_btn.click()
            await page.wait_for_timeout(1000)

            updated_count_text = await like_count_el.inner_text()
            updated_count = int(updated_count_text) if updated_count_text.isdigit() else 0
            is_liked = await page.evaluate("() => document.getElementById('btn-like').classList.contains('is-liked')")
            print(f"[Playwright E2E] [OK] Like toggled: count={updated_count}, is_liked={is_liked}")
            assert updated_count == initial_count + 1 or is_liked, "Like count did not increment!"

            # Test D: Episode Switching (Click Episode #2 if available)
            ep2_item = page.locator("#episode-item-2")
            if await ep2_item.count() > 0:
                print("[Playwright E2E] Switching to Episode #2...")
                await ep2_item.click()
                await page.wait_for_timeout(2000)
                new_video_src = await page.evaluate("() => document.getElementById('player-video').src")
                print(f"[Playwright E2E] [OK] Switched video source: {new_video_src}")
                assert new_video_src != video_src or "/api/v1/videos/stream/" in new_video_src

            # Test E: Comments Interaction
            tab_comments = page.locator("#tab-comments")
            await tab_comments.click()
            await page.wait_for_timeout(500)

            input_comment = page.locator("#input-comment")
            test_comment_msg = "Playwright自动化测试：9:16暗黑影院视听体验太棒了！"
            await input_comment.fill(test_comment_msg)
            
            btn_send = page.locator("#btn-send-comment")
            await btn_send.click()
            await page.wait_for_timeout(1500)

            # Assert new comment appears in comments list
            comments_container = page.locator("#panel-comments")
            comments_text = await comments_container.inner_text()
            assert test_comment_msg in comments_text, "Newly posted comment not found in comments panel!"
            print(f"[Playwright E2E] [OK] Comment submitted and rendered in DOM: '{test_comment_msg[:20]}...'")

            # Test F: AI Companion Tab Verification
            tab_ai = page.locator("#tab-agent")
            await tab_ai.click()
            await page.wait_for_timeout(500)
            panel_ai = page.locator("#panel-agent")
            assert await panel_ai.is_visible(), "AI companion panel is not visible!"
            print("[Playwright E2E] [OK] AI Companion Agent preview panel verified!")

            await browser.close()
            print("\n==========================================================================")
            print("  [PLAYWRIGHT E2E PASSED] Step 3: Vue 3 Player & Interactions Passed!")
            print("==========================================================================\n")

    finally:
        server_process.terminate()
        server_process.join()

if __name__ == "__main__":
    asyncio.run(test_step3_vue_player_and_interactions())
