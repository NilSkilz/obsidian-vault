#!/usr/bin/env bash
# Jarvis heartbeat — runs every 2h during waking hours (7am-11pm) via jarvis user cron.
# One-shot `claude -p` call, stateless like the Telegram bridge. Picks up Ops/Tasks.md
# "Now" items, does quick checks, acts on anything safe, logs to the day's daily log,
# and writes anything risky/irreversible to Ops/Proposals.md instead of just doing it.
set -euo pipefail

VAULT="/data/memory"
LOG="/home/jarvis/.local/state/jarvis-heartbeat.log"
CLAUDE_BIN="$(command -v claude || echo "$HOME/.local/bin/claude")"

mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) heartbeat start -----"

PROMPT='You are running as Jarvis'\''s heartbeat, an unattended check-in (not a chat reply).

1. Read Ops/Tasks.md. Only the "Now" and "Recurring" sections are yours to act on this run — ignore "Backlog / Ideas" entirely.
2. Run `Jarvis/bin/trello.sh cards "To Do"` to list cards in the To Do list on the "Jarvis" Trello board. Treat each card exactly like a Tasks.md item (see rule 3). Only the To Do list is yours — never touch Ideas or Backlog, those are un-triaged or parked.
3. For each item (from Tasks.md or Trello): do it if it'\''s safe and reversible (checking a service, reading state, updating a file in the vault). If it touches anything external (sending messages, posting, calling third-party APIs you have not already been explicitly cleared to use unattended) or is destructive/uncertain, do NOT do it — instead add a short entry to Ops/Proposals.md (problem/option/risk) and skip it. For a Trello card you complete, comment the outcome with `Jarvis/bin/trello.sh comment <id> "<text>"` and move it with `Jarvis/bin/trello.sh move <id> "Done"`. For a Trello card you skip, leave it in To Do (don'\''t move it) and just note it in Proposals.md.
4. Append a short entry to today'\''s daily log (Daily/YYYY-MM-DD.md, create the file only if this is the first real entry today) noting what you checked and did this run. Keep it to a few lines. If nothing needed doing, a one-line "nothing due" note is enough — do not pad it.
5. Do not message Rob directly from this run. Silence is fine unless something is actually broken or needs him.'

cd "$VAULT"
"$CLAUDE_BIN" -p "$PROMPT" --model sonnet --dangerously-skip-permissions \
  >/tmp/jarvis-heartbeat-out.$$ 2>&1 || {
    echo "$(date -Iseconds) ERROR: claude invocation failed"
    cat /tmp/jarvis-heartbeat-out.$$
    rm -f /tmp/jarvis-heartbeat-out.$$
    exit 0
  }
cat /tmp/jarvis-heartbeat-out.$$
rm -f /tmp/jarvis-heartbeat-out.$$

echo "----- $(date -Iseconds) heartbeat end -----"
