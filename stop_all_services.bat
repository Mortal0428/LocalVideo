@echo off
chcp 65001 >nul
title CinemaAgent 全栈微服务一键停止
color 0C

echo ==============================================================================
echo [CinemaAgent] 正在安全停止前后端与相关后台进程...
echo ==============================================================================

powershell -Command "$ports = @(8000, 5173); foreach ($p in $ports) { $conns = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue; if ($conns) { foreach ($c in $conns) { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host ('Stopped process on port ' + $p) } } }"

echo ==============================================================================
echo [SUCCESS] 端口 8000 与 5173 已全部安全释放。
echo ==============================================================================
pause
