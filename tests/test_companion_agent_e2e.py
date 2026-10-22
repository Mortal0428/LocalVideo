# -*- coding: utf-8 -*-
import os
import sys
import time
from playwright.sync_api import sync_playwright

def run_companion_agent_e2e():
    artifact_dir = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"
    screenshot_path = os.path.join(artifact_dir, "step15_companion_agent_rag_stream.png")
    highlights_screenshot_path = os.path.join(artifact_dir, "step15_highlights_timeline_list.png")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("1. Navigating to player page...")
        page.goto("http://127.0.0.1:5173/#/video/latest", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2500)

        # 2. Check and click Highlights tab using CSS ID
        print("2. Testing Highlights tab (#tab-btn-highlights)...")
        page.wait_for_selector("#tab-btn-highlights", timeout=15000)
        page.click("#tab-btn-highlights")
        page.wait_for_timeout(1500)
        page.screenshot(path=highlights_screenshot_path)
        print(f"Highlights screenshot saved to {highlights_screenshot_path}")

        # 3. Click Agent Companion Tab using CSS ID
        print("3. Switching to Companion Agent tab (#tab-btn-agent)...")
        page.wait_for_selector("#tab-btn-agent", timeout=15000)
        page.click("#tab-btn-agent")
        page.wait_for_timeout(1500)

        # 4. Click the 3rd prompt pill: 背景音乐唱的是什么歌曲？
        print("4. Clicking 3rd quick prompt pill (背景音乐唱的是什么歌曲？)...")
        page.wait_for_selector(".quick-prompt-pill", timeout=15000)
        prompt_pills = page.locator(".quick-prompt-pill")
        print(f"Found {prompt_pills.count()} quick prompt pills.")
        prompt_pills.last.click()

        # 5. Wait for SSE streaming response from DeepSeek-R1...
        print("5. Waiting for SSE streaming response from DeepSeek-R1...")
        page.wait_for_selector(".jump-timestamp-btn", timeout=25000)
        page.wait_for_timeout(14000)

        # Print the received AI text
        last_bubble = page.locator(".bubble-body-text").last
        print("AI Response text length:", len(last_bubble.inner_text()))

        # 6. Click the Action Card jump button to jump video to that timestamp
        jump_btn = page.locator(".jump-timestamp-btn").last
        jump_btn.click()
        page.wait_for_timeout(2000)

        # 7. Check video playback time
        current_time = page.evaluate("() => document.querySelector('video') ? document.querySelector('video').currentTime : 0")
        print(f"Video playback currentTime after jump: {current_time} seconds")

        # 8. Capture high-res screenshot of the Companion Agent panel
        print("8. Capturing companion agent screenshot...")
        page.screenshot(path=screenshot_path)
        print(f"Companion Agent screenshot saved to {screenshot_path}")

        browser.close()
        print("E2E Test execution completed successfully!")

if __name__ == "__main__":
    run_companion_agent_e2e()
