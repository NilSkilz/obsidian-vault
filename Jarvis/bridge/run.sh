#!/usr/bin/env bash
# Ensure the Jarvis Telegram bridge is running in tmux.
# Idempotent — safe for @reboot and a periodic watchdog cron.
export PATH="$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export JARVIS_MODEL="claude-opus-4-8"
tmux has-session -t jarvis-bridge 2>/dev/null && exit 0
tmux new -d -s jarvis-bridge 'python3 /data/memory/Jarvis/bridge/bridge.py'
