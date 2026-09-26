#!/usr/bin/env bash
# Contract Hunt sourcing poll (Projects/Contract Hunt.md, pipeline step 2+3).
# 1. Scrapes JobServe (headless Chrome) for fresh UK contract roles across a
#    few keyword searches. No login, no CAPTCHA evasion, it's the public site.
# 2. Dedupes against previously-seen job ids.
# 3. Pulls job-alert emails (LinkedIn Job Alerts etc) from the inbox via
#    `mail-tool.py jobmail`. The hourly email judge never sees these senders,
#    so they cannot be binned as noise before we read them.
# 4. A one-shot `claude -p` triages new roles against Rob's profile. Everything
#    triaged goes to the digest log so the evening briefing can give a receipt.
# 4b. Suitable JobServe matches (6+; bar history 8+ at launch, 7+ from 31 Aug,
#    6+ "apply if near suitable" from Rob 4 Sept) are APPLIED TO automatically via
#    ~/contract-hunt/auto-apply.sh (Rob's standing approval, 2026-08-28: "send
#    an application, no need to ask, just tell me in the evening"). Applications
#    land in jarvis-contract-hunt-applied.log for the evening brief. No live
#    Telegram ping any more; only a failed apply pings, since that needs him.
#    Exception: a JobServe "Verify Human" CAPTCHA wall (exit 2 from
#    auto-apply.sh) is transient, so it queues for retry silently (see the
#    retry-queue block below) and only pings after 3 walled attempts.
# 5. Bins the alert emails it has actioned (30-day iCloud recovery).
# Set DRYRUN=1 to print instead of pinging/binning. SKIP_SCRAPE=1 skips the
# ~20 min JobServe scrape (email-only pass, handy for testing).
set -uo pipefail

VAULT="/data/memory"
TOOLS="/home/jarvis/tools/contract-hunt"
BIN="$VAULT/Jarvis/bin"
STATE="$HOME/.local/state"
LOG="$STATE/jarvis-contract-hunt.log"
SEEN="$STATE/jarvis-contract-hunt-seen.txt"
DIGEST="$STATE/jarvis-contract-hunt-digest.log"
TCONF="$HOME/.config/jarvis/telegram.env"
CLAUDE_BIN="$(command -v claude || echo "$HOME/.local/bin/claude")"
DRYRUN="${DRYRUN:-0}"
SKIP_SCRAPE="${SKIP_SCRAPE:-0}"

SEARCHES=("typescript" "react contract" "node aws" "next.js" "full stack javascript" "test automation playwright" "react native" "ai engineer" "agentic ai" "llm engineer" "ai consultant")

mkdir -p "$STATE"; touch "$SEEN"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) contract-hunt poll start -----"

# --- Retry queue: applications that hit JobServe's "Verify Human" CAPTCHA
# wall on an earlier run (rate-based bot filter, transient; first seen
# 2026-09-26). We never automate past a CAPTCHA, so walled applies are queued
# here and re-tried at the START of each poll, before our own scrape hammers
# the site. 3 attempts total, then ping Rob with the link (needs one human
# click). Format: <attempts-so-far>TAB<job json>. ---
RETRYQ="$STATE/jarvis-contract-hunt-retry.jsonl"
if [ -s "$RETRYQ" ] && [ "$DRYRUN" != "1" ]; then
  RQTMP="$(mktemp)"
  while IFS=$'\t' read -r attempts job; do
    [ -n "$job" ] || continue
    rtitle="$(printf '%s' "$job" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("title","?"))' 2>/dev/null)"
    rid="$(printf '%s' "$job" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("id",""))' 2>/dev/null)"
    "$HOME/contract-hunt/auto-apply.sh" "$job" </dev/null; rrc=$?
    if [ "$rrc" -eq 0 ]; then
      echo "retry-queue: applied to '$rtitle' on attempt $((attempts+1))"
      set -a; source "$TCONF"; set +a
      curl -sS --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
        --data-urlencode "text=💼 Applied on your behalf (retry after JobServe's bot-wall cleared):
${rtitle}" >/dev/null || echo "telegram send failed"
    elif [ "$rrc" -eq 2 ] && [ "$((attempts+1))" -lt 3 ]; then
      echo "retry-queue: '$rtitle' still walled (attempt $((attempts+1)) of 3), keeping"
      printf '%s\t%s\n' "$((attempts+1))" "$job" >>"$RQTMP"
    else
      echo "retry-queue: giving up on '$rtitle' after $((attempts+1)) attempts (rc=$rrc)"
      set -a; source "$TCONF"; set +a
      curl -sS --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
        --data-urlencode "text=💼 Auto-apply kept hitting JobServe's Verify Human wall for:
