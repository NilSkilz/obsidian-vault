#!/usr/bin/env bash
# Home Assistant REST helper (rebuild of the pre-Proxmox ha-api.sh, 2026-07-03).
# Token: ~/.config/jarvis/ha.env (long-lived, created by Rob 2026-07-03).
# Usage:
#   ha-api.sh states                      # all entity ids + states
#   ha-api.sh state <entity_id>           # one entity
#   ha-api.sh call <domain> <service> [entity_id]   # e.g. call light turn_off light.kitchen
#   ha-api.sh raw <method> <path> [json]  # escape hatch, e.g. raw GET /api/config
set -euo pipefail
source "$HOME/.config/jarvis/ha.env"

api() { curl -s -m 10 -X "$1" -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" "${@:3}" "$HA_URL$2"; }

case "${1:-}" in
  states) api GET /api/states | python3 -c 'import json,sys; [print(e["entity_id"], "=", e["state"]) for e in json.load(sys.stdin)]' ;;
  state)  api GET "/api/states/$2" | python3 -m json.tool ;;
  call)   body="{}"; [ -n "${4:-}" ] && body="{\"entity_id\":\"$4\"}"; api POST "/api/services/$2/$3" -d "$body" ;;
  raw)    api "$2" "$3" ${4:+-d "$4"} ;;
  *) grep '^#   ' "$0" | cut -c3-; exit 1 ;;
esac
