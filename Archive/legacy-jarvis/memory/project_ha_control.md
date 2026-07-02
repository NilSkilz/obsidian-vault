---
name: project-ha-control
description: "Home Assistant control — credentials, key entities, helper script; full device control working"
metadata: 
  node_type: memory
  type: project
  originSessionId: d871236e-562f-4f4d-91ff-1477b43720da
---

Home Assistant is fully controllable from the container.

**Credentials:** `/home/rob/.claude.local/secrets/ha.env` — `HA_URL` (localhost ref), `HA_BEARER` (long-lived auth).
**Actual reachable URL from container:** `http://192.168.1.2:8123` (localhost:8123 resolves to container, not host).

**Helper script:** `/home/rob/.claude.local/scripts/ha-api.sh`
- `ha-api.sh get <path>` — GET any HA REST endpoint
- `ha-api.sh post <path> <json>` — POST to any HA service

**Key entities confirmed working:**
- `media_player.lg_webos_tv_ua73006la_3` — LG webOS TV (main, playing-capable); volume_set / volume_down work
- `light.living_room_lights` — Living Room Lights group (Hue spots + other bulbs)
- `light.living_room` — Living Room scene/area entity

**HA REST API patterns:**
- GET states: `GET /api/states` or `GET /api/states/<entity_id>`
- Call service: `POST /api/services/<domain>/<service>` with `{"entity_id": "..."}` body
- Common services: `light/turn_on`, `light/turn_off`, `media_player/volume_set` (with `volume_level: 0.0-1.0`), `media_player/volume_down`

**Why:** Rob asked for HA control via Telegram. Verified 2026-06-23: TV volume and lights both work.

**How to apply:** When Rob asks to control lights, TV, heating etc., look up the entity_id from `GET /api/states`, then call the appropriate service via ha-api.sh. For fuzzy entity lookup: filter states by `entity_id` and `friendly_name` matching the keyword.
