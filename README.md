# OBS Scripts

透過 OBS WebSocket v5 協定，用 Python 腳本在 macOS 上自動控制 OBS Studio 錄影。

## 功能

| 腳本 | 功能 |
|---|---|
| `start_obs_recording.py` | 自動偵測 OBS 是否開啟，未開啟則自動啟動，並開始錄製 |
| `stop_obs_now.py` | 立即停止 OBS 錄製 |
| `stop_obs_timer.py` | 設定倒數計時，時間到自動停止錄製 |

錄影開始／停止時，皆會跳出 macOS 系統通知。

---

## 環境需求

- macOS
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) 套件管理器
- OBS Studio（已啟用 WebSocket 伺服器）

### 啟用 OBS WebSocket 伺服器

在 OBS 中：**工具 → WebSocket 伺服器設定**

- 勾選「啟用 WebSocket 伺服器」
- 連接埠：`4455`
- 設定密碼，並更新三支腳本頂部的 `OBS_PASSWORD` 變數

---

## 安裝

```bash
git clone <repo-url>
cd OBS-Scripts
uv sync
```

---

## 使用方式

### 開始錄影

```bash
uv run start_obs_recording.py
```

- 若 OBS 尚未開啟，會自動啟動並等待初始化
- 連線成功後自動開始錄製

### 立即停止錄影

```bash
uv run stop_obs_now.py
```

### 倒數計時自動停止

**互動模式**（手動輸入時長）：

```bash
uv run stop_obs_timer.py
```

**參數模式**（供自動化流程呼叫）：

```bash
uv run stop_obs_timer.py <小時> <分鐘>

# 範例：2 小時 30 分鐘後停止
uv run stop_obs_timer.py 2 30
```

計時中按 `Ctrl+C` 可取消。

---

## 整合 macOS Automator 快速動作

可將開始／停止錄影綁定為全域鍵盤快捷鍵，詳細步驟請參考 [Automator_OBS_設定指南.md](./Automator_OBS_設定指南.md)。

| 快速動作 | 預設快捷鍵 |
|---|---|
| OBS 開始錄影 | `Cmd+Shift+R` |
| OBS 停止錄影 | `Cmd+Shift+S` |

Automator Shell 腳本範例：

```bash
export PATH="$HOME/.local/bin:$PATH"
cd "$HOME/OBS-Scripts"
uv run start_obs_recording.py
```
