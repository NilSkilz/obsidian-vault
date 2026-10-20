#!/usr/bin/env bash
# One-shot "stop the charge at N%" (e.g. Rob, 20 Oct 2026: charge to 60% now, rest at 00:30).
# Cron'd */2 by hand: ev-stop-at.sh <target%>. The car only reports SoC every 5-30 min, so it
# also estimates SoC from Shelly ch2 kWh since the last car reading (0.715 meter kWh per %,
# measured on the 19-20 Oct 40->80% charge). Stops via script.ev_charge_stop (watchdog stays
# quiet, cut-out rescue backs off 12h), Telegrams once, then removes its own crontab line.
# Gives up after 8h. State: ~/.local/state/ev-stop-at/.
set -uo pipefail
source "$HOME/.config/jarvis/ha.env"; source "$HOME/.config/jarvis/telegram.env"
H="${HA_URL:-http://192.168.1.4:8123}"; TARGET="${1:?target %}"; KWH_PER_PCT=0.715
S="$HOME/.local/state/ev-stop-at"; mkdir -p "$S"
st() { curl -s -m 10 -H "Authorization: Bearer $HA_TOKEN" "$H/api/states/$1" | python3 -c 'import json,sys; s=json.load(sys.stdin); print(s["state"], s["last_updated"])' 2>/dev/null || echo "? ?"; }
done_() { crontab -l | grep -v 'ev-stop-at.sh' | crontab -; rm -f "$S"/base "$S"/started; }
[ -f "$S/started" ] || date +%s > "$S/started"
[ $(( $(date +%s) - $(cat "$S/started") )) -gt 28800 ] && { echo "$(date '+%F %T') gave up" >> "$S/log"; done_; exit 0; }

read -r SOC SOC_T < <(st sensor.mg_mg4_electric_state_of_charge)
read -r KWH _ < <(st sensor.shellyem_34945470ed50_channel_2_energy)
read -r W _ < <(st sensor.shellyem_34945470ed50_channel_2_power)
# Rebase on every fresh car reading: base = "soc kwh soc_time".
if [ ! -f "$S/base" ] || [ "$(awk '{print $3}' "$S/base")" != "$SOC_T" ]; then
  [ "$SOC" != "?" ] && [ "$KWH" != "?" ] && echo "$SOC $KWH $SOC_T" > "$S/base"
fi
read -r BSOC BKWH _ < "$S/base"
EST=$(python3 -c "print(round(float('$BSOC')+(float('$KWH')-float('$BKWH'))/$KWH_PER_PCT,1))" 2>/dev/null || echo "$SOC")
echo "$(date '+%F %T') soc=$SOC est=$EST W=$W" >> "$S/log"
python3 -c "import sys; sys.exit(0 if max(float('$SOC'),float('$EST'))>=float('$TARGET')-0.5 else 1)" 2>/dev/null || exit 0

curl -s -m 15 -X POST -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" "$H/api/services/script/ev_charge_stop" -d '{}' >/dev/null
echo "$(date '+%F %T') STOPPED soc=$SOC est=$EST" >> "$S/log"
NEXT=$(crontab -l | grep -q ev-start-once.sh && echo " Restarts 00:30 on the cheap rate." || echo "")
curl -sS -m 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=⏸️ MG4 paused at ~$(printf '%.0f' "$EST")% ($(date +%H:%M)).$NEXT" >/dev/null
done_
