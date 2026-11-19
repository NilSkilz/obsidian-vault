#!/bin/bash
# One-off: lift the "Make Way (10)" cap off the MacBookPro (9e:e2:49:42:8f:89), set 2026-11-19 so Rob's Xbox got the line. Removes its own cron line.
source ~/.config/jarvis/unifi.env; H="X-API-KEY: $UNIFI_API_KEY"; B=https://192.168.1.1/proxy/network/api/s/default
curl -sk -H "$H" -H 'Content-Type: application/json' -X PUT $B/rest/user/906da159-e4ad-4e86-83ba-667e49b667e1 -d '{"usergroup_id":"82e4a50c-3beb-4432-b30c-e83aa5b8a5fa"}' >/dev/null
curl -sk -H "$H" -H 'Content-Type: application/json' -X POST $B/cmd/stamgr -d '{"cmd":"kick-sta","mac":"9e:e2:49:42:8f:89"}' >/dev/null
crontab -l | grep -v uncap-macbook-oneshot | crontab -
