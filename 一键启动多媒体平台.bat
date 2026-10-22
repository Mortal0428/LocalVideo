@echo off
chcp 65001 >nul
title CinemaAgent 多媒体视听与短剧平台服务

echo ======================================================================
echo          🎬 CinemaAgent 多媒体视听与短剧 Agent 平台 - 一键启动
echo ======================================================================
echo.
echo [1/3] 正在检测基础运行环境...
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未在系统 PATH 中找到 Python，请确认 Python 环境已正确安装！
    pause
    exit /b
)

echo [2/3] 检查中国联通云盘 OpenList 网关 (端口 5244)...
netstat -ano | findstr "5244" >nul
if %errorlevel% neq 0 (
    echo [提示] 检测到 OpenList 网关尚未启动。
    echo       正在自动启动 OpenList 沃盘中继服务...
    start "" "启动云盘OpenList.bat"
    timeout /t 3 /nobreak >nul
) else (
    echo [OK] 中国联通云盘网关 (OpenList:5244) 运行中！
)

echo [3/3] 启动 CinemaAgent 业务主服务 (FastAPI + Vue3 9:16影院播放器)...
echo.
echo ----------------------------------------------------------------------
echo  🚀 服务正在运行中！请在浏览器中访问：
echo  👉 http://127.0.0.1:8000/
echo ----------------------------------------------------------------------
echo.

start "" "http://127.0.0.1:8000/"

cd backend
python main.py

pause
