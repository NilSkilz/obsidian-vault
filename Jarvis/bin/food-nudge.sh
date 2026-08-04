#!/usr/bin/env bash
# Gentle meal-logging nudge for Rob. Cron fires this after a mealtime; if that
# meal isn't logged in Tide yet for today, it sends one light Telegram prompt.
# Only Rob gets nudged (Aimee has no chat bridge to Jarvis; she logs in the UI).
#
# Usage: food-nudge.sh <lunch|dinner|breakfast>
# Skips silently if: the meal is already logged, Rob has no calorie target set,
# or the API is unreachable. Never nags twice for the same meal.
set -euo pipefail

MEAL="${1:-lunch}"
HCONF="$HOME/.config/jarvis/health.env"
TCONF="$HOME/.config/jarvis/telegram.env"
LOG="$HOME/.local/state/jarvis-food-nudge.log"
mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) nudge ($MEAL) -----"

[ -f "$HCONF" ] && [ -f "$TCONF" ] || { echo "missing config"; exit 0; }
set -a; source "$HCONF"; source "$TCONF"; set +a
BASE="${TIDE_API_BASE:-http://192.168.1.16:3001}/api/family"

DAY="$(curl -sS --max-time 10 "${BASE}/health/day" \
  -H "X-Jarvis-Key: ${JARVIS_API_KEY}" -H "X-Jarvis-User: rob" 2>/dev/null)" || {
  echo "API unreachable; skipping"; exit 0; }

# Rob's block from the response.
ROB="$(echo "$DAY" | jq -c '.users[] | select(.name|ascii_downcase=="rob")' 2>/dev/null)" || ROB=""
[ -n "$ROB" ] || { echo "no rob block; skipping"; exit 0; }

# Not tracking? Don't nudge.
TARGET="$(echo "$ROB" | jq -r '.target // "null"')"
[ "$TARGET" != "null" ] || { echo "no target set; skipping"; exit 0; }

# Already logged this meal today? Done.
COUNT="$(echo "$ROB" | jq --arg m "$MEAL" '[.food[] | select(.mealType==$m)] | length')"
if [ "$COUNT" -gt 0 ]; then echo "$MEAL already logged ($COUNT); skipping"; exit 0; fi

EATEN="$(echo "$ROB" | jq -r '.eaten')"
case "$MEAL" in
  breakfast) MSG="Morning. No breakfast logged yet, want to tell me what you had? (or skip if you're fasting)";;
  lunch)     MSG="No lunch logged yet ($EATEN kcal so far today). What did you have?";;
  dinner)    MSG="No dinner on the log yet ($EATEN kcal today). What are you eating?";;
  *)         MSG="No $MEAL logged yet. What did you have?";;
esac

curl -sS --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=🍽 ${MSG}" >/dev/null || true
echo "nudged for $MEAL"
