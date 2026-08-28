#!/bin/sh
# Announce a message on an Echo via HA's Alexa Media Player integration.
# Usage: jarvis-say.sh "message" [device]   device: living_room_echo (default) | kitchen_dot | bedroom_dot | dexter_s_dot | logan_s_dot
# Note: kids' Dots are theirs; only use with a reason.
. "$HOME/.config/jarvis/ha.env"
MSG="$1"; DEV="${2:-living_room_echo}"
[ -z "$MSG" ] && { echo "usage: jarvis-say.sh \"message\" [device]" >&2; exit 1; }
BODY=$(python3 -c 'import json,sys; print(json.dumps({"entity_id":"notify.%s_announce"%sys.argv[2],"message":sys.argv[1]}))' "$MSG" "$DEV")
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Authorization: Bearer $HA_TOKEN" -H 'Content-Type: application/json' -d "$BODY" "$HA_URL/api/services/notify/send_message")
[ "$CODE" = "200" ] && echo "said on $DEV" || { echo "failed ($CODE) on $DEV" >&2; exit 1; }
