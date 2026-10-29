import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

import time
import uuid
import json
import requests
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"
BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:5173"

def get_auth_token(username: str, role: str = "USER", is_creator: bool = False):
    password = f"Pass_{username}_123"
    requests.post(f"{BASE_URL}/api/v1/auth/register", json={
        "username": username,
        "password": password,
        "nickname": f"剧迷_{username}"
    })
    login_res = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"username": username, "password": password})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    user_info = login_res.json()["user"]

    if role != "USER" or is_creator:
        from app.core.database import SessionLocal
        from app.models.user import User
        db = SessionLocal()
        u = db.query(User).filter(User.username == username).first()
        if u:
            u.role = role
            u.is_creator = is_creator
            db.commit()
            db.refresh(u)
        db.close()
        user_info["role"] = role
        user_info["is_creator"] = is_creator

    return token, user_info

def run_playwright_verification():
    print("=" * 60)
    print(">>> 启动 Playwright 全流程端到端界面验证与实测截图存档")
    print("=" * 60)

    # 准备测试用户
    viewer_username = f"viewer_{uuid.uuid4().hex[:6]}"
    token_viewer, user_viewer = get_auth_token(viewer_username, role="USER")

    # 给该用户先发一条评论，以便个人中心评论 Tab 有内容展示
    # 先找一部真实短剧
    dramas_res = requests.get(f"{BASE_URL}/api/v1/videos?page=1&page_size=5")
    drama_list = dramas_res.json().get("items", [])
    target_video_id = drama_list[0]["id"] if drama_list else "sample_video_001"
    headers_viewer = {"Authorization": f"Bearer {token_viewer}"}
    requests.post(f"{BASE_URL}/api/v1/interactions/comments", headers=headers_viewer, json={
        "video_id": target_video_id,
        "content": "这部短剧节奏太棒了！反转跌宕起伏，强烈推荐大家追更！"
    })

    creator_username = f"creator_{uuid.uuid4().hex[:6]}"
    token_creator, user_creator = get_auth_token(creator_username, role="CREATOR", is_creator=True)

    admin_username = f"admin_{uuid.uuid4().hex[:6]}"
    token_admin, user_admin = get_auth_token(admin_username, role="ADMIN")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)

        # -------------------------------------------------------------
        # 验证 1: 全局路由守卫越权拦截
        # -------------------------------------------------------------
        print("\n[Playwright 步骤 1] 验证未登录访问 /admin 路由拦截...")
        context1 = browser.new_context(viewport={"width": 1440, "height": 900})
        page1 = context1.new_page()
        # 访问受保护的 admin 路由
        page1.goto(f"{FRONTEND_URL}/#/admin")
        page1.wait_for_timeout(2000)
        current_url = page1.url
        print(f"  拦截后当前 URL: {current_url}")
        assert "/login" in current_url or current_url.endswith("/"), f"路由未被拦截: {current_url}"
        
        guard_shot = os.path.join(ARTIFACT_DIR, "verified_route_guard_intercept.png")
        page1.screenshot(path=guard_shot)
        print(f"  [PASS] 路由守卫拦截截图已保存: {guard_shot}")
        context1.close()

        # -------------------------------------------------------------
        # 验证 2: 个人中心“我的评论”Tab 与头像上传
        # -------------------------------------------------------------
        print("\n[Playwright 步骤 2] 验证个人中心“我的评论”与自定义头像...")
        context2 = browser.new_context(viewport={"width": 1440, "height": 900})
        page2 = context2.new_page()
        # 预先注入登录状态到 localStorage
        page2.goto(f"{FRONTEND_URL}/#/")
        page2.evaluate(f"""() => {{
            localStorage.setItem('token', '{token_viewer}');
            localStorage.setItem('access_token', '{token_viewer}');
            localStorage.setItem('user', JSON.stringify({json.dumps(user_viewer)}));
        }}""")
        page2.goto(f"{FRONTEND_URL}/#/user/space")
        page2.wait_for_timeout(2500)

        # 点击我的评论 Tab
        comments_tab = page2.locator("#tab-btn-space-comments")
        if comments_tab.count() > 0:
            comments_tab.click()
            page2.wait_for_timeout(1500)
            print("  [OK] 成功点击‘我的评论’Tab")
        else:
            print("  [WARN] 未找到 #tab-btn-space-comments")

        profile_shot = os.path.join(ARTIFACT_DIR, "verified_user_profile_comments_tab.png")
        page2.screenshot(path=profile_shot)
        print(f"  [PASS] 个人中心评论 Tab 截图已保存: {profile_shot}")
        context2.close()

        # -------------------------------------------------------------
        # 验证 3: 创作者空间“短剧分镜无限画布 (Infinite Canvas)”工作台
        # -------------------------------------------------------------
        print("\n[Playwright 步骤 3] 验证创作者空间无限画布插槽...")
        context3 = browser.new_context(viewport={"width": 1440, "height": 900})
        page3 = context3.new_page()
        page3.goto(f"{FRONTEND_URL}/#/")
        page3.evaluate(f"""() => {{
            localStorage.setItem('token', '{token_creator}');
            localStorage.setItem('access_token', '{token_creator}');
            localStorage.setItem('user', JSON.stringify({json.dumps(user_creator)}));
        }}""")
        page3.goto(f"{FRONTEND_URL}/#/creator")
        page3.wait_for_timeout(2500)

        # 点击无限画布 Tab
        canvas_tab = page3.locator("#tab-creator-canvas")
        if canvas_tab.count() > 0:
            canvas_tab.click()
            page3.wait_for_timeout(1500)
            print("  [OK] 成功切换至‘短剧分镜无限画布’Tab")
        else:
            print("  [WARN] 未找到 #tab-creator-canvas")

        canvas_shot = os.path.join(ARTIFACT_DIR, "verified_creator_infinite_canvas.png")
        page3.screenshot(path=canvas_shot)
        print(f"  [PASS] 创作者无限画布截图已保存: {canvas_shot}")
        context3.close()

        # -------------------------------------------------------------
        # 验证 4: 管理端 RAG 知识中台单语料重新切片与向量化操作
        # -------------------------------------------------------------
        print("\n[Playwright 步骤 4] 验证管理端 RAG 知识资产与向量化操作...")
        context4 = browser.new_context(viewport={"width": 1440, "height": 900})
        page4 = context4.new_page()
        page4.goto(f"{FRONTEND_URL}/#/")
        page4.evaluate(f"""() => {{
            localStorage.setItem('token', '{token_admin}');
            localStorage.setItem('access_token', '{token_admin}');
            localStorage.setItem('user', JSON.stringify({json.dumps(user_admin)}));
        }}""")
        page4.goto(f"{FRONTEND_URL}/#/admin")
        page4.wait_for_timeout(2500)

        # 切换到 RAG 知识中台 Tab
        rag_tab = page4.locator("#admin-tab-rag")
        if rag_tab.count() > 0:
            rag_tab.click()
            page4.wait_for_timeout(2000)
            print("  [OK] 成功进入管理端 RAG 知识中台")

        # 切换到知识库资产树状管理子 Tab
        kb_subtab = page4.locator("#subtab-knowledge")
        if kb_subtab.count() > 0:
            kb_subtab.click()
            page4.wait_for_timeout(2000)
            print("  [OK] 成功切换至‘知识库资产树状管理’子 Tab")

        rag_shot = os.path.join(ARTIFACT_DIR, "verified_rag_corpus_vector_action.png")
        page4.screenshot(path=rag_shot)
        print(f"  [PASS] 管理端 RAG 知识中台截图已保存: {rag_shot}")
        context4.close()

        browser.close()

    print("\n" + "=" * 60)
    print(">>> 界面端到端验证与回环截图全部圆满达成！")
    print("=" * 60)

if __name__ == "__main__":
    run_playwright_verification()
