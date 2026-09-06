"""
FakeGPS Pro - Automated GitHub Release Publisher
Builds ZIP archives and creates a formal release on GitHub via the official REST API.
"""
import os
import sys
import json
import zipfile
import requests
import subprocess
from datetime import datetime

REPO = "FerdinandChang/FakeGPS_Pro"
VERSION = "v1.1.0"
RELEASE_TITLE = "FakeGPS Pro v1.1.0 - 巨大蘑菇即時雷達與線上自動升級"

RELEASE_BODY = """# FakeGPS Pro v1.1.0 - 巨大蘑菇即時雷達與線上自動升級大改版

## 🍄 新增功能與重點特色

### 1. 皮皮蘑菇「巨大蘑菇即時雷達」
* **自動背景追蹤**：支援每 30 秒 / 60 秒自動掃描全台 Pipi Mushroom 即時資料庫。
* **智慧參戰篩選**：預設精準過濾「未滿 5 人 (可參戰)」或「0 人空場」的巨大蘑菇。
* **即時警報提醒**：新出現巨大菇時，立即發出雙音階清脆提示音，並於 Windows / macOS 桌面右下角彈出系統橫幅通知。
* **🚀 一鍵秒飛開打**：雷達卡片標註地標、座標與目前人數，點擊「一鍵秒飛」手機 GPS 瞬間傳送至現場！

### 2. Windows & macOS 雙平台線上無痛自動更新
* **靜默檢查**：開機背景自動比對最新發行版本。
* **一鍵升級重啟**：下載完成後由守護程序於 1 秒內自動完成檔案置換並重啟新版。
* **永久保留授權**：升級過程完全不影響現有電腦已啟用的序號憑證，免重新驗證！

### 3. 獨立桌面監控小工具 (`run_radar_tray.bat`)
* 支援在未開啟主視窗時於電腦背景獨立運行，發現目標即時報警。

---

## 📦 下載與安裝說明

* **Windows 使用者**：下載 `FakeGPS_Pro_Windows_v1.1.0.zip`，解壓縮後執行 `FakeGPS_Pro.exe` 即可（舊版使用者直接解壓覆蓋原資料夾升級）。
* **Mac 使用者**：下載對應晶片的 DMG 檔案（`AppleSilicon` 適用 M1/M2/M3/M4；`Intel` 適用舊款 Mac），雙擊開啟即可使用。
"""

def get_github_token():
    try:
        proc = subprocess.Popen(['git', 'credential', 'fill'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        out, _ = proc.communicate('protocol=https\nhost=github.com\n')
        creds = dict(line.split('=', 1) for line in out.strip().splitlines() if '=' in line)
        return creds.get('password')
    except Exception as e:
        print(f"取得 Git Token 失敗: {e}")
        return None

def create_windows_zip(dist_dir: str, output_zip: str):
    print(f"正在壓縮 {dist_dir} -> {output_zip} ...")
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, dist_dir)
                # 包含根目錄 FakeGPS_Pro/
                arcname = os.path.join("FakeGPS_Pro", rel_path)
                zf.write(full_path, arcname)
    print(f"壓縮完成！大小: {os.path.getsize(output_zip) / (1024*1024):.1f} MB")

def upload_asset(upload_url: str, file_path: str, asset_name: str, token: str):
    print(f"正在上傳資源 {asset_name} ...")
    clean_upload_url = upload_url.split('{')[0] + f"?name={asset_name}"
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/zip"
    }
    with open(file_path, "rb") as f:
        r = requests.post(clean_upload_url, headers=headers, data=f, timeout=120)
    if r.status_code in (200, 201):
        print(f"上傳成功: {asset_name}")
    else:
        print(f"上傳失敗 ({r.status_code}): {r.text}")

def main():
    token = get_github_token()
    if not token:
        print("無法取得 GitHub Token，結束。")
        return

    # 1. 確保 dist/FakeGPS_Pro 依賴齊全
    dist_dir = os.path.join("d:/FakeGPS", "dist", "FakeGPS_Pro")
    if not os.path.exists(dist_dir):
        print(f"找不到編譯目錄 {dist_dir}")
        return

    import shutil
    internal_wintun = os.path.join(dist_dir, "_internal", "pytun_pmd3", "wintun", "bin", "amd64", "wintun.dll")
    if os.path.exists("d:/FakeGPS/wintun.dll"):
        shutil.copy("d:/FakeGPS/wintun.dll", dist_dir)
    elif os.path.exists(internal_wintun):
        shutil.copy(internal_wintun, dist_dir)
    if os.path.exists("d:/FakeGPS/manual.html"):
        shutil.copy("d:/FakeGPS/manual.html", dist_dir)
    if os.path.exists("d:/FakeGPS/run_radar_tray.bat"):
        shutil.copy("d:/FakeGPS/run_radar_tray.bat", dist_dir)
    if os.path.exists("d:/FakeGPS/mushroom_radar_tray.py"):
        shutil.copy("d:/FakeGPS/mushroom_radar_tray.py", dist_dir)
    
    # 2. 建立 ZIP 包
    zip_v110 = os.path.join("d:/FakeGPS", "dist", "FakeGPS_Pro_Windows_v1.1.0.zip")
    zip_generic = os.path.join("d:/FakeGPS", "dist", "FakeGPS_Pro.zip")
    create_windows_zip(dist_dir, zip_v110)
    shutil.copy(zip_v110, zip_generic)

    # 3. 呼叫 GitHub API 建立或取得 Release
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    rel_url = f"https://api.github.com/repos/{REPO}/releases"
    get_rel = requests.get(f"{rel_url}/tags/{VERSION}", headers=headers)
    
    if get_rel.status_code == 200:
        release_data = get_rel.json()
        print(f"找到既有 Release {VERSION}")
    else:
        print(f"正在建立 GitHub Release {VERSION} ...")
        payload = {
            "tag_name": VERSION,
            "target_commitish": "main",
            "name": RELEASE_TITLE,
            "body": RELEASE_BODY,
            "draft": False,
            "prerelease": False
        }
        res = requests.post(rel_url, headers=headers, json=payload)
        if res.status_code not in (200, 201):
            print(f"建立 Release 失敗 ({res.status_code}): {res.text}")
            return
        release_data = res.json()
        print(f"Release 建立成功！URL: {release_data.get('html_url')}")

    upload_url = release_data.get("upload_url")
    
    # 刪除已存在的同名資產避免衝突
    existing_assets = release_data.get("assets", [])
    for a in existing_assets:
        if a.get("name") in ("FakeGPS_Pro_Windows_v1.1.0.zip", "FakeGPS_Pro.zip"):
            print(f"刪除舊資產 {a.get('name')} ...")
            requests.delete(a.get("url"), headers=headers)

    # 4. 上傳發布包
    upload_asset(upload_url, zip_v110, "FakeGPS_Pro_Windows_v1.1.0.zip", token)
    upload_asset(upload_url, zip_generic, "FakeGPS_Pro.zip", token)

    print()
    print("=" * 60)
    print(" 🎉 v1.1.0 正式發布完成！")
    print(f" 發布網址: {release_data.get('html_url')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