${rtitle}
It needs one human click, cover note is already written. Apply here:
https://www.jobserve.com/gb/en/W${rid}.jsap
Cover: ~/contract-hunt/out/cover-auto-${rid}.txt" >/dev/null || echo "telegram send failed"
    fi
  done <"$RETRYQ"
  mv "$RQTMP" "$RETRYQ"
fi

RAW="$(mktemp)"; NEWJOBS="$(mktemp)"
trap 'rm -f "$RAW" "$NEWJOBS"' EXIT

[ "$SKIP_SCRAPE" = "1" ] && SEARCHES=()
for q in "${SEARCHES[@]}"; do
  timeout 300 node "$TOOLS/scrape-jobserve.js" "$q" --days 2 --max 20 >>"$RAW" 2>>"$LOG.scrape" \
    || echo "scrape failed for '$q' (continuing)"
done

TOTAL="$(grep -c . "$RAW" || true)"
[ "${TOTAL:-0}" -eq 0 ] && echo "no jobs scraped"

# Dedupe: drop ids seen in previous runs, and repeats within this run.
python3 - "$RAW" "$SEEN" >"$NEWJOBS" <<'EOF'
import json, sys
raw, seenf = sys.argv[1], sys.argv[2]
seen = set(open(seenf).read().split())
out, batch = [], set()
for line in open(raw):
    line = line.strip()
    if not line: continue
    try: j = json.loads(line)
    except ValueError: continue
    jid = j.get('id', '')
    if not jid or jid in seen or jid in batch: continue
    batch.add(jid)
    out.append(j)
for j in out: print(json.dumps(j))
with open(seenf, 'a') as f:
    for jid in batch: f.write(jid + '\n')
EOF

NEW="$(grep -c . "$NEWJOBS" || true)"
echo "scraped=$TOTAL new=$NEW"

# --- Job-alert emails (LinkedIn etc). Dedupe LinkedIn job ids via the same
# seen file (prefixed li-) so a role in three alerts is triaged once. ---
JOBMAIL_RAW="$(mktemp)"; JOBMAIL_TXT="$(mktemp)"
python3 "$BIN/mail-tool.py" jobmail >"$JOBMAIL_RAW" 2>>"$LOG" || echo "jobmail fetch failed (continuing)"
MAIL_UIDS="$(sed -n 's/^=== uid \([0-9]*\)$/\1/p' "$JOBMAIL_RAW" | paste -sd, -)"
JOBMAIL=""
if [ -n "$MAIL_UIDS" ]; then
  python3 - "$JOBMAIL_RAW" "$SEEN" >"$JOBMAIL_TXT" <<'PYIN'
import re, sys
raw, seenf = sys.argv[1], sys.argv[2]
seen = set(open(seenf).read().split())
text = open(raw).read()
ids = list(dict.fromkeys(re.findall(r"linkedin\.com/jobs/view/(\d+)", text)))
fresh = [i for i in ids if "li-" + i not in seen]
for i in ids:
    if i not in fresh:
        text = text.replace(f"  https://www.linkedin.com/jobs/view/{i}\n",
                            f"  https://www.linkedin.com/jobs/view/{i}  (ALREADY TRIAGED, skip)\n")
tw = list(dict.fromkeys(re.findall(r"twine\.net/(projects/[a-z0-9-]+|ari/job/\d+)", text)))
freshtw = [i for i in tw if "tw-" + i.replace("/", "_") not in seen]
for i in tw:
    if i not in freshtw:
        text = text.replace(f"  https://www.twine.net/{i}\n",
                            f"  https://www.twine.net/{i}  (ALREADY TRIAGED, skip)\n")
with open(seenf, "a") as f:
    for i in fresh: f.write("li-" + i + "\n")
    for i in freshtw: f.write("tw-" + i.replace("/", "_") + "\n")
print(text)
PYIN
  JOBMAIL="$(cat "$JOBMAIL_TXT")"
  echo "job-alert emails: uids $MAIL_UIDS"
fi
rm -f "$JOBMAIL_RAW" "$JOBMAIL_TXT"

if [ "${NEW:-0}" -eq 0 ] && [ -z "$MAIL_UIDS" ]; then echo "nothing new"; exit 0; fi

PROMPT='You are Jarvis triaging freshly scraped UK contract job ads for Rob (unattended cron, not a chat). One JSON object per line below.

