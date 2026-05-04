#!/usr/bin/env python3

# ============================================================
#  OBS 開始錄製腳本（WebSocket 版）
#  使用方式：python3 start_obs_recording.py
#  需求：pip install websocket-client
#  功能：自動偵測 OBS 是否開啟，未開啟則自動啟動
# ============================================================

import websocket
import json
import uuid
import sys
import hashlib
import base64
import subprocess
import time

OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = "1aUvNbuQ4AlRIUp0"
OBS_LAUNCH_WAIT = 10  # 等待 OBS 啟動的秒數

def make_auth_response(password, salt, challenge):
    secret = base64.b64encode(
        hashlib.sha256((password + salt).encode()).digest()
    ).decode()
    auth = base64.b64encode(
        hashlib.sha256((secret + challenge).encode()).digest()
    ).decode()
    return auth

def is_obs_running():
    """檢查 OBS 是否已在執行"""
    result = subprocess.run(
        ["pgrep", "-x", "OBS"],
        capture_output=True, text=True
    )
    return result.returncode == 0

def launch_obs():
    """自動啟動 OBS"""
    print("🚀 OBS 尚未開啟，正在自動啟動...")
    subprocess.Popen(["open", "-a", "OBS"])

    # 等待 OBS 啟動並顯示倒數
    for i in range(OBS_LAUNCH_WAIT, 0, -1):
        print(f"\r   等待 OBS 初始化... {i} 秒  ", end="", flush=True)
        time.sleep(1)
    print("\r   OBS 初始化完成！               ")
    print()

def connect_and_start():
    """連線 WebSocket 並開始錄製"""
    ws = websocket.WebSocket()
    try:
        print("🔌 正在連線到 OBS WebSocket...")
        ws.connect(f"ws://{OBS_HOST}:{OBS_PORT}")

        # Step 1：接收 Hello (op=0)
        hello = json.loads(ws.recv())
        if hello.get("op") != 0:
            print("❌ 未收到 OBS Hello 訊息")
            sys.exit(1)

        # Step 2：計算密碼驗證
        auth_data = hello.get("d", {}).get("authentication", {})
        salt = auth_data.get("salt", "")
        challenge = auth_data.get("challenge", "")
        auth_response = make_auth_response(OBS_PASSWORD, salt, challenge)

        # Step 3：送出 Identify (op=1) 含驗證
        ws.send(json.dumps({
            "op": 1,
            "d": {
                "rpcVersion": 1,
                "authentication": auth_response
            }
        }))

        # Step 4：接收 Identified (op=2)
        identified = json.loads(ws.recv())
        if identified.get("op") != 2:
            print("❌ OBS 驗證失敗，請確認密碼是否正確")
            sys.exit(1)

        print("✅ 成功連線並驗證！")
        print()

        # Step 5：送出 StartRecord 請求
        request_id = str(uuid.uuid4())
        ws.send(json.dumps({
            "op": 6,
            "d": {
                "requestType": "StartRecord",
                "requestId": request_id
            }
        }))

        # Step 6：接收回應
        response = json.loads(ws.recv())
        result = response.get("d", {}).get("requestStatus", {})
        code = result.get("code", 0)

        if code == 100:
            print("⏺️  OBS 錄製已成功開始！")
            subprocess.run([
                "osascript", "-e",
                'display notification "OBS 錄製已開始" with title "OBS 計時器" sound name "Glass"'
            ])
        elif code == 506:
            print("⚠️  OBS 已經在錄製中了")
        else:
            print(f"❌ 啟動失敗，OBS 回應代碼：{code}")
            print(f"   訊息：{result.get('comment', '無')}")
            sys.exit(1)

    except ConnectionRefusedError:
        print("❌ 無法連線到 OBS WebSocket！")
        print("   OBS 可能還在初始化中，請稍後再試")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 發生錯誤：{e}")
        sys.exit(1)
    finally:
        ws.close()

def main():
    print("============================================")
    print("       OBS 開始錄製（WebSocket 版）")
    print("============================================")
    print()

    # 檢查 OBS 是否已開啟
    if is_obs_running():
        print("✅ OBS 已在執行中")
        print()
    else:
        launch_obs()

    # 連線並開始錄製
    connect_and_start()

    print()
    print("============================================")
    print("  完成！請確認 OBS 已開始錄製。")
    print("============================================")

if __name__ == "__main__":
    main()
