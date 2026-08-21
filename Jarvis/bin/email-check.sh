#!/usr/bin/env bash
# Jarvis hourly email check — cron runs this at :05, 7am-11pm.
# 1. Sweeps known-junk senders (mail-bin-senders.txt) from INBOX to the bin.
# 2. Grabs anything new since the last run; if there is any, a one-shot
#    `claude -p` judges whether it's worth pinging Rob on Telegram.
#    Silence is the default: marketing, newsletters and routine automation
#    never ping. Set DRYRUN=1 to print the would-be message instead of sending.
set -euo pipefail

VAULT="/data/memory"
BIN="$VAULT/Jarvis/bin"
LOG="$HOME/.local/state/jarvis-email-check.log"
TCONF="$HOME/.config/jarvis/telegram.env"
CLAUDE_BIN="$(command -v claude || echo "$HOME/.local/bin/claude")"
DRYRUN="${DRYRUN:-0}"

mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) email check start -----"

python3 "$BIN/mail-tool.py" sweep || echo "sweep failed (continuing)"

NEW="$(python3 "$BIN/mail-tool.py" new)" || { echo "fetch failed"; exit 0; }
if [ -z "$NEW" ]; then
  echo "no new mail"
  echo "----- $(date -Iseconds) email check end -----"
  exit 0
fi
echo "new mail:"
echo "$NEW"

PROMPT='You are Jarvis running Rob'\''s hourly unattended email check (not a chat reply). Below are the emails that arrived in his iCloud inbox in the last hour. Decide if ANY genuinely deserve interrupting him on Telegram.

Worth a ping: personal mail from a real human, anything about family or school, security/fraud alerts, money problems (failed payments, unexpected charges), a delivery arriving today, anything time-sensitive he would regret missing.
NOT worth a ping: marketing, newsletters, promos, social-media notifications, routine receipts and subscription renewals, automated service noise. When in doubt, stay quiet; he checks email himself eventually.

If nothing qualifies, reply with exactly NOTHING_INTERESTING and no other text.
Otherwise reply with ONLY the Telegram message to send: short and chat-shaped, warm and direct with a bit of dry wit, plain text (no markdown headers or tables), absolutely no em dashes. Lead with what the email is and why it matters. Do not use any tools.

New emails:
'

OUT="$(cd "$VAULT" && "$CLAUDE_BIN" -p "${PROMPT}${NEW}" --model sonnet --dangerously-skip-permissions 2>/dev/null)" || {
  echo "claude invocation failed"; exit 0; }
echo "verdict: $OUT"

case "$OUT" in
  *NOTHING_INTERESTING*) echo "nothing interesting"; ;;
  "") echo "empty verdict; staying quiet"; ;;
  *)
    if [ "$DRYRUN" = "1" ]; then
      echo "DRYRUN: would send the message above"
    else
      set -a; source "$TCONF"; set +a
      curl -sS --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
        --data-urlencode "text=📬 ${OUT}" >/dev/null && echo "pinged Rob" || echo "telegram send failed"
    fi
    ;;
esac
echo "----- $(date -Iseconds) email check end -----"
