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
- **Dropped offline 9 Oct 20:35 BST** (cloud_connection off, not on UniFi), 7 min after the schedule paused charging at 20:28, so it was idle (0 W) when it went. Rob suspects a trip (history of it). Schedule still intact on the Pod Point cloud. Note: the Shelly ch2 reads 0 W when idle, so it can't tell a dead charger from a sleeping one; cloud_connection + UniFi are the tells. Rob heard of a 'clip over the cable' fix: likely a CT clamp (load management, stops the main fuse overloading while charging) or a ferrite (RF only, doesn't stop trips). Neither fits an idle trip; check RCD type (pre-2019 Solo 3 needs Type B) and what else shares the RCD. Update 22:30: charger has its OWN consumer unit, fitted with it, so shared-RCD is ruled out and RCD type was presumably matched by the installer. Still offline at 22:30. Leading suspects for recurring idle trips on a dedicated outdoor circuit: moisture ingress (glands/unit/outdoor joints, check if trips follow rain) or a tired RCD. Ferrite clips (ChatGPT's Tesla-era suggestion) are harmless but don't address earth leakage. Test: reset; instant re-trip = hard fault (electrician), holds for days = nuisance/moisture. Update 22:45: Rob recalls trips used to cluster around midday when the solar was generating (tonight's 20:35 trip was in the dark, 242V, idle, so it doesn't fit). Shelly ch1 voltage, 60 days of hourly stats: exporting hours avg peak 246.7V vs 243.6V importing; sunny afternoons hit 250-252.7V, never logged >=253V (the UK ceiling and typical PEN-fault/overvoltage cut-out), but hourly sampling misses short spikes and summer was likely higher. Solar correlation argues AGAINST moisture (sunny = dry) and FOR voltage rise; worth checking whether that little CU has a PEN-fault/O-PEN device and what actually trips (RCD vs MCB vs PEN unit). Two causes possible. **Automation `automation.pod_point_trip_logger`** (id podpoint_trip_logger, 9 Oct): cloud_connection off for 5 min → logbook entry with voltage, house W (negative = exporting), status, cable. Check the logbook after each trip. **One-night watchdog 9-10 Oct:** `Jarvis/bin/ev-charge-watch.sh` on a 2-min cron pings Telegram if Shelly ch2 drops <500W twice running (trip vs normal stop via cloud_connection), self-removes from cron 10 Oct 10:00. Charger left in Manual mode at Rob's request (Smart off, so the Go schedule isn't enforced) until he says otherwise. **Second trip 9 Oct 23:10 BST, UNDER LOAD:** reset at 22:40 (Rob was out, someone at home flipped it), charged 6.9 kW from 22:46, then ch2 went 6.88 kW to 0 in one sample at 23:10:06 and the charger left wifi (UniFi last_seen 23:12). Voltage 239.4V under load (244V after), house ch1 ~2.8 kW at the time, so ~9.7 kW / ~40A total: no overvoltage, nowhere near the main fuse. Two trips in 3 hours, one idle, one under load, after a reset = genuine fault, not nuisance; electrician job (RCD/MCB/PEN unit, glands). Pod Point cloud_connection still read "on" for 5+ min after it died, so ev-charge-watch.sh now uses the UDM wifi association (MAC e0:5a:1b:97:8e:e8) as the trip tell. **Reset 23:18 BST (Rob home):** photo of the charger CU: single **GARO GR RCBO C40A, 30mA, Type A, 6kA, EN 61009**, -25°C rated, two blanks, no separate PEN/O-PEN device (Solo 3 does PEN detection internally, and its built-in 6mA DC detection is why Type A is correct, so RCD type is ruled out). It's an RCBO, so a trip could be earth leakage OR overcurrent and the handle doesn't say which; overcurrent is very unlikely (32A charger on a C40). So: earth leakage (insulation fault/moisture in charger, cable or glands) or a tired/oversensitive RCBO. Electrician should insulation-resistance test the circuit and trip-time/ramp test the RCBO; RCBO is a cheap part. Wall below the CU is bare breeze block, not damp (Rob, 23:24; I misread the photo). Charger signal strength -91 dBm (weak wifi, explains laggy cloud). Back charging 6.9 kW from 23:18 in Manual mode. **Rob's own tests 23:29:** RCBO T button trips cleanly (mechanism OK); he says it only trips under load. Caveat: the 20:35 trip was 7 min after a scheduled pause with the car still plugged in, so "car connected" may be the real condition. Trips also happened in the Tesla era (ferrite advice dated from then), so two different cars argues against the car's onboard charger and points at charger/cable/RCBO. Load + sunny-midday clustering + 24 min into a charge fits HEAT: a loose/high-resistance terminal or a heat-derated RCBO in a sun-facing box. Next trip: carefully feel the RCBO case and sniff for hot plastic straight after; tell the electrician to check terminal torque. Ferrite still ruled out (50Hz leakage, ferrite does nothing at 50Hz). **Overnight 9-10 Oct: held.** After the 23:18 reset it charged ~6 h straight at 6.9 kW (to 05:16, car hit 100%, ~44.6 kWh total on ch2 incl. the pre-trip 22:40-23:10 run), no trip, despite rain on and off 01:00-05:00 (weather.forecast_home, ~78% RH, 13C) and house load peaks up to 7.6 kW. So: 6 h at full load kills the loose-terminal HEAT theory (a high-resistance joint only gets hotter the longer it runs; Rob agrees it doesn't feel thermal), rain alone isn't the trigger, and house load isn't either (22:49 had 5.7 kW house + charger, no trip). Pattern so far: both 9 Oct trips came soon after the charger came back on (23:10 was 30 min after the 22:40 reset), then it held 6 h. Best remaining read: total earth leakage sitting near the RCBO's threshold (charger filter leakage + car onboard-charger leakage + any damp in glands/joints), tipping over some sessions and not others; a 30mA RCBO legally trips anywhere 15-30mA, so a sensitive-end unit makes this far likelier. Electrician tests that settle it: leakage-clamp reading of standing earth leakage while charging, RCBO ramp test (actual trip mA), insulation resistance test. If standing leakage is a big chunk of 30mA, fix the leak; if the RCBO trips low, swap it (cheap).
- **10 Oct 2026 midday: stop-start without tripping.** Car plugged in ~12:14 (Manual mode). Pattern: ~6.9 kW for 5-12 min, then the Pod Point itself goes `out-of-service` (its FAULT state; cable_status also drops to off) for ~7-11 min, then auto-retries as a brand new session. Cycles 12:14-12:26, 12:40-12:51, 13:02-13:07, restarted 13:16 (smart mode on + 3h override set at 13:16, so Rob likely hit Boost). Pod Point API lists each as a separate charge record. RCBO didn't trip, wifi/cloud stayed up, voltage ~240V at each cut (not the 253V PEN/overvoltage cut-out), 13.9C partly cloudy. So it's the charger's own protection firing and self-recovering, not the car being full. Fits the leakage-near-threshold read: the Pod Point's internal 6mA DC leakage detection can trip and auto-reset by itself, while bigger AC leakage takes out the 30mA RCBO. Can't confirm without the fault code (API gives status only). Next: Rob checks the LED colour/flash during an off phase, tries a different Type 2 cable if one's available (untethered unit; worn cable plug is a cheap suspect), and calls Pod Point support, who can read the unit's fault log remotely (commissioned Feb 2023, so probably just out of a 3-year warranty).

## EV Charging dashboard, added 2026-10-09
- Sidebar dashboard **"EV Charging"** at http://192.168.1.4:8123/ev-charging (storage mode, built by Jarvis via websocket, one sections view `mg4`).
- Right now: markdown summary (live kW from Shelly ch2, miles/hour, session kWh → % / miles / £ estimate assuming 64 kWh pack and 3.5 mi/kWh), power gauge, Pod Point status/cable/session/last cost tiles.
- Usage: Shelly ch2 energy statistics (today/week/month/last month, 30-day daily bars) and a 24h power history of charger vs rest of house.
- Controls (updated 9 Oct): overnight schedule toggle (smart mode), Go explainer, Boost 1h / Boost 3h / Stop boost buttons, charge mode, override end, and helper `input_number.ev_unit_rate` (p/kWh, set to 9.5 for Octopus Go on 9 Oct; drives the £ estimates).
- Pod Point session kWh lags badly (showed 2.9 kWh while the Shelly had logged 4.26 kWh). Trust the Shelly figures. `switch.psl_557234_charging_allowed` was `unavailable` at build time.
- **Open ask (9 Oct 2026, unanswered):** Rob wants a way to know/override smart-charging on ad-hoc plug-ins (e.g. home midday, might need the car later). Jarvis's proposal, ranked: 1) Telegram ping on plug-in outside the cheap window with Charge 1h/3h/Wait buttons (no hardware), 2) NFC sticker on the Pod Point for tap-to-boost 3h (works for Aimee too, ~£5, needs Rob to buy one), 3) charge on solar export even though Pod Point can't throttle below ~7kW, 4) once iSMART binding is done, target charge to real battery %. Rob didn't respond to "build 1 and 3 tonight?" (got derailed by the second trip) — raise it again.

## CarPlay (added 2026-10-10)
- Rob enabled CarPlay in the iOS Companion app (app 2026.5.0). The CarPlay layout is configured ON THE PHONE (Companion App Settings > CarPlay > Quick access), not server-side, so Jarvis can't pick entities for him. CarPlay only shows actionable domains: button, cover, input_boolean, input_button, light, lock, scene, script, switch (no sensors), plus Assist.
- Car-ready scripts Jarvis built (all `script.car_*`): `car_nearly_home` (Kitchen Dot announces "Rob is about ten minutes away", living lights on if sun is down), `car_lights_on` / `car_lights_off` (living + snug), `car_ev_smart` / `car_ev_manual` (Pod Point smart_charge_mode on/off). Existing `ev_boost_1h/3h/stop` and the Alexa routine buttons (`button.rob_stokes_me_com_goodnight`, `_my_schedule`) also work there.
- Not yet tested live (would announce / flip lights). Living Room Echo is unavailable, so the announce uses the Kitchen Dot.
- Ideas not built: auto "nearly home" from a home-approach zone, or from `sensor.iphone_audio_output` = CarPlay (sensor currently disabled in the app).
