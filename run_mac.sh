#!/bin/bash
# FakeGPS Pro - macOS 一鍵啟動腳本 (免打包直接執行)
cd "$(dirname "$0")"

echo "======================================================="
echo "          FakeGPS Pro - macOS 啟動器"
echo "======================================================="
echo ""

if ! command -v python3 &> /dev/null; then
    echo "錯誤: 尚未安裝 Python 3！請至 python.org 安裝 Python。"
    exit 1
fi

# 檢查是否已安裝依賴
if ! python3 -c "import webview, pymobiledevice3" &> /dev/null; then
    echo "偵測到尚未安裝相依套件，正在自動安裝..."
    python3 -m pip install -r requirements.txt
fi

echo "正在啟動 FakeGPS Pro..."
python3 main.py
