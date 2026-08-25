#!/usr/bin/env bash
# Contract Hunt sourcing poll (Projects/Contract Hunt.md, pipeline step 2+3).
# 1. Scrapes JobServe (headless Chrome) for fresh UK contract roles across a
#    few keyword searches. No login, no CAPTCHA evasion, it's the public site.
# 2. Dedupes against previously-seen job ids.
# 3. Pulls job-alert emails (LinkedIn Job Alerts etc) from the inbox via
#    `mail-tool.py jobmail`. The hourly email judge never sees these senders,
#    so they cannot be binned as noise before we read them.
# 4. A one-shot `claude -p` triages new roles against Rob's profile: strong
#    matches ping Telegram immediately, everything triaged goes to the digest
#    log so the evening briefing can give a daily receipt.
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

SEARCHES=("typescript" "react contract" "node aws" "next.js" "full stack javascript" "test automation playwright" "react native")

mkdir -p "$STATE"; touch "$SEEN"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) contract-hunt poll start -----"

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
with open(seenf, "a") as f:
    for i in fresh: f.write("li-" + i + "\n")
print(text)
PYIN
  JOBMAIL="$(cat "$JOBMAIL_TXT")"
  echo "job-alert emails: uids $MAIL_UIDS"
fi
rm -f "$JOBMAIL_RAW" "$JOBMAIL_TXT"

if [ "${NEW:-0}" -eq 0 ] && [ -z "$MAIL_UIDS" ]; then echo "nothing new"; exit 0; fi

PROMPT='You are Jarvis triaging freshly scraped UK contract job ads for Rob (unattended cron, not a chat). One JSON object per line below.

ROB PROFILE: senior full-stack dev, TypeScript/React/Node/AWS (serverless, SQS/SNS/DynamoDB), 13+ years. Wants OUTSIDE IR35 contract work via his own Ltd, FULLY REMOTE (UK), target £400-450/day, will look at £350+ if the fit is strong. This runs alongside a full-time job he is not disclosing, so prefer async/flexible/deliverable-based work; heavy-meeting or rigid-hours gigs score lower. Hybrid/onsite = reject. Inside IR35 or umbrella-only = reject (note it, do not ping). Wrong stack (Java, .NET, Dynamics, PHP etc where TS/React is incidental) = reject.

Duplicate roles (same job via several agencies) count once; mention the duplicate agencies on one line.

Two sources may follow. "JobServe jobs" are scraped ads with full text. "Job-alert emails" (LinkedIn Job Alerts etc) list several roles per email with only title, company and a link; the Links section lists them in the same order as the job cards. Triage each listed role as best you can from title + company; where the email gives too little to judge, score 5 and say "needs a look" rather than rejecting. Links marked ALREADY TRIAGED were scored in a previous run: skip them entirely. Ignore the alert boilerplate (it is not a role).

Reply in EXACTLY this format:
First a line per NEW job/role: "DIGEST: <score 0-9> | <title> | <rate or n/a> | <location/remote> | <agency/company> | <permalink or url>". Score 8-9 = apply-now fit, 5-7 = plausible, 0-4 = reject.
Then either exactly NOTHING_INTERESTING, or (only if at least one job scores 8+) a line "PING:" followed by a short Telegram message: chat-shaped, dry, plain text, no em dashes. Lead with the best role: title, rate, remote status, agency, permalink. Max 3 roles per ping. End with: reply "draft it" and I will write the application.

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

# Ping if the judge composed one
MSG="$(printf '%s\n' "$OUT" | sed -n '/^PING:/,$p' | sed '1s/^PING:[[:space:]]*//' | sed -e '/./,$!d')"
if [ -n "$MSG" ] && ! printf '%s' "$OUT" | grep -q 'NOTHING_INTERESTING'; then
  if [ "$DRYRUN" = "1" ]; then
    echo "DRYRUN: would ping:"; echo "$MSG"
  else
    set -a; source "$TCONF"; set +a
    curl -sS --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
      --data-urlencode "text=💼 ${MSG}" >/dev/null && echo "pinged Rob" || echo "telegram send failed"
  fi
else
  echo "no ping-worthy roles"
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
