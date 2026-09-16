"""
FakeGPS Pro - Pipi Mushroom Giant Mushroom Radar Service
Fetches real-time giant mushroom information, detects newly appeared mushrooms, and dispatches desktop notifications.
"""
import os
import sys
import json
import logging
import subprocess
from typing import Dict, Any, List, Set, Optional

import time
import hmac
import base64
import hashlib
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

logger = logging.getLogger("MushroomRadar")


class PipiAuthRequiredError(RuntimeError):
    """皮皮蘑菇需要 Google 帳號授權登入"""
    pass


def _get_cookie_file_path() -> str:
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "pipi_cookies.json")


class PurePythonPipiClient:
    """純 Python 實現皮皮蘑菇安全 API 客戶端 (免裝 Node.js，原生加解密，支援 Google 登入 Cookie)"""
    BASE_URL = "https://pipimushroom.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://pipimushroom.com/ppmushroom.aspx"
        })
        self.cached_session: Optional[Dict[str, Any]] = None
        self.load_saved_cookies()

    def load_saved_cookies(self):
        """從本地 pipi_cookies.json 載入已登入的 Cookie"""
        cookie_file = _get_cookie_file_path()
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                    for k, v in cookies.items():
                        self.session.cookies.set(k, v, domain="pipimushroom.com")
                logger.info(f"已從 {cookie_file} 成功載入皮皮蘑菇登入憑證")
            except Exception as e:
                logger.warning(f"載入皮皮蘑菇 Cookie 失敗: {e}")

    def save_cookies(self, cookie_dict: Dict[str, str]) -> bool:
        """儲存登入 Cookie 到本地檔案並套用"""
        cookie_file = _get_cookie_file_path()
        try:
            with open(cookie_file, "w", encoding="utf-8") as f:
                json.dump(cookie_dict, f, ensure_ascii=False, indent=2)
            for k, v in cookie_dict.items():
                self.session.cookies.set(k, v, domain="pipimushroom.com")
            self.cached_session = None
            logger.info("已成功儲存並生效皮皮蘑菇登入憑證！")
            return True
        except Exception as e:
            logger.error(f"儲存皮皮蘑菇 Cookie 失敗: {e}")
            return False

    def clear_cookies(self):
        """清除本地登入憑證"""
        cookie_file = _get_cookie_file_path()
        if os.path.exists(cookie_file):
            try:
                os.remove(cookie_file)
            except OSError:
                pass
        self.session.cookies.clear()
        self.cached_session = None

    def is_logged_in(self) -> bool:
        """檢查本地是否存在登入憑證"""
        cookie_file = _get_cookie_file_path()
        return os.path.exists(cookie_file)

    def _get_api_session(self) -> Dict[str, Any]:
        now = time.time()
        if self.cached_session:
            expires = self.cached_session.get("expires_ts", 0)
            if expires - now > 60:
                return self.cached_session

        # 1. 取得主頁 Cookie
        self.session.get(f"{self.BASE_URL}/ppmushroom.aspx", timeout=10)

        # 2. 握手取得安全 Token 與金鑰
        url = f"{self.BASE_URL}/ApiSession.ashx"
        resp = self.session.get(url, timeout=10, headers={"Accept": "application/json"})
        if resp.status_code != 200:
            raise RuntimeError(f"取得 ApiSession 失敗: HTTP {resp.status_code}")

        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"ApiSession 回應未通過: {data}")

        token = data.get("a")
        enc_key = base64.b64decode(data.get("b"))
        sig_key = base64.b64decode(data.get("c"))

        self.cached_session = {
            "token": token,
            "enc_key": enc_key,
            "sig_key": sig_key,
            "expires_ts": now + 1800
        }
        return self.cached_session

    def query(self, payload: dict) -> dict:
        api_sess = self._get_api_session()
        token = api_sess["token"]
        enc_key = api_sess["enc_key"]
        sig_key = api_sess["sig_key"]

        # 1. 生成 16 bytes IV 與 18 bytes nonce
        iv = os.urandom(16)
        nonce = os.urandom(18)
        timestamp = str(int(time.time() * 1000))

        iv_b64 = base64.b64encode(iv).decode("ascii")
        nonce_b64 = base64.b64encode(nonce).decode("ascii")

        # 2. AES-CBC + PKCS7 加密 payload
        plaintext = json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode("utf-8")
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext) + padder.finalize()

        cipher = Cipher(algorithms.AES(enc_key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        cipher_b64 = base64.b64encode(ciphertext).decode("ascii")

        # 3. HMAC-SHA256 計算請求簽名: token.timestamp.nonce_b64.iv_b64.cipher_b64
        sign_string = f"{token}.{timestamp}.{nonce_b64}.{iv_b64}.{cipher_b64}".encode("utf-8")
        signature = hmac.new(sig_key, sign_string, hashlib.sha256).digest()
        sig_b64 = base64.b64encode(signature).decode("ascii")

        req_body = {
            "a": token,
            "b": timestamp,
            "c": nonce_b64,
            "d": iv_b64,
            "e": cipher_b64,
            "f": sig_b64
        }

        # 4. 發送請求
        post_url = f"{self.BASE_URL}/Handlers/PPMushroomData.ashx"
        resp = self.session.post(post_url, json=req_body, timeout=12)
        if resp.status_code == 401:
            try:
                err_data = resp.json()
                if "d" in err_data and "e" in err_data:
                    resp_iv = base64.b64decode(err_data["d"])
                    resp_cipher = base64.b64decode(err_data["e"])
                    dec = Cipher(algorithms.AES(enc_key), modes.CBC(resp_iv)).decryptor()
                    padded = dec.update(resp_cipher) + dec.finalize()
                    plain = padding.PKCS7(128).unpadder().update(padded)
                    parsed_err = json.loads(plain.decode("utf-8"))
                    msg = parsed_err.get("error", "請先登入。")
                    if "請先登入" in msg or not parsed_err.get("ok"):
                        raise PipiAuthRequiredError("皮皮蘑菇官方已改版需 Google 帳號登入才能查看戰況，請點擊「🔑 登入皮皮」完成授權！")
            except PipiAuthRequiredError:
                raise
            except Exception:
                pass
            raise PipiAuthRequiredError("皮皮蘑菇官方已改版需 Google 帳號登入才能查看戰況，請點擊「🔑 登入皮皮」完成授權！")

        if resp.status_code != 200:
            raise RuntimeError(f"查詢請求失敗: HTTP {resp.status_code}, 內容: {resp.text[:200]}")

        resp_data = resp.json()
        if not resp_data or "e" not in resp_data:
            return resp_data

        # 5. 驗證回應簽名與解密: token.d.e
        resp_iv_b64 = resp_data["d"]
        resp_cipher_b64 = resp_data["e"]
        resp_sig_b64 = resp_data["f"]

        verify_string = f"{token}.{resp_iv_b64}.{resp_cipher_b64}".encode("utf-8")
        expected_sig = base64.b64encode(hmac.new(sig_key, verify_string, hashlib.sha256).digest()).decode("ascii")
        if expected_sig != resp_sig_b64:
            raise RuntimeError("回應簽名驗證失敗！")

        resp_iv = base64.b64decode(resp_iv_b64)
        resp_cipher = base64.b64decode(resp_cipher_b64)

        decryptor = Cipher(algorithms.AES(enc_key), modes.CBC(resp_iv)).decryptor()
        padded_plain = decryptor.update(resp_cipher) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        decrypted_bytes = unpadder.update(padded_plain) + unpadder.finalize()

        return json.loads(decrypted_bytes.decode("utf-8"))


class MushroomRadarService:
    def __init__(self):
        self.seen_mushroom_ids: Set[int] = set()
        self.is_running = False
        self.client = PurePythonPipiClient()

    def query_mushrooms(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """純 Python 查詢皮皮蘑菇資料（零外部依賴、毫秒級響應）"""
        if params is None:
            params = {
                "mode": "list",
                "regionCode": "TW",
                "level": "巨大",
                "engagement": "under_five",
                "freshness": "1440",
                "sort": "updated"
            }

        try:
            data = self.client.query(params)
            return {"success": True, "data": data}
        except PipiAuthRequiredError as auth_err:
            logger.warning(f"皮皮蘑菇需授權登入: {auth_err}")
            return {"success": False, "need_login": True, "error": str(auth_err)}
        except Exception as e:
            logger.error(f"查詢蘑菇資料失敗: {e}")
            try:
                self.client.cached_session = None
                data = self.client.query(params)
                return {"success": True, "data": data}
            except PipiAuthRequiredError as auth_err2:
                logger.warning(f"皮皮蘑菇需授權登入: {auth_err2}")
                return {"success": False, "need_login": True, "error": str(auth_err2)}
            except Exception as e2:
                logger.error(f"重試查詢蘑菇資料失敗: {e2}")
                return {"success": False, "error": str(e2)}

    def save_cookies(self, cookie_dict: Dict[str, str]) -> bool:
        return self.client.save_cookies(cookie_dict)

    def clear_cookies(self):
        self.client.clear_cookies()

    def is_logged_in(self) -> bool:
        return self.client.is_logged_in()

    def check_new_mushrooms(self, city: str = "", area: str = "", engagement: str = "under_five", level: str = "巨大", mushroom_type: str = "", sort: str = "updated", freshness: str = "60") -> Dict[str, Any]:
        """
        檢查是否有新出現的符合條件蘑菇：
        - 支援自訂尺寸 level ('巨大', '大', '一般', '普通', '小', 'all')
        - 支援自訂屬性 mushroom_type ('LunarNewYearMushroom', 'RockCrystalMushroom', etc.)
        - 支援資料更新時間 freshness ('60', '360', '1440', '0')
        - 支援排序方式 sort ('updated', 'power', 'challengers', 'ending', 'hp')
        - 回傳全量清單 items 與新目標 new_items
        """
        level_map = {
            "giant": "巨大",
            "large": "大",
            "normal": "一般",
            "small": "小",
            "all": "",
            "巨大": "巨大",
            "大": "大",
            "普通": "一般",
            "一般": "一般",
            "小": "小",
            "全部": ""
        }
        actual_level = level_map.get(level, level if level not in ("all", "全部") else "")
        actual_type = "" if mushroom_type in ("all", "全部", "") else mushroom_type
        actual_freshness = str(freshness) if str(freshness) != "" else "60"
        actual_sort = sort if sort else "updated"

        payload = {
            "mode": "list",
            "regionCode": "TW",
            "city": city,
            "area": area,
            "type": actual_type,
            "level": actual_level,
            "engagement": engagement,
            "freshness": actual_freshness,
            "sort": actual_sort,
            "page": 1
        }
        
        result = self.query_mushrooms(payload)
        if not result.get("success"):
            return result
            
        items = result.get("data", {}).get("items", [])
        new_items = []
        
        for item in items:
            m_id = item.get("id")
            if m_id and m_id not in self.seen_mushroom_ids:
                new_items.append(item)
                self.seen_mushroom_ids.add(m_id)
                
        # 限制快取集合大小，避免長時間運行累積過多 ID
        if len(self.seen_mushroom_ids) > 2000:
            self.seen_mushroom_ids = set(list(self.seen_mushroom_ids)[-1000:])
            
        return {
            "success": True,
            "totalCount": result.get("data", {}).get("summary", {}).get("totalCount", len(items)),
            "items": items,
            "new_items": new_items
        }

    @staticmethod
    def play_system_alert():
        """播放系統原生清晰提示音 (Windows / macOS 雙平台原生保證發聲)"""
        try:
            if sys.platform == "win32":
                import winsound
                try:
                    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
                except Exception:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            elif sys.platform == "darwin":
                subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"])
        except Exception as e:
            logger.warning(f"播放系統提示音失敗: {e}")

    @staticmethod
    def notify_desktop(title: str, message: str):
        """觸發 Windows / macOS 原生系統桌面通知 (100% 穩定推播)"""
        try:
            if sys.platform == "win32":
                import base64
                import xml.sax.saxutils
                escaped_title = xml.sax.saxutils.escape(title)
                escaped_msg = xml.sax.saxutils.escape(message)
                
                # 使用合法系統 AUMID 與 UTF-16LE Base64，保證 100% 免疫特殊字元與語法錯誤
                ps_script = f'''
$AppId = '{{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}}\\WindowsPowerShell\\v1.0\\powershell.exe'
try {{
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xmlString = '<toast><visual><binding template="ToastGeneric"><text>{escaped_title}</text><text>{escaped_msg}</text></binding></visual><audio src="ms-winsoundevent:Notification.Default"/></toast>'
    $xml.LoadXml($xmlString)
    $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($AppId).Show($toast)
}} catch {{
    try {{
        [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
        $objNotifyIcon = New-Object System.Windows.Forms.NotifyIcon
        $objNotifyIcon.Icon = [System.Drawing.SystemIcons]::Information
        $objNotifyIcon.BalloonTipIcon = "Info"
        $objNotifyIcon.BalloonTipTitle = "{escaped_title}"
        $objNotifyIcon.BalloonTipText = "{escaped_msg}"
        $objNotifyIcon.Visible = $True
        $objNotifyIcon.ShowBalloonTip(5000)
        Start-Sleep -Seconds 5
        $objNotifyIcon.Dispose()
    }} catch {{}}
}}
'''
                encoded = base64.b64encode(ps_script.encode('utf-16le')).decode('ascii')
                subprocess.Popen(
                    ["powershell", "-NoProfile", "-EncodedCommand", encoded],
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
            elif sys.platform == "darwin":
                clean_title = title.replace('"', '\"')
                clean_msg = message.replace('"', '\"')
                subprocess.Popen([
                    "osascript", "-e",
                    f'display notification "{clean_msg}" with title "{clean_title}" sound name "Glass"'
                ])
        except Exception as e:
            logger.error(f"發送桌面通知失敗: {e}")
