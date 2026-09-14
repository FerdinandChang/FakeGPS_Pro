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

sys.stdout.reconfigure(encoding='utf-8')

REPO = "FerdinandChang/FakeGPS_Pro"
VERSION = "v1.2.2"
RELEASE_TITLE = "FakeGPS Pro v1.2.2 - 🚀 一鍵秒飛真實瞬移修復與官網篩選排序全面對齊"

RELEASE_BODY = """# FakeGPS Pro v1.2.2 - 🚀 一鍵秒飛修復與蘑菇篩選排序官方同步

本版本針對「一鍵秒飛」與「蘑菇篩選條件與即時性」進行全面修復與深度優化：

## 🌟 重點修復與更新內容

### 1. 🚀 修復「一鍵秒飛」與「自動秒飛」無作用問題
* **底層 API 串接修復**：修正卡片點擊「一鍵秒飛」未正確呼叫後端 `teleport` 介面的問題。現在點擊「🚀 一鍵秒飛」瞬間覆蓋真實手機 GPS 座標就位開打！
* **地圖連動與安全防封**：秒飛同時自動平移並放大聚焦地圖視角，同步啟動建議冷卻倒數計時與綠色反饋提示。

### 2. 📊 蘑菇篩選條件與資料庫排序 100% 對齊皮皮蘑菇官方網站
* **新增「資料更新時間」篩選**：支援 **最近一小時 (預設最即時)**、**最近六小時**、**最近一天** 與 **全部時間**，徹底解決因舊版鎖定 24 小時導致拿到陳舊資料的問題！
* **新增「排序方式」切換**：全面支援 **最近更新 (預設)**、**總戰力最高**、**參加人數最多**、**即將結束** 與 **剩餘血量最低**，與官網排行完全同步！
* **官方種類代碼完整對齊**：支援當季最新 **華麗蘑菇 (活動)**、**元素菇**、**水晶**、**火**、**水**、**電**、**毒**、**冰藍** 等完整 14 種官方蘑菇分類。
* **智慧開啟戰況網頁**：點擊「🌐 開啟戰況網頁」自動將目前選取的所有縣市、種類、尺寸、參戰狀態、更新時間與排序組合成官網專屬連結直接開啟！

### 3. ⚡ 純 Python 原生加解密（免裝 Node.js）
* 延續 v1.2.1 的純 Python AES-256-CBC (PKCS#7) 與 HMAC-SHA256 架構，0.5 秒秒回，任何電腦解壓即用。

---

## 📦 下載與安裝說明

* **Windows 使用者**：下載 `FakeGPS_Pro_Windows_v1.2.2.zip`，解壓縮後執行 `FakeGPS_Pro.exe` 即可（亦可直接在軟體內點「🔄 檢查更新」一鍵線上自動升級！）。
* **Mac 使用者**：下載對應晶片的 DMG 檔案（`FakeGPS_Pro-AppleSilicon.dmg` 適用 M1/M2/M3/M4；`FakeGPS_Pro-Intel.dmg` 適用舊款 Intel Mac），雙擊開啟即可使用。
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
    zip_ver = os.path.join("d:/FakeGPS", "dist", f"FakeGPS_Pro_Windows_{VERSION}.zip")
    zip_generic = os.path.join("d:/FakeGPS", "dist", "FakeGPS_Pro.zip")
    create_windows_zip(dist_dir, zip_ver)
    shutil.copy(zip_ver, zip_generic)

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
        if a.get("name") in (f"FakeGPS_Pro_Windows_{VERSION}.zip", "FakeGPS_Pro.zip"):
            print(f"刪除舊資產 {a.get('name')} ...")
            requests.delete(a.get("url"), headers=headers)

    # 4. 上傳發布包
    upload_asset(upload_url, zip_ver, f"FakeGPS_Pro_Windows_{VERSION}.zip", token)
    upload_asset(upload_url, zip_generic, "FakeGPS_Pro.zip", token)

    print()
    print("=" * 60)
    print(f" 🎉 {VERSION} 正式發布完成！")
    print(f" 發布網址: {release_data.get('html_url')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
