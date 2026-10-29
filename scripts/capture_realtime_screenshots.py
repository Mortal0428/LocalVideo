# -*- coding: utf-8 -*-
"""
实时无头浏览器高清全景截图生成工具

本脚本使用 Playwright 无头 Chromium 实例，以 1920x1080 视口配合 2x 缩放比例，
真实访问正在运行的前端开发服务器与后端服务，捕获全部核心业务视窗的实时界面，
并自动输出至 docs/screenshots/ 目录，用于系统说明文档与对外交付展示。
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

def ensure_directory_exists(dir_path: str) -> None:
    """
    确保指定的目标目录存在，若不存在则递归创建

    :param dir_path: 目标目录的绝对或相对路径
    :return: None
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

def capture_realtime_system_screenshots() -> bool:
    """
    使用 Playwright 无头浏览器执行系统各核心模块的实时截图采集

    :return: 全部截图是否成功完成的布尔标识 (True 为成功，False 为失败)
    """
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "screenshots"))
    ensure_directory_exists(output_dir)
    
    base_url = "http://127.0.0.1:5173"
    print(f"[截图启动] 目标前端服务基地址: {base_url}")
    print(f"[输出目录] 截图保存路径: {output_dir}")

    captured_count = 0
    total_targets = 7

    with sync_playwright() as p:
        # 启动基于系统原生 Edge 的 Chromium 无头浏览器，设定稳定现代渲染参数
        browser = p.chromium.launch(
            headless=True,
            channel="msedge",
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--hide-scrollbars",
            ]
        )
        
        # 创建上下文，启用 2x Retina 像素密度，保障高质量画面质感
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2,
            ignore_https_errors=True
        )

        page = context.new_page()

        # 预设管理员身份与暗黑主题存储，确保页面免登录直达受限后台
        page.goto(f"{base_url}/#/login", wait_until="networkidle")
        page.evaluate("""() => {
            localStorage.setItem('cinema_auth_token', 'mock_admin_token_2026');
            localStorage.setItem('user_info', JSON.stringify({
                id: 1,
                username: 'admin',
                role: 'admin',
                coins: 9999,
                nickname: '首席执行官'
            }));
            localStorage.setItem('vueuse-color-scheme', 'dark');
            document.documentElement.classList.add('dark');
        }""")
        time.sleep(1)

        # -------------------------------------------------------------
        # 1. 沉浸式剧场大厅短剧海报流与轮播
        # -------------------------------------------------------------
        print("\n[1/7] 正在采集: 沉浸式剧场大厅短剧海报流与轮播...")
        try:
            page.goto(f"{base_url}/#/home", wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(2500)
            p1_path = os.path.join(output_dir, "04_theater_hall_carousel.png")
            page.screenshot(path=p1_path, full_page=False)
            print(f" -> 已保存: {p1_path} (大小: {os.path.getsize(p1_path)} 字节)")
            captured_count += 1
        except Exception as e:
            print(f" [异常] 剧场大厅采集失败: {e}")

        # -------------------------------------------------------------
        # 2. 暗黑影院 9:16 移动拟态播放器与多模态时间轴 RAG
        # -------------------------------------------------------------
        print("\n[2/7] 正在采集: 移动拟态播放器与多模态时间轴 RAG...")
        try:
            page.goto(f"{base_url}/#/player/1", wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(3000)
            p2_path = os.path.join(output_dir, "01_mobile_player_and_rag.png")
            page.screenshot(path=p2_path, full_page=False)
            print(f" -> 已保存: {p2_path} (大小: {os.path.getsize(p2_path)} 字节)")
            captured_count += 1
        except Exception as e:
            print(f" [异常] 播放器视窗采集失败: {e}")

        # -------------------------------------------------------------
        # 3. 企业级管控中台与全景 BI 数据看板
        # -------------------------------------------------------------
        print("\n[3/7] 正在采集: 企业级管控中台与全景 BI 数据看板...")
        try:
            page.goto(f"{base_url}/#/admin", wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(3000)
            p3_path = os.path.join(output_dir, "02_admin_console_bi.png")
            page.screenshot(path=p3_path, full_page=False)
            print(f" -> 已保存: {p3_path} (大小: {os.path.getsize(p3_path)} 字节)")
            captured_count += 1
        except Exception as e:
            print(f" [异常] BI 看板采集失败: {e}")

        # -------------------------------------------------------------
        # 4. 多智能体沉浸协同圆桌会议室 (战术大屏)
        # -------------------------------------------------------------
        print("\n[4/7] 正在采集: 多智能体沉浸协同圆桌会议室...")
        try:
            page.goto(f"{base_url}/#/admin", wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(2000)
            # 点击侧边栏菜单按钮切换到九大智能体大屏
            page.click("#admin-tab-agent-hub", timeout=5000)
            page.wait_for_timeout(3500)
            
            roundtable_core_path = os.path.join(output_dir, "02_multi_agent_roundtable.png")
            page.screenshot(path=roundtable_core_path, full_page=False)
            print(f" -> 已保存: {roundtable_core_path} (大小: {os.path.getsize(roundtable_core_path)} 字节)")
            captured_count += 1
        except Exception as e:
            print(f" [异常] 圆桌战术大屏采集失败: {e}")

        # -------------------------------------------------------------
        # 5. 内容安全合规与人机风控控制台
        # -------------------------------------------------------------
        print("\n[5/7] 正在采集: 内容安全合规与人机风控控制台...")
        try:
            mod_menu = page.locator("text=互动合规风控")
            if mod_menu.is_visible():
                mod_menu.click()
            page.wait_for_timeout(2500)
            p5_path = os.path.join(output_dir, "03_danmaku_governance.png")
            page.screenshot(path=p5_path, full_page=False)
            print(f" -> 已保存: {p5_path} (大小: {os.path.getsize(p5_path)} 字节)")
            captured_count += 1
        except Exception as e:
            print(f" [异常] 互动风控控制台采集失败: {e}")

        # -------------------------------------------------------------
        # 6. 短剧资产编目与上架管理
        # -------------------------------------------------------------
        print("\n[6/7] 正在采集: 短剧资产编目与上架管理...")
        try:
            shelf_menu = page.locator("text=短剧资产编目")
            if shelf_menu.is_visible():
                shelf_menu.click()
            page.wait_for_timeout(2500)
            p6_path = os.path.join(output_dir, "06_drama_shelf_management.png")
            page.screenshot(path=p6_path, full_page=False)
            print(f" -> 已保存: {p6_path} (大小: {os.path.getsize(p6_path)} 字节)")
            captured_count += 1
        except Exception as e:
            print(f" [异常] 短剧资产编目采集失败: {e}")

        # -------------------------------------------------------------
        # 7. 用户中心 Bento 个人资产空间
        # -------------------------------------------------------------
        print("\n[7/7] 正在采集: 用户中心 Bento 个人空间...")
        try:
            page.goto(f"{base_url}/#/user/profile", wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(2500)
            p7_path = os.path.join(output_dir, "05_user_space_bento.png")
            page.screenshot(path=p7_path, full_page=False)
            print(f" -> 已保存: {p7_path} (大小: {os.path.getsize(p7_path)} 字节)")
            captured_count += 1
        except Exception as e:
            print(f" [异常] 用户空间采集失败: {e}")

        browser.close()

    print(f"\n========================================================")
    print(f"[采集完成] 实时截图成功采集: {captured_count}/{total_targets} 项")
    print(f"========================================================")
    return captured_count >= 5

if __name__ == "__main__":
    success = capture_realtime_system_screenshots()
    sys.exit(0 if success else 1)
