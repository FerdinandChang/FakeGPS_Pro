"""
FakeGPS Pro - Cross-Platform Auto-Updater (Windows & macOS)
Supports GitHub Releases querying, architecture-specific package selection,
and OS-native in-place application replacement.
"""
import os
import sys
import time
import zipfile
import logging
import requests
import tempfile
import platform
import subprocess
import threading
from typing import Dict, Any, Optional, Callable

from core.version import CURRENT_VERSION, is_newer_version

logger = logging.getLogger("AutoUpdater")

GITHUB_REPO = "FerdinandChang/FakeGPS_Pro"
RELEASES_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

class AutoUpdater:
    def __init__(self, progress_callback: Optional[Callable[[int, str], None]] = None):
        self.progress_callback = progress_callback
        self.is_updating = False

    def check_for_updates(self) -> Dict[str, Any]:
        """向 GitHub Releases 查詢最新版本資訊 (自動適配 Windows 與 macOS 晶片架構)"""
        try:
            headers = {
                "User-Agent": "FakeGPS-Pro-Updater/1.0",
                "Accept": "application/vnd.github.v3+json"
            }
            resp = requests.get(RELEASES_API_URL, headers=headers, timeout=8)
            
            if resp.status_code == 404:
                return {
                    "success": True,
                    "has_update": False,
                    "message": "尚未發布任何 Releases 版本",
                    "current_version": CURRENT_VERSION
                }
            elif resp.status_code != 200:
                return {
                    "success": False,
                    "error": f"GitHub API 回應錯誤 ({resp.status_code})"
                }

            release_data = resp.json()
            remote_tag = release_data.get("tag_name", "").lstrip("v").strip()
            changelog = release_data.get("body", "無更新說明")
            
            is_mac = sys.platform == "darwin"
            is_arm = platform.machine() in ("arm64", "aarch64")

            assets = release_data.get("assets", [])
            download_url = None
            file_size = 0
            
            # 依作業系統與硬體架構篩選最適安裝包
            for asset in assets:
                name = asset.get("name", "").lower()
                if is_mac:
                    # macOS：優先尋找匹配當前晶片的壓縮檔或 DMG
                    if is_arm and ("applesilicon" in name or "arm64" in name):
                        download_url = asset.get("browser_download_url")
                        file_size = asset.get("size", 0)
                        break
                    elif not is_arm and ("intel" in name or "x86_64" in name):
                        download_url = asset.get("browser_download_url")
                        file_size = asset.get("size", 0)
                        break
                    elif "mac" in name:
                        download_url = asset.get("browser_download_url")
                        file_size = asset.get("size", 0)
                else:
                    # Windows：尋找 Windows ZIP
                    if "win" in name or ("mac" not in name and "intel" not in name and "applesilicon" not in name):
                        if name.endswith(".zip"):
                            download_url = asset.get("browser_download_url")
                            file_size = asset.get("size", 0)
                            break
                    
            if not download_url:
                # 若無單獨命名檔案，取第一個符合格式的資產或源碼包
                for asset in assets:
                    if asset.get("name", "").endswith(".zip") or asset.get("name", "").endswith(".dmg"):
                        download_url = asset.get("browser_download_url")
                        file_size = asset.get("size", 0)
                        break
                if not download_url:
                    download_url = release_data.get("zipball_url")

            has_update = is_newer_version(remote_tag, CURRENT_VERSION)

            return {
                "success": True,
                "has_update": has_update,
                "current_version": CURRENT_VERSION,
                "latest_version": remote_tag,
                "changelog": changelog,
                "download_url": download_url,
                "file_size": file_size,
                "published_at": release_data.get("published_at", "")
            }
        except Exception as e:
            logger.error(f"檢查更新失敗: {e}")
            return {
                "success": False,
                "error": f"連線至更新伺服器失敗: {str(e)}"
            }

    def start_download_and_install(self, download_url: str, on_progress=None) -> Dict[str, Any]:
        """啟動非同步下載並套用更新"""
        if self.is_updating:
            return {"success": False, "error": "更新程序已在執行中"}

        self.is_updating = True
        
        def _run():
            try:
                self._download_and_apply(download_url, on_progress)
            except Exception as e:
                logger.error(f"自動更新過程異常: {e}")
                if on_progress:
                    on_progress(-1, f"更新失敗: {str(e)}")
            finally:
                self.is_updating = False

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return {"success": True, "message": "已開始下載更新"}

    def _download_and_apply(self, download_url: str, on_progress=None):
        temp_dir = os.path.join(tempfile.gettempdir(), "FakeGPS_Update")
        os.makedirs(temp_dir, exist_ok=True)
        
        is_mac = sys.platform == "darwin"
        ext = ".dmg" if download_url.lower().endswith(".dmg") else ".zip"
        archive_path = os.path.join(temp_dir, f"update{ext}")
        extracted_dir = os.path.join(temp_dir, "extracted")

        if on_progress:
            on_progress(5, "正在連線至更新伺服器...")

        # 1. 串流下載檔案並回報進度
        headers = {"User-Agent": "FakeGPS-Pro-Updater/1.0"}
        with requests.get(download_url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            total_length = int(r.headers.get("content-length", 0))
            downloaded = 0
            
            with open(archive_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_length > 0 and on_progress:
                            pct = int((downloaded / total_length) * 75) + 5
                            on_progress(pct, f"正在下載更新檔 ({pct}%)...")

        if on_progress:
            on_progress(85, "下載完成，正在準備換檔...")

        # 2. 解壓縮 (針對 ZIP)
        if ext == ".zip":
            if os.path.exists(extracted_dir):
                import shutil
                shutil.rmtree(extracted_dir, ignore_errors=True)
            os.makedirs(extracted_dir, exist_ok=True)

            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(extracted_dir)

            entries = os.listdir(extracted_dir)
            source_dir = extracted_dir
            if len(entries) == 1 and os.path.isdir(os.path.join(extracted_dir, entries[0])):
                source_dir = os.path.join(extracted_dir, entries[0])
        else:
            source_dir = temp_dir

        if on_progress:
            on_progress(95, "正在啟動換檔守護程序...")
        time.sleep(1)

        # 3. 跨平台換檔重啟邏輯
        if is_mac:
            self._apply_mac_update(source_dir, archive_path, ext, temp_dir, on_progress)
        else:
            self._apply_windows_update(source_dir, temp_dir, on_progress)

    def _apply_windows_update(self, source_dir: str, temp_dir: str, on_progress):
        """Windows 換檔重啟"""
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
            target_exe = sys.executable
        else:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            target_exe = os.path.join(app_dir, "run.bat")

        bat_script = os.path.join(temp_dir, "apply_update.bat")
        bat_content = f"""@echo off
chcp 65001 >nul
echo 正在等待舊版程式關閉釋放檔案...
timeout /t 2 /nobreak >nul

echo 正在複製最新檔案覆蓋安裝目錄...
xcopy /y /e /q "{source_dir}\\*" "{app_dir}\\" >nul

echo 升級完成！正在重新啟動 FakeGPS Pro...
start "" "{target_exe}"

timeout /t 1 /nobreak >nul
exit
"""
        with open(bat_script, "w", encoding="utf-8") as f:
            f.write(bat_content)

        if on_progress:
            on_progress(100, "更新套用完畢，即將重啟！")
        time.sleep(1)

        subprocess.Popen(
            ["cmd.exe", "/c", bat_script],
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0,
            close_fds=True
        )
        os._exit(0)

    def _apply_mac_update(self, source_dir: str, archive_path: str, ext: str, temp_dir: str, on_progress):
        """macOS 換檔重啟"""
        # 尋找當前 .app 封裝位置
        target_app = "/Applications/FakeGPS_Pro.app"
        if getattr(sys, 'frozen', False):
            # sys.executable 通常在 FakeGPS_Pro.app/Contents/MacOS/FakeGPS_Pro
            curr_exe = sys.executable
            if ".app" in curr_exe:
                target_app = curr_exe[:curr_exe.find(".app") + 4]

        sh_script = os.path.join(temp_dir, "apply_update.sh")
        
        # 尋找新版 .app 目錄
        sh_content = f"""#!/bin/bash
sleep 2
echo "正在更新 FakeGPS Pro for macOS..."

NEW_APP=$(find "{source_dir}" -maxdepth 3 -name "*.app" -type d | head -n 1)

if [ -n "$NEW_APP" ] && [ -d "$NEW_APP" ]; then
    rm -rf "{target_app}"
    cp -R "$NEW_APP" "{target_app}"
    open "{target_app}"
else
    # 若是 DMG 檔
    if [ -f "{archive_path}" ] && [[ "{archive_path}" == *.dmg ]]; then
        MOUNT_DIR=$(hdiutil mount "{archive_path}" | grep "/Volumes" | awk '{{print $3}}')
        if [ -n "$MOUNT_DIR" ]; then
            DMG_APP=$(find "$MOUNT_DIR" -name "*.app" -type d | head -n 1)
            if [ -n "$DMG_APP" ]; then
                rm -rf "{target_app}"
                cp -R "$DMG_APP" "{target_app}"
            fi
            hdiutil unmount "$MOUNT_DIR" 2>/dev/null || true
            open "{target_app}"
        fi
    else
        open "{target_app}" 2>/dev/null || true
    fi
fi
exit 0
"""
        with open(sh_script, "w", newline="\n", encoding="utf-8") as f:
            f.write(sh_content)
            
        os.chmod(sh_script, 0o755)

        if on_progress:
            on_progress(100, "更新套用完畢，即將重啟！")
        time.sleep(1)

        subprocess.Popen(["/bin/bash", sh_script], close_fds=True)
        os._exit(0)
