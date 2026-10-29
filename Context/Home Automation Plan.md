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

## Rooms

_(filled in as Rob walks through them)_

## Open questions

- Which rooms first? Suggest the most-used shared spaces (living room, kitchen) then outward.
- Budget per room / overall?
- Zigbee: add a coordinator (USB stick on the Proxmox host, or SLZB-06 on PoE) before buying sensors?
