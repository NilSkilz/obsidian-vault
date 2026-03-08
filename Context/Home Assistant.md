# Home Assistant

**Smart home automation platform - the central hub**

## Connection Details
- **URL:** http://192.168.1.2:8123 (localhost:8123 from homeserver)
- **Status:** Supervised on Debian 12
- **Health:** `healthy: true`, `supported: false` (Plausible runs alongside)
- **User:** jarvis (admin)

## Current State
**Rob's assessment:** "collection of stuff" without clear vision  
**Goal:** Tidy up with a clear purpose and organized automation strategy

## Device Categories

### Lighting
- **Nanoleaf:** `light.aurora_52_50_96`
- **Living room:** `light.living_room_lights_led`, `switch.living_room_lights`
- **Snug:** `switch.snug_lights`
- **IKEA Matter/Thread:** KAJPLATS bulbs, BILRESA switch (working as of Mar 2026)

### Tesla Integration
**"Timmy" - Family Tesla:**
- `switch.timmy_charger`
- `switch.timmy_sentry_mode`  
- `button.timmy_horn`
- `climate.timmy_hvac_climate_system`

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
- **Dakboard:** pm2 service `jarvis-dakboard` on port 18850
- **Additional services:** Plausible analytics running alongside

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