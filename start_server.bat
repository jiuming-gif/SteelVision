@echo off
chcp 65001 >nul
title SteelVision Server (http://localhost:5000)
echo ============================================
echo   SteelVision 后端服务启动中...
echo   接口文档: http://localhost:5000/docs
echo   按 Ctrl+C 停止服务
echo ============================================
echo.
cd /d "%~dp0"
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
pause
