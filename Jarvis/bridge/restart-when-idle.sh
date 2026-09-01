#!/bin/sh
# Restart the Telegram bridge WITHOUT killing the run that asked for it.
# The bridge's claude jobs are its children, so a naive restart from inside a
# job is suicide: this waits for the given pid (the requesting run) to exit,
# then for the bridge to go idle (no claude children), then bounces the tmux
# session. Launch detached: setsid nohup restart-when-idle.sh <pid> "<reason>" &
WAIT_PID="$1"
REASON="${2:-new code}"
LOG="$HOME/.local/state/jarvis-bridge/restart.log"
while [ -n "$WAIT_PID" ] && [ -e "/proc/$WAIT_PID" ]; do sleep 3; done
BRIDGE_PID=$(pgrep -f '^python3 /data/memory/Jarvis/bridge/bridge.py' | head -1)
i=0
while [ -n "$BRIDGE_PID" ] && pgrep -P "$BRIDGE_PID" >/dev/null 2>&1 && [ $i -lt 200 ]; do
  sleep 3; i=$((i+1))
done
tmux kill-session -t jarvis-bridge 2>/dev/null
sleep 2
/data/memory/Jarvis/bridge/run.sh
echo "$(date -Is) bridge restarted: $REASON (waited on pid ${WAIT_PID:-none})" >> "$LOG"
