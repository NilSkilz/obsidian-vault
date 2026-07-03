#!/usr/bin/env bash
# Family calendar CLI — reads the published iCloud ICS feed (read-only, no CalDAV write).
# Usage:
#   calendar.sh today        # events today
#   calendar.sh tomorrow     # events tomorrow
#   calendar.sh week         # events for the next 7 days
set -euo pipefail

ENV_FILE="/home/jarvis/.config/jarvis/calendar.env"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$ENV_FILE"

cmd="${1:-today}"

case "$cmd" in
  today)
    d="$(date +%F)"
    python3 "$SCRIPT_DIR/calendar_ics.py" "$CALENDAR_ICS_URL" "$d"
    ;;
  tomorrow)
    d="$(date -d tomorrow +%F)"
    python3 "$SCRIPT_DIR/calendar_ics.py" "$CALENDAR_ICS_URL" "$d"
    ;;
  week)
    dates=()
    for i in 0 1 2 3 4 5 6; do
      dates+=("$(date -d "+$i day" +%F)")
    done
    python3 "$SCRIPT_DIR/calendar_ics.py" "$CALENDAR_ICS_URL" "${dates[@]}"
    ;;
  *)
    echo "usage: calendar.sh {today|tomorrow|week}" >&2
    exit 1
    ;;
esac