ROB PROFILE: senior full-stack dev, TypeScript/React/Node/AWS (serverless, SQS/SNS/DynamoDB), 13+ years. Wants OUTSIDE IR35 contract work via his own Ltd, prefers FULLY REMOTE (UK), target £400-450/day, will look at £350+ if the fit is strong. EQUALLY A TARGET (Rob, 14 Sept 2026): AI / agentic-systems roles (AI engineer, LLM engineer, agentic AI developer, AI automation/integration consultant). Rob has designed, built and operated a production agentic AI system continuously for over a year (LLM agents with persistent memory, tool use, scheduled autonomy, email/calendar/chat integrations) plus multi-agent Claude Code work; score these like core-stack roles. TS/Node-flavoured agent work can hit 8-9; Python-first roles are fine up to 7 when the substance is agent/LLM system design, RAG or LLM integration rather than deep ML. Model training / research-level ML / data-science-first roles = wrong fit, reject. This runs alongside a full-time job he is not disclosing, so prefer async/flexible/deliverable-based work; heavy-meeting or rigid-hours gigs score lower. Hybrid up to 2 days/week onsite in a major city (London, Manchester etc) is acceptable if the stack fits and the rate covers travel (Rob, 2 Sept 2026: he will hotel it for the right money); score those 6 when stack and rate fit, never 7+. Mostly/fully onsite (3+ days/week) = reject. Inside IR35 or umbrella-only = reject (note it, do not ping). Wrong stack (Java, .NET, Dynamics, PHP etc where TS/React is incidental) = reject.

Duplicate roles (same job via several agencies) count once; mention the duplicate agencies on one line.

Two sources may follow. "JobServe jobs" are scraped ads with full text. "Job-alert emails" (LinkedIn Job Alerts etc) list several roles per email with only title, company and a link; the Links section lists them in the same order as the job cards. Triage each listed role as best you can from title + company; where the email gives too little to judge, score 5 and say "needs a look" rather than rejecting. Links marked ALREADY TRIAGED were scored in a previous run: skip them entirely. Ignore the alert boilerplate (it is not a role). Twine digest emails (twine.net links) carry real descriptions, so triage those on the merits, not as "email-only, score 5". Twine is a freelance gig marketplace: most posts are small low-budget gigs, so hold Twine to the same rate bar (reject anything clearly under ~£350/day equivalent; tiny fixed budgets like $30-250 = reject). A 6+ Twine role does NOT trigger an automatic application (no way to apply programmatically); it pings Rob to apply himself, so 6+ still means "genuinely worth his time".

Reply in EXACTLY this format:
First a line per NEW job/role: "DIGEST: <score 0-9> | <title> | <rate or n/a> | <location/remote> | <agency/company> | <permalink or url>". Score 6-9 = apply-now fit (triggers an automatic application sent as Rob, standing approval "apply to them all if near suitable", 4 Sept), 5 = plausible but too thin or too ambiguous to apply blind, 0-4 = reject.
Then exactly one line: NOTHING_INTERESTING if nothing scored 6+, otherwise STRONG_MATCHES. Nothing else. An application goes out as Rob on every 6+, so score 6+ only when the ad is outside IR35 or IR35-unstated (never stated-inside), remote or hybrid up to 2 days/week, rate £350+ (or unstated), and the stack genuinely fits. Reserve 8-9 for squarely TS/React/Node/AWS fully-remote outside-IR35 bullseyes; 7 = strong-but-imperfect (adjacent stack emphasis, rate at the edge, minor ambiguity); 6 = near suitable (hybrid up to 2 days/week with fitting stack and travel-covering rate, or IR35/remote unstated but plausibly fine). Use 5 for email-only listings with no detail ("needs a look") and ads too vague to commit an application to. HARD deal-breakers score 4 or below no matter what: stated inside IR35, umbrella-only, 3+ days/week onsite, wrong stack, rate clearly under £350/day.

'

INPUT="JobServe jobs:
$(cat "$NEWJOBS")

Job-alert emails:
${JOBMAIL:-none}
"

OUT="$(cd "$VAULT" && "$CLAUDE_BIN" -p "${PROMPT}${INPUT}" --model sonnet --dangerously-skip-permissions 2>/dev/null)" || {
  echo "claude invocation failed"; exit 0; }
echo "verdict:"; echo "$OUT"

# Digest lines -> log for the evening brief
printf '%s\n' "$OUT" | grep -i '^DIGEST:' | while IFS= read -r line; do
  echo "$(date +%Y-%m-%d) $(date +%H:%M) ${line#DIGEST: }" >>"$DIGEST"
done

