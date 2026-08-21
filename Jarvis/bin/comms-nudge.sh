#!/usr/bin/env bash
# Evening nudge for Rob's Aimee Comms Log. Cron fires this once at 21:00.
# Asks Rob what he communicated to Aimee today; when he replies, Jarvis appends
# a dated entry to Context/Aimee Comms Log.md. Purpose: a neutral record of what
# was actually said (and what wasn't), for the recurring "did you tell me?" gap.
#
# Usage: comms-nudge.sh
# Skips silently if today's date already has an entry (Rob already told me and I
# logged it earlier). Fires once per day, so it never nags twice.
set -euo pipefail

TCONF="$HOME/.config/jarvis/telegram.env"
LOGFILE="/data/memory/Context/Aimee Comms Log.md"
LOG="$HOME/.local/state/jarvis-comms-nudge.log"
mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) comms nudge -----"

[ -f "$TCONF" ] || { echo "missing telegram config"; exit 0; }
set -a; source "$TCONF"; set +a

# Already logged something for today? Then skip the nudge.
TODAY="$(date +%Y-%m-%d)"
if [ -f "$LOGFILE" ] && grep -q "^## ${TODAY}" "$LOGFILE"; then
  echo "already an entry for ${TODAY}; skipping"; exit 0
fi

MSG="Comms log time. What did you tell Aimee today? Give me the gist of anything worth having on record (plans, decisions, feelings, logistics) and I'll log it. If nothing notable, just say so and I'll note a quiet day."

curl -sS --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=🗒 ${MSG}" >/dev/null || true
echo "nudged for comms log"
