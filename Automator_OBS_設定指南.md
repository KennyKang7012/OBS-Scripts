# OBS 錄影 Automator 快速動作設定指南

## 概覽

建立兩個 Automator 快速動作：

| 快速動作 | 快捷鍵 | 功能 |
|---|---|---|
| OBS 開始錄影 | `Cmd+Shift+R` | 自動啟動 OBS 並開始錄製 |
| OBS 停止錄影 | `Cmd+Shift+S` | 立即停止 OBS 錄製 |

---

## 第一步：建立「OBS 開始錄影」快速動作

### 1. 開啟 Automator
- 按 `Cmd+Space` 搜尋「Automator」並開啟

### 2. 新增文件
- 點選「新增文件」
- 選擇「快速動作」→「選擇」

### 3. 設定工作流程
- 右上角「工作流程收到」選擇：**沒有輸入**
- 在左側搜尋欄輸入「執行 Shell 工序指令碼」
- 雙擊加入右側工作區

### 4. 貼上腳本
將 Shell 欄位設為 `/bin/bash`，並貼上以下內容：

```bash
export PATH="$HOME/.local/bin:$PATH"
cd "$HOME/OBS-Scripts"
uv run start_obs_recording.py
```

### 5. 儲存
- `Cmd+S` 儲存
- 名稱輸入：`OBS 開始錄影`

### 6. 設定快捷鍵
- 前往「系統設定」→「鍵盤」→「鍵盤快速鍵」
- 左側選「服務」→「一般」
- 找到「OBS 開始錄影」→ 雙擊右側空白處
- 按下 `Cmd+Shift+R`

---

## 第二步：建立「OBS 停止錄影」快速動作

### 1. 重複上述步驟 1～3

### 2. 貼上腳本
Shell 欄位同樣設為 `/bin/bash`，貼上：

```bash
export PATH="$HOME/.local/bin:$PATH"
cd "$HOME/OBS-Scripts"
uv run stop_obs_now.py
```

### 3. 儲存
- 名稱輸入：`OBS 停止錄影`

### 4. 設定快捷鍵
- 同上步驟，設定快捷鍵為 `Cmd+Shift+S`

---

## 第三步：建立「立即停止」腳本

> 這支腳本專門用於手動立即停止錄影（不需要倒數計時）

在 `~/OBS-Scripts/` 內新增 `stop_obs_now.py`：

```python
#!/usr/bin/env python3

# ============================================================
#  OBS 立即停止錄製腳本（WebSocket 版）
#  使用方式：python3 stop_obs_now.py
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
```

---

## 完成後的使用方式

### 開始錄影
按下 `Cmd+Shift+R`
- OBS 自動啟動（若未開啟）
- 自動開始錄製
- 跳出系統通知

### 停止錄影（手動立即停止）
按下 `Cmd+Shift+S`
- 立即停止 OBS 錄製
- 跳出系統通知

### 停止錄影（倒數計時自動停止）
在 Terminal 執行：
```bash
cd ~/OBS-Scripts
uv run stop_obs_timer.py     # 互動模式
uv run stop_obs_timer.py 2 30  # 參數模式：2 小時 30 分鐘
```

---

## 最終檔案清單

```
~/OBS-Scripts/
├── start_obs_recording.py   # 開始錄影
├── stop_obs_now.py          # 立即停止錄影
├── stop_obs_timer.py        # 倒數計時停止錄影
├── pyproject.toml
├── uv.lock
└── .venv/
```
