#!/usr/bin/env bash
# Keep cracky.co.uk + *.cracky.co.uk pointed at the house's dynamic BT IP.
# Rebuild of the pre-Proxmox cloudflare-ddns.sh (2026-07-03).
# Token: ~/.config/jarvis/cloudflare.env (CF_API_TOKEN, needs Zone.DNS edit on cracky.co.uk)
# Cron: */10 as jarvis, logs to ~/.local/state/cloudflare-ddns.log
set -euo pipefail

source "$HOME/.config/jarvis/cloudflare.env"
ZONE_ID="abf35cddd4423cfe8bb4f34c993e0b85"
LOG="$HOME/.local/state/cloudflare-ddns.log"
mkdir -p "$(dirname "$LOG")"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >>"$LOG"; }

WAN=$(curl -s -m 10 https://api.ipify.org || true)
[[ "$WAN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || { log "ERROR could not determine WAN IP (got: '$WAN')"; exit 1; }

cf() { curl -s -m 15 -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" "$@"; }

records=$(cf "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=A&per_page=50")
echo "$records" | python3 -c 'import json,sys; sys.exit(0 if json.load(sys.stdin)["success"] else 1)' || { log "ERROR listing records: $records"; exit 1; }

echo "$records" | python3 -c '
import json, sys
for r in json.load(sys.stdin)["result"]:
    print(r["id"], r["name"], r["content"])' | while read -r id name content; do
  if [[ "$content" != "$WAN" ]]; then
    resp=$(cf -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$id" --data "{\"content\":\"$WAN\"}")
    if echo "$resp" | grep -q '"success":true'; then
      log "UPDATED $name: $content -> $WAN"
    else
      log "ERROR updating $name: $resp"
    fi
  fi
done
