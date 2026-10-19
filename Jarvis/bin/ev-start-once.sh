#!/bin/bash
# One-shot "start the car charging" (e.g. a paused day charge resumed at 00:30 for the cheap rate).
# Cron'd by hand for a single run; removes its own crontab line after firing.
source ~/.config/jarvis/ha.env
H="${HA_URL:-http://192.168.1.4:8123}"
curl -s -X POST -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  "$H/api/services/script/ev_charge_now" -d '{}' >/dev/null
crontab -l | grep -v 'ev-start-once.sh' | crontab -
