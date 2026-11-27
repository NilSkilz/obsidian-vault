#!/usr/bin/env bash
# Monthly overtime-claim reminder for Rob (asked 27 Nov 2026).
# Superdry payroll needs the OT email on the Thursday the week before payday.
# Payday = last Friday of the month, EXCEPT December, which pays the Friday
# before Christmas week (Dec 2025 paid Fri 19th, not the 26th).
# Cron runs this daily; it only pings on deadline day, and pings once.
#
# Usage: ot-reminder.sh [--dry-run YYYY-MM-DD]
set -euo pipefail

TCONF="$HOME/.config/jarvis/telegram.env"
LOG="$HOME/.local/state/jarvis-ot-reminder.log"
mkdir -p "$(dirname "$LOG")"

DRY=""; TODAY="$(date +%F)"
if [ "${1:-}" = "--dry-run" ]; then DRY=1; TODAY="${2:-$TODAY}"; fi
[ -z "$DRY" ] && exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) ot reminder (today=$TODAY) -----"

read -r DEADLINE PAYDAY < <(python3 -I - "$TODAY" <<'PY'
import sys, datetime as dt, calendar
t = dt.date.fromisoformat(sys.argv[1])
def payday(y, m):
    last = dt.date(y, m, calendar.monthrange(y, m)[1])
    d = last - dt.timedelta(days=(last.weekday() - 4) % 7)
    if m == 12 and d.day >= 22:   # Christmas week: paid a week early
        d -= dt.timedelta(days=7)
    return d
# deadline = Thursday of the week before payday (payday - 8 days)
p = payday(t.year, t.month)
print((p - dt.timedelta(days=8)).isoformat(), p.isoformat())
PY
)
echo "deadline=$DEADLINE payday=$PAYDAY"
[ "$TODAY" = "$DEADLINE" ] || { echo "not deadline day"; exit 0; }

PD="$(date -d "$PAYDAY" '+%a %-d %b')"
MSG="💷 Overtime email day. Payroll needs your OT claim today for payday ${PD}. Send it with the dates and hours for any extra work this month (it lives in your Outlook drafts if you started one)."
if [ -n "$DRY" ]; then echo "WOULD SEND: $MSG"; exit 0; fi

set -a; . "$TCONF"; set +a
curl -sS --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" --data-urlencode "text=${MSG}" >/dev/null \
  && echo "pinged Rob" || echo "telegram send failed"
