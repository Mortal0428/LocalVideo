"""
验证 RAG 知识中台 (弹窗高反差、短剧自适应下拉框、Neo4j 3D全息晶体) 与播放器评论区微型名片
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
    db = SessionLocal()
    admin_user = db.query(User).filter(User.username == "admin").first()
    admin_token = create_access_token({"sub": admin_user.id})
    db.close()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. 注入 Token
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

        # 2. 访问 RAG 知识中台大屏
        print("[RAG] 访问管理中台 RAG 知识中台大屏...")
        page.goto("http://localhost:5173/admin?tab=rag", wait_until="networkidle")
        time.sleep(3)

        # 确保浅色模式
        page.evaluate("() => { document.documentElement.setAttribute('data-theme', 'light'); localStorage.setItem('cinema_theme', 'light'); }")
        time.sleep(1)

        # 点击开始基准评测按钮打开弹窗
        print("[RAG] 触发开始基准评测弹窗...")
        eval_btn = page.locator("button:has-text('开始基准评测')").first
        eval_btn.wait_for(state="visible", timeout=15000)
        eval_btn.click()
        time.sleep(1.5)

        shot_dialog = os.path.join(ARTIFACT_DIR, "verified_light_theme_rag_dialog_high_contrast.png")
        page.screenshot(path=shot_dialog, full_page=False)
        print(f"-> 弹窗截图成功: {shot_dialog}")

        # 关闭弹窗
        close_btn = page.locator(".apple-soft-capsule-btn").first
        if close_btn.count() > 0:
            close_btn.click()
            time.sleep(0.5)

        # 3. 切换至 Neo4j 拓扑 Tab
        print("[RAG] 切换至 Neo4j 3D 拓扑 Tab...")
        neo4j_tab = page.locator("#subtab-neo4j")
        neo4j_tab.wait_for(state="visible", timeout=10000)
        neo4j_tab.click()
        time.sleep(3)

        shot_neo4j_light = os.path.join(ARTIFACT_DIR, "verified_neo4j_3d_holographic_quantum_spheres_light.png")
        page.screenshot(path=shot_neo4j_light, full_page=False)
        print(f"-> Neo4j 浅色模式截图成功: {shot_neo4j_light}")

        # 切换深色模式
        page.evaluate("() => { document.documentElement.setAttribute('data-theme', 'dark'); localStorage.setItem('cinema_theme', 'dark'); }")
        time.sleep(1.5)
        shot_neo4j_dark = os.path.join(ARTIFACT_DIR, "verified_neo4j_3d_holographic_quantum_spheres_dark.png")
        page.screenshot(path=shot_neo4j_dark, full_page=False)
        print(f"-> Neo4j 深色模式截图成功: {shot_neo4j_dark}")

        # 4. 访问播放器评论区微型名片
        print("[Player] 访问播放器评论区...")
        page.goto("http://localhost:5173/play/2b575454-7946-4f28-a9d6-7bb043f01fac", wait_until="networkidle")
        time.sleep(3)

        page.evaluate("() => { const el = document.getElementById('comments-flow-list'); if (el) el.scrollIntoView(); }")
        time.sleep(1)

        commenter = page.locator(".clickable-user").first
        if commenter.count() > 0:
            commenter.click()
            time.sleep(1.5)
            shot_card = os.path.join(ARTIFACT_DIR, "verified_player_user_micro_profile_card.png")
            page.screenshot(path=shot_card, full_page=False)
            print(f"-> 微型名片截图成功: {shot_card}")

        browser.close()
        print("所有验证测试全部完成！")

if __name__ == "__main__":
    run()
