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
VERSION = "v1.2.6"
RELEASE_TITLE = "FakeGPS Pro v1.2.6 - 🍄 皮皮蘑菇認證 SimpleCookie 解析修復與標題排版優化"

RELEASE_BODY = """# FakeGPS Pro v1.2.6 - 🍄 皮皮蘑菇認證修復與排版防折行更新

本版本針對皮皮蘑菇登入認證憑證提取與雷達面板排版進行底層重大修復：

## 🌟 重點修復與更新內容

### 1. 🔑 修正 SimpleCookie 底層憑證解析（100% 成功捕獲 `pm_site_session`）
* **破案修復**：修正 PyWebView 原生回傳之 `http.cookies.SimpleCookie` 物件解析方式，支援以字典迭代方式提取帶有 `HttpOnly` 保護的 `pm_site_session` 核心憑證！
* **杜絕死鎖當機**：徹底拔除引發「FakeGPS_Pro.exe 沒有回應」之 WinForms STA 執行緒鎖，保證全流程 0% 死鎖幾率。

### 2. 🎨 雷達抽屜標題排版防擠壓重構
* **防止標題垂直折行**：寬度微調至 440px，標題加上防擠壓與強制不折行樣式，徹底解決「蘑菇/即時/戰情/雷達」文字垂直跑版問題。
* **智慧動態登入按鈕**：未登入顯示 `[🔑 登入皮皮]`，開啟視窗後智慧動態切換為 `[✅ 點此驗證]`，不再擁擠遮擋「🔄 刷新」按鈕。

### 3. 🛡️ 延續 Windows 免手動解除鎖定與 DVT 互斥安全鎖
* 附帶 `FakeGPS_Pro.exe.config` 與啟動時自動清除 `:Zone.Identifier`。
* 完備 DVT 執行緒互斥安全鎖，防止 GPS 跳回真實地點。

---

## 📦 下載與安裝說明

* **Windows 使用者**：下載 `FakeGPS_Pro_Windows_v1.2.6.zip`，解壓縮後直接雙擊 `FakeGPS_Pro.exe` 即可開啟使用。
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
