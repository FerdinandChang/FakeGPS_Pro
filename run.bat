@echo off
title FakeGPS Pro - Launcher
cd /d "%~dp0"

echo ========================================================
echo   FakeGPS Pro - iOS Location Simulation Launcher
echo ========================================================
echo.
echo Starting Application...
py main.py
if %ERRORLEVEL% NEQ 0 (
    python main.py
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [ERROR] Failed to start. Please make sure requirements are installed.
        pause
    )
)
