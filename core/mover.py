"""
Movement Engine for Joystick and Multi-point Route Simulation.
Calculates geodesic distance, bearings, waypoint interpolation, and manages background moving threads.
"""
import math
import random
import time
import threading
import logging
from typing import List, Tuple, Callable, Optional, Dict

logger = logging.getLogger("MovementEngine")

EARTH_RADIUS = 6378137.0  # WGS-84 赤道半徑 (公尺)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """計算兩點之間的大圓距離 (公尺)"""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS * c

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """計算從 (lat1, lon1) 到 (lat2, lon2) 的方位角 (0~360 度，0 為北)"""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - \
        math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360.0) % 360.0

def move_coordinate(lat: float, lon: float, distance_m: float, bearing_deg: float) -> Tuple[float, float]:
    """根據指定距離(公尺)與方位角(度)，計算目的地的新經緯度"""
    if distance_m <= 0:
        return lat, lon

    delta_sigma = distance_m / EARTH_RADIUS
    theta = math.radians(bearing_deg)
    phi1 = math.radians(lat)
    lambda1 = math.radians(lon)

    phi2 = math.asin(
        math.sin(phi1) * math.cos(delta_sigma) +
        math.cos(phi1) * math.sin(delta_sigma) * math.cos(theta)
    )
    lambda2 = lambda1 + math.atan2(
        math.sin(theta) * math.sin(delta_sigma) * math.cos(phi1),
        math.cos(delta_sigma) - math.sin(phi1) * math.sin(phi2)
    )

    new_lat = math.degrees(phi2)
    new_lon = math.degrees(lambda2)
    # 正規化經度至 -180 ~ 180
    new_lon = (new_lon + 540.0) % 360.0 - 180.0
    return new_lat, new_lon

def get_cooldown_seconds(distance_meters: float) -> int:
    """根據移動距離計算建議的冷卻時間 (秒) - 依據 Pokemon Go 冷卻標準"""
    dist_km = distance_meters / 1000.0
    if dist_km < 1.0:
        return 10
    elif dist_km < 5.0:
        return 120    # 2 mins
    elif dist_km < 10.0:
        return 360    # 6 mins
    elif dist_km < 25.0:
        return 660    # 11 mins
    elif dist_km < 50.0:
        return 1200   # 20 mins
    elif dist_km < 100.0:
        return 2100   # 35 mins
    elif dist_km < 250.0:
        return 2700   # 45 mins
    elif dist_km < 500.0:
        return 3900   # 65 mins
    elif dist_km < 750.0:
        return 5400   # 90 mins
    elif dist_km < 1000.0:
        return 6000   # 100 mins
    else:
        return 7200   # 120 mins (2 hours max)


