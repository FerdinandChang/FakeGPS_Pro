"""
FakeGPS Pro - Main Desktop Application
Integrates PyWebView with iOS Location Service & Movement Engine.
"""
import os
import sys

# 攔截並防禦 PyInstaller 環境下 importlib.metadata.PackageNotFoundError
try:
    import importlib.metadata as _meta
    _orig_version = _meta.version
    _orig_dist = _meta.distribution

    def _safe_version(name: str):
        try:
            return _orig_version(name)
        except Exception:
            return "0.8.8"

    class _MockDistribution:
        def __init__(self, name):
            self.version = "0.8.8"
            self.metadata = {"Version": "0.8.8", "Name": name}

    def _safe_distribution(name: str):
        try:
            return _orig_dist(name)
        except Exception:
            return _MockDistribution(name)

    _meta.version = _safe_version
    _meta.distribution = _safe_distribution
except Exception:
    pass

import webview
import requests
import logging
from typing import List, Dict, Any

from core.ios_service import IOSLocationService
from core.license_manager import LicenseManager
from core.mover import (
    MovementEngine,
    haversine_distance,
    get_cooldown_seconds
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FakeGPS_Main")

class JsApi:
    """暴露給前端 JavaScript 呼叫的 API"""
    def __init__(self, window_holder, ios_service: IOSLocationService, mover: MovementEngine, license_mgr: LicenseManager):
        self.window_holder = window_holder
        self.ios_service = ios_service
        self.mover = mover
        self.license_mgr = license_mgr
        self.current_speed_kmh = 3.6

    def check_license(self) -> Dict[str, Any]:
        """檢查授權狀態與機器碼"""
        return self.license_mgr.get_status()

    def activate_license(self, serial_key: str) -> Dict[str, Any]:
        """提交序號進行雲端啟用核銷"""
        return self.license_mgr.activate_cloud_key(serial_key)

    def get_devices(self) -> List[Dict[str, str]]:
        """取得已連接的 iOS 裝置清單"""
        return self.ios_service.list_devices()

    def enable_developer_mode(self, serial: str = None) -> Dict[str, Any]:
        """透過 AMFI 服務強制讓 iPhone 顯示並嘗試開啟開發者模式"""
        return self.ios_service.enable_developer_mode(serial)

    def connect_device(self, serial: str) -> Dict[str, Any]:
        """連線指定裝置"""
        # 授權檢查防禦
        if not self.license_mgr.get_status().get("is_activated"):
            return {"success": False, "message": "軟體尚未啟用，請先輸入序號完成啟用！"}

        res = self.ios_service.connect(serial)
        if res.get("success"):
            # 若已有先前的座標，更新至手機
            cur_pos = self.mover.get_current_position()
            if cur_pos:
                self.ios_service.set_location(cur_pos[0], cur_pos[1])
            else:
                # 預設台北 101
                self.mover.set_current_position(25.033964, 121.564468)
                self.ios_service.set_location(25.033964, 121.564468)
        return res

    def teleport(self, lat: float, lon: float) -> Dict[str, Any]:
        """瞬間移動"""
        cur_pos = self.mover.get_current_position()
        dist_m = 0.0
        cooldown_sec = 0
        if cur_pos:
            dist_m = haversine_distance(cur_pos[0], cur_pos[1], lat, lon)
            cooldown_sec = get_cooldown_seconds(dist_m)

        self.mover.stop_all()
        self.mover.set_current_position(lat, lon)
        success = self.ios_service.set_location(lat, lon)

        return {
            "success": success,
            "message": "定位已成功覆蓋" if success else "裝置未連線或發送失敗",
            "distance_km": dist_m / 1000.0,
            "cooldown_sec": cooldown_sec
        }

    def calculate_distance_and_cooldown(self, lat1: float, lon1: float, lat2: float, lon2: float) -> Dict[str, Any]:
        """計算兩點距離與建議冷卻時間"""
        dist_m = haversine_distance(lat1, lon1, lat2, lon2)
        cooldown_sec = get_cooldown_seconds(dist_m)
        return {
            "distance_km": dist_m / 1000.0,
            "cooldown_sec": cooldown_sec
        }

    def set_speed(self, speed_kmh: float):
        """設定速度"""
        self.current_speed_kmh = speed_kmh

    def update_joystick(self, heading: float, active: bool):
        """更新搖桿狀態"""
        self.mover.update_joystick(heading, self.current_speed_kmh, active)

    def start_route(self, waypoints: List[List[float]], speed_kmh: float, loop: bool) -> Dict[str, Any]:
        """開始路線模擬"""
        pts = [(p[0], p[1]) for p in waypoints]
        self.mover.start_route(pts, speed_kmh, loop)
        return {"success": True}

    def stop_route(self) -> Dict[str, Any]:
        """停止路線模擬"""
        self.mover.stop_all()
        return {"success": True}

    def reset_gps(self) -> Dict[str, Any]:
        """清除模擬，還原真實 GPS"""
        self.mover.stop_all()
        ok = self.ios_service.clear_location()
        return {
            "success": ok,
            "message": "已成功還原真實 GPS！" if ok else "還原失敗或尚未連線"
        }

    def search_place(self, query: str) -> Dict[str, Any]:
        """透過 OpenStreetMap Nominatim 搜尋地名或地址"""
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": query,
                "format": "json",
                "limit": 5,
                "accept-language": "zh-TW,zh,en"
            }
            headers = {"User-Agent": "FakeGPSProDesktopApp/1.0"}
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for item in data:
                    results.append({
                        "name": item.get("display_name"),
                        "lat": float(item.get("lat")),
                        "lon": float(item.get("lon"))
                    })
                return {"success": True, "results": results}
        except Exception as e:
            logger.error(f"地名搜尋失敗: {e}")
        return {"success": False, "results": []}

    def open_manual(self) -> bool:
        """開啟本地使用手冊 HTML 檔案"""
        import webbrowser
        try:
            if getattr(sys, 'frozen', False):
                base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
            manual_path = os.path.join(base_dir, "manual.html")
            if not os.path.exists(manual_path):
                alt = os.path.join(base_dir, "_internal", "manual.html")
                if os.path.exists(alt):
                    manual_path = alt
            webbrowser.open(f"file:///{manual_path}")
            return True
        except Exception as e:
            logger.error(f"開啟手冊失敗: {e}")
            return False

    def open_url(self, url: str) -> bool:
        """使用系統預設瀏覽器開啟外部網頁"""
        import webbrowser
        try:
            webbrowser.open(url)
            return True
        except Exception as e:
            logger.error(f"開啟瀏覽器失敗: {e}")
            return False


