#!/usr/bin/env bash
# Ensure the Jarvis Telegram bridge is running in tmux.
# Idempotent, safe for @reboot and a periodic watchdog cron.
export PATH="$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
# PINNED to Opus 5.5 (Rob, 2026-11-16; was Fable 5.2 + auto for one day,
# 11-15 to 11-16). JARVIS_MODEL_AUTO=0 pins JARVIS_MODEL, so the usage-aware
# switch is off. To restore: JARVIS_MODEL="claude-fable-5-2", JARVIS_MODEL_AUTO=1.
export JARVIS_MODEL="claude-opus-5-5"
export JARVIS_MODEL_AUTO=0
tmux has-session -t jarvis-bridge 2>/dev/null && exit 0
tmux new -d -s jarvis-bridge 'python3 /data/memory/Jarvis/bridge/bridge.py'
