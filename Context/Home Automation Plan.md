# Home Automation Plan

Started 29 Oct 2026. Rob's idea: walk the house room by room, work out what HA already knows, what's missing, and how it all fits together. Shared household doc (Aimee can read and add to it). Implementation detail stays in `Context/Home Assistant.md`; this file is the plan.

## How we're doing it

1. **Rob describes a room**: who uses it and when, lights (type, switch, bulbs), heating, windows/doors, screens and speakers, anything plugged in that matters, and what annoys him about it now.
2. **Map it against HA**: what's already in there (inventory below), what's there but broken or orphaned.
3. **Gap list**: what to add (sensor, smart switch, bulb, plug), with rough cost.
4. **Behaviour**: what the room should actually *do*, written as plain rules ("when nobody's in the snug after 23:00, lights off").
5. Once every room is done: house-wide rules (presence, night mode, away mode, energy) and the order to build in.

## Principles (draft, to agree)

- **Physical switches always work.** Automation helps, it never stops a light switch doing its job. Aimee and the kids shouldn't need an app.
- **All automations live in HA**, Tide is the family glance and wall screens (see [[project_ha_tide_split]] in memory).
- **Local first** where there's a choice (Zigbee/ESPHome/Shelly over cloud-only kit), so the house still works when the internet wobbles.
- **Quiet by default.** Notifications only for things someone needs to act on.
- **Kids' rooms:** useful stuff only (lights, heating, bedtime routines), nothing that feels like surveillance.

## What HA knows today (snapshot 29 Oct 2026)

HA areas: Living Room, Kitchen, Bedroom, Garage, Snug. Most devices aren't assigned to an area yet.

| Room | In HA |
|---|---|
| Living room | Living-Light-Switch (ESP32, light + LEDs), Nest thermostat (only `climate` for the house), LG 50" TV, Living Room Echo |
| Snug | Snug-Light-Switch (ESP32, light + LEDs) |
| Kitchen | Kitchen Dot |
| Bedroom (Rob & Aimee) | Bedroom Dot, Lenovo Smart Clock (two duplicate entries, both unavailable) |
| Dexter's room | Dexter's Dot (unavailable since Aug), probably an Xbox |
| Logan's room | Logan's Dot (unavailable since Aug), probably an Xbox |
| Play room | main + ambient speaker Pis |
| Garage / outside | Shelly EM (ch1 house, ch2 Pod Point), Pod Point charger, MG4 |
| Unplaced | LG 43" TV, Philips 55" Android TV (unavailable), Samsung 32" monitor, three Xbox entries, Rob's MacBook |
| Whole house | Presence for all four (UniFi Wi-Fi, built 29 Oct), weather |

**Notably missing house-wide:** only two lights are controllable (living room and snug), no motion/occupancy sensors, no door/window sensors, no per-room temperature outside the living room, no smart plugs, no Zigbee coordinator.

**Tidy-up to do before building:** assign devices to areas, add areas for Dexter, Logan, play room, hallway/landing, outside; clear the duplicate TV, clock and Xbox entries; decide whether the dead Dots are coming back.

## Inventory pass (Rob, 29 Oct 2026)

Rob's kit list per room, matched against HA and the UniFi client list the same afternoon. Room-by-room behaviour (who uses it, what annoys) still to come.

**Big finding:** a lot of the "missing" kit is already on the network, just never connected to HA. A **Philips Hue bridge** is wired in (UniFi .173, MAC 00:17:88:6d:eb:d1) and the **Nanoleaf** ("Aurora", .60) is on Wi-Fi. Both are native HA integrations that only need a button press on the device to pair. A **Logitech Harmony Hub** (.142) is also on the network and not in HA.

