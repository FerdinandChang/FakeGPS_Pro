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
VERSION = "v1.2.5"
RELEASE_TITLE = "FakeGPS Pro v1.2.5 - 🍄 皮皮蘑菇 Google 登入支援與 Windows 免手動解鎖永久根治"

RELEASE_BODY = """# FakeGPS Pro v1.2.5 - 🍄 皮皮蘑菇 Google 登入支援與 Windows 免手動解鎖重大更新

本版本針對皮皮蘑菇官方網站（pipimushroom.com）近期安全性改版，以及 Windows 下載解壓縮後的組件鎖定問題進行底層重大升級：

## 🌟 重點修復與更新內容

### 1. 🔑 支援「皮皮蘑菇 Google 授權登入」（因應官網強制登入改版）
* **一鍵彈窗授權**：皮皮蘑菇官方自 9/15～9/16 起將戰況列表與地圖改為強制 Google 登入，未登入者一律回應 HTTP 401。新版在雷達介面新增「🔑 登入皮皮」按鈕，點擊彈出內嵌安全視窗即可快速完成 Google 授權！
* **自動提取與持久化憑證**：授權成功後自動提取 Session 認證憑證並保存在本地，**重開軟體免重複登入**！
* **無縫恢復即時戰況與一鍵秒飛**：帶憑證查詢徹底解決 HTTP 401 錯誤，蘑菇戰況更新、定時監控與一鍵秒飛全數恢復正常運作。

### 2. 🛡️ Windows 端「免手動解除鎖定」開發者端永久根治方案
* **附帶 `FakeGPS_Pro.exe.config`**：啟用 `<loadFromRemoteSources enabled="true"/>`，強制 .NET CLR 允許直接載入帶有網路標記的組件。
* **啟動時自動 Self-Unblock**：主程式啟動瞬間自動遞迴清除目錄下所有檔案的 `:Zone.Identifier`（Mark of the Web）。
* **雙擊即開零報錯**：未來任何使用者從 GitHub 下載 ZIP，解壓縮後直接雙擊執行即可秒開，**徹底終結 `Python.Runtime.dll` 解析失敗問題**！

### 3. ⚡ 延續 v1.2.4 的 DVT 執行緒互斥安全鎖
* 具備完整 `_io_lock` 互斥鎖與非阻塞讓位保活機制，保證手機 GPS 覆蓋 100% 穩定，絕不跳回真實地點。

---

## 📦 下載與安裝說明

* **Windows 使用者**：下載 `FakeGPS_Pro_Windows_v1.2.5.zip`，解壓縮後直接雙擊 `FakeGPS_Pro.exe` 即可開啟（免手動右鍵解除鎖定！）。
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
    if os.path.exists("d:/FakeGPS/FakeGPS_Pro.exe.config"):
        shutil.copy("d:/FakeGPS/FakeGPS_Pro.exe.config", dist_dir)
    
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
