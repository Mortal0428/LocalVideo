@echo off
chcp 65001 >nul
title CinemaAgent 全套微服务一键集群总控台
color 0A

echo ===============================================================================
echo                CinemaAgent 影视平台全套服务一键集群启动总控
echo ===============================================================================
echo   正在并行调度启动 5 大核心服务组件，各服务将在独立命令行窗口中输出实时日志：
echo   1. Redis 5.0 高速内存缓存中枢 (Port 6379)
echo   2. Neo4j 2026 知识图谱图数据库引擎 (Port 7474 / 7687)
echo   3. OpenList 夸克/网盘挂载网关服务 (Port 5244)
echo   4. FastAPI 后端分布式 API 调度中枢 (Port 8000)
echo   5. Vite 前端交互大屏与管理控制中台 (Port 5173)
echo ===============================================================================
echo.

set PROJECT_ROOT=%~dp0
if "%PROJECT_ROOT:~-1%"=="\" set PROJECT_ROOT=%PROJECT_ROOT:~0,-1%

:: 1. 检查并启动 Redis
echo [1/5] 检查 Redis 状态...
netstat -ano | findstr ":6379 " | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo   [OK] Redis 已在运行中 (Port 6379)
) else (
    echo   [启动中] 正在拉起 Redis 服务...
    start "CinemaAgent-Redis [Port 6379]" cmd /k "cd /d E:\tools\redis && echo [Redis 正在运行...] && redis-server.exe redis.windows.conf"
)

:: 2. 检查并启动 Neo4j
echo [2/5] 检查 Neo4j 状态...
netstat -ano | findstr ":7687 " | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo   [OK] Neo4j 已在运行中 (Port 7687 / 7474)
) else (
    echo   [启动中] 正在拉起 Neo4j 知识图谱数据库...
    start "CinemaAgent-Neo4j [Port 7687]" cmd /k "cd /d E:\neo4j-community-2026.02.2-windows\neo4j-community-2026.02.2\bin && echo [Neo4j 正在启动，首次加载需 5~10 秒...] && neo4j.bat console"
)

:: 3. 检查并启动 OpenList
echo [3/5] 检查 OpenList 状态...
netstat -ano | findstr ":5244 " | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo   [OK] OpenList 已在运行中 (Port 5244)
) else (
    echo   [启动中] 正在拉起 OpenList 网盘挂载网关...
    start "CinemaAgent-OpenList [Port 5244]" cmd /k "cd /d E:\浏览器下载内容 && echo [OpenList 云盘服务正在运行...] && openlist.exe server"
)

:: 4. 检查并启动 FastAPI 后端
echo [4/5] 检查 FastAPI 后端状态...
netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo   [OK] FastAPI 后端已在运行中 (Port 8000)
) else (
    echo   [启动中] 正在拉起 FastAPI 后端中枢...
    start "CinemaAgent-Backend [Port 8000]" cmd /k "cd /d %PROJECT_ROOT% && echo [FastAPI 后端核心启动中...] && E:\python\python.exe backend/main.py"
)

:: 5. 检查并启动 Vite 前端
echo [5/5] 检查 Vite 前端状态...
netstat -ano | findstr ":5173 " | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo   [OK] Vite 前端已在运行中 (Port 5173)
) else (
    echo   [启动中] 正在拉起 Vite 前端开发大屏...
    start "CinemaAgent-Frontend [Port 5173]" cmd /k "cd /d %PROJECT_ROOT%\frontend && echo [Vite 前端编译运行中...] && npm run dev"
)

echo.
echo ===============================================================================
echo 正在等待所有服务端口就绪与健康探活 (约需 3~5 秒)...
echo ===============================================================================
timeout /t 4 /nobreak >nul

echo.
echo ===============================================================================
echo                       服务就绪清单与访问看板
echo ===============================================================================
echo   - 影视平台用户大厅:   http://localhost:5173
echo   - 九大智能体总控中台: http://localhost:5173/#/admin
echo   - FastAPI Swagger 文档: http://127.0.0.1:8000/docs
echo   - OpenList 云盘控制台: http://127.0.0.1:5244
echo   - Neo4j 图数据库浏览器: http://127.0.0.1:7474 (bolt://localhost:7687)
echo   - Redis 缓存连接端口: 127.0.0.1:6379 (密码: 12345678)
echo ===============================================================================
echo 提示：各服务控制台已在独立窗口弹出并保持实时日志输出。如需关闭全部服务，请运行【一键停止全套服务.bat】。
echo.
pause
