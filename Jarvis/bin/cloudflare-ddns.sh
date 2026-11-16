#!/usr/bin/env bash
# Keep cracky.co.uk + *.cracky.co.uk pointed at the house's dynamic BT IP.
# Rebuild of the pre-Proxmox cloudflare-ddns.sh (2026-07-03).
# Token: ~/.config/jarvis/cloudflare.env (CF_API_TOKEN, needs Zone.DNS edit on cracky.co.uk)
# Cron: every minute as jarvis, logs to ~/.local/state/cloudflare-ddns.log
# Most runs stop at the cached-IP check; Cloudflare is only asked when the WAN IP
# has moved, or every 10 min as a safety net (was */10 flat until 2026-11-16, which
# left the public sites 522ing for up to 10 min after each BT IP change).
set -euo pipefail

source "$HOME/.config/jarvis/cloudflare.env"
ZONE_ID="da56dd2f412d61d964009ef8ec7368d6"
# Only these names track the house IP. Everything else (autodiscover -> Cloudflare
# email IPs, MX, TXT) is left alone.
MANAGED="cracky.co.uk www.cracky.co.uk *.cracky.co.uk"
LOG="$HOME/.local/state/cloudflare-ddns.log"
mkdir -p "$(dirname "$LOG")"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >>"$LOG"; }

WAN=$(curl -s -m 10 https://api.ipify.org || true)
[[ "$WAN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || { log "ERROR could not determine WAN IP (got: '$WAN')"; exit 1; }

# Cheap path: same IP as the last successful sync and not a 10-minute mark.
STATE="$HOME/.local/state/cloudflare-ddns.last"
if [[ "$(cat "$STATE" 2>/dev/null)" == "$WAN" ]] && (( 10#$(date +%M) % 10 != 0 )); then exit 0; fi

cf() { curl -s -m 15 -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" "$@"; }

records=$(cf "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=A&per_page=50")
echo "$records" | python3 -c 'import json,sys; sys.exit(0 if json.load(sys.stdin)["success"] else 1)' || { log "ERROR listing records: $records"; exit 1; }

echo "$records" | python3 -c '
import json, sys
for r in json.load(sys.stdin)["result"]:
    print(r["id"], r["name"], r["content"])' | { ok=1; while read -r id name content; do
  [[ " $MANAGED " == *" $name "* ]] || continue
  if [[ "$content" != "$WAN" ]]; then
    resp=$(cf -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$id" --data "{\"content\":\"$WAN\"}")
    if echo "$resp" | grep -q '"success":true'; then
      log "UPDATED $name: $content -> $WAN"
    else
      log "ERROR updating $name: $resp"
      ok=0
    fi
  fi
done
if (( ok )); then echo "$WAN" >"$STATE"; else rm -f "$STATE"; fi; }
