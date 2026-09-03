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

## Motivation

Came up unprompted in Rob's Fet chat with [[Mary]] (1 Sept 2026): she's obsessed with fucking machines and has used one before. Rob mentioned the old motor got poached for another project and floated remote-controlling it for her once she's back in Oxford in October. Not a commitment, just a live reason to actually revive this rather than let it stay an idea.

## Existing assets

- `github.com/NilSkilz/FuckIO-UI` (private): CRA + MUI slider UI, axios GET to firmware. Scaffold only, one App.js, but it shows the parameter model Rob liked.
- Rob's 2021 hardware: **still mostly exists** (confirmed 28 Aug 2026). **NEMA 23** stepper plus its driver (both believed to survive, driver model TBC). It **stalled sometimes** in 2021: almost certainly driver/PSU starved (a 2A-class driver on 12V will do exactly that to a NEMA 23), or crank binding, not a dead motor. Check the driver label before reusing it. It was mounted on a tripod, which was unstable; needs a firmer base (plywood sled or 2040/4040 ali extrusion frame, sub-£30). Check what survived before buying anything.
- Overlap with **Tethered** (safety, consent, check-ins) and the Saline Pump (ESP32 motor control, same toolchain).

## Open questions

- FuckIO firmware base or OSSM base?
- Build the plug (Edge-o-Matic DIY) or buy one?
- Which driver board survived (A4988/DRV8825 class = replace; TB6600/DM542 = keep)? And what PSU voltage?
- Base design: sled vs extrusion frame.
- Backend: reuse Tethered's stack, or standalone?

## Plug cost estimate (28 Aug 2026, ballpark)

Edge-o-Matic DIY from scratch, UK prices:
- ESP32 dev board: £6-10
- Pressure sensor: MPXV5100GP £12-20, or a generic 5V 15psi analog car/exhaust pressure sensor £6-10 (EOM community confirms these work)
- Inflatable butt plug with squeeze bulb (the plug's own bulb is the pump, no motor needed): £15-35
- Silicone tubing + tee: £5
- Small OLED/TFT + rotary encoder or buttons: £8-12
- Perfboard/wiring/enclosure: £10
- **Total roughly £60-90.** Rob already owns ESP32s and perfboard, so realistically £40-60.

Buying instead: Maus-Tec sells the EOM3000 built (historically ~$250-300 USD, plus shipping/import), and a cheaper DIY kit (bare board + parts). Building is the obvious call here, same toolchain as the Saline Pump.

## Full machine cost estimate (28 Aug 2026, ballpark UK prices)

Assumes the NEMA 23 is reused. Stalling fix = proper driver + 24-36V supply, so those are costed as new.

| Part | Cost | Notes |
|---|---|---|
| NEMA 23 stepper | £0 (have) | 2.8-3A, ~1.9 Nm typical. Replacement if dead: £25-35 |
| Driver: TB6600 (4A) | £12-18 | Cheap fix. Better: DM542 digital driver £25-35, quieter and smoother |
| Alt: closed-loop upgrade (iHSV57 servo, the OSSM default) | £90-130 | Cannot stall, encoder feedback. Only if budget allows |
| PSU 36V 10A (or 24V 15A) | £20-30 | The stalling fix. 12V is not enough for a 23 at speed |
| ESP32 | £0 (have) | FuckIO / OSSM firmware both target it |
| Linear motion: 2040 extrusion rail + carriage + GT2 belt + pulleys + idler | £35-55 | OSSM-style belt drive. Alt: crank + con-rod off a flywheel, £15-25 in printed/laser parts, simpler but fixed stroke |
| Frame/base: 2040/4040 extrusion + corner brackets, or 18mm ply sled | £25-45 | Replaces the tripod. Weight matters more than stiffness; add a sandbag pocket |
| Vac-U-Lock adapter + double-ended rod | £10-15 | Standard toy mount |
| E-stop mushroom button, wired to driver enable | £5-8 | Non-negotiable |
| Wiring, connectors, ferrules, enclosure for driver+PSU | £15-20 | |
| Printed parts (carriage ends, motor mount) | £0-15 | Depends on printer access |
| **Machine total** | **£125-200** reusing motor | **£220-330** with closed-loop servo |

Plus the plug (£40-60 above), plus £0 for the remote/backend if it rides on Tethered infra.

**Whole fuck-io, realistic: £170-260.** Buying equivalents: OSSM kit ~$300-400, EOM3000 ~$250-300, a Hismith is £250-500 with none of the integration. Build wins comfortably.

**Stalling diagnosis for the old rig:** (1) driver current limit set below motor rating, (2) 12V supply, torque collapses above a few hundred RPM, (3) microstepping too fine with no acceleration ramp in firmware, (4) mechanical binding on the tripod flexing. New driver + 36V PSU + StrokeEngine's acceleration profiles fix 1-3; the base fixes 4.
