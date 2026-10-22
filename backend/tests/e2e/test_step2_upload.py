import os
import sys
import math
import asyncio
import subprocess
import uvicorn
from multiprocessing import Process
from playwright.async_api import async_playwright

# Ensure backend root is on sys.path and configure UTF-8 output
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from main import app
from app.core.config import settings

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="warning")

def generate_test_video(path: str):
    """Generate a valid 2-second vertical (320x568) MP4 video via FFmpeg."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=duration=2:size=320x568:rate=25",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=2",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "aac",
        path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

async def test_step2_chunk_upload_and_pipeline():
    sample_video_path = os.path.join(settings.UPLOAD_DIR, "step2_test_video.mp4")
    generate_test_video(sample_video_path)
    file_size = os.path.getsize(sample_video_path)
    print(f"\n[Playwright E2E] Generated test video: {sample_video_path} ({file_size} bytes)")

    # Read binary bytes and split into 3 chunks
    with open(sample_video_path, "rb") as f:
        video_bytes = f.read()
    
    total_chunks = 3
    chunk_size = math.ceil(file_size / total_chunks)
    chunks = [video_bytes[i:i + chunk_size] for i in range(0, file_size, chunk_size)]
    print(f"[Playwright E2E] Sliced into {len(chunks)} chunks for chunked upload simulation.")

    # Launch server on port 8002
    server_process = Process(target=run_server, daemon=True)
    server_process.start()
    await asyncio.sleep(1.8)

    try:
        async with async_playwright() as p:
            print("[Playwright E2E] Launching Edge (Chromium) in Headless mode...")
            browser = await p.chromium.launch(headless=True, channel="msedge")
            context = await browser.new_context()
            api_client = context.request

            # Step A: Initialize Chunk Upload
            init_payload = {
                "title": "第2集：端到端分片上传与转码自测",
                "episode_num": 2,
                "filename": "step2_test_video.mp4",
                "total_chunks": len(chunks),
                "file_size": file_size
            }
            init_resp = await api_client.post("http://127.0.0.1:8002/api/v1/upload/init", data=init_payload)
            assert init_resp.status == 200, f"Init upload failed: {init_resp.status} - {await init_resp.text()}"
            init_data = (await init_resp.json())["data"]
            upload_id = init_data["upload_id"]
            episode_id = init_data["episode_id"]
            print(f"[Playwright E2E] [OK] Upload initialized! upload_id={upload_id}, episode_id={episode_id}")

            # Step B: Upload each chunk sequentially via multipart form
            for idx, chunk_data in enumerate(chunks):
                form_data = {
                    "upload_id": upload_id,
                    "chunk_index": str(idx),
                    "file": {
                        "name": f"chunk_{idx}.part",
                        "mimeType": "application/octet-stream",
                        "buffer": chunk_data
                    }
                }
                chunk_resp = await api_client.post("http://127.0.0.1:8002/api/v1/upload/chunk", multipart=form_data)
                assert chunk_resp.status == 200, f"Chunk {idx} upload failed: {chunk_resp.status}"
                print(f"[Playwright E2E] [OK] Chunk {idx}/{len(chunks) - 1} ({len(chunk_data)} bytes) uploaded successfully.")

            # Step C: Complete and trigger merge + background transcode
            complete_payload = {
                "upload_id": upload_id,
                "episode_id": episode_id,
                "total_chunks": len(chunks)
            }
            complete_resp = await api_client.post("http://127.0.0.1:8002/api/v1/upload/complete", data=complete_payload)
            assert complete_resp.status == 200, f"Complete upload failed: {complete_resp.status}"
            print("[Playwright E2E] [OK] Complete signal acknowledged, background transcode pipeline running...")

            # Step D: Poll status until READY
            is_ready = False
            for attempt in range(25):
                await asyncio.sleep(1.5)
                status_resp = await api_client.get(f"http://127.0.0.1:8002/api/v1/upload/status/{episode_id}")
                assert status_resp.status == 200
                st_data = (await status_resp.json())["data"]
                status = st_data.get("transcode_status")
                print(f"[Playwright E2E] Polling episode status... (attempt {attempt + 1}): {status}")
                if status == "READY":
                    is_ready = True
                    print(f"[Playwright E2E] [OK] Transcode and Unicom Cloud Disk sync completed! duration={st_data.get('duration_seconds')}s, raw_path={st_data.get('raw_file_path')}")
                    break
                elif status == "FAILED":
                    raise AssertionError("Transcode pipeline failed with status FAILED")

            assert is_ready, "Episode transcode timed out!"

            # Step E: Direct Headless Page Video Playback Verification
            stream_url = f"http://127.0.0.1:8002/api/v1/videos/stream/{episode_id}"
            print(f"[Playwright E2E] Testing video stream playback from Unicom Cloud via {stream_url} ...")
            
            page = await context.new_page()
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body>
                <video id="uploadedVideo" controls autoplay width="320">
                    <source src="{stream_url}" type="video/mp4">
                </video>
            </body>
            </html>
            """
            await page.set_content(html_content)
            await page.wait_for_timeout(2500)

            ready_state = await page.evaluate("() => document.getElementById('uploadedVideo').readyState")
            print(f"[Playwright E2E] [OK] Headless HTML5 <video> readyState: {ready_state} (>=1 means metadata loaded)")
            assert ready_state >= 1, f"Video element failed to load stream metadata, readyState={ready_state}"

            await browser.close()
            print("\n==========================================================================")
            print("  [PLAYWRIGHT E2E PASSED] Step 2: Chunk Upload & FFmpeg Cloud Sync Passed!")
            print("==========================================================================\n")

    finally:
        server_process.terminate()
        server_process.join()
        if os.path.exists(sample_video_path):
            os.remove(sample_video_path)

if __name__ == "__main__":
    asyncio.run(test_step2_chunk_upload_and_pipeline())
