"""
Unit tests for FakeGPS Movement Engine & Math
"""
import unittest
import time
from core.mover import (
    haversine_distance,
    calculate_bearing,
    move_coordinate,
    get_cooldown_seconds,
    MovementEngine
)

class TestMovementEngine(unittest.TestCase):
    def test_distance_and_bearing(self):
        # 台北 101 到 台北車站 (約 5.6 km)
        lat1, lon1 = 25.033964, 121.564468 # 台北101
        lat2, lon2 = 25.047781, 121.517042 # 台北車站

        dist = haversine_distance(lat1, lon1, lat2, lon2)
        self.assertAlmostEqual(dist / 1000.0, 5.0, delta=1.5) # 大約 5.0 ~ 5.5 km

        bearing = calculate_bearing(lat1, lon1, lat2, lon2)
        # 台北101 在東南，台北車站在西北，角度應在 270~360 之間 (西北)
        self.assertTrue(270 <= bearing <= 360, f"Bearing was {bearing}")

    def test_move_coordinate(self):
        # 往北移動 1000 公尺 (bearing = 0)
        lat, lon = 25.000000, 121.000000
        new_lat, new_lon = move_coordinate(lat, lon, 1000.0, 0.0)

        # 緯度應該增加 (北半球往北)，經度幾乎不變
        self.assertGreater(new_lat, lat)
        self.assertAlmostEqual(new_lon, lon, places=4)

        # 計算反向距離確認大約 1000 公尺
        calc_dist = haversine_distance(lat, lon, new_lat, new_lon)
        self.assertAlmostEqual(calc_dist, 1000.0, delta=1.0)

    def test_cooldown_calculation(self):
        self.assertEqual(get_cooldown_seconds(500), 10)
        self.assertEqual(get_cooldown_seconds(3000), 120)
        self.assertEqual(get_cooldown_seconds(20000), 660)
        self.assertEqual(get_cooldown_seconds(1500000), 7200)

    def test_movement_engine_joystick(self):
        updates = []
        def on_update(lat, lon):
            updates.append((lat, lon))

        engine = MovementEngine(on_update)
        engine.set_current_position(25.0, 121.0)

        # 啟動搖桿移動 (往北, 速度 36km/h = 10m/s)
        engine.update_joystick(heading_deg=0.0, speed_kmh=36.0, active=True)
        time.sleep(0.8) # 讓它在背景運算約 2~3 個 step
        engine.stop_all()

        self.assertGreater(len(updates), 0, "應收到座標更新 callback")
        final_lat, final_lon = engine.get_current_position()
        self.assertGreater(final_lat, 25.0, "緯度應往北增加")

if __name__ == "__main__":
    unittest.main()
