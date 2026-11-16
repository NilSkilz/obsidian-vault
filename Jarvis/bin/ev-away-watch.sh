#!/usr/bin/env bash
# One-off watch on a charge away from home (work post, public charger), where the home
# watchdog is blind because it keys on the Shelly. Rob, 16 Nov 2026: "let me know if
# anything interrupts it before then".
# Usage: setsid nohup ev-away-watch.sh <until HH:MM> >/dev/null 2>&1 &
# Polls the car every 2 min until <until>, Telegrams once per interruption (charging status
# leaves "Charging (AC)" on two checks running, or the cable comes out), re-arms if the
# charge resumes, and says so once if the car's data goes stale for 40+ min. Then exits.
set -uo pipefail
UNTIL="${1:?usage: ev-away-watch.sh <until HH:MM>}"
source "$HOME/.config/jarvis/ha.env"
source "$HOME/.config/jarvis/telegram.env"
STATE="$HOME/.local/state/ev-away-watch"; mkdir -p "$STATE"
LOG="$STATE/events.log"
END=$(date -d "today $UNTIL" +%s)

get() { curl -s -m 10 -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/states/$1" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("state","?"))' 2>/dev/null || echo "?"; }
tg() { curl -sS -m 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" --data-urlencode "text=$1" >/dev/null; }
age() { python3 -c 'import sys,datetime; print(int((datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(sys.argv[1])).total_seconds()))' "$1" 2>/dev/null || echo 999999; }

echo "$(date '+%F %T') watching until $UNTIL" >> "$LOG"
BAD=0; ALERTED=0; STALE_SAID=0
while [ "$(date +%s)" -lt "$END" ]; do
  STATUS=$(get sensor.mg_mg4_electric_charging_status)
  GUN=$(get binary_sensor.mg_mg4_electric_charging_gun_state)
  SOC=$(get sensor.mg_mg4_electric_state_of_charge)
  AGE=$(age "$(get sensor.mg_mg4_electric_last_update_time)")
  SOCS=$(printf '%.0f' "$SOC" 2>/dev/null || echo "?")
  T=$(date +%H:%M)

  if [ "$AGE" -gt 1200 ]; then
    # The poller hangs silently (see Context/Home Assistant.md): kick it, don't judge stale data.
    curl -s -m 15 -o /dev/null -X POST -H "Authorization: Bearer $HA_TOKEN" -H 'Content-Type: application/json' \
      -d '{"entity_id":"button.mg_mg4_electric_update_vehicle_data"}' "$HA_URL/api/services/button/press"
    if [ "$AGE" -gt 2400 ] && [ "$STALE_SAID" = 0 ]; then
      tg "👀 I've lost sight of the car: no fresh data from MG for $(( AGE / 60 )) min (last seen ${SOCS}%). Can't tell if it's still charging, worth a glance at the app."
      STALE_SAID=1; echo "$(date '+%F %T') stale ${AGE}s" >> "$LOG"
    fi
  elif [ "$STATUS" = "Charging (AC)" ] && [ "$GUN" = "on" ]; then
    [ "$ALERTED" = 1 ] && echo "$(date '+%F %T') charging again soc=$SOC" >> "$LOG"
    BAD=0; ALERTED=0; STALE_SAID=0
  else
    BAD=$(( BAD + 1 ))
    if [ "$BAD" -ge 2 ] && [ "$ALERTED" = 0 ]; then
      if [ "$GUN" != "on" ]; then
        tg "🔌 MG4 unplugged at work at $T on ${SOCS}%."
      else
        tg "⚡ Work charge has stopped at $T with the MG4 on ${SOCS}% (car says: $STATUS). Restart it at the post and tap Confirm charge in the Pod Point app."
      fi
      ALERTED=1; echo "$(date '+%F %T') alert status=$STATUS gun=$GUN soc=$SOC" >> "$LOG"
    fi
  fi
  sleep 120
done
echo "$(date '+%F %T') done at $UNTIL soc=$(get sensor.mg_mg4_electric_state_of_charge) status=$(get sensor.mg_mg4_electric_charging_status)" >> "$LOG"
