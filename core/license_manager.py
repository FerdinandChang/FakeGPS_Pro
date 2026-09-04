"""
FakeGPS Pro - License & Machine Binding Manager
Handles Windows hardware fingerprinting, local license verification, and cloud single-use activation.
"""
import os
import sys
import json
import hmac
import hashlib
import base64
import logging
import subprocess
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger("FakeGPS_License")

# Google Apps Script Web App 雲端驗證端點
LICENSE_API_URL = "https://script.google.com/macros/s/AKfycbxjnNBcQXr8I8Igi0emEUj4lVWAxgqYeRQWBdBLFdUGFogmxi4QsnE9-MlBsupDXRvDFg/exec"

# 本地 HMAC 簽名密鑰（混淆加固）
_SECRET_SALT = b"FakeGPS_Pro_Secret_Key_Salt_2026_iOS_Location"


def get_machine_id() -> str:
    """
    抓取系統底層硬體唯一識別碼：
    - Windows: 主機板 UUID + 註冊表 MachineGuid + CPU/電腦特徵
    - macOS: IOPlatformUUID + 硬體序號 (Serial Number) + 電腦特徵
    產出 16 碼格式化機器特徵碼（例如: A1B2-C3D4-E5F6-7890）
    """
    raw_identifiers = []

    if sys.platform == "win32":
        # 1. Windows: 讀取主機板 UUID
        try:
            output = subprocess.check_output(
                ["wmic", "csproduct", "get", "uuid"],
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            ).decode("utf-8", errors="ignore")
            lines = [l.strip() for l in output.splitlines() if l.strip() and "UUID" not in l.upper()]
            if lines:
                raw_identifiers.append(lines[0])
        except Exception:
            pass

        # 2. Windows: 讀取註冊表 MachineGuid
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            raw_identifiers.append(str(guid))
        except Exception:
            pass

        # 3. Windows: 讀取 CPU 資訊 / 電腦名稱
        try:
            raw_identifiers.append(os.environ.get("COMPUTERNAME", "UNKNOWN_PC"))
            raw_identifiers.append(os.environ.get("PROCESSOR_IDENTIFIER", "UNKNOWN_CPU"))
        except Exception:
            pass

    elif sys.platform == "darwin":
        # 1. macOS: 讀取 IOPlatformUUID
        try:
            cmd = "ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID"
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore")
            for part in output.split('"'):
                if "-" in part and len(part) >= 30:
                    raw_identifiers.append(part.strip())
                    break
        except Exception:
            pass

        # 2. macOS: 讀取硬體序號 Serial Number
        try:
            cmd = "system_profiler SPHardwareDataType | grep 'Serial Number'"
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore")
            if ":" in output:
                raw_identifiers.append(output.split(":")[-1].strip())
        except Exception:
            pass

        # 3. macOS: 備援電腦名稱
        try:
            import socket
            raw_identifiers.append(socket.gethostname())
        except Exception:
            pass

    else:
        # Linux / Other fallback
        try:
            import socket
            raw_identifiers.append(socket.gethostname())
        except Exception:
            pass

    if not raw_identifiers:
        raw_identifiers.append("FALLBACK_GENERIC_MACHINE_KEY_2026")

    raw_combined = "###".join(raw_identifiers)
    digest = hashlib.sha256(raw_combined.encode("utf-8")).hexdigest().upper()
    return f"{digest[0:4]}-{digest[4:8]}-{digest[8:12]}-{digest[12:16]}"


