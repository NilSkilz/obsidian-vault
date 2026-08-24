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
  ASK='Compose Rob'\''s MORNING briefing. Check: today'\''s weather (`Jarvis/bin/weather.sh today`, worth a quick line), today'\''s calendar (`Jarvis/bin/calendar.sh today`, family/personal events), today'\''s Trello "To Do"/"In Progress" cards (`Jarvis/bin/trello.sh cards "To Do"` and `... "In Progress"`), today'\''s Todoist tasks (`Jarvis/bin/todoist.sh today` for due-today items, plus `Jarvis/bin/todoist.sh list "Shared Todo"` for the open household list, no due dates but worth a mention if something stands out), Ops/Tasks.md "Now" items, anything blocked in Ops/Proposals.md that needs his call, and yesterday'\''s daily log for open follow-ups. Write it warm, friendly and upbeat, like a good morning message from someone who has his back. Open with a genuine greeting. Emojis are welcome (tasteful, not spammy). Length is up to you: say what is worth saying, no artificial line limit, but stay chat-shaped for Telegram, no headers/markdown tables. Lead with anything that actually needs him today (calendar events included); skip sections with nothing to say.'
else
  ASK='Compose Rob'\''s EVENING briefing. Check today'\''s daily log (Daily/YYYY-MM-DD.md) for what actually happened, any Trello cards moved/blocked today, any Todoist household tasks still open (`Jarvis/bin/todoist.sh today` and `Jarvis/bin/todoist.sh list "Shared Todo"`), tomorrow'\''s weather (`Jarvis/bin/weather.sh tomorrow`, so he can plan), tomorrow'\''s calendar (`Jarvis/bin/calendar.sh tomorrow`, so he knows what'\''s coming), and anything left open in Ops/Proposals.md. Write it warm, friendly and relaxed, like a wind-down note at the end of the day. Emojis are welcome (tasteful, not spammy). Length is up to you: say what is worth saying, no artificial line limit, but stay chat-shaped for Telegram, no headers/markdown tables. Focus on what moved, what'\''s still waiting on him, and anything on tomorrow'\''s calendar worth flagging tonight.'

  # Fold the Aimee comms-log nudge into this same message, but only if today has
  # no comms entry yet (if Rob already told me and I logged it, skip the ask).
  COMMSLOG="$VAULT/Context/Aimee Comms Log.md"
  TODAY="$(date +%Y-%m-%d)"
  COMMS_FALLBACK=""
  if ! { [ -f "$COMMSLOG" ] && grep -q "^## ${TODAY}" "$COMMSLOG"; }; then
    ASK="${ASK} Then, to close, add a short natural line asking Rob what he told Aimee today (plans, decisions, feelings, logistics) so I can log it for the record, and to just say if it was a quiet day. Keep it as one flowing message, not a separate section."
    COMMS_FALLBACK="🗒 And for the comms log: what did you tell Aimee today? Anything worth having on record (plans, decisions, feelings, logistics) and I'll log it. If nothing notable, just say so and I'll note a quiet day."
  fi

  # Fold the Tide mood check-in into this same message too, but only if Rob has
  # logged no mood in Tide's journal today. Silently skips if the API is down.
  MOOD_FALLBACK=""
  HCONF="$HOME/.config/jarvis/health.env"
  if [ -f "$HCONF" ]; then
    set -a; source "$HCONF"; set +a
    MBASE="${TIDE_API_BASE:-http://192.168.1.16:3001}/api/family"
    MTREND="$(curl -sS --max-time 10 "${MBASE}/journal?range=2" \
      -H "X-Jarvis-Key: ${JARVIS_API_KEY:-}" -H "X-Jarvis-User: rob" 2>/dev/null)" || MTREND=""
    if [ -n "$MTREND" ]; then
      MDAY="$(echo "$MTREND" | jq -r '.today // empty' 2>/dev/null)"
      if [ -n "$MDAY" ]; then
        MLOGGED="$(echo "$MTREND" | jq --arg d "$MDAY" \
          '[.entries[] | select(.date==$d and .mood!=null)] | length' 2>/dev/null)"
        if [ "${MLOGGED:-0}" = "0" ]; then
          ASK="${ASK} Also, still within the same single flowing message, gently invite Rob to a mood check-in: how today'\''s been on the whole, a 1-5 (1 rough, 5 great) or just how he'\''s doing, and note you'\''ll log it. Weave it in naturally, do not make it a separate section or a second message."
          MOOD_FALLBACK="🌤 And how's today been on the whole? Give me a 1-5 (1 rough, 5 great) or just tell me how you're doing, and I'll log it. Skip if you'd rather not."
        fi
      fi
    fi
  fi

  # Claude usage snapshot (Rob asked for this in the evening brief, 2026-08-21).
  # Fetched here so the model just states it rather than running anything.
  USAGE_LINE="$("$VAULT/Jarvis/bin/usage.sh" brief 2>/dev/null || true)"
  if [ -n "$USAGE_LINE" ]; then
    ASK="${ASK} Also include one short line on Claude usage, from this data (do not run any tool for it, just state it naturally): ${USAGE_LINE}."
  fi

  # Email-filter receipt (Rob gave the judge delete powers on 2026-08-23; this
  # is his daily audit trail of what it actually did).
  MAILSTATS="$HOME/.local/state/jarvis-mail-stats.log"
  MAILBINLOG="$HOME/.local/state/jarvis-mail-binned.log"
  MAILSUM=""
  if [ -f "$MAILSTATS" ]; then
    MAILSUM="$(awk -v d="$TODAY" '
      $1==d { for (i=3; i<=NF; i++) { split($i, kv, "="); t[kv[1]] += kv[2] } }
      END { if (t["seen"]+t["swept"]+t["binned"]+t["pinged"] > 0)
              printf "%d new emails, pinged him about %d, binned %d as sales/spam, swept %d from known-junk senders",
                     t["seen"], t["pinged"], t["binned"], t["swept"] }' "$MAILSTATS" 2>/dev/null)" || MAILSUM=""
  fi
  if [ -n "$MAILSUM" ]; then
    MAILWHO="$(grep "^${TODAY}	" "$MAILBINLOG" 2>/dev/null | cut -f2 | sed 's/ *<[^>]*>//' | sort -u | paste -sd ', ' -)" || MAILWHO=""
    ASK="${ASK} Also include one short receipt line on the email filter, from this data (no tools, just state it naturally): ${MAILSUM}${MAILWHO:+ (binned: ${MAILWHO})}. If anything was binned, note it sits in Deleted Messages for 30 days if he wants it back."
  fi

  # Ambient signal from the junk-mail traffic (Rob, 2026-08-24: be intuitive,
  # don't make him define per-site rules). No sender filter: hand the model a
  # week of everything swept/binned and let its own judgment decide what, if
  # anything, a mate would remark on. FetLife subjects carry who commented or
  # messaged; other senders can carry their own stories.
  SWEPTLOG="$HOME/.local/state/jarvis-mail-swept.log"
  WEEKAGO="$(date -d '6 days ago' +%Y-%m-%d)"
  MAILWEEK="$(cat "$SWEPTLOG" "$MAILBINLOG" 2>/dev/null | awk -F'\t' -v w="$WEEKAGO" '$1 >= w {print $1" | "$2" | "$3}' | sort | tail -150)" || MAILWEEK=""
  if [ -n "$MAILWEEK" ]; then
    ASK="${ASK} Also: below is this week'\''s pile of emails I auto-binned as junk before Rob ever saw them (one per line, date | sender | subject). Apps like FetLife also push-notify his phone, so never tell him to go check these emails. Read the pile the way a mate glancing at it would: if something today adds up to a genuine story worth a short aside (a FetLife post picking up comments, noticeably more messages than usual, one name cropping up again and again, a sudden flurry from some service that hints something happened in his life), weave ONE conversational observation into the briefing. Your judgment on what counts as interesting, it does not have to be FetLife and most days nothing will qualify. If nothing stands out, say nothing about any of this. The pile: ${MAILWEEK}"
  fi
