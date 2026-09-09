# Edge-o-Matic DIY Build (for Fuck-io)

Researched 9 Sept 2026, straight from the source repos. Part of [[Fuck-io]]: this is the orgasm-detecting plug that closes the loop.

## REVISED PLAN (9 Sept 2026, evening): headless, same ESP32 as the machine

Rob's call, and it's the right one: no screen, no encoder, no SD, no MOSFET, no second ESP32. The plug side reduces to **one analog pressure sensor wired into the machine's ESP32**, with everything (arousal graph, thresholds, machine control) exposed through one web app served off that ESP32. The commercial EOM needs standalone UI hardware; we have a phone.

What this wins:

- **BOM collapses.** Electronics for the plug side: sensor + a resistor + two caps, ~£12-20. Whole plug incl. the inflatable itself: **~£35-55** (was £40-60 with the UI parts).
- **No network hop in the safety loop.** Orgasm detection and motor stop live in the same firmware; no WebSocket between "detected" and "stop". Remote viewers get the stream over the web app, but the loop closes locally.
- **The only thing running to the wearer is an air tube.** Sensor sits in the machine's control box, plug connects by silicone tube. Zero electrical contact with the body, which is the nicest galvanic-isolation story possible.
- One codebase, one web app, one box.

What it costs:

- **nogasm-wifi firmware is no longer used as-is.** It becomes donor code: port the arousal algorithm (`OrgasmControl.cpp` in v0.4.0, rolling pressure average + clench spikes accumulate an arousal score + threshold) into the machine firmware. It's small and readable; this is an afternoon, not a project.
- This tips the machine firmware question to **custom firmware using StrokeEngine as a library** (FuckIO lineage) rather than stock OSSM firmware, since we're modifying either way. Rob's written the React control panel for exactly this before (FuckIO-UI, 2021).
- Single point of failure: one crash takes out sensing AND motion. Mitigations are the ones already planned anyway: hardware E-stop on driver enable (not the ESP32), watchdog reboot with motor enable defaulting OFF, pressure ceiling check in the sampling loop.

One hard technical constraint: **the sensor must be on an ADC1 pin (GPIO 32-39)**. ADC2 is unusable while WiFi is up, and this firmware is always on WiFi. The nogasm-wifi default of GPIO 34 is ADC1, keep it.

Everything below is the original standalone-build research. **Still current: the sensor choice, analog front-end, plumbing, and safety sections.** The OLED/encoder/SD/MOSFET rows and the v0.4.0 flash instructions are kept for reference only.

## How it works

Inflatable butt plug -> air line -> analog pressure sensor -> ESP32 ADC. Pelvic-floor contractions during arousal/orgasm show up as rhythmic pressure spikes; the firmware graphs arousal, detects orgasm, and can stop/ramp an output (or feed a remote over WebSocket). Design lineage: nogasm (Teensy, 2016) -> nogasm-wifi / Edge-o-Matic 3000 (ESP32, Maus-Tec).

## Sources (all verified 9 Sept 2026)

- Firmware: `github.com/MausTec/edge-o-matic-3000` (same code also lives at `MausTec/nogasm-wifi`, the old name)
- Original hardware design + schematic: `github.com/nogasm/nogasm` -> `pcb/nogasm_schematic.pdf` (read it, details below)
- Official docs: maustec.io/eom, support hub at support.maustec.io (How-To section)
- User guide PDF in the repo: `doc/Edge-o-Matic_UserGuide.pdf`
- WebSocket + serial API docs (the fuck-io integration hook): `doc/WebSocket.md`, `doc/Serial.md`
- Wokwi simulation of the firmware on a devkit (test with zero hardware): wokwi.com/projects/396062360906622977

## Firmware: which version to build (important)

- **v2.x (current)**: ESP-IDF, links a **precompiled binary HAL** (`eom-hal-dist`) with pins baked for Maus-Tec's own boards. Not breadboard-friendly.
- **v0.3.4 / v0.4.0 (recommended for DIY)**: plain Arduino-framework PlatformIO project, `board = esp32dev`, every pin in an editable `config.h`. This is the classic community breadboard build.
- The repo README's own advice for DIY: breadboard it per the original nogasm schematic (pressure front-end + MOSFET stage).

Build: `git clone https://github.com/MausTec/nogasm-wifi && git checkout v0.4.0`, open in PlatformIO, `pio run -e esp32dev -t upload`. WiFi credentials go in `config.json` on the SD card.

## Pin map (from firmware v0.1.4-v0.4.0 `config.h`, verified)

| Signal | GPIO |
|---|---|
| Pressure sensor analog in (`BUTT_PIN`) | 34 |
| Motor PWM out (MOSFET gate) | 15 |
| SD card CS (SPI, shared VSPI bus) | 5 |
| OLED SSD1306 128x64 SPI: DC / RESET / CS | 13 / 14 / 12 |
| SPI bus (OLED + SD): MOSI / MISO / SCK | 23 / 19 / 18 |
| Rotary encoder A / B / switch | 33 / 32 / 35 |
| Encoder RGB LED: R / G / B | 2 / 4 / 27 |

