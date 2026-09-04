#!/bin/bash
# FakeGPS Pro - macOS App 打包腳本
set -e

cd "$(dirname "$0")"

echo "======================================================="
echo "       FakeGPS Pro - 正在打包 macOS 獨立 .app 應用程式"
echo "======================================================="
echo ""

if ! command -v python3 &> /dev/null; then
    echo "錯誤: 尚未安裝 Python 3，請先安裝 Python (建議 3.10 ~ 3.13)"
    exit 1
fi

echo "[1/3] 檢查依賴環境..."
python3 -m pip install --upgrade pip
python3 -m pip install pyinstaller -r requirements.txt

echo "[2/3] 清理快取目錄..."
rm -rf build dist

echo "[3/3] 開始封裝 FakeGPS_Pro.app..."
python3 -m PyInstaller \
  --windowed \
  --name "FakeGPS_Pro" \
  --add-data "gui:gui" \
  --add-data "manual.html:." \
  --add-data "lzss.py:." \
  --add-data "lzfse.py:." \
  --add-data "pylzss.py:." \
  --add-data "parameter_decorators.py:." \
  --copy-metadata pyimg4 \
  --copy-metadata pymobiledevice3 \
  --copy-metadata developer_disk_image \
  --copy-metadata qh3 \
  --copy-metadata construct \
  --copy-metadata questionary \
  --collect-all pymobiledevice3 \
  --collect-all developer_disk_image \
  --collect-all qh3 \
  --collect-all pyimg4 \
  --collect-all webview \
  --noconfirm \
  --clean \
  main.py

cp manual.html dist/FakeGPS_Pro.app/Contents/Resources/ 2>/dev/null || true
cp manual.html dist/ 2>/dev/null || true

# 嘗試製作 DMG 映像檔
if command -v hdiutil &> /dev/null; then
    echo "正在製作 FakeGPS_Pro.dmg 安裝檔..."
    hdiutil create -volname "FakeGPS_Pro" -srcfolder "dist/FakeGPS_Pro.app" -ov -format UDZO "dist/FakeGPS_Pro.dmg"
    echo "DMG 安裝映像檔已生成: dist/FakeGPS_Pro.dmg"
fi

echo ""
echo "======================================================="
echo " 打包完成！成果檔案位於："
echo " 應用程式：dist/FakeGPS_Pro.app"
if [ -f "dist/FakeGPS_Pro.dmg" ]; then
    echo " DMG 安裝檔：dist/FakeGPS_Pro.dmg"
fi
echo "======================================================="
