#!/usr/bin/env bash
# One-night EV charge watchdog (Rob's ask, 9 Oct 2026: "let me know if it dies").
# Cron every 2 min. Pings Telegram once when the Pod Point stops drawing power
# (Shelly ch2 < 500W on two checks in a row), says whether it looks like a trip
# (cloud_connection off) or a normal stop (car full / paused). Re-arms if charging
# resumes. Removes its own cron line after EXPIRY.
set -uo pipefail
source "$HOME/.config/jarvis/ha.env"
source "$HOME/.config/jarvis/telegram.env"
source "$HOME/.config/jarvis/unifi.env"
STATE="$HOME/.local/state/ev-charge-watch"; mkdir -p "$STATE"
EXPIRY="${EV_WATCH_EXPIRY:-2026-10-10 10:00}"

if [ "$(date +%s)" -ge "$(date -d "$EXPIRY" +%s)" ]; then
  crontab -l | grep -v 'ev-charge-watch.sh' | crontab -; exit 0
fi

get() { curl -s -m 10 -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/states/$1" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("state","?"))' 2>/dev/null || echo "?"; }
tg() { curl -sS -m 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" --data-urlencode "text=$1" >/dev/null; }

W=$(get sensor.shellyem_34945470ed50_channel_2_power)
CLOUD=$(get binary_sensor.psl_557234_cloud_connection)
STATUS=$(get sensor.psl_557234_status)
# Pod Point cloud_connection lags by many minutes (it still read "on" after the
# 23:10 trip on 9 Oct), so the wifi association on the UDM is the real tell.
WIFI=$(curl -sk -m 10 -H "X-API-KEY: $UNIFI_API_KEY" "https://${UNIFI_HOST:-192.168.1.1}/proxy/network/api/s/default/stat/sta" \
  | python3 -c 'import json,sys; print("on" if any(c.get("mac")=="e0:5a:1b:97:8e:e8" for c in json.load(sys.stdin)["data"]) else "off")' 2>/dev/null || echo "?")
[ "$WIFI" = "off" ] && CLOUD=off
KWH_NOW=$(get sensor.shellyem_34945470ed50_channel_2_energy)
[ -f "$STATE/start_kwh" ] || echo "$KWH_NOW" > "$STATE/start_kwh"
ADDED=$(python3 -c "import sys; print(round((float(sys.argv[1])-float(sys.argv[2]))/1000,1))" "$KWH_NOW" "$(cat "$STATE/start_kwh")" 2>/dev/null || echo "?")

if python3 -c "import sys; sys.exit(0 if float(sys.argv[1])<500 else 1)" "$W" 2>/dev/null || [ "$W" = "unavailable" ]; then
  LOW=$(( $(cat "$STATE/low" 2>/dev/null || echo 0) + 1 )); echo "$LOW" > "$STATE/low"
  if [ "$LOW" -ge 2 ] && [ ! -f "$STATE/alerted" ]; then
    T=$(date +%H:%M)
    if [ "$CLOUD" = "off" ]; then
      MSG="⚡ Charger's died at about $T: no power and the Pod Point has dropped off the network, so it looks like a trip. ~${ADDED} kWh went in tonight (roughly $(python3 -c "print(int(float('$ADDED')*0.9/64*100))" 2>/dev/null || echo '?')% added). Reset it at its consumer unit and note which switch was down."
    else
      MSG="🔌 Car stopped drawing power at about $T (Pod Point still online, status: $STATUS). ~${ADDED} kWh went in tonight, roughly $(python3 -c "print(int(float('$ADDED')*0.9/64*100))" 2>/dev/null || echo '?')% added. If that's near 48 kWh it's just full; if not, check the car."
    fi
    tg "$MSG" && touch "$STATE/alerted"
  fi
else
  echo 0 > "$STATE/low"
  if [ -f "$STATE/alerted" ]; then rm -f "$STATE/alerted"; tg "✅ Charging's back on: $(printf '%.1f' "$W" 2>/dev/null) W at $(date +%H:%M)."; fi
fi
