@echo off
chcp 65001 >nul
title OpenList 云盘挂载服务
where python >nul 2>nul
if %errorlevel% equ 0 (
    python "%~dp0start_openlist.py"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$dir='E:\浏览器下载内容'; $exe=Join-Path $dir 'openlist.exe'; if (Test-Path $exe) { Start-Process 'http://127.0.0.1:5244'; Start-Process -FilePath $exe -ArgumentList 'server' -WorkingDirectory $dir -NoNewWindow } else { Write-Host '[错误] 未找到 openlist.exe' }"
    pause
)
