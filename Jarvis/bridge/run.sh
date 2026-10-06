#!/usr/bin/env bash
# Ensure the Jarvis Telegram bridge is running in tmux.
# Idempotent — safe for @reboot and a periodic watchdog cron.
export PATH="$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
# Pinned to Opus 5.5 at Rob's request (2026-10-06). To restore usage-aware
# Fable: set JARVIS_MODEL back to claude-fable-5 and JARVIS_MODEL_AUTO=1.
export JARVIS_MODEL="claude-opus-5-5"
export JARVIS_MODEL_AUTO=0
tmux has-session -t jarvis-bridge 2>/dev/null && exit 0
tmux new -d -s jarvis-bridge 'python3 /data/memory/Jarvis/bridge/bridge.py'
