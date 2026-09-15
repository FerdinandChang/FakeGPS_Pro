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
VERSION = "v1.2.3"
RELEASE_TITLE = "FakeGPS Pro v1.2.3 - 🛡️ 徹底根治 GPS 彈回真實地點 (Anti-Rubberbanding) 與自動靜默重連"

RELEASE_BODY = """# FakeGPS Pro v1.2.3 - 🛡️ 徹底根治 GPS 彈回真實地點與常駐心跳保活重大更新

本版本針對使用者反饋的「GPS 覆蓋後會突然跳回手機真實地點」與「需手動重新點擊已連線」現象進行底層架構級徹底根治：

## 🌟 重點修復與更新內容

### 1. 🛡️ 新增「防彈回常駐心跳守護者 (Anti-Rubberbanding Daemon)」
* **每 1.5 秒主動保活**：傳統虛擬定位只在點擊瞬間發送一筆資料，靜止時完全停止傳輸，導致 iOS 核心判定除錯結束而將 GPS 逾時還原。新版加入專屬背景守護執行緒，原地靜止時每 1.5 秒自動補發座標，DVT 模擬通道永久維持活躍狀態，**iOS 永不逾時重設**！
* **持續壓制 Wi-Fi / 基地台回彈**：持續性的模擬定位訊號能強勢壓制 Apple 背景掃描周圍 Wi-Fi 路由器 BSSID 產生的定位突刺，徹底杜絕原地跳回真身。

### 2. 🌊 微米級自然物理微震 (Micro-Jitter)
* 原地靜止時自動融入 ±0.000001 度（約 10~20 公分）自然物理微震，精準模擬真機衛星晶片的真實物理熱噪聲，防止 iOS 判定為凍結訊號，同時具備強效的**遊戲防封保護**。

### 3. 🔄 斷線自動靜默重連 (Silent Auto-Healing)
* 若因傳輸線微動、晃動或 Windows USB 節能休眠導致傳輸通道瞬斷，背景守護程式會**自動嘗試靜默重連並重新補發座標**，**徹底免去使用者必須手動再去按「已連線」的困擾**！

### 4. 🍄 完整繼承 v1.2.2 蘑菇戰情強化
* 包含全尺寸等級追蹤、一鍵秒飛真實瞬移、官方 14 種種類代碼對齊、最近一小時即時更新與官方 5 大排序方式同步。

---

## 📦 下載與安裝說明

* **Windows 使用者**：下載 `FakeGPS_Pro_Windows_v1.2.3.zip`，解壓縮後執行 `FakeGPS_Pro.exe` 即可（亦可直接在軟體內點「🔄 檢查更新」一鍵線上自動升級！）。
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
