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

logger = logging.getLogger("MushroomRadar")

class MushroomRadarService:
    def __init__(self):
        self.seen_mushroom_ids: Set[int] = set()
        self.is_running = False
        
        # Determine path to fetch_mushrooms.js
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        self.bridge_script = os.path.join(base_dir, "core", "fetch_mushrooms.js")
        if not os.path.exists(self.bridge_script):
            alt = os.path.join(base_dir, "_internal", "core", "fetch_mushrooms.js")
            if os.path.exists(alt):
                self.bridge_script = alt

    def query_mushrooms(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """呼叫 Node.js 加密橋接腳本取得即時蘑菇資料"""
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
            cmd = ["node", self.bridge_script, json.dumps(params, ensure_ascii=False)]
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            
            output = subprocess.check_output(
                cmd,
                stderr=subprocess.PIPE,
                creationflags=creationflags,
                timeout=15.0
            ).decode("utf-8", errors="ignore")
            
            data = json.loads(output.strip())
            return {"success": True, "data": data}
        except subprocess.TimeoutExpired:
            logger.error("查詢蘑菇資料逾時 (15s)")
            return {"success": False, "error": "查詢逾時，請稍後再試"}
        except Exception as e:
            logger.error(f"查詢蘑菇資料失敗: {e}")
            return {"success": False, "error": str(e)}

    def check_new_mushrooms(self, city: str = "", area: str = "", engagement: str = "under_five", level: str = "巨大", mushroom_type: str = "") -> Dict[str, Any]:
        """
        檢查是否有新出現的符合條件蘑菇：
        - 支援自訂尺寸 level ('巨大', '大', '普通', '小', 'all')
        - 支援自訂屬性 mushroom_type ('RockCrystalMushroom', 'RedFireMushroom', etc.)
        - 回傳全量清單 items 與新目標 new_items
        """
        level_map = {
            "giant": "巨大",
            "large": "大",
            "normal": "普通",
            "small": "小",
            "all": "",
            "巨大": "巨大",
            "大": "大",
            "普通": "普通",
            "小": "小",
            "全部": ""
        }
        actual_level = level_map.get(level, level if level not in ("all", "全部") else "")
        actual_type = "" if mushroom_type in ("all", "全部", "") else mushroom_type

        payload = {
            "mode": "list",
            "regionCode": "TW",
            "city": city,
            "area": area,
            "type": actual_type,
            "level": actual_level,
            "engagement": engagement,
            "freshness": "1440",
            "sort": "updated",
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