| Room | Kit (Rob) | In HA? | Gap / next step |
|---|---|---|---|
| **Garage** | Washing machine, tumble dryer | No | Energy-monitoring smart plug on each (13A-rated, e.g. Shelly Plug UK) for "washing's done" announcements and running cost. Check first whether either is a "smart" model with its own app |
| | Solar inverter (Solis S6-GR1P3.6K, WiFi datalogger fitted) | No | Add via the datalogger: local Solarman integration if the stick supports it, else SolisCloud. Puts real solar generation on the Energy dashboard (currently missing) |
| | Pod Point | Yes | Done (plus the MG4 and Shelly EM) |
| **Master bedroom** | LG TV | Probably (the 43" UA75006LA, duplicated) | Assign to Bedroom, delete the dead duplicate |
| | Amazon Dot | Yes, online again | Assign to Bedroom |
| | iMac | No (on Wi-Fi as Robs-iMac, .41) | Presence/"is it on" only if useful; low priority |
| | Wax melter | Yes (29 Oct) | Already on a Hue smart plug (two plugs named Bedroom / Living Room Wax Melter, both on at pairing). Auto-off safety net is now just an automation, no purchase |
| **Snug** | Light switch | Yes | Done |
| **Living room** | Light switch | Yes | Done |
| | 2 x smart bulbs (Tuya, corrected by Rob 29 Oct, was "3") | Yes (29 Oct) | Done: `light.living_room_bulb_1` / `_2` via the Tuya integration, area Living Room. They are the two "lwip0" clients with near-consecutive MACs `d8:c8:0c:b2:e6:5a` (.23) and `d8:c8:0c:b2:e6:87` (.66), both online since 28 Oct 07:04. Cloud control for now, local (LocalTuya) later if latency annoys. Third lwip0 (`80:a0:36:a9:ae:97`, .101) is a different device, unidentified |
| | Amazon Echo | Yes (currently unavailable) | Assign to Living Room; check why it dropped |
| | LG TV | Yes (50" UA73006LA, three entries) | Keep the working one, delete duplicates |
| **Hallway** | DAKboard | No (Pi on Wi-Fi, .85) | Fine as is; it already shows Jarvis notifications. Hallway area needed for future sensors |
| **Play room** | Nanoleaf | Yes (29 Oct) | Done: `light.nanoleaf`, area Play Room, local control incl. its saved effects |
| | 6 x IKEA GU10 bulbs | Partly (29 Oct) | Hue bridge has 3 IKEA dimmables (bridge calls them Hallway 1-3). Where the other 3 are paired is unknown |
| | 2 x Philips Hue bulbs | Yes (29 Oct) | Hue bridge paired; the two colour spots ARE in the living room (Rob confirmed 29 Oct), renamed Living Room Spot 1/2 and part of cinema mode |
| | Music Assistant speakers (main + ambient Pis) | Yes | Main speakers currently unavailable, ambient fine |
| **Loft** | UniFi Dream Machine | Used for presence | Optional: full UniFi integration for network health |
| **Kitchen** | (not listed) | Kitchen Dot | Rob to walk it |
| **Dexter's / Logan's rooms** | (not listed) | Dots, offline since Aug | Rob to walk them |

**Living room automations (built 29 Oct 2026, Rob asked):** "cinema mode": lights off while the TV plays, dim warm on pause, back up when the TV goes off. Details in `Context/Home Assistant.md` (Lighting).

**HA area naming:** the dungeon room stays **"Play room"** in HA. HA area names show up in the app and on any wall screen, and the kids can see those.

**Quick wins (minutes, need someone at the device):** ~~Hue bridge~~ (paired 29 Oct, see `Context/Home Assistant.md` Lighting), ~~Nanoleaf~~ (paired 29 Oct), then sort which hub the IKEA bulbs live on. That alone takes the house from 2 controllable lights to ~13.

## Rooms

_(behaviour per room, filled in as Rob walks through them)_

## Open questions

- What is the third lwip0 device (.101)? (Not in Rob's Tuya account, so likely a different app or unpaired.) IKEA GU10s: paired to the Hue bridge, an IKEA hub, or Alexa?
- Washer/dryer: are either "smart" (own app)? Makes/models.
- Which rooms first? Suggest the most-used shared spaces (living room, kitchen) then outward.
- Budget per room / overall?
- Zigbee: add a coordinator (USB stick on the Proxmox host, or SLZB-06 on PoE) before buying sensors?
