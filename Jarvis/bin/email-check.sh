#!/usr/bin/env bash
# Jarvis hourly email check, cron runs this at :05, 7am-11pm.
# 1. Sweeps known-junk senders (mail-bin-senders.txt) from INBOX to the bin.
# 2. Grabs anything new since the last run; if there is any, a one-shot
#    `claude -p` judges each email twice over:
#      a) is it clear sales/marketing/spam? -> binned (Deleted Messages,
#         30-day iCloud recovery). Rob asked for this on 2026-08-23.
#      b) does anything genuinely deserve a Telegram ping? Silence is the
#         default: routine automation and quiet-but-real mail never ping.
# 3. Appends a stats line + binned-mail record so the evening briefing can
#    give Rob a daily receipt of what the filter did.
# Set DRYRUN=1 to print would-be actions instead of binning/sending.
set -euo pipefail

VAULT="/data/memory"
BIN="$VAULT/Jarvis/bin"
LOG="$HOME/.local/state/jarvis-email-check.log"
STATS="$HOME/.local/state/jarvis-mail-stats.log"
BINLOG="$HOME/.local/state/jarvis-mail-binned.log"
TCONF="$HOME/.config/jarvis/telegram.env"
CLAUDE_BIN="$(command -v claude || echo "$HOME/.local/bin/claude")"
DRYRUN="${DRYRUN:-0}"

mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) email check start -----"

SEEN=0; SWEPT=0; BINNED=0; PINGED=0
write_stats() {
  # Only write a line when something actually happened; zero-lines are noise.
  if [ $((SEEN + SWEPT + BINNED + PINGED)) -gt 0 ]; then
    echo "$(date +%Y-%m-%d) $(date +%H:%M) seen=$SEEN swept=$SWEPT binned=$BINNED pinged=$PINGED" >>"$STATS"
  fi
  echo "----- $(date -Iseconds) email check end -----"
}
trap write_stats EXIT

SWEEP_OUT="$(python3 "$BIN/mail-tool.py" sweep)" || { SWEEP_OUT=""; echo "sweep failed (continuing)"; }
[ -n "$SWEEP_OUT" ] && echo "$SWEEP_OUT"
SWEPT="$(printf '%s\n' "$SWEEP_OUT" | awk '/^swept /{n+=$2} END{print n+0}')"

NEW="$(python3 "$BIN/mail-tool.py" new)" || { echo "fetch failed"; exit 0; }
if [ -z "$NEW" ]; then
  echo "no new mail"
  exit 0
fi
echo "new mail:"
echo "$NEW"
SEEN="$(printf '%s\n' "$NEW" | grep -c '^=== uid ')"

PROMPT='You are Jarvis running Rob'\''s hourly unattended email check (not a chat reply). Below are the emails that arrived in his iCloud inbox in the last hour, each headed by "=== uid N". You have two jobs.

JOB 1, bin the junk. Rob has asked for clear sales/marketing/spam to be deleted for him: promo blasts, discount offers, sale announcements, marketing newsletters, cold outreach, obvious spam. Be conservative. NEVER bin: personal mail from a real human, anything about family or school, receipts, order/shipping/delivery confirmations, account/security/password/billing mail, appointment or booking mail, anything legal or government, job-board alerts or anything from a recruiter (Rob is contract hunting; the Contract Hunt poll owns job mail, you never bin it), or anything you are not sure about. Unsure means keep, a wrongly kept promo costs nothing, a wrongly binned email costs trust.

