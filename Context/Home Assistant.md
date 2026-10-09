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
The core **Alexa Devices** integration (`alexa_devices`, config entry `01KXS4B998D8SWTMZYBP6MZQT8`, account rob_stokes@me.com) is installed, not the HACS Alexa Media Player. Entities use the **new-style notify entities**, not the old `notify.alexa_media_*` services:
- `notify.<device>_announce` (Alexa "announcement" chime + speech) and `notify.<device>_speak` (plain TTS), called via `notify.send_message` with `entity_id` + `message`.
- Devices: `living_room_echo`, `kitchen_dot`, `bedroom_dot`, `dexter_s_dot`, `logan_s_dot`. Also `media_player.<device>` for each.
- **Helper:** `Jarvis/bin/jarvis-say.sh "message" [device]` (default living_room_echo). Verified working 2026-08-28 11:41.
- **Status 2026-08-28:** Living Room Echo online and announcing. Kitchen, Bedroom, Dexter's and Logan's Dots all went `unavailable` at 2026-08-26 11:14 (same second, so likely an integration reload after which Amazon reported them offline). Needs a physical check: are they plugged in / on wifi / still in the Alexa app? Reloaded the entry 28 Aug 11:50, no change: diagnostics (`/api/diagnostics/config_entry/<id>`) show Amazon's API itself returning `online=False` for all four Dots, so the fault is Amazon-side (device/wifi/account), not HA. Reload: `curl -X POST $HA_URL/api/config/config_entries/entry/<id>/reload`.
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
- Pre-rebuild this box ran a Dakboard service and Plausible analytics alongside HA. **DAKboard confirmed alive and in use (Rob, 25 Sep 2026): it carries a Jarvis notification iframe. Subscription (£4.59/mo) stays.** Plausible still unconfirmed. See `Context/Infrastructure.md` for the current tooling picture.

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
## Pod Point (EV charger), added 2026-10-09

- Custom integration `pod_point` (mattrayner/pod-point-home-assistant-component 2.0.7), installed by hand into `/config/custom_components/pod_point` over HAOS SSH (no HACS on this instance). Config entry `01M4GZZZNT5M2JVGKX2QM907J4`, account rob_stokes@me.com. Creds in `~/.config/jarvis/podpoint.env` on CT 110.
- Charger PSL-557234, S7-2C (7kW, untethered). Entities `*.psl_557234_*`: status, cable_status, current_energy (session kWh), total_energy, last_completed_charge_cost, charge_mode, smart_charge_mode switch, charging_allowed switch.
- Cloud-polled and laggy (session kWh trails reality by many minutes). For live power use Shelly EM ch2 (`sensor.shellyem_34945470ed50_channel_2_power`), which is clamped on the Pod Point circuit. Ch1 (`sensor.shellyem_34945470ed50_channel_1_power`) is the rest of the house, excluding the charger; it goes negative when solar is exporting. Typical evening baseline ~650W, overnight ~380W.
- Charger wifi is weak (~-83 dB).
- Updates are manual (no HACS): re-download the release zip and restart core.
- **Overnight schedule (9 Oct 2026):** the Octopus Go window (00:30-05:30 daily) lives ON the charger as a Pod Point charge schedule + Smart mode, set by `Jarvis/bin/podpoint-schedule.py set 00:30 05:30` (venv `~/.venvs/podpoint`, podpointclient 1.6.1; `show` / `clear` too). Charger enforces it locally, so no HA/cloud dependency at 00:30. Verified: charger dropped from 6.9kW to 0 within ~2 min of setting it. **Never use `switch.psl_557234_charging_allowed`**: the integration can only write an all-day block or wipe the schedule, so it destroys the window (removed from the dashboard). Smart charge mode switch is safe (mode only; off = charge any time, on = schedule back). Boosts: scripts `ev_boost_1h`, `ev_boost_3h`, `ev_boost_stop` (pod_point.charge_now / stop_charge_now). If the window changes (BST/GMT or tariff), rerun the script.

## EV Charging dashboard, added 2026-10-09
- Sidebar dashboard **"EV Charging"** at http://192.168.1.4:8123/ev-charging (storage mode, built by Jarvis via websocket, one sections view `mg4`).
- Right now: markdown summary (live kW from Shelly ch2, miles/hour, session kWh → % / miles / £ estimate assuming 64 kWh pack and 3.5 mi/kWh), power gauge, Pod Point status/cable/session/last cost tiles.
- Usage: Shelly ch2 energy statistics (today/week/month/last month, 30-day daily bars) and a 24h power history of charger vs rest of house.
- Controls (updated 9 Oct): overnight schedule toggle (smart mode), Go explainer, Boost 1h / Boost 3h / Stop boost buttons, charge mode, override end, and helper `input_number.ev_unit_rate` (p/kWh, set to 9.5 for Octopus Go on 9 Oct; drives the £ estimates).
- Pod Point session kWh lags badly (showed 2.9 kWh while the Shelly had logged 4.26 kWh). Trust the Shelly figures. `switch.psl_557234_charging_allowed` was `unavailable` at build time.
