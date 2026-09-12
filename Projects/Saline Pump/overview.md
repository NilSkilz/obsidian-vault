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
- 2026-09-11: **both pumps running on the assembled board** (the FET deaths were solder-joint intermittents, fixed by rework). Enclosure printing. Firmware Stage 6b written and flashed: gauge UI on the GC9A01s (port of `gauge-mockup.html`) + the same gauges on the phone page + dosing model + 60..100% speed slider, in `firmware/gauges/gauges.ino`.
- 2026-09-12: **Stage 7 written and compiling clean** (81% flash, 16% RAM). Two additions:
  - **Encoders live.** Turn = 1% speed per detent, applied instantly if the pump is running; the knob and the phone slider share one variable so they can't disagree. Short press = STOP that side from any state; hold 1.2s = start (long-hold so a knock can't start a pump). Quadrature decoded in an ISR reading the GPIO input registers directly, because the 40ms-per-frame draw loop would drop detents if polled.
  - **Flow calibration is a button, not a reflash.** Calibrate runs a side at 100% for exactly 60s with a countdown on the glass, you type the ml caught, it stores ml/min-at-100% in NVS. Survives reboot and OTA. Until that's done every volume on the rig is a guess (default 100 ml/min).
  - Phone page verified in a real headless browser: no JS errors, gauges and CAL state render correctly.
  - **Stage 7a, the boot fix (14:55).** Stage 7 as first flashed would not boot: no heartbeat LED, no web server, dead-looking board. Cause was firmware, not hardware. `setup()` armed CHANGE interrupts on all four encoder lines whether or not an encoder was plugged in, and **Enc R's CLK/DT are GPIO34/35, input-only with no internal pull-up**. With the KY-040s not yet wired (they mount to an enclosure still on the printer) both pins floated and chattered, and two floating pins firing edge interrupts flat out starved `loop()`. Enc L on 27/26 was never at risk: its internal pull-ups hold it quiet unwired. Fixed three ways, so a knob can never cost a boot again: (1) knobs are **off until declared wired**, per side, from a KNOBS panel on the phone page, persisted in NVS; (2) a 40ms steadiness probe refuses to arm an interrupt on a flickering pin; (3) a guard in `loop()` counts ISR entries per second and disarms anything firing like a floating input (>4000/s), clearing the opt-in so the next boot comes up clean. Also `QTAB` moved to DRAM (an IRAM ISR reading a flash-resident table crashes if it fires during an NVS write or an OTA), and `setup()` now blinks the LED three times on entry so "did it boot at all" is answerable without a serial cable.
  - **Jarvis is not pushing OTA for now, at Rob's call** (a previous OTA push left the board not booting). ArduinoOTA is still compiled in, but Rob flashes over USB from the vault sketch until it's trusted again.
- Next: flash Stage 7a, then run the wet calibration, then HX711 load cells to replace the estimated reservoir level with a real weight.
