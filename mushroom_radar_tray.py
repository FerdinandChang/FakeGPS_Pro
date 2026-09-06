"""
FakeGPS Pro - 巨大蘑菇獨立桌面背景監控小工具 (Option 3)
可在 FakeGPS Pro 關閉時獨立運行於背景，定時輪詢皮皮蘑菇資料庫，
一發現未滿 5 人的巨大蘑菇立即發出桌面氣泡通知與聲音提示。
"""
import os
import sys
import time
import json
import logging
from datetime import datetime

# 強制 UTF-8 輸出
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 設定根目錄
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.mushroom_service import MushroomRadarService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("RadarTray")

def play_alert_sound():
    try:
        if sys.platform == "win32":
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        else:
            print("\a", end="", flush=True)
    except Exception:
        pass

def main():
    print("=" * 60)
    print("       🍄 FakeGPS Pro - 巨大蘑菇獨立桌面背景雷達")
    print("=" * 60)
    print("  監控條件：全台灣・未滿 5 人 (可直接參戰)・巨大蘑菇")
    print("  檢查間隔：每 30 秒自動刷新")
    print("  通知方式：Windows 桌面系統彈窗 + 提示音效")
    print("  結束方式：按下 Ctrl + C 隨時結束程式")
    print("=" * 60)
    print()

    radar = MushroomRadarService()
    interval_seconds = 30
    check_round = 1

    # 首次啟動播放一次確認音
    play_alert_sound()

    try:
        while True:
            now_str = datetime.now().strftime("%H:%M:%S")
            print(f"[{now_str}] 第 {check_round} 次掃描巨大蘑菇資料庫...", end="", flush=True)

            res = radar.check_new_mushrooms(city="", area="", engagement="under_five")
            if res.get("success"):
                items = res.get("items", [])
                new_items = res.get("new_items", [])
                print(f" [完成] 目前共 {len(items)} 顆在線，新發現 {len(new_items)} 顆！")

                # 如果有新發現的巨大蘑菇
                if new_items:
                    play_alert_sound()
                    for m in new_items:
                        place = m.get("place", "未知地標")
                        city_area = f"{m.get('city', '')} {m.get('area', '')}".strip()
                        type_name = m.get("typeName", "巨大蘑菇")
                        count = m.get("challengerCount", 0)
                        lat = m.get("lat", 0)
                        lng = m.get("lng", 0)

                        print(f"  🔥 【新巨大菇】[{city_area}] {type_name} ({place}) | 人數: {count}/5 | 座標: {lat}, {lng}")

                    first = new_items[0]
                    title = f"🍄 發現 {len(new_items)} 顆未滿 5 人巨大蘑菇！"
                    body = f"[{first.get('city', '')} {first.get('area', '')}] {first.get('typeName', '')} ({first.get('place', '')}) 人數: {first.get('challengerCount', 0)}/5"
                    radar.notify_desktop(title, body)
            else:
                print(f" [失敗: {res.get('error', '未知錯誤')}]")

            check_round += 1
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\n[系統] 巨大蘑菇監控程式已正常停止。")

if __name__ == "__main__":
    main()
