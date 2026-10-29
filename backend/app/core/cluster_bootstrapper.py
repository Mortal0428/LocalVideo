# -*- coding: utf-8 -*-
"""
==============================================================================
【核心模块】：backend/app/core/cluster_bootstrapper.py
【业务定位】：全栈依赖服务集群智能探测与一键联调引导器
【核心功能】：
  在本地或 PyCharm 中运行 backend/main.py 启动后端时：
  1. 端口智能探测（check_port_listening）：快速探测 Redis (6379)、Neo4j (7687)、
     OpenList (5244) 以及 Vite 前端服务 (5173) 是否已在线；
  2. 独立控制台拉起（launch_in_new_console）：对于尚未运行的依赖服务，自动在
     Windows 环境下调用 CREATE_NEW_CONSOLE 弹出独立的控制台窗口拉起该服务并打印实时日志；
  3. 服务就绪看板打印：向开发者终端打印全栈微服务清单与直达访问链接，实现开箱即用。
==============================================================================
"""
import os
import sys
import time
import socket
import logging
import subprocess
from typing import Dict, Any, List

logger = logging.getLogger("cluster_bootstrapper")

# 全栈依赖服务注册配置表
DEPENDENCY_SERVICES: List[Dict[str, Any]] = [
    {
        "name": "Redis 内存高速缓存",
        "port": 6379,
        "title": "CinemaAgent-Redis [Port 6379]",
        "cwd": r"E:\tools\redis",
        "command": r"redis-server.exe redis.windows.conf",
        "description": "提供双驱会话与缓存加速 (密码: 12345678)",
    },
    {
        "name": "Neo4j 知识图谱数据库",
        "port": 7687,
        "title": "CinemaAgent-Neo4j [Port 7687/7474]",
        "cwd": r"E:\neo4j-community-2026.02.2-windows\neo4j-community-2026.02.2\bin",
        "command": r"neo4j.bat console",
        "description": "提供 Graph RAG 实体三元组图谱检索 (bolt://localhost:7687)",
    },
    {
        "name": "OpenList 云盘网关",
        "port": 5244,
        "title": "CinemaAgent-OpenList [Port 5244]",
        "cwd": r"E:\个人项目作品\Agent项目",
        "command": r"openlist.exe server",
        "description": "提供夸克/联通云盘短剧资产本地秒级直链",
    },
    {
        "name": "Vite 前端界面",
        "port": 5173,
        "title": "CinemaAgent-Frontend [Port 5173]",
        "cwd": os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../frontend")),
        "command": r"cmd.exe /c npm run dev",
        "description": "Vue3 前台影视大厅与后台智能体中台",
    },
]

def check_port_listening(port: int, host: str = "127.0.0.1") -> bool:
    """
    【大白话功能】：通过轻量 TCP Socket 连接测试某个本地端口是否正在监听。
    超时设为 0.3 秒，探测极速，绝不拖慢系统启动速度。
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def launch_in_new_console(title: str, cwd: str, command: str) -> bool:
    """
    【大白话功能】：在 Windows 环境下新开一个独立黑框控制台运行指定的外部命令。
    保证日志互不干扰，即使某一个子服务崩溃也不会影响主服务运行。
    """
    if not os.path.exists(cwd):
        logger.warning(f"[ClusterBootstrapper] 目标工作目录不存在: {cwd}")
        return False

    try:
        full_cmd = f'cmd.exe /k "title {title} && echo [{title} 运行中，实时日志打印中...] && {command}"'
        # Windows CREATE_NEW_CONSOLE 标志位 (0x00000010)
        creation_flags = 0x00000010
        subprocess.Popen(
            full_cmd,
            cwd=cwd,
            shell=False,
            creationflags=creation_flags,
        )
        return True
    except Exception as e:
        logger.error(f"[ClusterBootstrapper] 拉起独立窗口异常 ({title}): {e}")
        return False

def launch_cluster_dependencies():
    """
    【大白话功能】：全栈集群依赖总控引导入口。
    开机自检 4 大核心依赖，未启动的自动弹出窗口拉起，并打印全局服务拓扑地图。
    """
    # 支持通过环境变量跳过外部拉起
    if os.getenv("CINEMA_AUTO_BOOTSTRAP", "1").lower() in ("0", "false", "no"):
        print("[ClusterBootstrapper] CINEMA_AUTO_BOOTSTRAP=0, 跳过外部拉起")
        return

    print("\n" + "=" * 80)
    print("      CinemaAgent 影视平台全栈服务集群启动引导 (PyCharm 直跑模式)")
    print("=" * 80)

    any_launched = False
    for idx, svc in enumerate(DEPENDENCY_SERVICES, 1):
        name = svc["name"]
        port = svc["port"]
        title = svc["title"]
        cwd = svc["cwd"]
        command = svc["command"]

        if check_port_listening(port):
            print(f" [{idx}/4] {name} (Port {port:<4}) ... [已在线 (就绪)]")
        else:
            print(f" [{idx}/4] {name} (Port {port:<4}) ... [未运行 -> 正在新窗口拉起...]")
            ok = launch_in_new_console(title, cwd, command)
            if ok:
                any_launched = True
            else:
                print(f"       提示: 拉起 {name} 失败，检查目录: {cwd}")

    # 若拉起了新服务，留出 2 秒让子进程初始化端口监听
    if any_launched:
        print("\n 正在等待后台服务完成初始化 (约 2~3 秒)...")
        time.sleep(2.5)

    print("-" * 80)
    print("                    全局服务清单与直达链接")
    print("-" * 80)
    print("   - 用户影视大厅:       http://localhost:5173")
    print("   - 智能体管理中台:     http://localhost:5173/#/admin")
    print("   - 后端 Swagger API:   http://127.0.0.1:8000/docs")
    print("   - OpenList 网盘后台:  http://127.0.0.1:5244")
    print("   - Neo4j 图数据库后台: http://127.0.0.1:7474 (bolt://localhost:7687)")
    print("   - Redis 高速缓存端口: 127.0.0.1:6379 (密码: 12345678)")
    print("=" * 80)
    print(" 各服务的独立 Windows 控制台已在任务栏展开，可随时查看实时运行日志。\n")
