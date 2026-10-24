@echo off
chcp 65001 >nul
title CinemaAgent 全套服务一键停止中枢
color 0C

echo ===============================================================================
echo                CinemaAgent 影视平台全套服务安全下线总控
echo ===============================================================================
echo 正在安全停止 5 大服务进程，释放占用端口...
echo.

:: 1. 停止 Redis
echo [1/5] 停止 Redis 服务...
taskkill /f /im redis-server.exe >nul 2>&1
echo   [已关闭] Redis 服务进程已终止。

:: 2. 停止 OpenList
echo [2/5] 停止 OpenList 云盘服务...
taskkill /f /im openlist.exe >nul 2>&1
echo   [已关闭] OpenList 服务进程已终止。

:: 3. 停止 Neo4j
echo [3/5] 停止 Neo4j 知识图谱...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":7687 " ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":7474 " ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo   [已关闭] Neo4j 图数据库已下线。

:: 4. 停止 FastAPI 后端 (8000 端口)
echo [4/5] 停止 FastAPI 后端中枢 (Port 8000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo   [已关闭] 后端端口已释放。

:: 5. 停止 Vite 前端 (5173 端口)
echo [5/5] 停止 Vite 前端服务 (Port 5173)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo   [已关闭] 前端端口已释放。

echo.
echo ===============================================================================
echo                 全部 5 大微服务已成功停止，端口资源已彻底释放！
echo ===============================================================================
echo.
pause
