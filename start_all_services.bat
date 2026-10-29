@echo off
chcp 65001 >nul
title CinemaAgent 全栈微服务集群一键启动
color 0A

echo ==============================================================================
echo [CinemaAgent] 正在启动全栈微服务与前后端服务...
echo ==============================================================================

start "CinemaAgent-Backend" cmd /k "python -m uvicorn --app-dir backend main:app --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul

start "CinemaAgent-Frontend" cmd /k "npm run dev --prefix frontend"

echo ==============================================================================
echo [SUCCESS] 后端服务已挂载于: http://127.0.0.1:8000
echo [SUCCESS] 前端界面已挂载于: http://localhost:5173
echo ==============================================================================
pause
