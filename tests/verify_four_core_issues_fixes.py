"""
CinemaAgent 工业级端到端全量闭环验证脚本 (精确直连模式)
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.path.insert(0, "backend")
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import create_access_token

ARTIFACT_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"

def run():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    db = SessionLocal()
    admin_user = db.query(User).filter(User.username == "admin").first()
    admin_token = create_access_token({"sub": admin_user.id})
    db.close()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("[Step 1] 注入 Admin 登录态...")
        page.goto("http://localhost:5173/", wait_until="networkidle")
        page.evaluate(f"""() => {{
            localStorage.setItem('cinema_access_token', '{admin_token}');
            localStorage.setItem('token', '{admin_token}');
            localStorage.setItem('access_token', '{admin_token}');
            localStorage.setItem('user', JSON.stringify({{
                id: '{admin_user.id}',
                username: '{admin_user.username}',
                role: 'ADMIN',
                nickname: '超级管理员'
            }}));
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('cinema_theme', 'light');
        }}""")
        time.sleep(1)

        # 1. 验证播放器页面，点击剧迷头像弹出微型社交名片
        print("[Step 2] 访问有真实评论的短剧播放页，验证剧迷微型社交名片浮层...")
        page.goto("http://localhost:5173/play/2b575454-7946-4f28-a9d6-7bb043f01fac", wait_until="networkidle")
        time.sleep(2.5)

        page.evaluate("() => { const el = document.getElementById('comments-flow-list'); if (el) el.scrollIntoView(); }")
        time.sleep(1)

        commenter = page.locator(".clickable-user").first
        if commenter.count() > 0:
            commenter.click()
            time.sleep(1.5)
            shot3 = os.path.join(ARTIFACT_DIR, "verified_player_user_micro_profile_card.png")
            page.screenshot(path=shot3, full_page=False)
            print(f"-> 截图存档: {shot3}")

        # 2. 直达后台管理 RAG 知识中台大屏 (?tab=rag)
        print("[Step 3] 访问管理中台 RAG 知识中台大屏 (?tab=rag)...")
        page.goto("http://localhost:5173/admin?tab=rag", wait_until="networkidle")
        time.sleep(3)

        page.evaluate("() => { document.documentElement.setAttribute('data-theme', 'light'); localStorage.setItem('cinema_theme', 'light'); }")
        time.sleep(1)

        # 验证弹窗按钮与短剧下拉框 (触发开始基准评测弹窗)
        print("[Step 4] 触发基准评测弹窗，验证浅色模式高反差按钮与短剧下拉框防截断...")
        eval_btn = page.locator("button:has-text('开始基准评测')").first
        if eval_btn.count() > 0:
            eval_btn.click()
            time.sleep(1.5)
            shot4 = os.path.join(ARTIFACT_DIR, "verified_light_theme_rag_dialog_high_contrast.png")
            page.screenshot(path=shot4, full_page=False)
            print(f"-> 截图存档: {shot4}")

            # 关闭弹窗
            close_btn = page.locator(".apple-soft-capsule-btn").first
            if close_btn.count() > 0:
                close_btn.click()
                time.sleep(0.5)

        # 3. 切换到 Neo4j 拓扑 Tab
        print("[Step 5] 切换至 Neo4j 3D 拓扑 Tab，验证全息晶体球体与全库规模指示牌...")
        neo4j_tab = page.locator("#subtab-neo4j")
        if neo4j_tab.count() > 0:
            neo4j_tab.click()
            time.sleep(3)

            shot5 = os.path.join(ARTIFACT_DIR, "verified_neo4j_3d_holographic_quantum_spheres_light.png")
            page.screenshot(path=shot5, full_page=False)
            print(f"-> 截图存档: {shot5}")

            # 切换深色模式下查看 3D 全息球体与空间网格
            page.evaluate("() => { document.documentElement.setAttribute('data-theme', 'dark'); localStorage.setItem('cinema_theme', 'dark'); }")
            time.sleep(1.5)

            shot6 = os.path.join(ARTIFACT_DIR, "verified_neo4j_3d_holographic_quantum_spheres_dark.png")
            page.screenshot(path=shot6, full_page=False)
            print(f"-> 截图存档: {shot6}")

        browser.close()
        print("闭环验证全部执行完毕！")

if __name__ == "__main__":
    run()
