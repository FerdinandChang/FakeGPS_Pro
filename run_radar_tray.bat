@echo off
chcp 65001 >nul
title 🍄 FakeGPS Pro - 巨大蘑菇獨立桌面雷達
cd /d "%~dp0"

echo 正在啟動巨大蘑菇桌面監控小工具...
python mushroom_radar_tray.py
if %errorlevel% neq 0 (
    echo.
    echo 執行發生錯誤，請確認 Python 環境已安裝。
    pause
)