JOB 2, decide if ANY email genuinely deserves interrupting Rob on Telegram.
Worth a ping: personal mail from a real human, anything about family or school, security/fraud alerts, money problems (failed payments, unexpected charges), cloud/hosting cost alerts (AWS Budgets, billing threshold emails: always ping, Rob runs a kill switch for runaway bills), a delivery arriving today, anything time-sensitive he would regret missing. ALWAYS ping any recruiter/agency reply about one of Rob'\''s job applications that needs action or shows movement: interview requests, pre-screening questionnaires or links to complete, callbacks, shortlisting, even rejections from a named human. Boilerplate "we received your application" acks are NOT worth a ping; a reply that asks Rob to DO something always is (missed one on 28 Sep, it sat unread for two days).
NOT worth a ping: marketing, newsletters, promos, social-media notifications, routine receipts and subscription renewals, automated service noise, and repeat nags about a long-standing account state Rob already knows about (e.g. Google Workspace cracky.co.uk storage/read-only/grace-period notices: that account has been read-only since March 2026 by choice, never ping it; Rob said 14 Oct "I don'"'"'t rly need to hear about emails like this"). A notice is only news if the state CHANGED recently. When in doubt, stay quiet; he checks email himself eventually.

Reply in EXACTLY this format, nothing else:
First line: "BIN: 123,456" (the uid numbers to bin, comma-separated) or "BIN: none".
Second line onward: either exactly NOTHING_INTERESTING, or ONLY the Telegram message to send: short and chat-shaped, warm and direct with a bit of dry wit, plain text (no markdown headers or tables), absolutely no em dashes. Lead with what the email is and why it matters. Do not use any tools. Get the BIN line right first time: never correct yourself, never add commentary or a second BIN line.

New emails:
'

# Memory of what we've already pinged, so recurring nags (weekly reminders
# about the same thing) aren't treated as news every time. Rob, 14 Oct:
# "they send one once per week and you message me about it... maybe remember".
PINGLOG="$HOME/.local/state/jarvis-mail-pinged.log"
CUTOFF="$(date -d '-60 days' +%Y-%m-%d)"
PAST="$( [ -f "$PINGLOG" ] && awk -F'\t' -v c="$CUTOFF" '$1 >= c {print "- " $1 ": " $2}' "$PINGLOG" | tail -40 )"
if [ -n "$PAST" ]; then
  PROMPT="${PROMPT%New emails:*}PINGS ALREADY SENT in the last 60 days (one per line). If a new email is the same notice/reminder/topic as one of these, do NOT ping again unless something has materially changed (new deadline, new amount, escalation). Rob has already heard it once; repeats are noise.
${PAST}

New emails:
"
fi

OUT="$(cd "$VAULT" && "$CLAUDE_BIN" -p "${PROMPT}${NEW}" --model sonnet --dangerously-skip-permissions 2>/dev/null)" || {
  echo "claude invocation failed"; exit 0; }
echo "verdict: $OUT"

# --- Job 1: bin what the judge flagged, but only uids we actually fetched ---
# Last BIN line wins (judge occasionally self-corrects mid-reply).
BIN_RAW="$(printf '%s\n' "$OUT" | grep -i '^BIN:' | tail -1 | sed 's/^[Bb][Ii][Nn]:[[:space:]]*//' | tr -d ' ')" || BIN_RAW=""
BIN_UIDS=""
if [ -n "$BIN_RAW" ] && [ "$BIN_RAW" != "none" ]; then
  for u in ${BIN_RAW//,/ }; do
    case "$u" in (*[!0-9]*|'') continue ;; esac
    if printf '%s\n' "$NEW" | grep -q "^=== uid ${u}\$"; then
      BIN_UIDS="${BIN_UIDS:+$BIN_UIDS,}$u"
    else
      echo "ignoring unknown uid $u from judge"
    fi
  done
fi
if [ -n "$BIN_UIDS" ]; then
  if [ "$DRYRUN" = "1" ]; then
    echo "DRYRUN: would bin uids $BIN_UIDS"
  else
    python3 "$BIN/mail-tool.py" bin "$BIN_UIDS" || echo "bin call failed"
    BINNED="$(printf '%s\n' "$BIN_UIDS" | tr ',' '\n' | grep -c .)"
    # Record who got binned so the evening briefing can show a receipt.
    for u in ${BIN_UIDS//,/ }; do
      printf '%s\n' "$NEW" | awk -v u="$u" -v d="$(date +%Y-%m-%d)" '
        $0=="=== uid "u {hit=1; next}
        hit && /^From: / {from=substr($0,7)}
        hit && /^Subject: / {print d"\t"from"\t"substr($0,10); exit}' >>"$BINLOG"
    done
    echo "binned uids: $BIN_UIDS"
  fi
fi

# --- Job 2: ping if the judge composed a message ---
# Only what follows the LAST BIN line is the message (drops any self-correction chatter).
MSG="$(printf '%s\n' "$OUT" | awk 'tolower($0) ~ /^bin:/ {buf=""; next} {buf=buf $0 "\n"} END {printf "%s", buf}' | sed -e '/./,$!d')" || MSG=""
case "$MSG" in
  *NOTHING_INTERESTING*) echo "nothing interesting"; ;;
  "") echo "empty verdict; staying quiet"; ;;
  *)
    if [ "$DRYRUN" = "1" ]; then
      echo "DRYRUN: would send the message above"
    else
      set -a; source "$TCONF"; set +a
      curl -sS --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
        --data-urlencode "text=📬 ${MSG}" >/dev/null && { PINGED=1; echo "pinged Rob"; printf '%s\t%s\n' "$(date +%Y-%m-%d)" "$(printf '%s' "$MSG" | tr '\n\t' '  ' | cut -c1-300)" >>"$PINGLOG"; } || echo "telegram send failed"
    fi
    ;;
esac
