#!/usr/bin/env bash
# Jarvis <-> Tide mood/journal bridge. Lets a Jarvis chat session drop a mood
# check-in (or a written journal entry) onto Rob's or Aimee's PRIVATE Tide
# journal when they say something like "feeling rough today" in chat.
#
# Auth: the shared JARVIS_API_KEY as X-Jarvis-Key, acting on behalf of a named
# user via X-Jarvis-User. Same key + base as the health bridge, so it reuses
# ~/.config/jarvis/health.env. The Express authGuard honours this on the LAN,
# and the /journal route stamps loggedBy:'jarvis' and files it to that user's
# own private journal (each parent only ever sees their own).
#
# Mood scale is 1-5 (1 = rough, 5 = great) to match the UI faces.
#
# Usage:
#   jarvis-mood.sh log   <user> <1-5> ["note"]              # quick mood check-in
#   jarvis-mood.sh entry <user> <1-5|-> "title" "body"      # fuller journal entry
#   jarvis-mood.sh trend <user> [days]                      # read back mood series (JSON)
#
# <user> is a Tide username (rob | aimee). Kids are never valid (API 403s them).
# I read the mood off what Rob tells me: rough/awful ~1-2, meh ~3, good ~4,
# great ~5. When unsure, ask him rather than guess wildly.
set -euo pipefail

CONF="$HOME/.config/jarvis/health.env"
[ -f "$CONF" ] || { echo "missing $CONF" >&2; exit 1; }
set -a; source "$CONF"; set +a
BASE="${TIDE_API_BASE:-http://192.168.1.16:3001}/api/family"

hdr=(-H "X-Jarvis-Key: ${JARVIS_API_KEY}")

cmd="${1:-}"; shift || true
case "$cmd" in
  log)
    user="$1"; mood="$2"; note="${3:-}"
    curl -sS -X POST "${BASE}/journal" "${hdr[@]}" \
      -H "X-Jarvis-User: ${user}" -H "Content-Type: application/json" \
      -d "$(jq -n --argjson m "$mood" --arg b "$note" \
            '{mood:$m} + (if $b == "" then {} else {body:$b} end)')"
    ;;
  entry)
    user="$1"; mood="$2"; title="$3"; body="$4"
    if [ "$mood" = "-" ]; then moodJson="null"; else moodJson="$mood"; fi
    curl -sS -X POST "${BASE}/journal" "${hdr[@]}" \
      -H "X-Jarvis-User: ${user}" -H "Content-Type: application/json" \
      -d "$(jq -n --argjson m "$moodJson" --arg t "$title" --arg b "$body" \
            '{mood:$m, title:$t, body:$b}')"
    ;;
  trend)
    user="$1"; days="${2:-30}"
    curl -sS "${BASE}/journal?range=${days}" "${hdr[@]}" -H "X-Jarvis-User: ${user}"
    ;;
  *)
    echo "usage: jarvis-mood.sh log|entry|trend <user> ..." >&2; exit 2 ;;
esac
echo
