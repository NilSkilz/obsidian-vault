#!/usr/bin/env bash
# Jarvis cron health check, runs once a day.
# Why this exists: the 2-hourly heartbeat died on a shell quoting bug on
# 2026-08-25 and nobody noticed for 8 weeks / 479 failed runs, because a cron
# that fails still "runs". This watches two things per job: is its log fresh,
# and does its tail contain a hard failure signature. Pings Rob only on a
# problem, stays silent otherwise.
set -uo pipefail

STATE="$HOME/.local/state"
LOG="$STATE/jarvis-cron-health.log"
TCONF="$HOME/.config/jarvis/telegram.env"

# label|logfile|max age in hours (0 = don't age-check, error-scan only)
JOBS="
heartbeat|$STATE/jarvis-heartbeat.log|10
email check|$STATE/jarvis-email-check.log|10
glitchtip check|$STATE/jarvis-glitchtip-check.log|10
contract hunt|$STATE/jarvis-contract-hunt.log|15
evening briefing|$STATE/jarvis-briefing.log|26
food nudge|$STATE/jarvis-food-nudge.log|26
vault git sync|$STATE/memory-git-sync.log|26
finance sync|$HOME/finance/sync.log|30
weekly self-learn|$STATE/jarvis-self-learn.log|192
movie recs|$STATE/jarvis-movie-recs.log|192
idea scout|$STATE/jarvis-inspiration.log|192
blog suggest|$STATE/jarvis-blog-suggest.log|192
docker updates|$STATE/jarvis-docker-updates.log|192
ev planner errors|$STATE/ev-planner/errors.log|0
ev cost errors|$STATE/ev-cost/errors.log|0
"

# Hard failure signatures. A job can log the word "error" (or "killed") in
# normal prose, so these are deliberately shapes that only appear when
# something actually broke, and the match is CASE SENSITIVE for the same
# reason: a weekly idea-scout write-up containing "killed" is not an outage.
SIGS='syntax error|command not found|Traceback \(most recent call last\)|No such file or directory|Permission denied|Killed process|Out of memory|unbound variable'

PROBLEMS=""
now=$(date +%s)

while IFS='|' read -r label file maxage; do
  [ -z "${label:-}" ] && continue
  if [ ! -e "$file" ]; then
    # An error log that has never been written is good news, not a problem.
    [ "$maxage" = "0" ] && continue
    PROBLEMS="${PROBLEMS}- ${label}: no log at all (${file})"$'\n'
    continue
  fi

  if [ "$maxage" != "0" ]; then
    age_h=$(( (now - $(stat -c %Y "$file")) / 3600 ))
    if [ "$age_h" -gt "$maxage" ]; then
      PROBLEMS="${PROBLEMS}- ${label}: silent for ${age_h}h (expected within ${maxage}h)"$'\n'
    fi
  fi

  # Only ever scan what was written recently. These logs are append-only, so a
  # blanket tail would re-report a failure that was fixed weeks ago, every day,
  # forever. Most logs carry ISO run markers, so cut from the first line
  # bearing today's or yesterday's date; if a log has no dates at all (the two
  # python error logs), fall back to mtime and just report the last line.
  today=$(date +%F); yday=$(date -d yesterday +%F)
  start=$(grep -nm1 -e "$today" -e "$yday" "$file" 2>/dev/null | cut -d: -f1)
  if [ -n "${start:-}" ]; then
    recent=$(tail -n "+${start}" "$file")
  elif [ $(( (now - $(stat -c %Y "$file")) / 3600 )) -le 26 ]; then
    recent=$(tail -n 20 "$file")
  else
    recent=""
  fi

  if [ -n "$recent" ]; then
    hits=$(printf '%s\n' "$recent" | grep -cE "$SIGS")
    if [ "${hits:-0}" -gt 0 ]; then
      sample=$(printf '%s\n' "$recent" | grep -E "$SIGS" | tail -n 1 | cut -c1-160)
      PROBLEMS="${PROBLEMS}- ${label}: ${hits} failure line(s) since yesterday, e.g. ${sample}"$'\n'
    fi
  fi
done <<< "$JOBS"

echo "----- $(date -Iseconds) cron health -----" >> "$LOG"

if [ -z "$PROBLEMS" ]; then
  echo "all clear" >> "$LOG"
  exit 0
fi

echo "$PROBLEMS" >> "$LOG"

if [ -f "$TCONF" ]; then
  # shellcheck disable=SC1090
  . "$TCONF"
  MSG="🩺 Cron health: something has gone quiet or is failing."$'\n\n'"${PROBLEMS}"$'\n'"Logs are in ~/.local/state/. I'll look at it on my next run."
  curl -sS --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" --data-urlencode "text=${MSG}" >/dev/null \
    && echo "pinged Rob" >> "$LOG" || echo "telegram send failed" >> "$LOG"
fi
