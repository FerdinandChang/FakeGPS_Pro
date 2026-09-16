"""
FakeGPS Pro - Main Desktop Application
Integrates PyWebView with iOS Location Service & Movement Engine.
"""
import os
import sys

# -------------------------------------------------------------
# Windows Self-Unblock: 自動清除 Mark of the Web (Zone.Identifier)
# 徹底免除使用者手動解除鎖定，避免 .NET CLR (pythonnet) 無法載入 Python.Runtime.dll
# -------------------------------------------------------------
if sys.platform == "win32":
    try:
        app_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
        for root, _, files in os.walk(app_dir):
            for f in files:
                ads = os.path.join(root, f) + ":Zone.Identifier"
                if os.path.exists(ads):
                    try:
                        os.remove(ads)
                    except OSError:
                        pass
    except Exception:
        pass

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
from core.mushroom_service import MushroomRadarService
from core.updater import AutoUpdater
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
        self.mushroom_radar = MushroomRadarService()
        self.updater = AutoUpdater()
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

    def query_giant_mushrooms(self, city: str = "", area: str = "", engagement: str = "under_five", level: str = "巨大", mushroom_type: str = "", sort: str = "updated", freshness: str = "60") -> Dict[str, Any]:
        """查詢蘑菇即時資料（支援尺寸、屬性、參戰、排序與更新時間過濾）"""
        return self.mushroom_radar.check_new_mushrooms(city, area, engagement, level, mushroom_type, sort, freshness)

    def notify_desktop(self, title: str, message: str) -> bool:
        """觸發系統原生桌面通知"""
        self.mushroom_radar.notify_desktop(title, message)
        return True

    def play_system_alert(self) -> bool:
        """觸發系統原生提示音 (Windows/macOS)"""
        self.mushroom_radar.play_system_alert()
        return True

    def check_for_updates(self) -> Dict[str, Any]:
        """檢查線上 GitHub Releases 是否有新版本"""
        return self.updater.check_for_updates()

    def get_pipi_auth_status(self) -> Dict[str, Any]:
        """檢查皮皮蘑菇登入狀態"""
        return {"is_logged_in": self.mushroom_radar.is_logged_in()}

    def logout_pipi(self) -> Dict[str, Any]:
        """登出皮皮蘑菇並清除 Cookie"""
        self.mushroom_radar.clear_cookies()
        return {"success": True}

    def set_pipi_cookie_manual(self, cookie_str: str) -> Dict[str, Any]:
        """手動貼入 Cookie 字串"""
        try:
            cookie_dict = {}
            clean_str = cookie_str.strip()
            if clean_str.startswith("{") and clean_str.endswith("}"):
                cookie_dict = json.loads(clean_str)
            else:
                for item in clean_str.split(";"):
                    if "=" in item:
                        k, v = item.strip().split("=", 1)
                        cookie_dict[k.strip()] = v.strip()
            if not cookie_dict:
                return {"success": False, "message": "未解析到有效 Cookie"}
            
            ok = self.mushroom_radar.save_cookies(cookie_dict)
            return {"success": ok, "message": "Cookie 已成功儲存！" if ok else "儲存失敗"}
        except Exception as e:
            return {"success": False, "message": f"解析失敗: {e}"}

    def _safe_get_cookies_from_win(self, win) -> Dict[str, str]:
        """線程安全地從 pywebview 視窗取得 Cookie（不會造成死鎖）"""
        cookie_dict = {}
        if not win:
            return cookie_dict

        # 最優先：直接呼叫 BrowserView.get_cookies()
        # 這個方法內建 Invoke + Semaphore，任何執行緒都安全，且能取到 HttpOnly Cookie
        if sys.platform == "win32":
            try:
                import webview.platforms.winforms as wf
                inst = wf.BrowserView.instances.get(win.uid)
                if inst and hasattr(inst, 'get_cookies'):
                    cookies = inst.get_cookies() or []
                    for c in cookies:
                        name = getattr(c, 'name', None) or (c.get('name') if isinstance(c, dict) else None)
                        value = getattr(c, 'value', None) or (c.get('value') if isinstance(c, dict) else None)
                        if name and value:
                            cookie_dict[name] = value
                    if cookie_dict:
                        logger.info(f"BrowserView.get_cookies() 抓到 {len(cookie_dict)} 個: {list(cookie_dict.keys())}")
            except Exception as e:
                logger.debug(f"BrowserView.get_cookies() 失敗: {e}")

        # 備用：pywebview Window.get_cookies()（可能受 @_loaded_call 限制）
        if not cookie_dict:
            try:
                cookies = win.get_cookies() or []
                for c in cookies:
                    name = getattr(c, 'name', None) or (c.get('name') if isinstance(c, dict) else None)
                    value = getattr(c, 'value', None) or (c.get('value') if isinstance(c, dict) else None)
                    if name and value:
                        cookie_dict[name] = value
            except Exception as e:
                logger.debug(f"win.get_cookies() 失敗: {e}")

        return cookie_dict

    def get_pipi_cookies_from_main_win(self) -> Dict[str, Any]:
        """從主視窗 WebView2 抓取皮皮蘑菇 Cookie（所有 WebView2 共用 Cookie 儲存）"""
        if not (self.window_holder and self.window_holder[0]):
            return {"success": False, "error": "主視窗未就緒"}

        main_win = self.window_holder[0]
        cookie_dict = self._safe_get_cookies_from_win(main_win)

        logger.info(f"主視窗抓取到的 Cookie: {list(cookie_dict.keys())}")

        if not cookie_dict:
            return {"success": False, "error": "未抓到任何 Cookie，請確認已在登入視窗完成 Google 授權"}

        has_auth = "ASP.NET_SessionId" in cookie_dict or "pm_site_session" in cookie_dict
        if not has_auth:
            return {"success": False, "error": f"未找到認證 Cookie (抓到: {list(cookie_dict.keys())})，請先完成 Google 登入"}

        self.mushroom_radar.save_cookies(cookie_dict)
        test_res = self.mushroom_radar.query_mushrooms({"mode": "list", "page": 1})
        if test_res.get("success"):
            return {"success": True, "message": f"登入成功！抓到 {len(cookie_dict)} 個 Cookie"}
        else:
            return {"success": False, "error": test_res.get("error", "Cookie 已儲存但 API 驗證失敗")}

    def open_pipi_login(self) -> Dict[str, Any]:
        """開啟內嵌視窗進行 Google 授權登入皮皮蘑菇"""
        login_url = "https://pipimushroom.com/login.aspx?ReturnUrl=ppmushroom.aspx"
        try:
            if hasattr(self, '_login_win') and self._login_win:
                try:
                    self._login_win.destroy()
                except Exception:
                    pass
                self._login_win = None

            login_win = webview.create_window(
                title="登入皮皮蘑菇 (Google 帳號授權)",
                url=login_url,
                width=540,
                height=700,
                min_size=(450, 600),
                resizable=True,
                confirm_close=False
            )
            self._login_win = login_win

            import threading
            import time
            def _monitor():
                for _ in range(300):
                    time.sleep(1.5)
                    try:
                        if not hasattr(self, '_login_win') or not self._login_win:
                            break

                        cur_url = ""
                        try:
                            cur_url = login_win.get_current_url() or ""
                        except Exception:
                            pass

                        # 只在使用者明確已離開登入頁面後才嘗試抓取
                        is_on_pipi_site = (
                            "pipimushroom.com" in cur_url and
                            "login.aspx" not in cur_url and
                            "GoogleAuth.ashx" not in cur_url and
                            "accounts.google.com" not in cur_url
                        )

                        if is_on_pipi_site:
                            # 從登入視窗抓 Cookie（BrowserView.get_cookies 線程安全）
                            cookie_dict = self._safe_get_cookies_from_win(login_win)
                            if not cookie_dict:
                                # 備用：從主視窗抓（同一用戶資料目錄共用）
                                if self.window_holder and self.window_holder[0]:
                                    cookie_dict = self._safe_get_cookies_from_win(self.window_holder[0])

                            if cookie_dict:
                                self.mushroom_radar.save_cookies(cookie_dict)

                            test_res = self.mushroom_radar.query_mushrooms({"mode": "list", "page": 1})
                            if test_res.get("success"):
                                logger.info("驗證成功！已自動關閉登入視窗！")
                                if self.window_holder and self.window_holder[0]:
                                    try:
                                        self.window_holder[0].evaluate_js("if(window.onPipiLoginSuccess) window.onPipiLoginSuccess();")
                                    except Exception:
                                        pass
                                time.sleep(0.5)
                                try:
                                    login_win.destroy()
                                except Exception:
                                    pass
                                self._login_win = None
                                break
                    except Exception as e:
                        logger.warning(f"登入監聽異常: {e}")
                        continue

            t = threading.Thread(target=_monitor, daemon=True)
            t.start()
            return {"success": True, "message": "已開啟登入視窗"}
        except Exception as e:
            logger.error(f"開啟登入視窗失敗: {e}")
            return {"success": False, "message": f"開啟登入視窗失敗: {e}"}

    def confirm_pipi_login(self) -> Dict[str, Any]:
        """手動確認登入：從所有可用 WebView2 視窗抓取 Cookie 並驗證"""
        cookie_dict = {}

        # 1. 先試登入視窗
        if hasattr(self, '_login_win') and self._login_win:
            cookie_dict = self._safe_get_cookies_from_win(self._login_win)

        # 2. 不管登入視窗有沒有，再試主視窗（關鍵！WebView2 共用 Cookie 儲存）
        if self.window_holder and self.window_holder[0]:
            main_cookies = self._safe_get_cookies_from_win(self.window_holder[0])
            for k, v in main_cookies.items():
                if k not in cookie_dict:
                    cookie_dict[k] = v

        logger.info(f"confirm_pipi_login 抓到 Cookie: {list(cookie_dict.keys())}")

        if cookie_dict:
            self.mushroom_radar.save_cookies(cookie_dict)

        test_res = self.mushroom_radar.query_mushrooms({"mode": "list", "page": 1})
        if test_res.get("success"):
            if hasattr(self, '_login_win') and self._login_win:
                try:
                    self._login_win.destroy()
                except Exception:
                    pass
                self._login_win = None
            if self.window_holder and self.window_holder[0]:
                try:
                    self.window_holder[0].evaluate_js("if(window.onPipiLoginSuccess) window.onPipiLoginSuccess();")
                except Exception:
                    pass
            return {"success": True, "message": "登入成功！"}
        else:
            err = test_res.get("error", "驗證未通過")
            cookie_info = f"（已抓取 Cookie: {list(cookie_dict.keys()) if cookie_dict else '無'}）"
            return {"success": False, "message": f"{err} {cookie_info}"}

    def start_auto_update(self, download_url: str) -> Dict[str, Any]:
        """開始下載並套用線上自動更新"""
        def _on_progress(pct: int, msg: str):
            if self.window_holder and self.window_holder[0]:
                try:
                    clean_msg = msg.replace('"', '\\"').replace("'", "\\'")
                    self.window_holder[0].evaluate_js(f"window.onUpdateProgress({pct}, '{clean_msg}');")
                except Exception:
                    pass

        return self.updater.start_download_and_install(download_url, on_progress=_on_progress)


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
        webview.start(debug=False)
    finally:
        mover.stop_all()
        ios_service.disconnect()

if __name__ == "__main__":
    main()
