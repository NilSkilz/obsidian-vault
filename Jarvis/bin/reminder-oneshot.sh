#!/usr/bin/env bash
# Generic one-shot reminder to Rob on Telegram.
# Usage (from cron): reminder-oneshot.sh <unique-tag> <message>
# Sends <message> to Rob's private Telegram, then strips its OWN cron line
# (matched by <unique-tag>) so it fires exactly once.
set -euo pipefail

TAG="${1:?usage: reminder-oneshot.sh <tag> <message>}"
MSG="${2:?usage: reminder-oneshot.sh <tag> <message>}"
LOG="/home/jarvis/.local/state/jarvis-briefing.log"
CONF="$HOME/.config/jarvis/telegram.env"

mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) reminder-oneshot ($TAG) start -----"

set -a
source "$CONF"
set +a

# Cron entries are single-line, so newlines arrive as literal "\n" — expand them.
MSG="$(printf '%b' "$MSG")"

curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=${MSG:0:4000}" >/dev/null

# Fire once: strip this reminder's line (matched by its unique tag) out of the crontab.
( crontab -l 2>/dev/null | grep -v "reminder-oneshot.sh $TAG" ) | crontab - || true

echo "----- $(date -Iseconds) reminder-oneshot ($TAG) end (cron line removed) -----"
