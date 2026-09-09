# Edge-o-Matic DIY Build (for Fuck-io)

Researched 9 Sept 2026, straight from the source repos. Part of [[Fuck-io]]: this is the orgasm-detecting plug that closes the loop.

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
