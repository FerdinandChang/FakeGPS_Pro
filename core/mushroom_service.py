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

    def check_new_mushrooms(self, city: str = "", area: str = "", engagement: str = "under_five") -> Dict[str, Any]:
        """
        檢查是否有新出現的未滿 5 人巨大蘑菇：
        - 回傳全量清單 items
        - 回傳新偵測到的目標 new_items（用於觸發音效與通知）
        """
        payload = {
            "mode": "list",
            "regionCode": "TW",
            "city": city,
            "area": area,
            "type": "",
            "level": "巨大",
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
    def notify_desktop(title: str, message: str):
        """觸發 Windows / macOS 原生系統通知"""
        try:
            if sys.platform == "win32":
                clean_title = title.replace('"', '`"').replace("'", "''")
                clean_msg = message.replace('"', '`"').replace("'", "''")
                ps_cmd = (
                    '[void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms"); '
                    '$objNotifyIcon = New-Object System.Windows.Forms.NotifyIcon; '
                    '$objNotifyIcon.Icon = [System.Drawing.SystemIcons]::Information; '
                    '$objNotifyIcon.BalloonTipIcon = "Info"; '
                    f'$objNotifyIcon.BalloonTipTitle = "{clean_title}"; '
                    f'$objNotifyIcon.BalloonTipText = "{clean_msg}"; '
                    '$objNotifyIcon.Visible = $True; '
                    '$objNotifyIcon.ShowBalloonTip(6000); '
                    'Start-Sleep -Seconds 1; '
                    '$objNotifyIcon.Dispose()'
                )
                subprocess.Popen(
                    ["powershell", "-NoProfile", "-Command", ps_cmd],
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
