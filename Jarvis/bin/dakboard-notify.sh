#!/usr/bin/env bash
# Post alerts to the Jarvis DAKboard wall panel (wall.cracky.co.uk).
#
# The panel is a static page served from CT 110 (this box) at
# /home/jarvis/dakboard/www/, iframed by Rob's DAKboard. This script is the
# only thing that writes alerts.json; the page polls it every 20s.
#
# Levels: ok | info | warn | alert  (control the accent colour + sort order)
#
# Usage:
#   dakboard-notify.sh add <level> <title> [detail]   # prepend an alert (keeps newest 8)
#   dakboard-notify.sh clear                           # remove all alerts (-> "All clear")
#   dakboard-notify.sh list                            # print current alerts.json
#
# Examples:
#   dakboard-notify.sh add warn  "Thin pool 88%" "local-lvm creeping up, trim due"
#   dakboard-notify.sh add info  "Bins tomorrow" "Recycling + food waste"
#   dakboard-notify.sh add alert "HA offline"    "home-assistant not responding"
set -euo pipefail

STATE="${WALL_STATE:-/home/jarvis/dakboard}"
FILE="$STATE/alerts.json"
MAX="${WALL_MAX:-8}"

now_iso() { date --iso-8601=seconds; }
now_hm()  { date +%H:%M; }

ensure() {
  mkdir -p "$STATE"
  [ -f "$FILE" ] || echo '{"updated":"","alerts":[]}' > "$FILE"
}

cmd="${1:-}"; shift || true
case "$cmd" in
  add)
    level="${1:-info}"; title="${2:-}"; detail="${3:-}"
    case "$level" in ok|info|warn|alert) ;; *) echo "level must be ok|info|warn|alert" >&2; exit 1;; esac
    [ -n "$title" ] || { echo "title required" >&2; exit 1; }
    ensure
    tmp="$(mktemp)"
    jq \
      --arg level "$level" --arg title "$title" --arg detail "$detail" \
      --arg time "$(now_hm)" --arg updated "$(now_iso)" --argjson max "$MAX" \
      '{updated:$updated,
        alerts: ([{level:$level,title:$title,detail:$detail,time:$time}] + (.alerts // []))[0:$max]}' \
      "$FILE" > "$tmp" && mv "$tmp" "$FILE"
    echo "posted [$level] $title"
    ;;
  clear)
    ensure
    tmp="$(mktemp)"
    jq --arg updated "$(now_iso)" '{updated:$updated,alerts:[]}' "$FILE" > "$tmp" && mv "$tmp" "$FILE"
    echo "cleared"
    ;;
  list)
    ensure; cat "$FILE"
    ;;
  *)
    grep '^#' "$0" | sed 's/^# \{0,1\}//'
    exit 1
    ;;
esac
