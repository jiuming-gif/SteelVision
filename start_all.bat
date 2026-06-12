@echo off
chcp 65001 >nul
title SteelVision - 一键启动

echo ============================================
echo   SteelVision 一键启动
echo   同时启动后端服务 + 桌面客户端
echo ============================================
echo.

echo [1/2] 启动后端服务 (端口 5000)...
cd /d "%~dp0"
start "SteelVision Server" cmd /c "uvicorn main:app --host 0.0.0.0 --port 5000"

echo 等待后端服务就绪...
timeout /t 5 /nobreak >nul

echo [2/2] 启动桌面客户端...
start "SteelVision Client" cmd /c "python client.py"

echo.
echo 服务端: http://localhost:5000/docs
echo 客户端已启动
echo.
pause
