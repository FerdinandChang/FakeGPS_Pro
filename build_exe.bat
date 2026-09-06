@echo off
title FakeGPS Pro - EXE 打包程式
cd /d "%~dp0"

echo =======================================================
echo          FakeGPS Pro - 正在打包獨立免安裝 EXE
echo =======================================================
echo.

python -m PyInstaller --noconsole --name "FakeGPS_Pro" ^
  --add-data "gui;gui" ^
  --add-data "core/fetch_mushrooms.js;core" ^
  --add-data "manual.html;." ^
  --add-data "lzss.py;." ^
  --add-data "lzfse.py;." ^
  --add-data "pylzss.py;." ^
  --add-data "parameter_decorators.py;." ^
  --copy-metadata pyimg4 ^
  --copy-metadata pymobiledevice3 ^
  --copy-metadata developer_disk_image ^
  --copy-metadata pytun_pmd3 ^
  --copy-metadata qh3 ^
  --copy-metadata construct ^
  --copy-metadata questionary ^
  --collect-all pymobiledevice3 ^
  --collect-all pytun_pmd3 ^
  --collect-all developer_disk_image ^
  --collect-all qh3 ^
  --collect-all pyimg4 ^
  --collect-all webview ^
  --noconfirm ^
  main.py

echo 正在複製必要依賴檔案...
copy /y wintun.dll dist\FakeGPS_Pro\ >nul
copy /y manual.html dist\FakeGPS_Pro\ >nul

echo.
echo =======================================================
echo  打包完成！成果檔案位於：dist\FakeGPS_Pro
echo =======================================================
pause
