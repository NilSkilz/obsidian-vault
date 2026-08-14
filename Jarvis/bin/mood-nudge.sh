#!/usr/bin/env bash
# Gentle mood check-in nudge for Rob. Cron fires this once in the evening; if
# Rob hasn't logged a mood in Tide's journal today, it sends one light Telegram
# prompt inviting a 1-5 check-in. Only Rob gets nudged (Aimee logs in the UI).
#
# Usage: mood-nudge.sh
# Skips silently if: a mood is already logged today, or the API is unreachable.
# Fires once per day, so it never nags twice.
set -euo pipefail

HCONF="$HOME/.config/jarvis/health.env"
TCONF="$HOME/.config/jarvis/telegram.env"
LOG="$HOME/.local/state/jarvis-mood-nudge.log"
mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) mood nudge -----"

[ -f "$HCONF" ] && [ -f "$TCONF" ] || { echo "missing config"; exit 0; }
set -a; source "$HCONF"; source "$TCONF"; set +a
BASE="${TIDE_API_BASE:-http://192.168.1.16:3001}/api/family"

TREND="$(curl -sS --max-time 10 "${BASE}/journal?range=2" \
  -H "X-Jarvis-Key: ${JARVIS_API_KEY}" -H "X-Jarvis-User: rob" 2>/dev/null)" || {
  echo "API unreachable; skipping"; exit 0; }

TODAY="$(echo "$TREND" | jq -r '.today // empty')"
[ -n "$TODAY" ] || { echo "no today field; skipping"; exit 0; }

# Already logged a mood today? Done.
LOGGED="$(echo "$TREND" | jq --arg d "$TODAY" \
  '[.entries[] | select(.date==$d and .mood!=null)] | length')"
if [ "$LOGGED" -gt 0 ]; then echo "mood already logged today ($LOGGED); skipping"; exit 0; fi

MSG="How's today been on the whole? Give me a 1-5 (1 rough, 5 great) or just tell me how you're doing, and I'll log it. Skip if you'd rather not."

curl -sS --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=🌤 ${MSG}" >/dev/null || true
echo "nudged for mood"