class MovementEngine:
    def __init__(self, location_callback: Callable[[float, float], None]):
        self.location_callback = location_callback  # 呼叫 iOS service 的 callback
        self.current_lat: Optional[float] = None
        self.current_lon: Optional[float] = None

        # 狀態控制
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None

        # 搖桿狀態
        self.is_joystick_active = False
        self.joystick_heading = 0.0  # 度
        self.joystick_speed_kmh = 3.6  # 預設步行 3.6 km/h

        # 路線狀態
        self.is_route_active = False
        self.route_waypoints: List[Tuple[float, float]] = []
        self.route_loop = False
        self.route_speed_kmh = 10.0

    def set_current_position(self, lat: float, lon: float):
        """同步目前位置"""
        with self._lock:
            self.current_lat = lat
            self.current_lon = lon

    def get_current_position(self) -> Optional[Tuple[float, float]]:
        with self._lock:
            if self.current_lat is not None and self.current_lon is not None:
                return self.current_lat, self.current_lon
            return None

    # ==================== 搖桿控制 ====================

    def update_joystick(self, heading_deg: float, speed_kmh: float, active: bool = True):
        """更新搖桿方向與速度"""
        with self._lock:
            self.joystick_heading = heading_deg
            self.joystick_speed_kmh = max(0.1, speed_kmh)
            self.is_joystick_active = active

        if active and (self._worker_thread is None or not self._worker_thread.is_alive()):
            self._start_joystick_thread()

    def stop_joystick(self):
        """停止搖桿移動"""
        with self._lock:
            self.is_joystick_active = False

    def _start_joystick_thread(self):
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._joystick_loop, daemon=True)
        self._worker_thread.start()

    def _joystick_loop(self):
        """搖桿背景運算迴圈 (頻率 ~4Hz，即每 250ms 一次)"""
        interval = 0.25
        while not self._stop_event.is_set():
            with self._lock:
                active = self.is_joystick_active
                heading = self.joystick_heading
                speed_kmh = self.joystick_speed_kmh
                cur_lat = self.current_lat
                cur_lon = self.current_lon

            if not active:
                time.sleep(interval)
                continue

            if cur_lat is None or cur_lon is None:
                time.sleep(interval)
                continue

            # 速度換算為每秒公尺 (m/s)，加入微幅擬真抖動 (±3%)
            speed_mps = (speed_kmh / 3.6) * random.uniform(0.97, 1.03)
            step_distance = speed_mps * interval

            # 微幅角度擾動 (±1 度)
            step_heading = (heading + random.uniform(-1.0, 1.0)) % 360.0

            next_lat, next_lon = move_coordinate(cur_lat, cur_lon, step_distance, step_heading)
            
            with self._lock:
                self.current_lat = next_lat
                self.current_lon = next_lon

            # 發送給 iOS 設備
            try:
                self.location_callback(next_lat, next_lon)
            except Exception as e:
                logger.error(f"Callback 執行錯誤: {e}")

            if self._stop_event.wait(timeout=interval):
                break

    # ==================== 多點路線循跡 ====================

    def start_route(self, waypoints: List[Tuple[float, float]], speed_kmh: float, loop: bool = False):
        """開始沿指定多點路徑自動前進"""
        if len(waypoints) < 2:
            logger.warning("路徑點至少需要 2 個點")
            return

        self.stop_all()
        with self._lock:
            self.route_waypoints = waypoints
            self.route_speed_kmh = max(0.1, speed_kmh)
            self.route_loop = loop
            self.is_route_active = True
            # 起點
            self.current_lat, self.current_lon = waypoints[0]

        # 立即傳送起點
        self.location_callback(self.current_lat, self.current_lon)

        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._route_loop, daemon=True)
        self._worker_thread.start()

    def _route_loop(self):
        """路線循跡運算迴圈"""
        interval = 0.5  # 500ms 一次更新
        
        while not self._stop_event.is_set():
            with self._lock:
                waypoints = list(self.route_waypoints)
                loop = self.route_loop
                speed_kmh = self.route_speed_kmh

            if not waypoints or len(waypoints) < 2:
                break

            # 遍歷每條線段
            for i in range(len(waypoints) - 1):
                p_start = waypoints[i]
                p_end = waypoints[i + 1]

                cur_lat, cur_lon = p_start
                total_dist = haversine_distance(p_start[0], p_start[1], p_end[0], p_end[1])
                bearing = calculate_bearing(p_start[0], p_start[1], p_end[0], p_end[1])

                traveled_dist = 0.0

                while traveled_dist < total_dist:
                    if self._stop_event.is_set() or not self.is_route_active:
                        return

                    # 擬真速度與位移
                    speed_mps = (speed_kmh / 3.6) * random.uniform(0.96, 1.04)
                    step = speed_mps * interval
                    traveled_dist += step

                    if traveled_dist >= total_dist:
                        # 到達此路段終點
                        cur_lat, cur_lon = p_end
                    else:
                        cur_lat, cur_lon = move_coordinate(cur_lat, cur_lon, step, bearing)

                    with self._lock:
                        self.current_lat = cur_lat
                        self.current_lon = cur_lon

                    self.location_callback(cur_lat, cur_lon)
                    if self._stop_event.wait(timeout=interval):
                        return

            # 一輪結束，若未開啟循環則停止
            if not loop:
                with self._lock:
                    self.is_route_active = False
                logger.info("路線導航完成")
                break
            else:
                # 循環：若循環開啟，稍微停頓 2 秒後再反向或從頭開始
                if self._stop_event.wait(timeout=2.0):
                    return

    def stop_all(self):
        """停止所有移動任務"""
        self._stop_event.set()
        with self._lock:
            self.is_joystick_active = False
            self.is_route_active = False
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
