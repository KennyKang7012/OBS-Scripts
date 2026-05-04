#!/usr/bin/env python3

# ============================================================
#  OBS 自動停止錄製計時器（WebSocket 版）
#
#  【模式一】互動模式：
#    python3 stop_obs_timer.py
#
#  【模式二】參數模式（供 Cowork 使用）：
#    python3 stop_obs_timer.py 2 30    # 2 小時 30 分鐘
#    python3 stop_obs_timer.py 3 0     # 3 小時整
#
#  需求：pip install websocket-client
# ============================================================

import websocket
import json
import uuid
import sys
import time
import hashlib
import base64
import subprocess

OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = "1aUvNbuQ4AlRIUp0"

def make_auth_response(password, salt, challenge):
    secret = base64.b64encode(
        hashlib.sha256((password + salt).encode()).digest()
    ).decode()
    auth = base64.b64encode(
        hashlib.sha256((secret + challenge).encode()).digest()
    ).decode()
    return auth

def obs_stop_recording():
    ws = websocket.WebSocket()
    try:
        ws.connect(f"ws://{OBS_HOST}:{OBS_PORT}")

        # Hello
        hello = json.loads(ws.recv())
        if hello.get("op") != 0:
            print("❌ 未收到 OBS Hello 訊息")
            return False

        # 計算驗證
        auth_data = hello.get("d", {}).get("authentication", {})
        salt = auth_data.get("salt", "")
        challenge = auth_data.get("challenge", "")
        auth_response = make_auth_response(OBS_PASSWORD, salt, challenge)

        # Identify 含驗證
        ws.send(json.dumps({
            "op": 1,
            "d": {
                "rpcVersion": 1,
                "authentication": auth_response
            }
        }))

        # Identified
        identified = json.loads(ws.recv())
        if identified.get("op") != 2:
            print("❌ OBS 驗證失敗，請確認密碼是否正確")
            return False

        # StopRecord
        request_id = str(uuid.uuid4())
        ws.send(json.dumps({
            "op": 6,
            "d": {
                "requestType": "StopRecord",
                "requestId": request_id
            }
        }))

        response = json.loads(ws.recv())
        result = response.get("d", {}).get("requestStatus", {})
        code = result.get("code", 0)

        if code == 100:
            print("⏹️  OBS 錄製已成功停止！")
            return True
        elif code == 506:
            print("⚠️  OBS 目前沒有在錄製")
            return True
        else:
            print(f"❌ 停止失敗，OBS 回應代碼：{code}")
            print(f"   訊息：{result.get('comment', '無')}")
            return False

    except ConnectionRefusedError:
        print("❌ 無法連線到 OBS！請確認：")
        print("   1. OBS 已開啟")
        print("   2. WebSocket 伺服器已啟用（工具 > WebSocket 伺服器設定）")
        print(f"   3. 埠號設定為 {OBS_PORT}")
        return False
    except Exception as e:
        print(f"❌ 發生錯誤：{e}")
        return False
    finally:
        ws.close()

def main():
    print("============================================")
    print("  OBS 自動停止錄製計時器（WebSocket 版）")
    print("============================================")
    print()

    # ── 判斷模式 ──────────────────────────────────
    if len(sys.argv) == 3:
        try:
            input_hours = int(sys.argv[1])
            input_minutes = int(sys.argv[2])
        except ValueError:
            print("❌ 參數格式錯誤！請輸入整數")
            print("   範例：python3 stop_obs_timer.py 2 30")
            sys.exit(1)
        print(f"📌 參數模式：{input_hours} 小時 {input_minutes} 分鐘")

    elif len(sys.argv) == 1:
        print("請輸入錄影時長：")
        print()
        while True:
            try:
                input_hours = int(input("  小時（0～9）："))
                if 0 <= input_hours <= 9:
                    break
                print("  ⚠️  請輸入 0～9 的整數")
            except ValueError:
                print("  ⚠️  請輸入數字")

        while True:
            try:
                input_minutes = int(input("  分鐘（0～59）："))
                if 0 <= input_minutes <= 59:
                    break
                print("  ⚠️  請輸入 0～59 的整數")
            except ValueError:
                print("  ⚠️  請輸入數字")
    else:
        print("❌ 參數數量錯誤！")
        print("   互動模式：python3 stop_obs_timer.py")
        print("   參數模式：python3 stop_obs_timer.py <小時> <分鐘>")
        sys.exit(1)

    # ── 共用邏輯 ──────────────────────────────────
    if input_hours == 0 and input_minutes == 0:
        print("❌ 錄影時長不能為 0")
        sys.exit(1)

    total_seconds = input_hours * 3600 + input_minutes * 60
    end_timestamp = time.time() + total_seconds
    end_time_str = time.strftime("%H:%M:%S", time.localtime(end_timestamp))

    print()
    print("✅ 設定完成！")
    print(f"   錄影時長：{input_hours} 小時 {input_minutes} 分鐘")
    print(f"   預計停止時間：{end_time_str}")
    print()
    print("⏳ 倒數計時中...（此視窗請保持開啟）")
    print("   按 Ctrl+C 可取消計時")
    print("============================================")
    print()

    try:
        elapsed = 0
        while elapsed < total_seconds:
            remaining = total_seconds - elapsed
            h = remaining // 3600
            m = (remaining % 3600) // 60
            s = remaining % 60
            print(f"\r   剩餘時間：{h:02d}:{m:02d}:{s:02d}  ", end="", flush=True)
            time.sleep(1)
            elapsed += 1
    except KeyboardInterrupt:
        print("\n\n⛔ 計時已取消")
        sys.exit(0)

    print("\n")
    print("⏰ 時間到！正在停止 OBS 錄影...")

    success = obs_stop_recording()

    if success:
        subprocess.run([
            "osascript", "-e",
            'display notification "OBS 錄製已自動停止" with title "OBS 計時器" sound name "Glass"'
        ])

    print()
    print("============================================")
    print("  完成！請確認 OBS 已停止錄製。")
    print("============================================")

if __name__ == "__main__":
    main()
