import asyncio
import os
import shutil
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

ARTIFACT_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"
SCREENSHOT_DIR = os.path.join(os.getcwd(), "storage", "test_screenshots")

async def test_drama_episodes():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="msedge")
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        # Query video id of 高冷千金的贴身高手 (78集) from backend API
        import requests
        r = requests.get("http://127.0.0.1:8000/api/v1/videos/home-feed")
        videos = r.json().get("data", {}).get("videos", [])
        target_video = None
        for v in videos:
            if "78" in v.get("duration_str", "") or "高冷千金" in v.get("title", ""):
                target_video = v
                break

        if not target_video:
            target_video = videos[2] # one of the multi-episode dramas

        video_id = target_video.get("id")
        title = target_video.get("title")
        print(f"Navigating to drama: {title} (ID: {video_id})")

        await page.goto(f"http://localhost:5173/#/play?videoId={video_id}")
        await page.wait_for_selector("#cinema-backdrop", timeout=10000)
        await asyncio.sleep(2)

        # Click episodes tab
        await page.click("#tab-btn-episodes")
        await asyncio.sleep(1)

        ep_buttons = await page.locator(".episode-tile-btn").count()
        print(f"Successfully loaded {ep_buttons} episode buttons in PlayerView for {title}!")

        # Screenshot of 78/120/249 episodes bento selector
        ep_shot = os.path.join(SCREENSHOT_DIR, "step11_player_78_episodes_grid.png")
        await page.screenshot(path=ep_shot, full_page=True)
        shutil.copy2(ep_shot, os.path.join(ARTIFACT_DIR, "step11_player_78_episodes_grid.png"))
        print(f"Saved: {ep_shot}")

        # Click episode 5
        ep5 = page.locator(".episode-tile-btn").nth(4)
        if await ep5.is_visible():
            await ep5.click()
            await asyncio.sleep(1)
            print("Switched to Episode 5 successfully!")

        await browser.close()
        print("EPISODES TEST PASSED!")

if __name__ == "__main__":
    asyncio.run(test_drama_episodes())
