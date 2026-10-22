import asyncio
import os
import sys
import httpx
from playwright.async_api import async_playwright

# Ensure backend root on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.core.database import SessionLocal
from app.models.user import User
from app.models.video import Video, VideoEpisode

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "../../storage/test_screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

BASE_URL = "http://127.0.0.1:8000"

async def test_step13_all():
    print("\n=======================================================")
    print("  🚀 [Playwright E2E] 开始执行 Step 13 全流程端到端自动化验收")
    print("=======================================================\n")

    # 1. API Verification: Admin BI Metrics & Pan Sync
    print("[1/5] 测试 Admin BI Metrics & 夸克网盘全量同步接口...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Admin login via quick-switch
        admin_login = await client.post(f"{BASE_URL}/api/v1/auth/quick-switch/ADMIN")
        assert admin_login.status_code == 200, f"Admin login failed: {admin_login.text}"
        admin_token = admin_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}

        # BI Metrics
        bi_resp = await client.get(f"{BASE_URL}/api/v1/admin/bi-metrics", headers=headers)
        assert bi_resp.status_code == 200, f"BI metrics failed: {bi_resp.text}"
        bi_data = bi_resp.json()["data"]["bi_cards"]
        print(f"  ✓ BI Metrics 获取成功: 总播放={bi_data['total_views']}, 短剧数={bi_data['total_dramas']}, 总集数={bi_data['total_episodes']}, 注册用户={bi_data['total_users']}")

        # Pan Sync All
        sync_resp = await client.post(f"{BASE_URL}/api/v1/admin/pan/sync-all", headers=headers)
        assert sync_resp.status_code == 200, f"Pan sync failed: {sync_resp.text}"
        sync_data = sync_resp.json()["data"]
        assert sync_data["dramas_found"] >= 5, f"Expected at least 5 dramas, got {sync_data['dramas_found']}"
        assert sync_data["total_episodes"] >= 500, f"Expected >500 episodes, got {sync_data['total_episodes']}"
        print(f"  ✓ 夸克网盘短剧同步验证通过: 识别到 {sync_data['dramas_found']} 部短剧，共 {sync_data['total_episodes']} 集！")

    # 2. RBAC Workflow: Ordinary user applies -> Admin approves -> Role changes
    print("\n[2/5] 测试普通用户申请审核员与创作者 -> 管理员中台审批流转...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Register test candidate
        test_username = f"candidate_{int(asyncio.get_event_loop().time())}"
        reg_resp = await client.post(f"{BASE_URL}/api/v1/auth/register", json={
            "username": test_username,
            "password": "password123",
            "nickname": "合规测试官"
        })
        assert reg_resp.status_code == 200, f"Register candidate failed: {reg_resp.text}"
        user_id = reg_resp.json()["id"]

        login_resp = await client.post(f"{BASE_URL}/api/v1/auth/login", json={
            "username": test_username,
            "password": "password123"
        })
        assert login_resp.status_code == 200, f"Login candidate failed: {login_resp.text}"
        user_token = login_resp.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # Apply for Reviewer
        apply_rev_resp = await client.post(f"{BASE_URL}/api/v1/user/apply-reviewer", json={
            "reviewer_name": "专业风控测试员",
            "bio": "具备短视频内容合规审核资质"
        }, headers=user_headers)
        assert apply_rev_resp.status_code == 200
        print(f"  ✓ 用户 @{test_username} 成功提交审核员申请")

        # Admin gets applications
        apps_resp = await client.get(f"{BASE_URL}/api/v1/admin/applications", headers=headers)
        assert apps_resp.status_code == 200
        rev_apps = apps_resp.json()["data"]["reviewers"]
        assert any(a["user_id"] == user_id for a in rev_apps), "Candidate not found in pending reviewer apps"

        # Admin approves Reviewer
        approve_resp = await client.post(f"{BASE_URL}/api/v1/admin/reviewers/review", json={
            "user_id": user_id,
            "action": "APPROVE"
        }, headers=headers)
        assert approve_resp.status_code == 200
        print(f"  ✓ 管理员已成功核准 @{test_username} 为认证审核员！")

        # Check user profile
        prof_resp = await client.get(f"{BASE_URL}/api/v1/user/profile", headers=user_headers)
        assert prof_resp.status_code == 200
        assert prof_resp.json()["data"]["is_reviewer"] is True
        assert prof_resp.json()["data"]["role"] == "REVIEWER"
        print(f"  ✓ 验证目标账号权限实时更新: is_reviewer=True, role=REVIEWER")

    # 3. Headless Browser Playwright Testing
    print("\n[3/5] 启动无头浏览器，进行前端视觉与交互端到端验收...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="msedge")
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # Step A: Admin Console Page & Tabs
        print("  -> 访问管理员中台并验证 BI 驾驶舱与 Element Plus 组件...")
        # Inject admin token into localStorage
        await page.goto(f"{BASE_URL}/#/")
        await page.evaluate(f"""() => {{
            localStorage.setItem('cinema_access_token', '{admin_token}');
            localStorage.setItem('user', JSON.stringify({{"id": "admin", "username": "admin", "role": "ADMIN", "nickname": "超级管理员"}}));
        }}""")
        await page.goto(f"{BASE_URL}/#/admin")
        await page.wait_for_selector("#section-bi-dashboard", timeout=15000)

        # Take screenshot of Admin BI Dashboard
        admin_shot = os.path.join(SCREENSHOT_DIR, "step13_admin_bi_dashboard.png")
        await page.screenshot(path=admin_shot, full_page=False)
        print(f"  ✓ 管理员 BI 驾驶舱渲染成功，已截图存证: {admin_shot}")

        # Click Pan Sync button in Admin Console and check toast
        sync_btn = page.locator("#btn-admin-sync-pan")
        await sync_btn.click()
        await page.wait_for_selector("#admin-sync-toast", timeout=15000)
        toast_text = await page.locator("#admin-sync-toast").inner_text()
        print(f"  ✓ 管理员点击同步按钮反馈: {toast_text}")
        assert "扫描识别" in toast_text and "0 部短剧" not in toast_text, f"Toast still says 0! Got: {toast_text}"

        # Click to Users Tab
        await page.click("text=用户与权限治理")
        await page.wait_for_selector("#section-users-rbac", timeout=8000)
        users_shot = os.path.join(SCREENSHOT_DIR, "step13_admin_users_rbac.png")
        await page.screenshot(path=users_shot)
        print(f"  ✓ 用户 RBAC 权限大厅正常渲染: {users_shot}")

        # Step B: User Profile Page Dual Qualification
        print("\n[4/5] 测试个人中心双轨资质入驻卡片...")
        await page.goto(f"{BASE_URL}/#/user/space")
        await page.wait_for_selector("#dual-qualification-box", timeout=15000)
        profile_shot = os.path.join(SCREENSHOT_DIR, "step13_user_space_dual_qualification.png")
        await page.screenshot(path=profile_shot)
        print(f"  ✓ 个人中心创作者与审核员双轨入驻卡片渲染成功: {profile_shot}")

        # Step C: Player 249 Episodes Chunking & Speed/Resolution
        print("\n[5/5] 测试 249 集短剧选集分块 (1-50, 51-100, 全部) 与倍速/清晰度控制...")
        # Find drama with maximum episodes (>50)
        db = SessionLocal()
        from sqlalchemy import func
        drama_max = (
            db.query(Video, func.count(VideoEpisode.id).label('ep_cnt'))
            .join(VideoEpisode, Video.id == VideoEpisode.video_id)
            .group_by(Video.id)
            .order_by(func.count(VideoEpisode.id).desc())
            .first()
        )
        assert drama_max is not None, "No drama with episodes found"
        drama_id = drama_max[0].id
        total_eps = drama_max[1]
        db.close()
        print(f"  -> 加载测试短剧 ID: {drama_id}, 包含 {total_eps} 集")

        await page.goto(f"{BASE_URL}/#/video/{drama_id}")
        await page.wait_for_selector("#player-video", timeout=15000)
        # Wait for async episode list to be fetched and chunk tabs rendered
        await page.wait_for_selector("#episode-chunk-tabs", timeout=15000)
        has_chunks = await page.is_visible("#episode-chunk-tabs")
        print(f"  ✓ 选集分块导航栏渲染检测: {has_chunks}")
        assert has_chunks, "Expected #episode-chunk-tabs to be visible for drama with >50 episodes"
        chunk_buttons = await page.locator("#episode-chunk-tabs button").all_inner_texts()
        print(f"  ✓ 自动计算分块胶囊: {chunk_buttons}")
        assert any("1-50" in b for b in chunk_buttons)
        assert any("51-100" in b for b in chunk_buttons)

        # Click 51-100 chunk
        await page.click("text=51-100")
        await page.wait_for_timeout(500)
        visible_ep_texts = await page.locator(".ep-num-line").all_inner_texts()
        print(f"  ✓ 切换至 51-100 分块后，当前首项集数: {visible_ep_texts[0] if visible_ep_texts else 'None'}")
        assert "第 51 集" in (visible_ep_texts[0] if visible_ep_texts else "")

        # Test Playback Speed Button
        await page.click("#btn-playback-rate")
        await page.wait_for_selector("#menu-playback-speed", timeout=3000)
        print("  ✓ 倍速调节菜单成功弹出！")
        # Click 1.5x
        await page.click('[id="speed-opt-1.5"]')
        rate = await page.evaluate("() => document.getElementById('player-video').playbackRate")
        print(f"  ✓ 视频原生播放倍速已生效: {rate}x")
        assert rate == 1.5, f"Expected playbackRate=1.5, got {rate}"

        # Test Resolution Button
        await page.click("#btn-resolution")
        await page.wait_for_selector("#menu-resolution", timeout=3000)
        print("  ✓ 清晰度画质切换菜单成功弹出！")
        await page.click("text=4K 原画")
        res_text = await page.locator("#btn-resolution").inner_text()
        print(f"  ✓ 当前选定清晰度画质: {res_text}")
        assert "4K" in res_text

        # Capture Player Screenshot
        player_shot = os.path.join(SCREENSHOT_DIR, "step13_player_chunks_speed_res.png")
        await page.screenshot(path=player_shot)
        print(f"  ✓ 播放器选集分块与倍速清晰度控制条截图存证: {player_shot}")

        await browser.close()

    print("\n=======================================================")
    print("  🎉 [PASSED] Step 13 全流程自动化测试全部 100% 通过！")
    print("=======================================================\n")

if __name__ == "__main__":
    asyncio.run(test_step13_all())
