import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.path.insert(0, "backend")
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import create_access_token

ARTIFACT_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"

db = SessionLocal()
admin_user = db.query(User).filter(User.username == "admin").first()
admin_token = create_access_token({"sub": admin_user.id})
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
            id: '{admin_user.id}',
            username: '{admin_user.username}',
            role: 'ADMIN'
        }}));
        document.documentElement.setAttribute('data-theme', 'light');
    }}""")
    page.reload(wait_until="networkidle")
    time.sleep(1)

    # 点击后台管理导航
    print("Clicking .admin-nav-link...")
    page.locator(".admin-nav-link").click()
    time.sleep(2)

    shot = os.path.join(ARTIFACT_DIR, "debug_admin_view.png")
    page.screenshot(path=shot, full_page=False)
    print(f"Admin shot: {shot}")

    # 点击 RAG 知识与评测
    page.locator("#admin-tab-rag").click()
    time.sleep(2)
    shot_rag = os.path.join(ARTIFACT_DIR, "debug_rag_center.png")
    page.screenshot(path=shot_rag, full_page=False)
    print(f"RAG shot: {shot_rag}")

    # 1. 打开 LLM 裁判配置弹窗（图一验证）
    print("Opening Judge Config Dialog...")
    page.locator("button:has-text('切换MiMo/DeepSeek')").click()
    time.sleep(1)
    shot_dialog = os.path.join(ARTIFACT_DIR, "verified_light_theme_rag_dialog.png")
    page.screenshot(path=shot_dialog, full_page=False)
    print(f"Dialog shot: {shot_dialog}")

    # 点击“取消”按钮关闭弹窗
    print("Closing Dialog via cancel button...")
    page.locator("button:has-text('取消')").click()
    time.sleep(1)

    # 2. 点击 Neo4j 图谱交互拓扑 Tab
    print("Switching to Neo4j Tab...")
    page.locator("#subtab-neo4j").click()
    time.sleep(4)
    shot_neo4j = os.path.join(ARTIFACT_DIR, "verified_neo4j_3d_hologram.png")
    page.screenshot(path=shot_neo4j, full_page=False)
    print(f"Neo4j shot: {shot_neo4j}")

    # 3. 访问播放器页面验证评论微型名片
    print("Navigating to Player view...")
    page.goto("http://localhost:5173/player/1")
    time.sleep(3)
    # 滚动到评论区
    page.evaluate("window.scrollTo(0, 1000)")
    time.sleep(1)
    
    # 查找评论者头像或名称并点击
    commenter = page.locator(".comment-author-trigger").first
    if commenter.count() > 0:
        print("Clicking commenter trigger...")
        commenter.click()
        time.sleep(1)
        shot_card = os.path.join(ARTIFACT_DIR, "verified_player_micro_profile_card.png")
        page.screenshot(path=shot_card, full_page=False)
        print(f"Profile card shot: {shot_card}")
    else:
        print("No commenter trigger found, checking player comments...")

    browser.close()
