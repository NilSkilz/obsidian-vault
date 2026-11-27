#!/usr/bin/env bash
# Picks up the "↻ refresh" button on cracky.co.uk/finances.
# Cron runs this every minute; it checks Tide every 10s for ~50s, and when a
# parent has queued a refresh it runs finance-sync.py (which reports its own
# start/finish back to Tide). flock stops it overlapping the 05:20 nightly run
# or itself. See Projects/Tide Finances.md.
set -u
LOCK=/tmp/finance-sync.lock
LOG=/home/jarvis/finance/sync.log
ENVF=/home/jarvis/.config/jarvis/health.env
KEY=$(grep '^JARVIS_API_KEY=' "$ENVF" | cut -d= -f2-)
BASE=$(grep '^TIDE_API_BASE=' "$ENVF" | cut -d= -f2-)
BASE=${BASE:-http://192.168.1.16:3001}

HEART=/home/jarvis/.local/state/jarvis-finance-poll.log  # cron-health liveness
reached=0
for i in 1 2 3 4 5; do
  pending=$(curl -fsS -m 8 -H "X-Jarvis-Key: $KEY" "$BASE/api/finance/sync-status" 2>/dev/null \
    | python3 -c 'import json,sys; print(json.load(sys.stdin).get("pending"))' 2>/dev/null)
  [ -n "$pending" ] && reached=1
  if [ "$pending" = "True" ]; then
    echo "$(date -Is) manual refresh requested" >> "$LOG"
    flock -n "$LOCK" python3 /data/memory/Jarvis/bin/finance-sync.py >> "$LOG" 2>&1
  fi
  [ "$i" -lt 5 ] && sleep 10
done
# Only touch the heartbeat when Tide answered, so an unreachable Tide shows up
# in cron-health as "silent" rather than hiding behind a fresh file.
[ "$reached" = 1 ] && echo "$(date -Is) ok" > "$HEART"
exit 0
