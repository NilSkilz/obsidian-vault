#!/usr/bin/env bash
# Jarvis morning/evening briefing — sent to Rob on Telegram.
# One-shot `claude -p` call that reads the vault, composes a short briefing,
# and sends it directly (unlike heartbeat, this run is ALLOWED to message Rob).
set -euo pipefail

MODE="${1:?usage: briefing.sh morning|evening}"
VAULT="/data/memory"
LOG="/home/jarvis/.local/state/jarvis-briefing.log"
CONF="$HOME/.config/jarvis/telegram.env"
CLAUDE_BIN="$(command -v claude || echo "$HOME/.local/bin/claude")"

mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) briefing ($MODE) start -----"

set -a
source "$CONF"
set +a

if [ "$MODE" = "morning" ]; then
  ASK='Compose Rob'\''s MORNING briefing. Check: today'\''s weather (`Jarvis/bin/weather.sh today`, worth a quick line), today'\''s calendar (`Jarvis/bin/calendar.sh today`, family/personal events), today'\''s Trello "To Do"/"In Progress" cards (`Jarvis/bin/trello.sh cards "To Do"` and `... "In Progress"`), today'\''s Todoist tasks (`Jarvis/bin/todoist.sh today` for due-today items, plus `Jarvis/bin/todoist.sh list "Shared Todo"` for the open household list, no due dates but worth a mention if something stands out), Ops/Tasks.md "Now" items, anything blocked in Ops/Proposals.md that needs his call, and yesterday'\''s daily log for open follow-ups. Keep it tight: 3-6 short lines, chat-shaped for Telegram, no headers/markdown tables. Lead with anything that actually needs him today (calendar events included); skip sections with nothing to say.'
else
  ASK='Compose Rob'\''s EVENING briefing. Check today'\''s daily log (Daily/YYYY-MM-DD.md) for what actually happened, any Trello cards moved/blocked today, any Todoist household tasks still open (`Jarvis/bin/todoist.sh today` and `Jarvis/bin/todoist.sh list "Shared Todo"`), tomorrow'\''s weather (`Jarvis/bin/weather.sh tomorrow`, so he can plan), tomorrow'\''s calendar (`Jarvis/bin/calendar.sh tomorrow`, so he knows what'\''s coming), and anything left open in Ops/Proposals.md. Keep it tight: 3-6 short lines, chat-shaped for Telegram, no headers/markdown tables. Focus on what moved, what'\''s still waiting on him, and anything on tomorrow'\''s calendar worth flagging tonight.'
fi

PROMPT="You are Jarvis, writing an unattended briefing message to Rob (not a chat reply to a prompt — he will just receive this as a Telegram message). ${ASK} No em dashes. If genuinely nothing happened and nothing is waiting on him, a one-line 'quiet one, nothing needs you' is fine — don't pad it."

cd "$VAULT"
BRIEF="$("$CLAUDE_BIN" -p "$PROMPT" --model sonnet --dangerously-skip-permissions 2>/tmp/jarvis-briefing-err.$$)" || {
  echo "$(date -Iseconds) ERROR: claude invocation failed"
  cat /tmp/jarvis-briefing-err.$$
  rm -f /tmp/jarvis-briefing-err.$$
  exit 0
}
rm -f /tmp/jarvis-briefing-err.$$

echo "$BRIEF"

curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_ALLOWED_CHAT}" \
  --data-urlencode "text=${BRIEF:0:4000}" >/dev/null

echo "----- $(date -Iseconds) briefing ($MODE) end -----"
