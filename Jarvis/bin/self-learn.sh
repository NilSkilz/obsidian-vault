#!/usr/bin/env bash
# Jarvis weekly self-learn — read the week's Telegram conversation, distil
# durable lessons into memory, and report what was learned.
#
# The Telegram bridge (Jarvis/bridge/bridge.py) already logs the FULL
# conversation to ~/.local/state/jarvis-bridge/conversation.log (not just the
# rolling 16-turn buffer it feeds back per prompt). That file IS the chat
# archive. This script slices the new material since it last ran (tracked by a
# byte offset, so it's robust to multi-line entries and needs no timestamps),
# hands it to an agentic `claude -p` run in the vault, and lets that run write
# durable lessons following the CLAUDE.md + auto-memory rules. It ends by
# sending Rob a short Telegram summary of what it actually learned.
#
# Mirrors briefing.sh: cron -> claude -p in the vault -> Telegram. This run is
# ALLOWED to message Rob (unlike heartbeat).
set -euo pipefail

VAULT="/data/memory"
CONVO="$HOME/.local/state/jarvis-bridge/conversation.log"
OFFSET_FILE="$HOME/.local/state/jarvis-self-learn.offset"
LOG="$HOME/.local/state/jarvis-self-learn.log"
CONF="$HOME/.config/jarvis/telegram.env"
CLAUDE_BIN="$(command -v claude || echo "$HOME/.local/bin/claude")"
MIN_NEW_LINES=15   # below this, not enough new chat to be worth a distil run

mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) self-learn start -----"

set -a
source "$CONF"
set +a

send_tg() {
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=${1:0:4000}" >/dev/null || true
}

if [ ! -f "$CONVO" ]; then
  echo "no conversation log at $CONVO, nothing to learn from"
  exit 0
fi

END="$(wc -c < "$CONVO")"
START=0
if [ -f "$OFFSET_FILE" ]; then
  START="$(cat "$OFFSET_FILE" 2>/dev/null || echo 0)"
fi
# Log rotated/truncated since last run? Reset and process from the top.
if ! [[ "$START" =~ ^[0-9]+$ ]] || [ "$START" -gt "$END" ]; then
  echo "offset ($START) > size ($END) or invalid; resetting to 0"
  START=0
fi

if [ "$START" -ge "$END" ]; then
  echo "no new conversation since last run (offset=$START, size=$END); skipping"
  exit 0
fi

SLICE="$(mktemp /tmp/jarvis-self-learn.XXXXXX)"
trap 'rm -f "$SLICE" /tmp/jarvis-self-learn-err.$$' EXIT
# Bytes [START, END): exactly the new material since last run.
tail -c +"$((START + 1))" "$CONVO" | head -c "$((END - START))" > "$SLICE"

NEW_LINES="$(wc -l < "$SLICE")"
echo "new material: $NEW_LINES lines, $((END - START)) bytes (offset $START -> $END)"
if [ "$NEW_LINES" -lt "$MIN_NEW_LINES" ]; then
  echo "under $MIN_NEW_LINES lines of new chat; skipping quietly, not advancing offset"
  exit 0
fi

read -r -d '' PROMPT <<PROMPT_EOF || true
You are Jarvis, running your WEEKLY SELF-LEARN pass (unattended, on a cron). This is not a chat reply. Nobody is waiting on the other end while you work; take the time to do it properly, then send one short Telegram summary at the end.

Your job: read the past week's Telegram conversation between you and Rob (below), and distil any DURABLE lessons into your persistent memory, exactly as you would if you'd noticed them live. Then report back what you learned.

The conversation slice for this week is in the file: $SLICE
Read it in full first.

You have TWO memory systems, both already documented in your CLAUDE.md / system context. Use whichever fits each lesson:
  1. The VAULT at $VAULT (this working dir) — your rich Obsidian knowledge, git-backed. Durable facts go in the right file: infra facts -> Context/Infrastructure.md, technical lessons -> Decisions/Technical Lessons Learned.md, people -> People/*.md, projects -> Projects/*.md, etc.
  2. The AUTO-MEMORY at /home/jarvis/.claude/projects/-data-memory/memory/ — one fact per file with frontmatter, indexed in MEMORY.md. This is for lessons about HOW you should work (feedback), ongoing project state, user facts, and reference pointers. Follow the exact format and rules in your system context (frontmatter, [[links]], one-line MEMORY.md pointer).

Rules for this pass:
- Extract only what is genuinely DURABLE and not already recorded. Skip transient chatter, one-off tasks already done, and anything the repo/git history already captures. Before writing, CHECK for an existing file/section that already covers it and update that rather than duplicating. Correct anything that turns out to be wrong.
- Typical catch: feedback Rob gave on how you work, corrections, preferences, new facts about people/projects/infra, decisions made, recurring friction worth a standing fix.
- Quality over volume. It is completely fine to learn nothing durable in a quiet week. Do NOT invent lessons to look busy.
- No em dashes anywhere (hard rule).
- When you edit the vault, commit it (the vault git workflow in CLAUDE.md); the auto-memory dir persists on disk on its own.

When done, your FINAL message must be a short, mobile-friendly Telegram summary for Rob: what you learned this week and where you filed it (a few bullet-ish lines, warm and direct, no preamble, no markdown headers/tables). If nothing durable came up, say so in one honest line. That final message is the ONLY thing that gets sent to Rob, so make it the summary and nothing else.
PROMPT_EOF

cd "$VAULT"
SUMMARY="$("$CLAUDE_BIN" -p "$PROMPT" --model claude-opus-4-8 --dangerously-skip-permissions 2>/tmp/jarvis-self-learn-err.$$)" || {
  echo "$(date -Iseconds) ERROR: claude invocation failed"
  cat /tmp/jarvis-self-learn-err.$$ || true
  echo "not advancing offset; will retry the same slice next run"
  exit 0
}

echo "--- summary ---"
echo "$SUMMARY"
echo "---------------"

# Success: advance the marker to where we sliced. Anything appended during the
# run (>= END) rolls into next week's pass.
echo "$END" > "$OFFSET_FILE"

send_tg "🧠 Weekly self-learn

$SUMMARY"

echo "----- $(date -Iseconds) self-learn end (offset now $END) -----"
