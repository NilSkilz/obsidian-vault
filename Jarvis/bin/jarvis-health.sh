#!/usr/bin/env bash
# Jarvis <-> Tide health bridge. Lets a Jarvis chat session log what Rob (or
# Aimee) ate / did into Tide's calorie tracker, and read back the day so far.
#
# Auth: a shared key (JARVIS_API_KEY) sent as X-Jarvis-Key, acting on behalf of
# a named user via X-Jarvis-User. The Express authGuard honours this for
# server-side callers on the LAN. Config lives in ~/.config/jarvis/health.env.
#
# Usage:
#   jarvis-health.sh food     <user> <breakfast|lunch|dinner|snack> <kcal> "desc"
#   jarvis-health.sh exercise <user> <kcal_burned> "desc" [minutes]
#   jarvis-health.sh day      [user]        # today's totals + entries (JSON)
#
# <user> is a Tide username (rob | aimee). I estimate the calories myself from
# what Rob tells me, then call this. Kids are never valid here (API 403s them).
set -euo pipefail

CONF="$HOME/.config/jarvis/health.env"
[ -f "$CONF" ] || { echo "missing $CONF" >&2; exit 1; }
set -a; source "$CONF"; set +a
BASE="${TIDE_API_BASE:-http://192.168.1.16:3001}/api/family"

hdr=(-H "X-Jarvis-Key: ${JARVIS_API_KEY}")

cmd="${1:-}"; shift || true
case "$cmd" in
  food)
    user="$1"; meal="$2"; kcal="$3"; desc="$4"
    curl -sS -X POST "${BASE}/health/food" "${hdr[@]}" \
      -H "X-Jarvis-User: ${user}" -H "Content-Type: application/json" \
      -d "$(jq -n --arg m "$meal" --arg d "$desc" --argjson c "$kcal" \
            '{mealType:$m, description:$d, calories:$c}')"
    ;;
  exercise)
    user="$1"; kcal="$2"; desc="$3"; mins="${4:-null}"
    curl -sS -X POST "${BASE}/health/exercise" "${hdr[@]}" \
      -H "X-Jarvis-User: ${user}" -H "Content-Type: application/json" \
      -d "$(jq -n --arg d "$desc" --argjson c "$kcal" --argjson mn "$mins" \
            '{description:$d, calories:$c, minutes:$mn}')"
    ;;
  day)
    user="${1:-rob}"
    curl -sS "${BASE}/health/day" "${hdr[@]}" -H "X-Jarvis-User: ${user}"
    ;;
  *)
    echo "usage: jarvis-health.sh food|exercise|day ..." >&2; exit 2 ;;
esac
echo