## Analog front-end (from the nogasm schematic)

- Sensor in the original: **NXP MP3V5050GP** (0-50 kPa gauge, ported, **3V supply**, so its output range suits the ESP32 ADC directly).
- Original signal path: sensor Vout -> 750R -> MCP6001 op-amp unity buffer -> ADC, with 0.33uF on the output and 1uF + 0.01uF decoupling on the sensor supply. On an ESP32 the op-amp buffer is skippable for a short breadboard run: keep the RC (750R + 0.33uF) as a low-pass, feed GPIO 34 directly.
- Motor stage (only if driving a vibe motor locally): logic-level N-MOSFET (original: BUK92150-55A; IRLZ44N is the easy modern stand-in), 750R gate resistor, 10k gate pulldown, flyback diode (MRA4004/1N4007) across the motor, 12V motor supply. **For fuck-io we may skip this entirely**: the machine reacts over WebSocket, the plug doesn't need to drive anything.

## BOM (UK, Sept 2026, prices ballpark, check before ordering)

| # | Part | Est. | Notes |
|---|---|---|---|
| 1 | ESP32 DevKit (WROOM-32) | £0 (have) | `esp32dev` target |
| 2 | Pressure sensor **MP3V5050GP** | ~£10-18, check Mouser/Farnell stock | First choice: 3V, ADC-direct. Alt: MPXV5050GP or MPXV5100GP (5V versions, need a 2:1 divider on Vout). Community also uses generic 5V analog car-pressure sensors |
| 3 | Inflatable butt plug **with squeeze bulb** | £15-35 | The bulb is the pump AND the manual dump valve. Don't buy one without it |
| 4 | Silicone tube (4mm ID) + tee fitting | ~£5 | Plug -> tee -> sensor port; bulb on the third leg |
| 5 | OLED SSD1306 128x64, **SPI 7-pin version** | ~£5-8 | Not the 4-pin I2C one; firmware wires DC/RES/CS |
| 6 | Rotary encoder, SparkFun COM-10982 (RGB illuminated) | ~£3-5 | Generic EC11 works if you don't wire the RGB pins |
| 7 | MicroSD SPI module + small card | ~£5 | Config/WiFi creds live on SD in the DIY builds |
| 8 | Passives: 750R x2, 10k, 15k, 1uF, 0.33uF, 0.01uF | ~£2 | Front-end + gate network |
| 9 | (Optional) IRLZ44N + 1N4007 + 12V PSU | ~£8-12 | Only if driving a local vibe motor |
| 10 | Perfboard, wire, enclosure | ~£10 | Have most of it |

**Realistic spend with parts on hand: £40-60**, matching the earlier estimate in [[Fuck-io]].

### Revised headless BOM (the one to actually order)

| # | Part | Est. |
|---|---|---|
| 1 | Pressure sensor MP3V5050GP (or 5V MPXV + divider) | £10-18 |
| 2 | Inflatable plug with squeeze bulb | £15-35 |
| 3 | Silicone tube (4mm ID) + tee | ~£5 |
| 4 | Passives: 750R, 0.33uF, decoupling caps | ~£2 |

Rows 5-9 of the table above (OLED, encoder, SD, MOSFET stage) are **dropped**. ESP32 is the machine's own.

### Revised build order

1. Sensor + RC front-end on the machine ESP32 (GPIO 34), sketch that streams raw ADC over a websocket, blow in the tube, watch it move in the browser.
2. Port the v0.4.0 arousal algorithm, tune against the raw stream.
3. Plumb plug + tee + bulb, test inflate/deflate and the pressure ceiling.
4. Wire detection into the motion loop (stop/ramp actions), then build out the web app properly.

## Plumbing

Cut the plug's bulb hose, splice the tee in: plug on one leg, sensor port on another, bulb back on the third. Bulb inflates as normal; its bleed valve stays reachable as the manual deflate. Keep total inflation modest: 50 kPa is about 7.25 psi, and the firmware has a pressure ceiling setting; set it well below sensor max.

## Build order

1. Breadboard ESP32 + OLED + encoder + SD, flash v0.4.0, confirm UI works (or dry-run the Wokwi sim first).
2. Wire the sensor front-end, blow gently into the tube, watch the pressure graph.
3. Plumb the plug + tee + bulb, test inflate/deflate and the ceiling alarm.
4. WiFi up, hit the WebSocket API, confirm live arousal stream (this is the fuck-io hook).
5. Perfboard + enclosure once it all behaves.

## Safety

- Manual deflate (the bulb valve) always within reach of the person wearing it, non-negotiable.
- Firmware pressure ceiling set conservatively; the sensor is gauge-type so readings are relative to room pressure.
- Same rule as the machine: network dropout = safe state, never "hold last command".
