#!/usr/bin/env bash
# Jarvis Slack check — polls Rob's work Slack (Superdry) for new DMs and
# @mentions, pings Telegram only when a real human needs him.
#
# Why polling: the claude.ai Slack connector is pull-only. True push (Events
# API / Socket Mode) needs a Slack app installed in the Superdry workspace,
# which is admin-gated corporate territory. So: cron, every 15 min in work
# hours, weekdays.
#
# The window is tracked in a state file (unix ts). Each run searches only
# messages after the last successful run, so nothing is double-pinged and a
# failed run re-covers its window next time. Set DRYRUN=1 to print instead
# of sending.
set -euo pipefail

VAULT="/data/memory"
STATE="$HOME/.local/state/jarvis-slack-check.ts"
LOG="$HOME/.local/state/jarvis-slack-check.log"
STATS="$HOME/.local/state/jarvis-slack-stats.log"
TCONF="$HOME/.config/jarvis/telegram.env"
CLAUDE_BIN="$(command -v claude || echo "$HOME/.local/bin/claude")"
DRYRUN="${DRYRUN:-0}"
# Cron jobs run Opus 5 (model split, 2026-08-24); Fable stays reserved for chat.
MODEL="${JARVIS_SLACK_MODEL:-claude-opus-5}"
ROB_SLACK_ID="U02NT2J251S"

mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) slack check start -----"

NOW="$(date +%s)"
LAST="$(cat "$STATE" 2>/dev/null || true)"
case "$LAST" in (*[!0-9]*|'') LAST=$((NOW - 3600)) ;; esac
# Never look back more than 12h (first run, or long downtime): stale pings
# about yesterday's Slack are noise, not signal.
[ "$LAST" -lt $((NOW - 43200)) ] && LAST=$((NOW - 43200))
echo "window: $LAST -> $NOW"

PROMPT="You are Jarvis running Rob's unattended work-Slack check (a cron job, not a chat reply). Rob's Slack user id is ${ROB_SLACK_ID}.

Use ToolSearch to load mcp__claude_ai_Slack__slack_search_public_and_private, then run EXACTLY two searches, both with after=\"${LAST}\", sort=\"timestamp\", include_context=false, response_format=\"concise\":
1. query \"to:me\" with channel_types \"im,mpim\" (new DMs and group DMs to Rob)
2. query \"<@${ROB_SLACK_ID}>\" with channel_types \"public_channel,private_channel\" (new channel mentions of Rob)

Then decide whether anything genuinely deserves interrupting Rob on Telegram.
Worth a ping: a real human DMing Rob or mentioning him with something that needs him: a question, a request, a blocker, a heads-up he would regret missing.
NOT worth a ping: bot or app DMs (Jira, GitHub, calendar and CI bots), automated notifications, messages Rob sent himself, bare thank-yous or pleasantries with nothing to act on. When in doubt about a real human's message, ping; when in doubt about automation, stay quiet.

CRITICAL, before pinging about ANY message: check Rob hasn't already dealt with it. Load mcp__claude_ai_Slack__slack_read_thread (threaded messages) or mcp__claude_ai_Slack__slack_read_channel (DMs, to see the conversation after the message) and look at what happened next. If Rob (${ROB_SLACK_ID}) has replied after it, or the thread shows it resolved, it is handled: say nothing about it. Reminding Rob of things he already answered is worse than silence (it happened 2026-08-24 with two DMs he'd already replied to).

If several things landed, combine them into ONE message.

When something IS worth a ping and you can confidently answer it yourself (from the message, its thread, or the vault at ${VAULT}: Context/Work Context.md and Daily/ are fair game to Read), append a suggested reply Rob can copy-paste, on its own line as: Suggested reply: ... . Only do this when you actually know the answer; a guess dressed as a draft is worse than nothing, so if unsure just describe what they want.
Confluence (Rob's standing permission, 2026-08-27): if the question is a factual one about Superdry work that a Confluence page would plausibly answer (how does X work, where is the doc for Y, what did we decide about Z, testing steps, ticket context), you MAY load mcp__claude_ai_Atlassian__searchConfluenceUsingCql and run ONE or TWO targeted searches (the TP space is the usual home), and getConfluencePage on a hit if needed. If a page clearly answers it, the suggested reply should be the page link plus a one-line gist (that is exactly how Rob answered Isaac on 2026-08-27: a Confluence link). Use discretion: skip Confluence for chit-chat, scheduling, opinion asks, anything obviously answerable from the thread, or vague questions where you would be fishing. Rob said do not go overboard and search for every little thing. The thread and channel read tools are ONLY for the handled-check above and for context on a message you are already going to ping about; never for anything else.

Reply in EXACTLY one of two forms, nothing else:
- the single word NOTHING_NEW
- ONLY the Telegram message to send: short and chat-shaped, warm and direct with a bit of dry wit, plain text (no markdown headers or tables), absolutely no em dashes. Lead with who wants what.

Do NOT send, react to, or mark anything on Slack. Read-only. Beyond the searches, the thread-read and vault-Read exceptions above, use no other tools."

OUT="$(cd "$VAULT" && "$CLAUDE_BIN" -p "$PROMPT" --model "$MODEL" --dangerously-skip-permissions 2>/dev/null)" || {
  echo "claude invocation failed; window not advanced"; exit 0; }
echo "verdict: $OUT"

# Only advance the window after a successful judge run.
if [ "$DRYRUN" != "1" ]; then
  printf '%s' "$NOW" >"$STATE"
fi

case "$OUT" in
  *NOTHING_NEW*|"")
    echo "nothing new"
    ;;
  *)
    if [ "$DRYRUN" = "1" ]; then
      echo "DRYRUN: would send the message above"
    else
      set -a; source "$TCONF"; set +a
      curl -sS --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
        --data-urlencode "text=💬 ${OUT}" >/dev/null \
        && { echo "pinged Rob"; echo "$(date +%Y-%m-%d) $(date +%H:%M) pinged" >>"$STATS"; } \
        || echo "telegram send failed"
    fi
    ;;
esac
echo "----- $(date -Iseconds) slack check end -----"
