# -*- coding: utf-8 -*-
"""
CinemaAgent - OpenList 网盘网关服务独立启动器
彻底杜绝 Windows 批处理 (.bat) 中文路径乱码问题，开箱即用启动 OpenList 网盘服务并自动打开浏览器后台。
"""
import os
import sys
import time
import socket
import webbrowser
import subprocess

OPENLIST_DIR = r"E:\浏览器下载内容"
EXE_PATH = os.path.join(OPENLIST_DIR, "openlist.exe")

def is_port_in_use(port: int = 5244) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0

def main():
    print("=" * 60)
    print("      正在启动 OpenList 网盘网关服务 (CinemaAgent 存储底座)...")
    print("      后台访问地址: http://127.0.0.1:5244")
    print("=" * 60)

    if not os.path.exists(EXE_PATH):
        print(f"[错误] 未找到 OpenList 主程序: {EXE_PATH}")
        print("请检查该路径是否存在 openlist.exe。")
        input("\n按回车键退出...")
        return

    # 检查 5244 端口是否已经处于运行状态
    if is_port_in_use(5244):
        print("[提示] 检测到 OpenList 服务已经在运行中 (端口 5244 处于监听状态)！")
        print("正在为您打开浏览器后台: http://127.0.0.1:5244")
        webbrowser.open("http://127.0.0.1:5244")
        input("\n按回车键保持窗口...")
        return

    # 自动弹出浏览器后台
    print("正在唤起浏览器后台页面...")
    webbrowser.open("http://127.0.0.1:5244")

    # 启动 openlist.exe server 并保持运行
    print(f"正在以工作目录 [{OPENLIST_DIR}] 启动 openlist.exe server ...")
    try:
        subprocess.run([EXE_PATH, "server"], cwd=OPENLIST_DIR)
    except KeyboardInterrupt:
        print("\nOpenList 服务已手动停止。")
    except Exception as e:
        print(f"\n[异常] OpenList 启动失败: {e}")
        input("\n按回车键退出...")

if __name__ == "__main__":
    main()
