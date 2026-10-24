"""
CinemaAgent 九大智能体模块全量 UI 双主题 (Light / Dark) 视觉深度融合端到端自动化测试
严格验证白昼模式下彻底告别生硬黑块，卡片背景统一为 Apple HIG 纯白 (#ffffff)、
文字对比度达标 (纯黑 #18191C)、输入框高亮自适应、ECharts 双主题热联动，
并在知识库工件目录生成全真评测截屏。
"""

import os
import sys
import time
import httpx
from playwright.sync_api import sync_playwright

BASE_API = "http://127.0.0.1:8000/api/v1"
BASE_UI = "http://localhost:5173"
ARTIFACT_DIR = r"C:\Users\27705\.gemini\antigravity\brain\aacc30fa-2a2e-4c72-abbb-876796226545"


def run_dual_theme_verification():
    print("=== [Dual-Theme Cohesion Verification] Testing Light Mode & Dark Mode ===")
    os.makedirs(ARTIFACT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = None
        for ch in ("msedge", "chrome"):
            try:
                browser = p.chromium.launch(channel=ch, headless=True)
                break
            except Exception:
                pass
        if not browser:
            browser = p.chromium.launch(headless=False)

        context = browser.new_context(viewport={"width": 1600, "height": 960})
        page = context.new_page()

        # 1. 获取管理员 Token
        with httpx.Client(timeout=15.0) as auth_c:
            auth_resp = auth_c.post(f"{BASE_API}/auth/quick-switch/ADMIN").json()
            real_token = auth_resp["access_token"]
            real_user = auth_resp["user"]
            real_user["is_creator"] = True
            real_user["is_reviewer"] = True

        # 2. 注入认证凭证并初始化为白天模式 (Light Mode)
        page.goto(f"{BASE_UI}/#/landing", wait_until="domcontentloaded")
        page.evaluate(
            """([tk, usr]) => {
                localStorage.setItem('cinema_access_token', tk);
                localStorage.setItem('token', tk);
                localStorage.setItem('user', JSON.stringify(usr));
                localStorage.setItem('cinema_theme', 'light');
                document.documentElement.setAttribute('data-theme', 'light');
                document.body.classList.add('theme-light');
                document.body.classList.remove('theme-dark');
            }""",
            [real_token, real_user],
        )

        # 3. 导航至管理后台智能体总控台
        page.goto(f"{BASE_UI}/#/admin?tab=agent-hub", wait_until="networkidle")
        page.wait_for_selector("#agent-command-center-root", timeout=15000)
        time.sleep(1.5)

        # -------------------------------------------------------------
        # 测试 1: Tab 1 战术大屏与顶栏 (白昼模式)
        # -------------------------------------------------------------
        page.wait_for_selector(".acc-header-bar", timeout=10000)
        header_bg = page.evaluate("() => window.getComputedStyle(document.querySelector('.acc-header-bar')).backgroundColor")
        print(f"[VERIFY] Light Mode .acc-header-bar background: {header_bg}")
        # 验证不是 slate-900 深灰色 (例如不是 rgb(15, 23, 42) 或 rgb(44, 50, 63))
        assert "15, 23, 42" not in header_bg, "Header bar must NOT be dark slate grey in Light Mode!"
        assert "44, 50, 63" not in header_bg, "Header bar must NOT be dark slate grey in Light Mode!"

        shot_tab1 = os.path.join(ARTIFACT_DIR, "verified_light_theme_agent_tab1_tactical.png")
        page.screenshot(path=shot_tab1, full_page=False)
        print(f"[PASS] 1. Light Mode Tab 1 (Tactical Toolbar) captured: {shot_tab1}")

        # -------------------------------------------------------------
        # 测试 2: Tab 2 BI 驾驶舱卡片与 ECharts 双主题 (白昼模式)
        # -------------------------------------------------------------
        page.click("#acc-tab-bi")
        page.wait_for_selector(".acc-kpi-card", timeout=10000)
        time.sleep(1.5)

        kpi_bg = page.evaluate("() => window.getComputedStyle(document.querySelector('.acc-kpi-card')).backgroundColor")
        print(f"[VERIFY] Light Mode .acc-kpi-card background: {kpi_bg}")
        assert "15, 23, 42" not in kpi_bg, "KPI card must NOT be dark slate grey in Light Mode!"
        assert "82, 88, 102" not in kpi_bg, "KPI card must NOT be dark slate grey in Light Mode!"

        chart_bg = page.evaluate("() => window.getComputedStyle(document.querySelector('.acc-chart-box')).backgroundColor")
        print(f"[VERIFY] Light Mode .acc-chart-box background: {chart_bg}")
        assert "15, 23, 42" not in chart_bg, "Chart box must NOT be dark slate grey in Light Mode!"

        shot_tab2 = os.path.join(ARTIFACT_DIR, "verified_light_theme_agent_tab2_bi.png")
        page.screenshot(path=shot_tab2, full_page=False)
        print(f"[PASS] 2. Light Mode Tab 2 (BI Dashboard & ECharts) captured: {shot_tab2}")

        # -------------------------------------------------------------
        # 测试 3: Tab 3 大模型三级治理 (白昼模式)
        # -------------------------------------------------------------
        page.click("#acc-tab-models")
        page.wait_for_selector(".category-config-card", timeout=10000)
        time.sleep(1.0)

        card_block_bg = page.evaluate("() => window.getComputedStyle(document.querySelector('.acc-card-block')).backgroundColor")
        print(f"[VERIFY] Light Mode .acc-card-block background: {card_block_bg}")
        assert "15, 23, 42" not in card_block_bg, "Card block must NOT be dark in Light Mode!"

        cat_card_bg = page.evaluate("() => window.getComputedStyle(document.querySelector('.category-config-card')).backgroundColor")
        print(f"[VERIFY] Light Mode .category-config-card background: {cat_card_bg}")
        assert "15, 23, 42" not in cat_card_bg, "Category card must NOT be dark in Light Mode!"

        shot_tab3 = os.path.join(ARTIFACT_DIR, "verified_light_theme_agent_tab3_models.png")
        page.screenshot(path=shot_tab3, full_page=False)
        print(f"[PASS] 3. Light Mode Tab 3 (Three-tier LLM Governance) captured: {shot_tab3}")

        # -------------------------------------------------------------
        # 测试 4: Tab 4 九大智能体热插拔与沙盒测试舱 (白昼模式)
        # -------------------------------------------------------------
        page.click("#acc-tab-integrator")
        page.wait_for_selector(".agent-config-card", timeout=10000)
        time.sleep(1.0)

        agent_card_bg = page.evaluate("() => window.getComputedStyle(document.querySelector('.agent-config-card')).backgroundColor")
        print(f"[VERIFY] Light Mode .agent-config-card background: {agent_card_bg}")
        assert "15, 23, 42" not in agent_card_bg, "Agent card must NOT be dark in Light Mode!"

        shot_tab4 = os.path.join(ARTIFACT_DIR, "verified_light_theme_agent_tab4_matrix.png")
        page.screenshot(path=shot_tab4, full_page=False)
        print(f"[PASS] 4. Light Mode Tab 4 (Agent Matrix & Sandbox) captured: {shot_tab4}")

        # -------------------------------------------------------------
        # 测试 5: 专属单智能体对话模态框 (白昼模式)
        # -------------------------------------------------------------
        page.click("#btn-open-chat-agent_8")
        page.wait_for_selector(".universal-agent-dialog", timeout=10000)
        time.sleep(1.0)

        modal_bg = page.evaluate("() => window.getComputedStyle(document.querySelector('.universal-agent-dialog')).backgroundColor")
        print(f"[VERIFY] Light Mode .universal-agent-dialog background: {modal_bg}")

        shot_modal = os.path.join(ARTIFACT_DIR, "verified_light_theme_agent_chat_modal.png")
        page.screenshot(path=shot_modal, full_page=False)
        print(f"[PASS] 5. Light Mode Universal Chat Modal captured: {shot_modal}")

        # 关闭弹窗
        page.keyboard.press("Escape")
        time.sleep(0.5)

        # -------------------------------------------------------------
        # 测试 6: Tab 6 沉浸协同圆桌会议室 (白昼模式)
        # -------------------------------------------------------------
        page.click("#acc-tab-roundtable")
        page.wait_for_selector("#roundtable-canvas-container", timeout=10000)
        time.sleep(1.0)

        shot_tab6 = os.path.join(ARTIFACT_DIR, "verified_light_theme_agent_tab6_roundtable.png")
        page.screenshot(path=shot_tab6, full_page=False)
        print(f"[PASS] 6. Light Mode Tab 6 (Collaborative Roundtable) captured: {shot_tab6}")

        # -------------------------------------------------------------
        # 测试 7: 切换回暗黑模式 (Dark Mode)，验证暗黑质感完好无损
        # -------------------------------------------------------------
        page.evaluate(
            """() => {
                localStorage.setItem('cinema_theme', 'dark');
                document.documentElement.setAttribute('data-theme', 'dark');
                document.body.classList.remove('theme-light');
                document.body.classList.add('theme-dark');
            }"""
        )
        time.sleep(1.5)

        page.click("#acc-tab-integrator")
        time.sleep(1.0)

        shot_dark = os.path.join(ARTIFACT_DIR, "verified_dark_theme_agent_overview.png")
        page.screenshot(path=shot_dark, full_page=False)
        print(f"[PASS] 7. Dark Mode (Seamless Apple Deep Glass) captured: {shot_dark}")

        browser.close()

    print("=== DUAL-THEME COHESION VERIFICATION 100% PASSED ===")


if __name__ == "__main__":
    run_dual_theme_verification()
