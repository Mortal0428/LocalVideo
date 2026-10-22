import asyncio
import os
import sys

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from playwright.async_api import async_playwright

ARTIFACTS_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"

async def run_e2e_test():
    print("=== 开始端到端自动化验收测试 (Step 12: 主题切换、自定义模型配置、管理员同步与暗黑模式) ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # Step 1: Open Portal on Port 8000 (FastAPI static dist)
        print("[1/5] 打开平台主页 http://127.0.0.1:8000/ ...")
        await page.goto("http://127.0.0.1:8000/", wait_until="networkidle", timeout=20000)
        await page.wait_for_timeout(2000)

        # Verify home feed has real Quark dramas
        cards = await page.locator(".bento-card").all()
        print(f"-> 视听大厅当前加载了 {len(cards)} 个短剧卡片")
        assert len(cards) > 0, "首页未渲染出任何短剧卡片！"

        # Screenshot Light Mode
        light_path = os.path.join(ARTIFACTS_DIR, "step12_portal_light_quark_dramas.png")
        await page.screenshot(path=light_path)
        print(f"-> 已捕获白天明亮模式大厅截图: {light_path}")

        # Step 2: Test Theme Toggle (Light -> Dark -> System)
        print("[2/5] 测试主题切换器 (☀️ / 🌙 / 💻) ...")
        theme_dark_btn = page.locator("#btn-theme-dark")
        await theme_dark_btn.click()
        await page.wait_for_timeout(800)
        theme_val = await page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        print(f"-> 切换至暗黑模式: data-theme={theme_val}")
        assert theme_val == "dark", f"暗黑模式切换失败，当前为 {theme_val}"

        dark_path = os.path.join(ARTIFACTS_DIR, "step12_portal_dark_mode.png")
        await page.screenshot(path=dark_path)
        print(f"-> 已捕获暗黑夜间模式大厅截图: {dark_path}")

        # Switch back to light
        await page.locator("#btn-theme-light").click()
        await page.wait_for_timeout(500)
        theme_val = await page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        print(f"-> 切换回浅色模式: data-theme={theme_val}")
        assert theme_val == "light", f"浅色模式切换失败，当前为 {theme_val}"

        # Step 3: Test Engine Settings Modal (Custom Model & ADMIN Protection)
        print("[3/5] 测试模型引擎配置（自定义模型自由输入 + 管理员 RBAC）...")
        # First ensure non-admin
        await page.locator("#btn-role-user").click()
        await page.wait_for_timeout(1000)
        
        # Open modal
        await page.locator("#btn-engine-settings").click()
        await page.wait_for_timeout(1000)

        # Check read-only notice
        notice_visible = await page.locator("#engine-readonly-notice").is_visible()
        print(f"-> 普通用户打开模型配置，是否显示只读提示: {notice_visible}")
        assert notice_visible, "非管理员未展示只读锁定警告！"

        # Click switch to ADMIN in modal
        print("-> 点击一键切换为管理员 (ADMIN)...")
        await page.locator("#btn-switch-admin-in-modal").click()
        await page.wait_for_timeout(1200)

        # Check input is now enabled
        chat_input = page.locator("#input-chat-model")
        is_disabled = await chat_input.is_disabled()
        print(f"-> 切换管理员后，输入框是否仍禁用: {is_disabled}")
        assert not is_disabled, "切换管理员后模型输入框未解锁！"

        # Type custom model name
        custom_model = "qwen2.5:7b-custom-rag"
        await chat_input.fill("")
        await chat_input.fill(custom_model)
        await page.wait_for_timeout(500)

        # Screenshot modal
        modal_path = os.path.join(ARTIFACTS_DIR, "step12_engine_settings_custom_model_admin.png")
        await page.screenshot(path=modal_path)
        print(f"-> 已捕获模型引擎自定义配置截图: {modal_path}")

        # Save config
        print("-> 保存自定义模型配置...")
        await page.locator("#btn-save-engine-config").click()
        await page.wait_for_timeout(1500)

        # Step 4: Test Admin Console & Full Pan Sync Button
        print("[4/5] 测试管理员控制台与一键全量同步网盘短剧...")
        await page.goto("http://127.0.0.1:8000/#/admin", wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(2000)

        sync_btn = page.locator("#btn-admin-sync-pan")
        assert await sync_btn.is_visible(), "管理员控制台未找到【一键全量同步网盘短剧】按钮！"

        print("-> 点击一键全量同步网盘短剧按钮...")
        await sync_btn.click()
        toast = page.locator("#admin-sync-toast")
        await toast.wait_for(state="visible", timeout=25000)
        toast_text = await toast.text_content()
        print(f"-> 同步反馈提示: {toast_text}")
        assert "同步成功" in toast_text or "扫描识别" in toast_text, f"同步提示内容异常: {toast_text}"

        admin_path = os.path.join(ARTIFACTS_DIR, "step12_admin_console_sync_success.png")
        await page.screenshot(path=admin_path)
        print(f"-> 已捕获管理员同步控制台截图: {admin_path}")

        # Step 5: Test Login Page in Light & Dark Mode
        print("[5/5] 测试登录认证中心与全站主题自适应...")
        await page.goto("http://127.0.0.1:8000/#/login", wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(1000)

        login_light_path = os.path.join(ARTIFACTS_DIR, "step12_login_page_adaptive_light.png")
        await page.screenshot(path=login_light_path)
        print(f"-> 已捕获白天模式登录中心截图: {login_light_path}")

        # Switch to dark on login page
        await page.locator("#btn-login-theme-dark").click()
        await page.wait_for_timeout(800)
        theme_val = await page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        assert theme_val == "dark", "登录页夜间模式切换失败！"

        login_dark_path = os.path.join(ARTIFACTS_DIR, "step12_login_page_adaptive_dark.png")
        await page.screenshot(path=login_dark_path)
        print(f"-> 已捕获暗黑模式登录中心截图: {login_dark_path}")

        await browser.close()
        print("=== Step 12 全流程测试 100% 通过！ ===")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
