# Home Assistant

**Smart home automation platform - the central hub**

## Connection Details
- **URL:** http://192.168.1.4:8123 (verified reachable 2026-07-02)
- **User:** jarvis (admin)

> **Post-rebuild note (2026-07-02):** HA moved to `192.168.1.4` in the Proxmox rebuild. The device/entity lists below are carried over from the old NUC and have NOT yet been re-confirmed against the new instance. Verify with `GET /api/states` before relying on any specific entity_id. See `Context/Infrastructure.md`.

## Current State
**Rob's assessment:** "collection of stuff" without clear vision  
**Goal:** Tidy up with a clear purpose and organized automation strategy

## Device Categories

### Lighting
- **Nanoleaf:** `light.aurora_52_50_96`
- **Living room:** `light.living_room_lights_led`, `switch.living_room_lights`
- **Snug:** `switch.snug_lights`
- **IKEA Matter/Thread:** KAJPLATS bulbs, BILRESA switch (working as of Mar 2026)

### Tesla Integration (GONE)
**"Timmy" the family Tesla is no longer owned (confirmed by Rob 2026-07-03).** The `timmy_*` entities are dead; the integration should be removed from HA if it's still installed. Tesla widget/cards were stripped from Mission Control the same day.

### Alexa Ecosystem
Alexa Media Player (HACS) survived the rebuild and is installed. Entities use the **new-style notify entities**, not the old `notify.alexa_media_*` services:
- `notify.<device>_announce` (Alexa "announcement" chime + speech) and `notify.<device>_speak` (plain TTS), called via `notify.send_message` with `entity_id` + `message`.
- Devices: `living_room_echo`, `kitchen_dot`, `bedroom_dot`, `dexter_s_dot`, `logan_s_dot`. Also `media_player.<device>` for each.
- **Helper:** `Jarvis/bin/jarvis-say.sh "message" [device]` (default living_room_echo). Verified working 2026-08-28 11:41.
- **Status 2026-08-28:** Living Room Echo online and announcing. Kitchen, Bedroom, Dexter's and Logan's Dots all went `unavailable` at 2026-08-26 11:14 (same second, so likely an integration reload after which Amazon reported them offline). Needs a physical check: are they plugged in / on wifi / still in the Alexa app? If they show in the Alexa app but not HA, reload the Alexa Media Player integration.
- Aimee's preference: voice announcements over phone notifications, Living Room Echo for family stuff. Kids' Dots are theirs, don't announce on them without a reason.

**Note:** Alexa integration was [[Aimee]]'s idea - she gets full credit! 🏆

### LG TV (living room, webOS)
- **Entity:** `media_player.lg_webos_tv_ua73006la_2` (webostv integration; `_1` is Cast, `_3` is Music Assistant, ignore those for control)
- **Remote:** `webostv.button` service (UP/DOWN/LEFT/RIGHT/ENTER/BACK/HOME/EXIT/MENU/VOLUMEUP/MUTE/digits/RED etc). Verified working 2026-08-28.
- **"TV Remote" dashboard** at http://192.168.1.4:8123/tv-remote (sidebar, storage mode, created by Jarvis via websocket 2026-08-28 when Rob lost the physical remote). D-pad, volume, numbers, colours, source shortcuts, power.

### Other Entities
- **OctoPrint:** 3D printer monitoring
- **Tumble dryer:** Sensor integration
- **Climate controls:** Various zones

### Scripts
- `script.goodnight` — Turn off living room + snug lights

## Thread/Matter Integration
**Status:** WORKING (Mar 2026)
- **Border Router:** ZBT-2 coordinator
- **IPv6 requirement:** `net.ipv6.conf.all.forwarding=1` enabled
- **Devices:** IKEA KAJPLATS bulbs, BILRESA switch paired successfully
- **Commissioning:** Use HA Companion app (Docker can't access BLE)
- **Note:** BILRESA scroll wheel not fully exposed in Matter yet (button works)
- **Troubleshooting:** Restart OTBR if "NoBufs" errors appear

## Presence Tracking
**Current:** Only [[Rob]] tracked  
**Missing:** [[Aimee]], [[Dexter]], [[Logan]] need HA Companion app installed

## Project Integration
### Mission Control
- **Sensors:** `sensor.mission_control_api`, `binary_sensor.mission_control_online`
- **Health monitoring:** Tracks [[Mission Control]] container status

### Haven  
- **Sensors:** `sensor.haven`, `binary_sensor.haven_online`
- **Presence integration:** Meal planning based on who's home
- **Calendar parsing:** Away events for smart meal suggestions

## System Services
- **Music Assistant** runs a builtin Snapcast server (`:1704`) feeding the two play-room speaker Pis. Full detail: [[Play Room Speakers]].
- Pre-rebuild this box ran a Dakboard service and Plausible analytics alongside HA. Not yet re-confirmed on the Proxmox setup. See `Context/Infrastructure.md` for the current tooling picture.

## Technical Lessons
- **Docker/BLE limitation:** Can't access Bluetooth from containers
- **Commissioning approach:** Use phone's HA Companion app for Thread/Matter
- **IPv6 forwarding:** Required for Thread Border Router functionality
- **OTBR stability:** Restart if buffer errors occur

## Future Vision
**Cleanup needed:** Transform from "collection of stuff" to purposeful automation
**Focus areas:** 
- Organized device grouping
- Meaningful automation workflows  
- Family-friendly interface
- Integration with [[Haven]] and [[Mission Control]]

## Tags
#home-assistant #smart-home #automation #thread #matter #alexa #tesla

## Links
- [[Mission Control]] - Dashboard and monitoring
- [[Haven]] - Family app integration
- [[Aimee]] - Primary voice interface user
- [[Dexter]] - Personal Alexa device
- [[Logan]] - Personal Alexa device
- [[Tesla]] - "Timmy" integration
- [[Thread Border Router]] - ZBT-2 setup
- [[Play Room Speakers]] - Snapcast Pis (main + ambient) fed by Music Assistant