# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

macOS Python scripts that control OBS Studio recording via the OBS WebSocket v5 protocol. Designed to be triggered by macOS Automator quick actions bound to keyboard shortcuts (`Cmd+Shift+R` to start, `Cmd+Shift+S` to stop).

## Commands

```bash
# Install dependencies
uv sync

# Run scripts
uv run start_obs_recording.py          # Start OBS recording (auto-launches OBS if not running)
uv run stop_obs_now.py                 # Immediately stop recording
uv run stop_obs_timer.py               # Interactive countdown timer, then stop
uv run stop_obs_timer.py 2 30          # Timer mode: stop after 2h 30m
```

## Architecture

All three scripts share the same OBS WebSocket v5 handshake pattern (duplicated across files, not shared):

1. Connect to `ws://localhost:4455`
2. Receive `Hello` (op=0), extract `salt` + `challenge`
3. Compute auth: `base64(sha256(base64(sha256(password+salt)) + challenge))`
4. Send `Identify` (op=1) with auth response
5. Receive `Identified` (op=2) to confirm success
6. Send a `Request` (op=6) — either `StartRecord` or `StopRecord`
7. OBS status code `100` = success, `506` = already in desired state

After recording starts/stops, scripts fire a macOS system notification via `osascript`.

`start_obs_recording.py` additionally checks if OBS is running via `pgrep -x OBS` and auto-launches it with `open -a OBS` if not, waiting `OBS_LAUNCH_WAIT` seconds for initialization.

`stop_obs_timer.py` supports both interactive input and CLI arguments (`<hours> <minutes>`), and runs a blocking countdown loop with `Ctrl+C` cancellation support.

## OBS WebSocket Configuration

- Host: `localhost`, Port: `4455`
- Password is hardcoded as `OBS_PASSWORD` at the top of each script — update all three files when changing it
- Requires OBS WebSocket server enabled: Tools → WebSocket Server Settings
