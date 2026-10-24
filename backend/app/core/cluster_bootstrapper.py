# -*- coding: utf-8 -*-
"""
CinemaAgent 集群全套依赖服务自启引导中枢 (PyCharm / CLI 一键启动引导器)
当开发者在 PyCharm 中点击绿色运行小三角（运行 backend/main.py）时，
本模块会自动并行探活并按需拉起 Redis、Neo4j、OpenList 与 Vite 前端服务。
每个服务在独立的控制台窗口中输出实时日志，并具备防端口冲突的智能探活机制。
"""

import os
import sys
import time
import socket
import logging
import subprocess
from typing import Dict, Any, List

logger = logging.getLogger("cluster_bootstrapper")

# 核心依赖服务的拓扑与物理路径配置
DEPENDENCY_SERVICES: List[Dict[str, Any]] = [
    {
        "name": "Redis 内存高速缓存",
        "port": 6379,
        "title": "CinemaAgent-Redis [Port 6379]",
        "cwd": r"E:\tools\redis",
        "command": r"redis-server.exe redis.windows.conf",
        "description": "提供双驱会话隔离缓存与高频只读加速 (密码: 12345678)",
    },
    {
        "name": "Neo4j 知识图谱数据库",
        "port": 7687,
        "title": "CinemaAgent-Neo4j [Port 7687/7474]",
        "cwd": r"E:\neo4j-community-2026.02.2-windows\neo4j-community-2026.02.2\bin",
        "command": r"neo4j.bat console",
        "description": "提供 Graph RAG 实体三元组与剧情图谱检索 (bolt://localhost:7687)",
    },
    {
        "name": "OpenList 云盘挂载网关",
        "port": 5244,
        "title": "CinemaAgent-OpenList [Port 5244]",
        "cwd": r"E:\浏览器下载内容",
        "command": r"openlist.exe server",
        "description": "提供夸克/阿里云盘影视资产秒级挂载与高速直链解析",
    },
    {
        "name": "Vite 前端交互大屏",
        "port": 5173,
        "title": "CinemaAgent-Frontend [Port 5173]",
        "cwd": os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../frontend")),
        "command": r"cmd.exe /c npm run dev",
        "description": "Vue3 前台影视大厅、个人空间与后台九大智能体总控中心",
    },
]


def check_port_listening(port: int, host: str = "127.0.0.1") -> bool:
    """快速 TCP 端口探活检查，超时 0.3 秒"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def launch_in_new_console(title: str, cwd: str, command: str) -> bool:
    """在 Windows 上利用 CREATE_NEW_CONSOLE 拉起独立带标题的命令行窗口，输出各自日志"""
    if not os.path.exists(cwd):
        logger.warning(f"[ClusterBootstrapper] 目标工作目录不存在: {cwd}")
        return False

    try:
        # 组装 Windows cmd 命令并设置独立窗口标题
        full_cmd = f'cmd.exe /k "title {title} && echo [{title} 正在运行，实时日志输出中...] && {command}"'
        
        # Windows CREATE_NEW_CONSOLE 标志 (0x00000010)
        creation_flags = 0x00000010
        subprocess.Popen(
            full_cmd,
            cwd=cwd,
            shell=False,
            creationflags=creation_flags,
        )
        return True
    except Exception as e:
        logger.error(f"[ClusterBootstrapper] 拉起服务窗口异常 ({title}): {e}")
        return False


def launch_cluster_dependencies():
    """
    集群自启总控入口：
    探测并按需拉起 4 大外部依赖服务，在控制台打印美化的就绪访问看板。
    """
    # 允许通过环境变量关闭自启
    if os.getenv("CINEMA_AUTO_BOOTSTRAP", "1").lower() in ("0", "false", "no"):
        print("[ClusterBootstrapper] CINEMA_AUTO_BOOTSTRAP=0, 跳过外部依赖服务自启。")
        return

    print("\n" + "=" * 80)
    print("      CinemaAgent 影视平台全套服务集群自启中枢 (PyCharm 运行三角直启模式)")
    print("=" * 80)

    any_launched = False
    for idx, svc in enumerate(DEPENDENCY_SERVICES, 1):
        name = svc["name"]
        port = svc["port"]
        title = svc["title"]
        cwd = svc["cwd"]
        command = svc["command"]

        if check_port_listening(port):
            print(f" [{idx}/4] {name} (Port {port:<4}) ... [已在运行中 (就绪)]")
        else:
            print(f" [{idx}/4] {name} (Port {port:<4}) ... [未运行 -> 正在新独立窗口拉起...]")
            ok = launch_in_new_console(title, cwd, command)
            if ok:
                any_launched = True
            else:
                print(f"       警告: 启动 {name} 失败，请检查路径: {cwd}")

    # 若新拉起了服务，稍作缓冲以便端口开始监听
    if any_launched:
        print("\n 正在等待新唤起的服务完成初始化握手 (约需 2~3 秒)...")
        time.sleep(2.5)

    print("-" * 80)
    print("                    全套微服务就绪清单与访问看板")
    print("-" * 80)
    print("   - 用户影视大厅:       http://localhost:5173")
    print("   - 九大智能体总控中台: http://localhost:5173/#/admin")
    print("   - 后端 Swagger API:   http://127.0.0.1:8000/docs")
    print("   - OpenList 云盘控制台: http://127.0.0.1:5244")
    print("   - Neo4j 图数据库平台: http://127.0.0.1:7474 (bolt://localhost:7687)")
    print("   - Redis 高速缓存端口: 127.0.0.1:6379 (密码: 12345678)")
    print("=" * 80)
    print(" 各服务已在独立的 Windows 控制台窗口中实时滚动输出日志，可自由查看。\n")
