@echo off
chcp 65001 >nul
title OpenList 云盘挂载服务
echo ========================================================
echo        正在启动 OpenList 联通云盘挂载网关服务...
echo        后台访问地址: http://127.0.0.1:5244
echo ========================================================
cd /d "E:\浏览器下载内容"
start http://127.0.0.1:5244
openlist.exe server
pause
