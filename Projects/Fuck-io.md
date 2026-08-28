# Fuck-io

**Status:** idea, noted 28 Aug 2026. Not greenlit, no budget, no timeline.

## The idea

A stepper-motor fucking machine, built on an existing open source design, paired with an orgasm-detecting butt plug, with remote control over the internet. Working name: **fuck-io**.

Three parts:

1. **Machine.** Stepper-driven linear actuator. Rob has done this before: `FuckIO-UI` on GitHub (Dec 2021) was a React/MUI control panel for theelims' **FuckIO** ESP32 firmware (speed / depth / stroke / sensation / pattern, start/stop, sent as GET params to an ESP32 at `fuckio.pidgeonsnest.uk`). The other big open source option is **OSSM** (Open Source Sex Machine, KinkyMakers): ESP32 + closed-loop servo/stepper (iHSV57 style), belt-driven rail, big community, active firmware. FuckIO's motion library (StrokeEngine) is the more elegant motion model; OSSM has the hardware momentum. Decide which base to build on before buying anything.
2. **Orgasm detection.** The known open source design is the **Edge-o-Matic 3000** (MausTec, evolved from the nogasm project): inflatable butt plug + pressure sensor, detects the rhythmic pelvic-floor contractions of orgasm as pressure spikes. Its firmware already exposes a WebSocket API and can drive external toys, so the plug side is mostly integration work, not invention. It can also be built DIY (ESP32 + pressure sensor + inflatable plug) rather than bought.
3. **Remote control over the internet.** The 2021 UI already did this (crudely, plain GET to a public hostname, no auth). Proper version: machine and plug both talk to a broker/backend, web UI for the remote party, auth, and an in-room hard stop that the remote side cannot override.

## The interesting bit

The plug closes the loop. Orgasm detected -> machine reacts (stop for denial/edging, or hold/ramp for forced). The remote operator gets the same signal live. That feedback loop is what makes it more than a machine plus a remote.

## Safety notes (non-negotiable if this gets built)

- Physical E-stop on the machine, wired to the driver enable, not to the microcontroller.
- Stroke depth and speed limits set locally by the person on the machine; the remote side operates within them, cannot raise them.
- Network dropout = machine stops, never "hold last command".
- Inflatable plug: pressure ceiling in firmware, manual deflate valve.

## Existing assets

- `github.com/NilSkilz/FuckIO-UI` (private): CRA + MUI slider UI, axios GET to firmware. Scaffold only, one App.js, but it shows the parameter model Rob liked.
- Rob's 2021 hardware: unknown whether the ESP32/stepper build still exists. Ask.
- Overlap with **Tethered** (safety, consent, check-ins) and the Saline Pump (ESP32 motor control, same toolchain).

## Open questions

- FuckIO firmware base or OSSM base?
- Build the plug (Edge-o-Matic DIY) or buy one?
- Does the 2021 machine still exist, and what motor/driver was it?
- Backend: reuse Tethered's stack, or standalone?
