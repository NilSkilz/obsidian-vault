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
**Device List:**
- `notify.alexa_media_bedroom_dot`
- `notify.alexa_media_kitchen_dot`
- `notify.alexa_media_living_room_echo`
- `notify.alexa_media_dexter_s_dot`
- `notify.alexa_media_logan_s_dot`
- `notify.alexa_media_rob_s_echo_dot`
- `notify.alexa_media_everywhere`
- `notify.alexa_media_last_called`

**Note:** Alexa integration was [[Aimee]]'s idea - she gets full credit! 🏆

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