@echo off
chcp 65001 >nul
title SteelVision Client
echo ============================================
echo   SteelVision 桌面客户端启动中...
echo   确保后端服务已在 http://localhost:5000 运行
echo ============================================
echo.
cd /d "%~dp0"
python client.py
pause
