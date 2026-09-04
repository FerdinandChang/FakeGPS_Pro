#!/bin/bash
# FakeGPS Pro - macOS 環境安裝腳本
cd "$(dirname "$0")"

echo "======================================================="
echo "       FakeGPS Pro - 正在安裝 macOS 所需環境套件"
echo "======================================================="
echo ""

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo ""
echo "環境安裝完成！現在可以執行 ./run_mac.sh 啟動軟體。"
