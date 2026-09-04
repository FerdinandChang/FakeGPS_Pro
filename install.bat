@echo off
title FakeGPS Pro - Auto Installer
cd /d "%~dp0"

echo =======================================================
echo          FakeGPS Pro - Environment Setup
echo =======================================================
echo.
echo [1/3] Checking Python environment...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python not found! Please install Python.
        pause
        exit /b
    )
)
echo Python detected.
echo.

echo [2/3] Installing required packages (Pure Python Wheels)...
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
py -m pip install traitlets ipython gpxpy psutil
py -m pip install --no-deps pymobiledevice3==11.3.0
if %errorlevel% neq 0 (
    python -m pip install -r requirements.txt
    python -m pip install --no-deps pymobiledevice3==11.3.0
)
echo.

echo [3/3] Checking iTunes support...
echo Note: Please make sure Apple iTunes (Windows version) is installed.
echo.
echo =======================================================
echo          Installation Complete! Run run.bat to start.
echo =======================================================
echo.
pause