fi

PROMPT="You are Jarvis, writing an unattended briefing message to Rob (not a chat reply to a prompt — he will just receive this as a Telegram message). ${ASK} No em dashes. If genuinely nothing happened and nothing is waiting on him, a one-line 'quiet one, nothing needs you' is fine — don't pad it."

cd "$VAULT"
BRIEF="$("$CLAUDE_BIN" -p "$PROMPT" --model claude-opus-4-8 --dangerously-skip-permissions 2>/tmp/jarvis-briefing-err.$$)" || {
  echo "$(date -Iseconds) ERROR: claude invocation failed"
  cat /tmp/jarvis-briefing-err.$$
  rm -f /tmp/jarvis-briefing-err.$$
  # If the briefing failed but a comms and/or mood ask was due, at least send
  # those so the daily records don't silently go missing.
  if [ "$MODE" = "evening" ] && { [ -n "${COMMS_FALLBACK:-}" ] || [ -n "${MOOD_FALLBACK:-}" ]; }; then
    FB="$(printf '%s' "${COMMS_FALLBACK:-}")"
    [ -n "${COMMS_FALLBACK:-}" ] && [ -n "${MOOD_FALLBACK:-}" ] && FB="${FB}"$'\n\n'
    FB="${FB}${MOOD_FALLBACK:-}"
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
      --data-urlencode "text=${FB}" >/dev/null || true
    echo "$(date -Iseconds) sent comms/mood-only fallback"
  fi
  exit 0
}
rm -f /tmp/jarvis-briefing-err.$$

echo "$BRIEF"

curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=${BRIEF:0:4000}" >/dev/null

echo "----- $(date -Iseconds) briefing ($MODE) end -----"
