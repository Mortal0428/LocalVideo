import asyncio
import os
import sys
import uvicorn
from multiprocessing import Process
from playwright.async_api import async_playwright

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from main import app
from app.core.database import SessionLocal
from app.models.video import VideoEpisode

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")

async def test_step1_cloud_stream_headless():
    # 1. Fetch valid seeded episode_id from MySQL
    db = SessionLocal()
    episode = db.query(VideoEpisode).filter(VideoEpisode.raw_file_path.like("%乘风2026%")).first()
    db.close()
    
    assert episode is not None, "Seeded episode not found in database!"
    episode_id = episode.id
    print(f"\n[Playwright E2E] Testing Episode ID: {episode_id} ({episode.title})")

    # 2. Launch FastAPI Test Server on port 8001
    server_process = Process(target=run_server, daemon=True)
    server_process.start()
    await asyncio.sleep(1.5)  # Wait for server warm up

    try:
        # 3. Launch Headless Playwright Browser
        async with async_playwright() as p:
            print("[Playwright E2E] Launching Edge (Chromium) in Headless mode...")
            browser = await p.chromium.launch(headless=True, channel="msedge")
            context = await browser.new_context()

            # Test A: Cloud Files List Endpoint
            api_client = context.request
            files_resp = await api_client.get("http://127.0.0.1:8001/api/v1/videos/cloud-files")
            assert files_resp.status == 200, f"Expected 200, got {files_resp.status}"
            files_data = await files_resp.json()
            print(f"[Playwright E2E] [OK] Cloud Files listing succeeded! Files detected: {len(files_data.get('data', []))}")

            # Test B: Initial Range Stream Request (First 2KB)
            stream_url = f"http://127.0.0.1:8001/api/v1/videos/stream/{episode_id}"
            headers_start = {"Range": "bytes=0-2048", "User-Agent": "Playwright-Headless"}
            
            print(f"[Playwright E2E] Requesting initial chunk from Unicom Cloud via {stream_url} ...")
            resp_start = await api_client.get(stream_url, headers=headers_start)
            
            assert resp_start.status == 206, f"Expected 206 Partial Content, got {resp_start.status}"
            headers_dict = resp_start.headers
            assert "bytes 0-2048" in headers_dict.get("content-range", ""), f"Invalid Content-Range: {headers_dict.get('content-range')}"
            
            body_start = await resp_start.body()
            assert len(body_start) == 2049, f"Expected 2049 bytes, got {len(body_start)}"
            assert b"ftyp" in body_start[:16], "Missing MP4 'ftyp' container header in stream!"
            print(f"[Playwright E2E] [OK] Head chunk verified: HTTP 206, size={len(body_start)}B, ftyp signature confirmed!")

            # Test C: Middle Seeking Range Request (Simulate User Fast-Forward to mid-video)
            headers_seek = {"Range": "bytes=2000000-2004096", "User-Agent": "Playwright-Headless"}
            print("[Playwright E2E] Requesting seek chunk (offset ~2MB) to test player fast-forwarding...")
            resp_seek = await api_client.get(stream_url, headers=headers_seek)
            
            assert resp_seek.status == 206, f"Expected 206 on seek, got {resp_seek.status}"
            assert "bytes 2000000-2004096" in resp_seek.headers.get("content-range", "")
            body_seek = await resp_seek.body()
            assert len(body_seek) == 4097, f"Expected 4097 bytes, got {len(body_seek)}"
            print(f"[Playwright E2E] [OK] Fast-forward seeking chunk verified: HTTP 206, offset 2MB, size={len(body_seek)}B!")

            # Test D: Direct Headless Page Video Element Playback Check
            page = await context.new_page()
            # Inject a minimal video element to test native browser playback capability
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body>
                <video id="testVideo" controls autoplay width="320">
                    <source src="{stream_url}" type="video/mp4">
                </video>
            </body>
            </html>
            """
            await page.set_content(html_content)
            await page.wait_for_timeout(2000)
            
            # Check video element readyState in headless browser
            ready_state = await page.evaluate("() => document.getElementById('testVideo').readyState")
            print(f"[Playwright E2E] [OK] Headless HTML5 <video> readyState: {ready_state} (>=1 means metadata loaded)")
            assert ready_state >= 1, f"Video element failed to load metadata, readyState={ready_state}"

            await browser.close()
            print("\n=======================================================")
            print("  [PLAYWRIGHT E2E PASSED] Step 1: Unicom Cloud Disk Stream Verification Passed!")
            print("=======================================================\n")
    finally:
        server_process.terminate()
        server_process.join()

if __name__ == "__main__":
    asyncio.run(test_step1_cloud_stream_headless())