# Auto-apply: every JobServe job the judge scored 6+ (matched by permalink or
# id back to the scraped JSON) gets an application via auto-apply.sh.
APPLIED_N=0; FAILED_N=0; WALLED_N=0; FAILED_MSG=""; SENT_MSG=""
while IFS= read -r line; do
  score="$(printf '%s' "$line" | sed 's/^DIGEST:[[:space:]]*//' | cut -d'|' -f1 | tr -dc '0-9')"
  [ -n "$score" ] && [ "$score" -ge 6 ] || continue
  link="$(printf '%s' "$line" | grep -oE 'jobserve\.com/[A-Za-z0-9]+' | tail -1)"
  [ -n "$link" ] || continue
  job="$(grep -F "$link" "$NEWJOBS" | head -1)"
  [ -n "$job" ] || { echo "auto-apply: no scraped job for $link (email-only role, nothing to submit)"; continue; }
  # </dev/null is load-bearing: claude -p inside auto-apply.sh slurps inherited
  # stdin, which is this loop's DIGEST list, so a second 6+ role never got read
  # (caught 2026-09-15: 7-scored role silently skipped after the first apply).
  if [ "$DRYRUN" = "1" ]; then
    echo "DRYRUN: would auto-apply to $link"; DRYRUN=1 "$HOME/contract-hunt/auto-apply.sh" "$job" </dev/null; continue
  fi
  "$HOME/contract-hunt/auto-apply.sh" "$job" </dev/null; rc=$?
  if [ "$rc" -eq 0 ]; then
    APPLIED_N=$((APPLIED_N+1)); SENT_MSG="${SENT_MSG}${line#DIGEST: }
"
  elif [ "$rc" -eq 2 ]; then
    # CAPTCHA wall: queue for automatic retry next poll, no ping (Rob, 26 Sept:
    # fix issues myself, only interrupt him when it genuinely needs him).
    WALLED_N=$((WALLED_N+1)); printf '1\t%s\n' "$job" >>"$RETRYQ"
    echo "auto-apply: walled, queued for retry next poll: $link"
  else FAILED_N=$((FAILED_N+1)); FAILED_MSG="${FAILED_MSG}${line#DIGEST: }
"; fi
done < <(printf '%s\n' "$OUT" | grep -i '^DIGEST:')
echo "auto-apply: sent=$APPLIED_N walled=$WALLED_N failed=$FAILED_N"

# Instant receipt per application (Rob, 6 Sept: he was missing the evening-brief
# receipts, so each sent application now pings him a one-liner immediately).
if [ "$APPLIED_N" -gt 0 ] && [ "$DRYRUN" != "1" ]; then
  set -a; source "$TCONF"; set +a
  curl -sS --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=💼 Applied on your behalf just now:
${SENT_MSG}Full detail in tonight's brief as usual." >/dev/null || echo "telegram send failed"
fi

# Twine matches can't be auto-applied (no API; applying needs Rob's login and
# free tier is 1 pitch/day), so a 6+ Twine role pings Rob to spend the pitch.
TWINE_MSG=""
while IFS= read -r line; do
  score="$(printf '%s' "$line" | sed 's/^DIGEST:[[:space:]]*//' | cut -d'|' -f1 | tr -dc '0-9')"
  [ -n "$score" ] && [ "$score" -ge 6 ] || continue
  printf '%s' "$line" | grep -q 'twine\.net' || continue
  TWINE_MSG="${TWINE_MSG}${line#DIGEST: }
"
done < <(printf '%s\n' "$OUT" | grep -i '^DIGEST:')
if [ -n "$TWINE_MSG" ]; then
  if [ "$DRYRUN" = "1" ]; then
    echo "DRYRUN: would ping Twine matches:"; printf '%s' "$TWINE_MSG"
  else
    set -a; source "$TCONF"; set +a
    curl -sS --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
      --data-urlencode "text=💼 Twine match worth a look (I can't apply there, free tier = 1 pitch/day, needs your login):
${TWINE_MSG}" >/dev/null || echo "telegram send failed"
  fi
fi

# Only a failed application is worth interrupting Rob for.
if [ "$FAILED_N" -gt 0 ] && [ "$DRYRUN" != "1" ]; then
  set -a; source "$TCONF"; set +a
  curl -sS --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=💼 Tried to auto-apply and it fell over, might want a look:
${FAILED_MSG}Log: ~/.local/state/jarvis-contract-hunt.log" >/dev/null || echo "telegram send failed"
fi

# Alert emails are actioned: bin them (Deleted Messages, 30-day recovery).
if [ -n "$MAIL_UIDS" ]; then
  if [ "$DRYRUN" = "1" ]; then
    echo "DRYRUN: would bin job-alert uids $MAIL_UIDS"
  else
    python3 "$BIN/mail-tool.py" bin "$MAIL_UIDS" && echo "binned job-alert uids $MAIL_UIDS" || echo "bin failed"
  fi
fi
echo "----- $(date -Iseconds) contract-hunt poll end -----"
