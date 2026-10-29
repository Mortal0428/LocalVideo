import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.path.insert(0, "backend")
from app.core.database import SessionLocal
from app.models.user import User
from app.models.video import Video
from app.core.security import create_access_token

ARTIFACT_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"

db = SessionLocal()
admin_user = db.query(User).filter(User.username == "admin").first()
admin_id = admin_user.id
admin_name = admin_user.username
admin_token = create_access_token({"sub": admin_id})

first_video = db.query(Video).first()
video_id = first_video.id
db.close()

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    page.goto("http://localhost:5173/")
    page.evaluate(f"""() => {{
        localStorage.setItem('cinema_access_token', '{admin_token}');
        localStorage.setItem('token', '{admin_token}');
        localStorage.setItem('access_token', '{admin_token}');
        localStorage.setItem('user', JSON.stringify({{
            id: '{admin_id}',
            username: '{admin_name}',
            role: 'ADMIN'
        }}));
        document.documentElement.setAttribute('data-theme', 'light');
    }}""")
    
    print(f"Visiting player page via hash URL: http://localhost:5173/#/play/{video_id}")
    page.goto(f"http://localhost:5173/#/play/{video_id}")
    page.wait_for_load_state("networkidle")
    time.sleep(3)

    # 滚动到评论区
    print("Scrolling to comment box...")
    page.evaluate("window.scrollTo(0, 800)")
    time.sleep(1)

    # 截图当前播放器页面以验证
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "debug_player_real.png"))

    # 在输入框中输入评论并提交
    print("Writing comment in input box...")
    input_box = page.locator("#input-comment")
    if input_box.count() > 0:
        input_box.fill("这反转节奏太强了！顾总这一波眼神杀完全绝杀全场，坐等下一集更新！")
        time.sleep(1)
        print("Clicking submit comment...")
        page.locator("#btn-submit-comment").click()
        time.sleep(2)

    # 点击评论者头像/昵称打开名片
    print("Locating clickable user...")
    clickable = page.locator(".clickable-user").first
    if clickable.count() > 0:
        clickable.click()
        time.sleep(2)
        shot_card = os.path.join(ARTIFACT_DIR, "verified_player_user_micro_profile_card.png")
        page.screenshot(path=shot_card, full_page=False)
        print(f"Captured card shot: {shot_card}")
    else:
        print("No clickable user found!")

    browser.close()
