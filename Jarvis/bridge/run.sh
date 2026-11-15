#!/usr/bin/env bash
# Ensure the Jarvis Telegram bridge is running in tmux.
# Idempotent, safe for @reboot and a periodic watchdog cron.
export PATH="$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
# Fable 5.2 with the usage-aware switch on (Rob, 2026-11-15; was pinned to
# Opus 5.5 since 2026-10-06). JARVIS_MODEL_AUTO=0 pins JARVIS_MODEL instead.
export JARVIS_MODEL="claude-fable-5-2"
export JARVIS_MODEL_AUTO=1
tmux has-session -t jarvis-bridge 2>/dev/null && exit 0
tmux new -d -s jarvis-bridge 'python3 /data/memory/Jarvis/bridge/bridge.py'