class LicenseManager:
    """本機授權管理員：負責驗證、儲存憑證並對接雲端單次核銷 API"""
    def __init__(self):
        self.machine_id = get_machine_id()
        if sys.platform == "darwin":
            self.license_dir = os.path.expanduser("~/Library/Application Support/FakeGPS_Pro")
        else:
            self.license_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "FakeGPS_Pro")
        os.makedirs(self.license_dir, exist_ok=True)
        self.license_file = os.path.join(self.license_dir, "license.dat")
        self._is_active = False
        self._license_info = {}

    def _generate_signature(self, machine_id: str, key: str, activated_at: str) -> str:
        """生成本地防篡改 HMAC 簽名"""
        payload = f"{machine_id}::{key}::{activated_at}".encode("utf-8")
        return hmac.new(_SECRET_SALT, payload, hashlib.sha256).hexdigest()

    def verify_local_license(self) -> bool:
        """驗證本地是否存在合法且未被篡改的授權證書"""
        if not os.path.exists(self.license_file):
            self._is_active = False
            return False

        try:
            with open(self.license_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
            
            # Base64 解碼
            json_str = base64.b64decode(content.encode("utf-8")).decode("utf-8")
            data = json.loads(json_str)

            saved_machine_id = data.get("machine_id")
            saved_key = data.get("key")
            saved_time = data.get("activated_at")
            saved_signature = data.get("signature")

            # 1. 驗證機器碼是否吻合當前電腦
            if saved_machine_id != self.machine_id:
                logger.warning(f"授權機器碼不符: {saved_machine_id} != {self.machine_id}")
                self._is_active = False
                return False

            # 2. 驗證 HMAC 簽名防篡改
            expected_sig = self._generate_signature(saved_machine_id, saved_key, saved_time)
            if not hmac.compare_digest(saved_signature, expected_sig):
                logger.warning("授權簽名校驗失敗，檔案可能已被手動竄改")
                self._is_active = False
                return False

            self._is_active = True
            self._license_info = data
            logger.info(f"本地授權校驗通過！序號: {saved_key}")
            return True

        except Exception as e:
            logger.error(f"讀取本地授權失敗: {e}")
            self._is_active = False
            return False

    def activate_cloud_key(self, serial_key: str) -> Dict[str, Any]:
        """
        向 Google 試算表雲端發送單次核銷與機器綁定請求（含自動重試與冷啟動容錯）
        """
        clean_key = serial_key.strip().upper()
        if not clean_key:
            return {"success": False, "message": "請輸入有效序號"}

        params = {
            "action": "activate",
            "key": clean_key,
            "machineId": self.machine_id
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FakeGPS/1.0"
        }

        # 最多嘗試 2 次（防止 Google Apps Script 首次冷啟動喚醒超時）
        last_err = ""
        for attempt in range(1, 3):
            try:
                logger.info(f"第 {attempt} 次向雲端核銷序號: {clean_key} (Machine: {self.machine_id})")
                
                # connect timeout: 10s, read timeout: 35s
                res = requests.get(
                    LICENSE_API_URL,
                    params=params,
                    headers=headers,
                    allow_redirects=True,
                    timeout=(10, 35)
                )

                if res.status_code != 200:
                    last_err = f"雲端伺服器回應異常 (HTTP {res.status_code})"
                    continue

                result = res.json()
                if result.get("success"):
                    activated_at = result.get("activatedAt", "")
                    
                    # 寫入本地加密授權檔
                    license_payload = {
                        "machine_id": self.machine_id,
                        "key": clean_key,
                        "activated_at": activated_at,
                        "signature": self._generate_signature(self.machine_id, clean_key, activated_at)
                    }
                    
                    json_bytes = json.dumps(license_payload).encode("utf-8")
                    b64_str = base64.b64encode(json_bytes).decode("utf-8")
                    
                    with open(self.license_file, "w", encoding="utf-8") as f:
                        f.write(b64_str)

                    self._is_active = True
                    self._license_info = license_payload
                    logger.info(f"🎉 雲端核銷成功並已儲存本地憑證！")
                    return {"success": True, "message": result.get("message", "啟用成功！")}
                else:
                    # 業務邏輯拒絕（例如序號不存在、已被使用），直接回傳無需重試
                    return {"success": False, "message": result.get("message", "序號驗證失敗")}

            except requests.exceptions.Timeout:
                last_err = "Google 伺服器回應較慢（冷啟動中），正在自動重試..."
                logger.warning(f"第 {attempt} 次請求連線逾時，準備重試...")
            except requests.exceptions.RequestException as e:
                last_err = f"網路連線失敗: {str(e)}"
                logger.warning(f"第 {attempt} 次請求異常: {e}")
            except Exception as e:
                last_err = f"系統錯誤: {str(e)}"
                logger.error(f"核銷過程異常: {e}")
                break

        return {"success": False, "message": f"驗證逾時: {last_err}，請稍候 3 秒後再次點擊啟用！"}

    def get_status(self) -> Dict[str, Any]:
        """回傳當前授權狀態與機器碼"""
        return {
            "is_activated": self._is_active or self.verify_local_license(),
            "machine_id": self.machine_id,
            "key": self._license_info.get("key", ""),
            "activated_at": self._license_info.get("activated_at", "")
        }
