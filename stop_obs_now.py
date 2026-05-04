#!/usr/bin/env python3

# ============================================================
#  OBS 立即停止錄製腳本（WebSocket 版）
#  使用方式：python3 stop_obs_now.py
#  需求：pip install websocket-client
# ============================================================

import websocket
import json
import uuid
import sys
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

def main():
    print("============================================")
    print("       OBS 立即停止錄製（WebSocket 版）")
    print("============================================")
    print()

    ws = websocket.WebSocket()
    try:
        print("🔌 正在連線到 OBS WebSocket...")
        ws.connect(f"ws://{OBS_HOST}:{OBS_PORT}")

        # Hello
        hello = json.loads(ws.recv())
        if hello.get("op") != 0:
            print("❌ 未收到 OBS Hello 訊息")
            sys.exit(1)

        # 計算驗證
        auth_data = hello.get("d", {}).get("authentication", {})
        salt = auth_data.get("salt", "")
        challenge = auth_data.get("challenge", "")
        auth_response = make_auth_response(OBS_PASSWORD, salt, challenge)

        # Identify
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
            print("❌ OBS 驗證失敗")
            sys.exit(1)

        print("✅ 成功連線並驗證！")
        print()
        print("⏹️  正在停止 OBS 錄製...")

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
            print("✅ OBS 錄製已成功停止！")
            subprocess.run([
                "osascript", "-e",
                'display notification "OBS 錄製已停止" with title "OBS 計時器" sound name "Glass"'
            ])
        elif code == 506:
            print("⚠️  OBS 目前沒有在錄製")
        else:
            print(f"❌ 停止失敗，OBS 回應代碼：{code}")
            sys.exit(1)

    except ConnectionRefusedError:
        print("❌ 無法連線到 OBS！請確認 OBS 已開啟且 WebSocket 已啟用")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 發生錯誤：{e}")
        sys.exit(1)
    finally:
        ws.close()

    print()
    print("============================================")
    print("  完成！請確認 OBS 已停止錄製。")
    print("============================================")

if __name__ == "__main__":
    main()
