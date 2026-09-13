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
VERSION = "v1.2.0"
RELEASE_TITLE = "FakeGPS Pro v1.2.0 - 🍄 蘑菇戰情中心大改版與全尺寸自訂追蹤"

RELEASE_BODY = """# FakeGPS Pro v1.2.0 - 🍄 蘑菇戰情中心全功能升級與小螢幕 RWD 修復

本版本帶來全方位的蘑菇戰情強化、全尺寸追蹤、一鍵秒飛開打與小螢幕自適應排版優化：

## 🌟 重點更新內容

### 1. 🍄 蘑菇全尺寸等級 (Level) 與屬性 (Type) 自訂追蹤
* **全尺寸切換**：可自訂篩選 **巨大菇 (預設)**、**大菇**、**普通菇**、**小菇** 或 **全部尺寸**，不再受限於單一等級！
* **特定屬性篩選**：支援水晶菇 💎、火菇 🔥、水菇 💧、電菇 ⚡、毒菇 🟣、節慶活動菇 🎃 精準追蹤。
* **刷新頻率升級**：新增 **5 秒 (極速搶位)**、**10 秒 (飛速)** 與 **15 秒 (推薦)** 靈敏更新選項。

### 2. ⚡ 發現目標自動秒飛 (Auto-Teleport) 與安全防封保護
* 勾選「發現目標自動秒飛」後，雷達掃描到符合條件的新蘑菇自動瞬移就位！
* 內建 **60 秒安全防封冷卻閥** 與去重快取，兼顧快速搶位開打與遊戲帳號安全。

### 3. 📱 徹底根治小螢幕 RWD 頂部按鈕被擠壓文字垂直折行
* 頂部按鈕加入防折行與隱藏式平滑橫向捲動保護。
* 螢幕寬度收窄時（<1260px / <1100px / <950px）漸進折疊次要文字，文字絕不垂直排版，版面美觀俐落。

### 4. ⚔️ 統整全軟體命名與戰情面板整合
* 純點與戰情分工整併：戰情卡片完整遷移至「🍄 蘑菇戰情」面板與抽屜。
* 左側 Tab 4 統一名稱為「📍 皮皮純點」，Tab 5 統一名稱為「🍄 蘑菇戰情」。

### 5. 🔔 100% 零漏接雙保險通知與除錯模式關閉
* 修復 Windows 10/11 原生 Toast 橫幅推播，並加入網頁視覺發光 Toast 氣泡（免疫勿擾模式）。
* 前端 Web Audio 雙音階提示音 + 後端原生系統警示音雙保險發聲。
* 關閉啟動時預設彈出的 Edge DevTools 視窗。

### 6. 🍎 macOS 雙架構全面支援與手冊擴充
* 完整支援 Apple Silicon (M1/M2/M3/M4) 與 Intel 晶片 Mac。
* 說明手冊新增 Mac 用戶專屬指南（免裝 iTunes、Gatekeeper 一鍵解鎖與晶片選擇）。

---

## 📦 下載與安裝說明

* **Windows 使用者**：下載 `FakeGPS_Pro_Windows_v1.2.0.zip`，解壓縮後執行 `FakeGPS_Pro.exe` 即可（亦可直接在軟體內點「🔄 檢查更新」一鍵線上自動升級！）。
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
