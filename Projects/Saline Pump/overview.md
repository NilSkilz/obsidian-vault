# Saline Pump

A DIY controlled saline infusion rig for breast inflation play. Rob's project, for Aimee.

## What it's for

Aimee enjoys saline injected into her breast tissue: the sensation and the temporary size increase. Precedent:
- Rob has done it before with bottles of saline and syringes (manual).
- Aimee has done it with Sean, gravity-fed from saline bags.

The goal is to replace the manual/gravity method with a controlled, measurable, symmetric pump rig: known volume per side, known rate, hands-free, repeatable.

## Concept

- 3D-printed enclosure housing two peristaltic pumps (one per breast, for symmetry), electronics, and power.
- ESP32 brain with a web interface (phone-driven) for set-and-go control.
- Sterile tubing from saline reservoir(s) → pumps → needles into the subcutaneous breast tissue.

## Core requirements

- **Two independent channels** (left/right) so each side can be dosed and balanced separately.
- **Volume-target dosing**: set a target ml per side, pump stops automatically when reached.
- **Rate control**: slow, comfortable infusion matching the gravity-feed pace she's used to.
- **Live readout**: volume delivered + elapsed time per side, on the phone.
- **Hard limits + e-stop**: firmware volume cap and a physical kill switch.

## Safety (this is going into her body, so it leads)

Subcutaneous saline infusion. Not IV, which lowers some risks, but still real. Non-negotiables:
- **Sterility**: sterile saline only, single-use sterile needles + tubing. Peristaltic pumps help here (fluid only ever touches the inside of the tube, never the pump mechanism).
- **Air**: fully prime/purge lines before needle insertion. Subcutaneous air isn't an embolism the way IV air is, but purge anyway.
- **Volume + rate caps**: conservative hard limits in firmware, not just the UI.
- **Comfort**: body-temp saline is far more comfortable than cold. Warming is a v2 nice-to-have; keep v1 simple.
- **Full sign-off from Aimee** on volumes and rate before any run. This is her body and her play.

## Status

- 2026-08-14: design phase, electronics + circuit.
- 2026-08-20: PCB v1 ordered, pinout locked (see [[hardware]]).
- 2026-09-11: **both pumps running on the assembled board** (the FET deaths were solder-joint intermittents, fixed by rework). Enclosure printing. Firmware Stage 6 written: gauge UI on the GC9A01s (port of `gauge-mockup.html`) + dosing model, in `firmware/gauges/gauges.ino`. Next: flow calibration (ML_PER_MIN_AT_100 timed-jug test), then encoders (Stage 7), then HX711 load cells replace the estimated reservoir level.