def main():
    ios_service = IOSLocationService()
    window_container = []

    def on_location_updated(lat: float, lon: float):
        # 1. 寫入 iOS 設備
        ios_service.set_location(lat, lon)
        # 2. 同步回傳前端視窗更新地圖標記
        if window_container and window_container[0]:
            try:
                window_container[0].evaluate_js(f"window.updateCurrentLocation({lat:.6f}, {lon:.6f});")
            except Exception:
                pass

    mover = MovementEngine(location_callback=on_location_updated)
    mover.set_current_position(25.033964, 121.564468)

    license_mgr = LicenseManager()
    api = JsApi(window_container, ios_service, mover, license_mgr)

    # 取得 GUI 網頁路徑 (自動相容 PyInstaller 打包環境)
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    gui_path = os.path.join(base_dir, "gui", "index.html")
    if not os.path.exists(gui_path):
        alt_path = os.path.join(base_dir, "_internal", "gui", "index.html")
        if os.path.exists(alt_path):
            gui_path = alt_path

    # 建立桌面視窗
    window = webview.create_window(
        title="FakeGPS Pro - iOS 定位修改與移動模擬器",
        url=gui_path,
        js_api=api,
        width=1180,
        height=780,
        min_size=(900, 600),
        resizable=True
    )
    window_container.append(window)

    try:
        webview.start(debug=True)
    finally:
        mover.stop_all()
        ios_service.disconnect()

if __name__ == "__main__":
    main()
