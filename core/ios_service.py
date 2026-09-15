"""
iOS Location Service Manager using pymobiledevice3
Supports iOS 15/16 Legacy DtSimulateLocation and iOS 17/18/26+ Userspace RSD Tunnel + DVT LocationSimulation.
Employs a dedicated background asyncio thread with threadsafe execution for 100% concurrency stability.
"""
import time
import random
import asyncio
import threading
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("iOSLocationService")

class IOSLocationService:
    def __init__(self):
        self.lockdown = None
        self.rsd = None
        self.dvt = None
        self.location_service = None
        self.current_device_info = None
        self.is_connected = False
        self.current_lat: Optional[float] = None
        self.current_lon: Optional[float] = None
        self._is_ios17_plus = False
        self.last_sent_time = 0.0
        self.last_connected_serial: Optional[str] = None
        
        # 建立執行緒安全互斥鎖，保證 DVT 通道與 USB Mux 傳輸絕不發生跨執行緒並發衝突
        self._io_lock = threading.Lock()

        # 建立獨立專屬的背景 Asyncio Event Loop 執行緒
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._start_loop, daemon=True, name="AsyncIOServiceWorker")
        self._thread.start()

        # 建立防彈回 (Anti-Rubberbanding) 常駐心跳保活守護執行緒
        self._heartbeat_stop = threading.Event()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True, name="LocationHeartbeatDaemon")
        self._heartbeat_thread.start()

    def _start_loop(self):
        """背景持續運行事件迴圈，處理所有 DTX 通道與網路封包"""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _run_async(self, coro, timeout: float = 20.0):
        """跨執行緒安全執行 async 協程"""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)

    def list_devices(self) -> List[Dict[str, str]]:
        """掃描 USB 連接的 iOS 裝置"""
        devices = []
        try:
            from pymobiledevice3.usbmux import list_devices
            raw_devices = self._run_async(list_devices(), timeout=5.0)
            for dev in raw_devices:
                serial = str(dev.serial)
                connection_type = str(getattr(dev, 'connection_type', 'USB'))
                devices.append({
                    "serial": serial,
                    "connection_type": connection_type,
                    "name": f"iPhone ({serial[:8]}...)",
                })
        except Exception as e:
            logger.error(f"掃描 USB 裝置失敗: {e}")
        return devices

    def connect(self, serial: Optional[str] = None) -> Dict[str, any]:
        """連線至指定的 iOS 裝置並啟動模擬定位服務"""
        with self._io_lock:
            try:
                from pymobiledevice3.lockdown import create_using_usbmux
                from pymobiledevice3.services.mobile_image_mounter import auto_mount
                from pymobiledevice3.exceptions import AlreadyMountedError, DeveloperModeIsNotEnabledError

                logger.info(f"正在連線裝置 (serial={serial})...")
                self.lockdown = self._run_async(create_using_usbmux(serial=serial))
                
                name = str(self.lockdown.display_name or "iPhone")
                version = str(self.lockdown.product_version or "Unknown")
                try:
                    model_raw = self._run_async(self.lockdown.get_value(key="ProductType"))
                    model = str(model_raw) if model_raw else "iPhone"
                except Exception:
                    model = "iPhone"

                self.current_device_info = {
                    "name": name,
                    "version": version,
                    "model": model,
                    "udid": str(self.lockdown.identifier),
                }
                logger.info(f"成功識別裝置: {name} (iOS {version}, {model})")

                # 檢查並掛載 Developer Disk Image (無論 iOS 15/16 還是 iOS 17/18 均需要掛載 DDI 才能啟動 dtservicehub)
                logger.info("正在檢查並掛載 Developer Disk Image (DDI)...")
                try:
                    self._run_async(auto_mount(self.lockdown), timeout=60.0)
                    logger.info("Developer Disk Image 掛載完成")
                except AlreadyMountedError:
                    logger.info("Developer Disk Image 已經掛載，直接使用")
                except DeveloperModeIsNotEnabledError:
                    raise RuntimeError("您的 iPhone 尚未開啟【開發者模式】！請在 iPhone 上前往「設定」→「隱私權與安全性」→「開發者模式」將其開啟，並重新開機確認。")
                except Exception as mount_err:
                    logger.warning(f"DDI 掛載提示: {mount_err}")

                # 判斷是否為 iOS 17+ (包括 iOS 17, 18, 26)
                major_ver = 0
                try:
                    major_ver = int(version.split(".")[0])
                except Exception:
                    major_ver = 17

                if major_ver >= 17:
                    self._is_ios17_plus = True
                    logger.info("檢測為 iOS 17+ 系統，正在建立 Userspace RSD Tunnel 通道...")
                    from pymobiledevice3.remote.userspace_tunnel import establish_userspace_rsd
                    from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
                    from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation

                    self.rsd = self._run_async(establish_userspace_rsd(serial=serial or self.lockdown.udid), timeout=30.0)
                    self.dvt = DvtProvider(self.rsd)
                    self.location_service = LocationSimulation(self.dvt)
                    
                    # 進入 DVT 服務連線
                    self._run_async(self.location_service.connect(), timeout=15.0)
                    logger.info("iOS 17+ DVT LocationSimulation 通道已成功建立！")
                else:
                    self._is_ios17_plus = False
                    from pymobiledevice3.services.simulate_location import DtSimulateLocation
                    self.location_service = DtSimulateLocation(self.lockdown)
                    logger.info("iOS Legacy SimulateLocation 服務已啟動")

                self.last_connected_serial = serial or getattr(self.lockdown, 'udid', None)
                self.is_connected = True
                return {
                    "success": True,
                    "device": self.current_device_info,
                    "message": "已成功連線並啟動定位服務"
                }

            except Exception as e:
                err_msg = str(e)
                logger.error(f"連線裝置失敗: {err_msg}")
                self.is_connected = False
                
                if "dtservicehub" in err_msg or "DeveloperMode" in err_msg or "開發者模式" in err_msg:
                    # 自動嘗試發送 AMFI 喚醒指令，強制讓 iPhone 設定現形
                    try:
                        from pymobiledevice3.services.amfi import AmfiService
                        if self.lockdown:
                            self._run_async(AmfiService(self.lockdown).reveal_developer_mode_option_in_ui(), timeout=5.0)
                            logger.info("已自動發送 AMFI 喚醒指令，強制讓 iPhone 設定中現形【開發者模式】！")
                    except Exception:
                        pass

                    user_friendly_msg = (
                        "連線失敗：iPhone 尚未開啟【開發者模式】。\n\n"
                        "已為您強制喚醒 iPhone 設定選單！請依照以下步驟啟用：\n"
                        "1. 打開 iPhone「設定」→「隱私權與安全性」\n"
                        "2. 滑到最底部，點選【開發者模式】（剛剛已強制讓它顯示）\n"
                        "3. 切換為「開啟」，並點選「重新啟動」手機\n"
                        "4. 重開機解鎖後點擊「開啟」並輸入螢幕密碼即完成！"
                    )
                elif "PasswordProtected" in err_msg or "Passcode" in err_msg or "Pairing" in err_msg or "Trust" in err_msg:
                    user_friendly_msg = "連線失敗：請解鎖 iPhone 螢幕，並在彈出的提示中點選「信任這部電腦」。"
                else:
                    user_friendly_msg = f"連線失敗: {err_msg}。請確認 iPhone 已解鎖並信任此電腦。"
                    
                return {
                    "success": False,
                    "message": user_friendly_msg
                }

    def enable_developer_mode(self, serial: Optional[str] = None) -> Dict[str, any]:
        """透過 Apple AMFI 服務強制讓 iPhone 顯示並嘗試啟用開發者模式"""
        try:
            from pymobiledevice3.lockdown import create_using_usbmux
            from pymobiledevice3.services.amfi import AmfiService
            from pymobiledevice3.exceptions import DeviceHasPasscodeSetError

            lockdown = self.lockdown
            if not lockdown:
                lockdown = self._run_async(create_using_usbmux(serial=serial), timeout=10.0)
                self.lockdown = lockdown

            # 檢查當前開發者模式狀態
            try:
                is_enabled = self._run_async(lockdown.get_developer_mode_status(), timeout=5.0)
                if is_enabled:
                    return {
                        "success": True,
                        "message": "iPhone 目前已經開啟開發者模式！"
                    }
            except Exception:
                pass

            amfi = AmfiService(lockdown)
            
            # 1. 強制讓 iPhone 設定介面顯示「開發者模式」選單
            self._run_async(amfi.reveal_developer_mode_option_in_ui(), timeout=5.0)
            logger.info("已成功發送 AMFI 喚醒指令：開發者模式選項已強制在 iPhone 設定中現形！")

            # 2. 嘗試發送啟用指令（若無密碼會直接重啟並啟用；若有密碼會提示需輸入密碼）
            try:
                self._run_async(amfi.enable_developer_mode(enable_post_restart=False), timeout=10.0)
                return {
                    "success": True,
                    "message": "已成功向 iPhone 發送啟用請求！手機即將自動重新開機，開機解鎖後請在畫面點選「開啟」即可完成。"
                }
            except DeviceHasPasscodeSetError:
                return {
                    "success": True,
                    "need_passcode": True,
                    "message": (
                        "已強制讓 iPhone 顯示【開發者模式】！\n\n"
                        "因為您的 iPhone 有設定螢幕解鎖密碼（Apple 硬體晶片級防護規定必須手動確認）：\n"
                        "請打開 iPhone「設定」→「隱私權與安全性」→ 滑到最底已出現【開發者模式】，點進去點選「開啟」並輸入手機密碼重開機即可！"
                    )
                }

        except Exception as e:
            logger.error(f"啟用開發者模式失敗: {e}")
            return {
                "success": False,
                "message": f"操作失敗: {str(e)}。請確認 iPhone 已解鎖螢幕並信任此電腦。"
            }

    def set_location(self, lat: float, lon: float) -> bool:
        """設定/覆蓋手機 GPS 座標"""
        if not self.is_connected or not self.location_service:
            logger.warning("未連線至定位服務，無法發送座標")
            return False

        with self._io_lock:
            if not self.is_connected or not self.location_service:
                return False
            try:
                flat = round(float(lat), 6)
                flon = round(float(lon), 6)
                self._run_async(self.location_service.set(flat, flon), timeout=10.0)
                self.current_lat = flat
                self.current_lon = flon
                self.last_sent_time = time.time()
                logger.info(f"已成功覆蓋 GPS 座標至: {flat:.6f}, {flon:.6f}")
                return True
            except Exception as e:
                logger.error(f"發送座標失敗: {e}")
                return False

    def clear_location(self) -> bool:
        """清除模擬定位，還原手機真實 GPS"""
        with self._io_lock:
            self.current_lat = None
            self.current_lon = None
            if not self.is_connected or not self.location_service:
                logger.warning("未連線至定位服務，無法還原座標")
                return False
            try:
                self._run_async(self.location_service.clear(), timeout=10.0)
                logger.info("已成功清除模擬定位，還原真實 GPS！")
                return True
            except Exception as e:
                logger.error(f"清除模擬定位失敗: {e}")
                return False

    def _heartbeat_loop(self):
        """
        防彈回/防跳回真實位置 (Anti-Rubberbanding) 常駐心跳守護執行緒：
        - 每隔 3 秒檢查一次，僅在閒置超過 5 秒時溫和補發當前座標維持 USB 活躍與 DVT channel 活絡；
        - 使用非阻塞鎖 (acquire(blocking=False))：主執行緒有動作（瞬移/秒飛/搖桿/循跡）時立即自動讓位，絕不搶佔通道；
        - 徹底移除背景 self.connect()，避免在通訊抖動時把正常連線打爛重置。
        """
        while not self._heartbeat_stop.is_set():
            time.sleep(3.0)
            if not self.is_connected or not self.location_service:
                continue
            if self.current_lat is None or self.current_lon is None:
                continue
            
            # 若距離上次主動發送尚未滿 5 秒，表示通道非常活躍，略過本次保活
            now = time.time()
            if now - self.last_sent_time < 5.0:
                continue

            # 使用非阻塞鎖：若使用者正在操作或移動，主動讓位絕不搶鎖
            if not self._io_lock.acquire(blocking=False):
                continue

            try:
                # 雙重檢查狀態，確保獲取鎖時仍處於連線中
                if self.is_connected and self.location_service and self.current_lat is not None and self.current_lon is not None:
                    self._run_async(self.location_service.set(self.current_lat, self.current_lon), timeout=10.0)
                    self.last_sent_time = time.time()
            except Exception as e:
                logger.warning(f"保活訊號維持提示: {e}")
            finally:
                self._io_lock.release()

    def disconnect(self):
        """斷開連線"""
        with self._io_lock:
            self.current_lat = None
            self.current_lon = None
            try:
                if self.location_service:
                    try:
                        self._run_async(self.location_service.clear(), timeout=3.0)
                    except Exception:
                        pass
                    if hasattr(self.location_service, 'close'):
                        try:
                            self._run_async(self.location_service.close(), timeout=3.0)
                        except Exception:
                            pass
                    self.location_service = None
                self.dvt = None
                self.rsd = None
                self.lockdown = None
                self.is_connected = False
                self.current_device_info = None
                logger.info("已中斷 iOS 裝置連線")
            except Exception as e:
                logger.error(f"斷開連線時發生錯誤: {e}")
