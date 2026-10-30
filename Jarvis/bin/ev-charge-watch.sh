#!/usr/bin/env bash
# EV charge watchdog. Rob, 16 Oct 2026: "until this is fixed I want it to always notify me,
# whenever I start it charging it turns the watchdog on". Permanent cron every 2 min until
# the Pod Point fault (trips + dark cut-outs) is fixed; then delete the cron line.
#
# Arms itself on any charge (Shelly ch2 >= 500W on two checks running, whoever started it).
# When an armed charge stops (< 500W twice running) it Telegrams once: full at the car's
# limit, a trip (charger off wifi), a Pod Point cut-out (LED dark), unplugged, or a plain
# stop under the limit. Only the dashboard Stop button stays quiet (since 16 Oct nothing
# else stops a charge on purpose: no 00:30 hold, no 05:30 stop, no planner top-up).
set -uo pipefail
source "$HOME/.config/jarvis/ha.env"
source "$HOME/.config/jarvis/telegram.env"
source "$HOME/.config/jarvis/unifi.env"
STATE="$HOME/.local/state/ev-charge-watch"; mkdir -p "$STATE"

get() { curl -s -m 10 -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/states/$1" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("state","?"))' 2>/dev/null || echo "?"; }
# Seconds since an automation/script last ran (huge if never).
since() { curl -s -m 10 -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/states/$1" | python3 -c '
import json,sys,datetime
t=json.load(sys.stdin).get("attributes",{}).get("last_triggered")
print(int((datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(t)).total_seconds()) if t else 10**9)' 2>/dev/null || echo 1000000000; }
tg() { curl -sS -m 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" --data-urlencode "text=$1" >/dev/null; }
lt() { python3 -c "import sys; sys.exit(0 if float(sys.argv[1])<float(sys.argv[2]) else 1)" "$1" "$2" 2>/dev/null; }
# Wifi association on the UDM: the real "is the charger alive" tell (see the trip notes below).
podwifi() { curl -sk -m 10 -H "X-API-KEY: $UNIFI_API_KEY" "https://${UNIFI_HOST:-192.168.1.1}/proxy/network/api/s/default/stat/sta" \
  | python3 -c 'import json,sys; print("on" if any(c.get("mac")=="e0:5a:1b:97:8e:e8" for c in json.load(sys.stdin)["data"]) else "off")' 2>/dev/null || echo "?"; }

# Wake-up alarm. Rob, 26 Oct 2026: the 22:51 trip went unnoticed while he slept; when the car
# is set to 100% (he needs a full battery in the morning) a trip should wake him so he can reset
# it. Bedroom Dot announcement, repeated every ~4 min (max 6, ~20 min) until the charger is back
# on wifi. If DND is on we switch it off for the announcement and put it back.
WAKE_DEV=bedroom_dot
announce() {
  local dnd body code
  dnd=$(get switch.${WAKE_DEV}_do_not_disturb)
  [ "$dnd" = "on" ] && curl -s -m 10 -o /dev/null -X POST -H "Authorization: Bearer $HA_TOKEN" -H 'Content-Type: application/json' \
    -d "{\"entity_id\":\"switch.${WAKE_DEV}_do_not_disturb\"}" "$HA_URL/api/services/switch/turn_off" && sleep 3
  body=$(python3 -c 'import json,sys; print(json.dumps({"entity_id":"notify.%s_announce"%sys.argv[2],"message":sys.argv[1]}))' "$1" "$WAKE_DEV")
  code=$(curl -s -m 15 -o /dev/null -w "%{http_code}" -X POST -H "Authorization: Bearer $HA_TOKEN" -H 'Content-Type: application/json' \
    -d "$body" "$HA_URL/api/services/notify/send_message")
  [ "$dnd" = "on" ] && sleep 15 && curl -s -m 10 -o /dev/null -X POST -H "Authorization: Bearer $HA_TOKEN" -H 'Content-Type: application/json' \
    -d "{\"entity_id\":\"switch.${WAKE_DEV}_do_not_disturb\"}" "$HA_URL/api/services/switch/turn_on"
  [ "$code" = "200" ]
}
WAKE_MSG="Rob, wake up. The car charger has tripped and the car is set to charge to a hundred percent. Please reset the charger switch in its little fuse box."
if [ -f "$STATE/wake" ]; then
  N=$(cat "$STATE/wake"); AGE=$(( $(date +%s) - $(stat -c %Y "$STATE/wake") ))
  if [ "$(podwifi)" = "on" ]; then
    rm -f "$STATE/wake"; echo "$(date '+%F %T') wake cleared (charger back on wifi)" >> "$STATE/events.log"
  elif [ "$N" -ge 6 ]; then
    rm -f "$STATE/wake"; echo "$(date '+%F %T') wake gave up after $N" >> "$STATE/events.log"
    tg "😴 Announced the trip on the Bedroom Dot $N times and the charger's still off. Stopping the alarm; reset it when you see this."
  elif [ "$AGE" -ge 230 ]; then
    announce "$WAKE_MSG"; echo $(( N + 1 )) > "$STATE/wake"
    echo "$(date '+%F %T') wake announce $(( N + 1 ))" >> "$STATE/events.log"
  fi
fi

W=$(get sensor.shellyem_34945470ed50_channel_2_power)
KWH_NOW=$(get sensor.shellyem_34945470ed50_channel_2_energy)

if lt "$W" 500 || [ "$W" = "unavailable" ]; then
  echo 0 > "$STATE/high"
  LOW=$(( $(cat "$STATE/low" 2>/dev/null || echo 0) + 1 )); echo "$LOW" > "$STATE/low"
  [ -f "$STATE/armed" ] && [ "$LOW" -ge 2 ] || exit 0
  T=$(date +%H:%M)
  SOC=$(get sensor.mg_mg4_electric_state_of_charge); LIMIT=$(get number.mg_mg4_electric_target_soc)
  # SAIC's charging-data call can fail for hours (30 Oct: target_soc unavailable all day), so a
  # limit Jarvis just set by hand is written to limit_hint and used for up to 18h when the car won't say.
  case "$LIMIT" in ''|*[!0-9.]*) LIMIT="?"
    [ -n "$(find "$STATE/limit_hint" -mmin -1080 2>/dev/null)" ] && LIMIT=$(cat "$STATE/limit_hint");; esac
  GUN=$(get binary_sensor.mg_mg4_electric_charging_gun_state)
  CLOUD=$(get binary_sensor.psl_557234_cloud_connection)
  STATUS=$(get sensor.psl_557234_status)
  # Pod Point cloud_connection lags by many minutes (still "on" after the 23:10 trip on
  # 9 Oct), so the wifi association on the UDM is the real trip tell.
  WIFI=$(podwifi)
  [ "$WIFI" = "off" ] && CLOUD=off
  # A trip takes minutes to show: 25 Oct 22:51 the Pod Point was still "charging", cloud on
  # and on wifi at 22:54, cloud only went off at 22:59, so this said "not a trip". If nothing
  # else explains the stop yet, hold the verdict for up to ~10 min (LOW 2..6) and recheck.
  if [ "$CLOUD" != "off" ] && [ "$STATUS" = "charging" ] && [ "$GUN" != "off" ] && [ "$LOW" -lt 6 ] \
     && [ "$(since script.ev_charge_stop)" -ge 900 ] \
     && { [ "$SOC" = "?" ] || [ "$LIMIT" = "?" ] || lt "$SOC" "$(python3 -c "print(float('$LIMIT')-1.5)")"; }; then
    exit 0
  fi
  rm -f "$STATE/armed"
  ADDED=$(python3 -c "import sys; print(round(float(sys.argv[1])-float(sys.argv[2]),1))" "$KWH_NOW" "$(cat "$STATE/start_kwh" 2>/dev/null)" 2>/dev/null || echo "?")
  SOCS=$(printf '%.0f' "$SOC" 2>/dev/null || echo "?")
  LOG="$(date '+%F %T') stop W=$W soc=$SOC status=$STATUS cloud=$CLOUD wifi=$WIFI gun=$GUN added=$ADDED"

  # Deliberate stop (dashboard Stop button): say nothing.
  if [ "$(since script.ev_charge_stop)" -lt 900 ]; then
    echo "$LOG (deliberate, quiet)" >> "$STATE/events.log"; exit 0
  fi
  echo "$LOG" >> "$STATE/events.log"

  if [ "$CLOUD" = "off" ]; then
    MSG="⚡ Charger's died at $T with the MG4 on ${SOCS}%: no power and the Pod Point's off the network, so it looks like a trip. ~${ADDED} kWh went in. Reset it at its consumer unit and note which switch was down."
    # Car set to 100% = Rob needs a full battery, so wake him (Bedroom Dot, repeats until reset).
    if python3 -c "import sys; sys.exit(0 if float(sys.argv[1])>=95 else 1)" "$LIMIT" 2>/dev/null; then
      if announce "$WAKE_MSG"; then echo 1 > "$STATE/wake"; MSG="$MSG 🔊 Announcing it on the Bedroom Dot every few minutes until the charger's back."
      else echo 1 > "$STATE/wake"; MSG="$MSG ⚠️ Tried to announce on the Bedroom Dot but it failed; will retry."; fi
      echo "$(date '+%F %T') wake announce 1" >> "$STATE/events.log"
    fi
  elif [ "$SOC" != "?" ] && [ "$LIMIT" != "?" ] && ! lt "$SOC" "$(python3 -c "print(float('$LIMIT')-1.5)")"; then
    MSG="✅ MG4's done: ${SOCS}% at $T (limit ${LIMIT%.*}%). ~${ADDED} kWh went in."
  elif [ "$GUN" = "off" ]; then
    MSG="🔌 MG4 unplugged at $T on ${SOCS}%. ~${ADDED} kWh went in."
  elif [ "$STATUS" = "out-of-service" ]; then
    MSG="🔌 Charging stopped at $T on ${SOCS}%: the Pod Point cut itself out (LED dark), not a trip. The planner restarts it from the car within ~10-20 min if it doesn't retry itself. ~${ADDED} kWh in so far."
  else
    MSG="🔌 Charging stopped at $T on ${SOCS}%, short of the ${LIMIT%.*}% limit. Pod Point still online (status: $STATUS), not a trip. ~${ADDED} kWh went in. Check the car/app."
  fi
  tg "$MSG" && touch "$STATE/alerted"
else
  echo 0 > "$STATE/low"
  HIGH=$(( $(cat "$STATE/high" 2>/dev/null || echo 0) + 1 )); echo "$HIGH" > "$STATE/high"
  if [ "$HIGH" -ge 2 ] && [ ! -f "$STATE/armed" ]; then
    # Count from the first high sample, ~2 min ago; close enough.
    echo "$KWH_NOW" > "$STATE/start_kwh"; touch "$STATE/armed"
    echo "$(date '+%F %T') armed W=$W" >> "$STATE/events.log"
    if [ -f "$STATE/alerted" ]; then
      rm -f "$STATE/alerted"
      tg "✅ Charging's back on: $(python3 -c "print(round(float('$W')/1000,1))" 2>/dev/null) kW at $(date +%H:%M), MG4 on $(printf '%.0f' "$(get sensor.mg_mg4_electric_state_of_charge)" 2>/dev/null)%."
    fi
  fi
fi
