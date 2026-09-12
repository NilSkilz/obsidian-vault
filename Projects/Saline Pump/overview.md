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
  - **Stage 7b, instrument the boot (15:10).** 7a's floating-pin theory did **not** fix it: Rob flashed it and still got no LED and nothing past the ROM header on serial. Two guesses is one too many, so 7b stops theorising and makes the board report instead. Serial now comes up **first**, before anything that can hang, and prints a build banner (`STAGE 7b` + compile timestamp), `esp_reset_reason()` and the heap figures; every risky init step prints a numbered checkpoint **before** it runs (`[1] PWM` … `[8] BOOT COMPLETE`), so the last line on the monitor is the thing that killed it. The boot blink went from 3x60ms (360ms total, genuinely easy to miss) to 3x250ms. `loop()` prints an `alive` line every 10s with uptime, heap, WiFi state and IP.
  - **The real 7a bug found while instrumenting:** if the 112KB frame-buffer malloc failed, `setup()` sat in `while(true) delay(1000)` forever. No LED, no web server, no further serial: indistinguishable from a dead board, and a prime suspect for what Rob was actually seeing. A frame buffer is now **never** allowed to cost a boot: a failed allocation just disables the two round screens, says so, and WiFi/phone UI/pumps/knobs carry on. Same principle as the knobs.
  - **`firmware/blink/blink.ino`** added: a 10-line "is this board alive?" sketch (gates forced LOW, LED at 1Hz, serial banner). It splits one question into two when the rig looks dead: blink works = board and upload path are fine, fault is in `gauges.ino`; blink fails too = board, cable, port or IDE settings, and no firmware change will help.
  - **Stage 7c, bench mode (15:20).** Board is out of the PCB socket and loose on the desk while we work on the phone UI: nothing plugged in, no screens, no KY-040s. Two switches at the top of `gauges.ino`, `ENABLE_SCREENS` and `ENABLE_KNOBS`, now **compile those peripherals out** rather than skipping them at runtime. Both default to `0`. With screens out there is no 112KB frame buffer at all (~112KB more heap for WiFi), no SPI, no CS pins driven and no per-frame redraw eating ~40ms a tick; with knobs out the encoder pins are never even set to `INPUT`, so nothing can attach an interrupt to a floating GPIO34/35. The phone page shows an amber BENCH MODE banner and hides the KNOBS card, and `/status` reports `knobs` + `screens`, so it is obvious from the UI which build is on the board. Pumps, the firmware caps, the stall floor, the low-reservoir stop and the E-stop are untouched and still live. **Board back in the socket: set both `#define`s to 1 and reflash.**

  - **Stage 7d, the page stops being a cockpit (15:35).** Rob's verdict on the 7c page: confusing, the big number looked low-res, and the flow calibration felt like it took ages to react. All three were real, and all three are fixed.
    - **Two views.** "Run" is just the two gauges, speed, target and Start/Stop/Prime. "Settings" holds flow calibration, refill/reset, knobs and the safety notes. STOP ALL stays pinned to the bottom of both.
    - **Crisp text.** The canvas was a 240x240 backing store stretched over a 240 CSS px box on a 2-3x phone screen, so every glyph was browser-upscaled. The backing store is now sized to `devicePixelRatio` (capped at 2) with the context scaled to match.
    - **Responsiveness, three separate causes.** (1) Every endpoint now answers with the **full status JSON** instead of `"ok"`, so a tap gets fresh truth in one round trip instead of waiting up to 700ms for the next poll to find out what its own command did. (2) `WebServer` serves **one client at a time**, so overlapping fetches sat in the TCP backlog: all page traffic now goes through a single queue and a button tap jumps the queue. Polling is adaptive (400ms active / 1500ms idle / 250ms for 2.5s after a tap). (3) Delivered ml, elapsed time, reservoir level and the calibration countdown are **advanced locally** off the known flow rate between polls and corrected by each poll, so the 60s countdown ticks every second instead of lurching. Taps also patch the UI optimistically before the request goes out, and the draw loop is 30fps active / 10fps idle / off entirely on the Settings tab or a backgrounded page (it was a flat 60fps redraw of two faces forever, which is what made touch feel sticky).
    - **Tide theming.** Lifted from `mission-control/src/tide/tide.css`: dark ground, one gradient voice, an ambient breathing glow, hairline sections instead of boxed cards, pill buttons. Tide runs coral/rose; this rig runs **teal** with coral as the rationed accent (dose ring, warnings, RIGHT badge). The GC9A01 faces were recoloured to the same palette so the glass and the phone read as one object. Verified in headless Chrome at 320 / 390 / 820px against a mocked `/status`.
    - 80% flash, 16% RAM. Bench switches still both `0`.

  - **Stage 7e, screens on (2026-09-12, 17:45).** Board back in the socket, both GC9A01s and both KY-040s physically plugged in, running on USB only (no 12V, so the pumps cannot turn: safest possible first power-up). `ENABLE_SCREENS` is now **1**, `ENABLE_KNOBS` stays **0** on purpose, one subsystem at a time. The KY-040s can stay plugged in with this build because nothing in it ever touches an encoder pin, so a floating-input boot hang is off the table by construction.
    - **Boot splash.** Each panel names itself before the normal face: LEFT (teal) / RIGHT (coral), "screen ok", and the CS pin that drove it, held 1.5s. It catches three faults on sight: dead or unpowered panel (stays black), CS_L/CS_R swapped at the header (LEFT lands on the right-hand glass), both CS lines tied or shorted (both panels show the same word). `SCREEN_SPLASH` switch at the top of the file, set it to 0 once the rig is trusted.
    - **Checkpoint [4] split into letters,** because "it stopped at [4]" is too coarse with two panels, a shared bus and a shared RST: `[4a]` SPI.begin, `[4b]` tftL.begin, `[4c]` tftR.begin, `[4d]/[4e]` splashes, `[4f]/[4g]` first faces. The last letter on the monitor IS the fault. Banner now reads `STAGE 7e` and `PERIPHERALS:` instead of `BENCH MODE:`.
    - **The redraw cadence had to change or it would have undone Stage 7d.** A face is a 240x240 render plus a 115KB SPI push, and at 27MHz that push alone blocks `loop()` for ~34ms; the old flat 40ms tick meant the board drew essentially all the time and the web server got the scraps. 7d's responsiveness work was measured with the glass compiled OUT, so switching screens on would have brought the lag straight back. Now: **something moving** = 60ms alternating with the water animating; **everything idle** = a face is pushed only when a cheap signature of what `drawFace()` actually draws changes, plus a 1s safety refresh. Side effect worth keeping: the water holds still when nothing is pumping, so moving glass = a pump is turning, readable across the room.
    - **UTF-8 fix.** The page served as `text/html` with no charset and no `<meta charset>`, so the middle dots in the status line rendered as `Â·` on a browser whose locale default is not UTF-8. Both ends now say utf-8.
    - Page re-verified in headless Chrome against a mocked `/status`: no JS errors, correct banner in both the knobs-compiled-out and the frame-buffer-alloc-failed cases (`/status` gained `scomp` so the page can tell "compiled out" from "would not allocate"). 82% flash, 16% RAM.
    - **Not yet proven on hardware:** written, compiled and page-verified here, but nobody has flashed it. Flash with the serial monitor open at 115200 and read the checkpoints.

- Next: flash Stage 7e with the serial monitor open (the checkpoint line it stops on IS the diagnosis) and confirm both panels splash their own side, then `ENABLE_KNOBS 1` and reflash, then pumps dry on 12V, then the wet calibration, then HX711 load cells to replace the estimated reservoir level with a real weight.
