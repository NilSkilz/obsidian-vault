#!/usr/bin/env bash
# One-shot personal check-in with Rob — follow-up on the 2026-07-15 post-play-date
# re-entry anxiety (he asked to "catch up in a couple of days").
# Scheduled by hand for 2026-07-17 morning; removes its OWN cron line after sending
# so it only ever fires once. Sends to Rob's private Telegram (same chat as briefings).
set -euo pipefail

VAULT="/data/memory"
LOG="/home/jarvis/.local/state/jarvis-briefing.log"
CONF="$HOME/.config/jarvis/telegram.env"
CLAUDE_BIN="$(command -v claude || echo "$HOME/.local/bin/claude")"

mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) checkin-oneshot start -----"

set -a
source "$CONF"
set +a

PROMPT="You are Jarvis, sending Rob a short, warm, private Telegram check-in (he just receives it, it is not a reply to a prompt). Context: on 2026-07-15 he came home from a play date with Tash and hit his usual pre-arrival anxiety waiting for Aimee to get home. Read People/Rob - Personal context.md, the 'post-play-date re-entry' section, for the full picture and what helped. He asked me to catch up in a couple of days. Gently ask how that evening with Aimee actually went, and lightly whether he has had any thought about the calm-moment conversation (only if it feels natural, do not push it). Tone: a mate following up because he said he would, not a therapist and not a lecture. A few sentences, low pressure. No em dashes."

cd "$VAULT"
MSG="$("$CLAUDE_BIN" -p "$PROMPT" --model claude-opus-4-8 --dangerously-skip-permissions 2>/tmp/jarvis-checkin-err.$$)" || {
  echo "$(date -Iseconds) ERROR: claude invocation failed"
  cat /tmp/jarvis-checkin-err.$$ 2>/dev/null || true
  rm -f /tmp/jarvis-checkin-err.$$
  exit 0
}
rm -f /tmp/jarvis-checkin-err.$$

echo "$MSG"

curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=${MSG:0:4000}" >/dev/null

# Fire once: strip this script's line out of the crontab.
( crontab -l 2>/dev/null | grep -v 'checkin-oneshot.sh' ) | crontab - || true

echo "----- $(date -Iseconds) checkin-oneshot end (cron line removed) -----"
