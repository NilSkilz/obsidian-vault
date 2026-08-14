# Saline Pump — Hardware & Electronics

Design notes for the ESP32-controlled dual peristaltic saline rig. Working doc, 2026-08-14.

## Architecture (v1 proposal)

```
Battery/PSU ─┬── Buck (→5V) ── ESP32 (3V3 onboard) ── web UI (WiFi AP or LAN)
             │                     │
             │                     ├── 2×GPIO ← Encoder L (flow-rate knob, L) + push
             │                     └── 2×GPIO ← Encoder R (flow-rate knob, R) + push
             │
             ├── MOSFET Q1 (PWM) ── Pump L (12V peristaltic) ── flyback diode
             └── MOSFET Q2 (PWM) ── Pump R (12V peristaltic) ── flyback diode

Reservoir(s) ── tubing ── Pumps ── tubing ── needles → breast tissue

Volume tracking: load cell under reservoir (weight → ml), OR time × calibrated flow rate.
E-stop: physical NC button in the 12V pump rail (kills pumps even if ESP32 hangs).
```

## Bill of materials (draft)

| Part | Pick | Notes |
|---|---|---|
| MCU | ESP32 devkit (WROOM) | WiFi, LEDC PWM, ADC, cheap |
| Pumps ×2 | 12V peristaltic (e.g. Kamoer NKP / generic) | Unidirectional; fluid only touches tube. Choose one with food/medical-grade silicone tube |
| Pump driver ×2 | Logic-level N-MOSFET (IRLZ44N) OR DRV8871 module | Low-side switch + PWM speed. MOSFET is simplest for unidirectional |
| Flow knobs ×2 | Rotary encoder (EC11, detented, w/ push switch) | Relative deltas → firmware. Turns forever, no end stop. Push = per-side STOP or mode. NOT a pot |
| Flyback diode ×2 | Schottky (1N5822) across pump | Motor is inductive; protect the MOSFET |
| PSU | 12V 3–5A brick | Sized to both pumps + margin |
| Buck | 12→5V (MP1584 / LM2596) | Feed ESP32 5V pin |
| Volume sense ×2 | HX711 + load cell (1–5kg), **one per reservoir** | Weigh reservoir; 1g ≈ 1ml saline. HX711 amp lives **in the printed base** next to the cell |
| Reservoir base ×2 | 3D printed, load cell + HX711 built in | Connects to main unit by a cable + 4-pole **3.5mm TRRS** jack (see note) |
| Display | **2× round GC9A01 240×240 SPI** (one gauge per pump), or 1× ST7789 1.3" split-screen | Round gauge = one value per face, so it wants one per side. Two costs +1 GPIO over one. Phone UI still does fine control |
| E-stop | NC momentary/latching button | In series with pump 12V rail |
| Enclosure | 3D printed | Houses pumps, PCB, PSU inlet, tube pass-throughs, TFT window |

## Why these choices

- **Peristaltic over syringe/diaphragm**: fluid never contacts the mechanism, so the only sterile path is the disposable tube + needle. Also self-priming and gives a roughly known volume per revolution.
- **MOSFET low-side PWM**: pumps run one direction only, so a full H-bridge is overkill. One logic-level MOSFET per pump, driven by ESP32 LEDC PWM, sets speed = flow rate. A DRV8871 module is a tidier drop-in if we want current limiting.
- **Load cell for volume**: peristaltic pumps drift with tube wear and back-pressure, so "time × nominal flow" alone will be off. Weighing the reservoir gives a true delivered-volume measurement (1 ml saline ≈ 1.0 g). Close the loop: pump until Δweight = target. One shared reservoir means one load cell can't split L/R, so either two reservoirs or track per-channel by sequencing (do L, then R).
- **Hardware e-stop in the power rail**: firmware caps are necessary but not sufficient. A physical switch that cuts pump power independent of the ESP32 is the real safety backstop.

## Reservoirs: two printed bases, sensor built in

Two reservoirs, each sitting on its own 3D-printed base with a load cell + HX711 built in. Confirmed direction. Gives clean per-side volume with no sequencing hack, and no cross-contamination between sides.

**The jack gotcha (important):** a raw load cell has **4 wires** (E+, E-, A+, A-) carrying tiny millivolt signals. Sending those analog down a cable + jack picks up noise and wrecks accuracy. So: **put the HX711 amplifier inside the printed base**, right next to the cell, and run the *digital* side back to the main unit. The digital side is also 4 wires (VCC, GND, DT, SCK), so:

- Use a **4-conductor 3.5mm TRRS** jack (not a normal 3-pole TRS — that only has 3 contacts). Cheap, self-aligning, easy to unplug per side.
- Or a small keyed connector (JST-SM, GX12 aviation) if we want something more rugged / idiot-proof than a headphone jack.
- Each side is one plug: unplug a base, swap it, done. Two jacks on the main unit, one per reservoir.
- Firmware reads two HX711 channels. They can **share the SCK (clock) line** and use separate DT (data) pins, saving a GPIO.

## Display: two round gauges, one per pump

Rob likes the round GC9A01 "gauge" look, and it suits the round knobs. A round face naturally shows *one* value, so the clean version is **one round display per pump** — left gauge for the left pump, right for the right. Rob flagged this himself; it's the nicer design, not a dealbreaker if we drop to one.

**Two displays barely costs anything.** They're SPI, so both share the same bus — **MOSI, SCK, DC, RST and backlight are all common** — and each display only needs its **own CS (chip-select) pin**. So going from one round TFT to two is **+1 GPIO**, not double the wiring. Firmware just toggles the right CS before drawing each gauge.

- **Buy the GC9A01 module that breaks out CS.** Some of the cheapest 1.28" round boards tie CS to ground (single-display assumption) — those can't be multiplexed. Confirm a CS pin on the header before ordering two.
- Each gauge shows: live rate, delivered ml, run/stop, and goes big/red on STOP for that side. Phone UI stays the place for exact target entry.
- **GPIO budget (two round displays):** shared SPI = MOSI, SCK, DC, RST (4) + **2× CS** + 2× backlight (or tie both BL high / one PWM) ≈ 8. Two encoders = 4 + 2 push = 6. Two PWM pumps = 2. Two HX711 sharing clock = 3. ≈ **18 GPIOs**, still comfortable on a WROOM devkit. Keep ADC2 pins free (WiFi conflict) and avoid strapping pins for anything that must be a clean level at boot.
- **Fallback if pins/budget get tight:** one ST7789 1.3" square split down the middle (L | R). Works, just less pretty than two round gauges.

## Flow knobs (rotary encoders, not pots)

We want rate settable from **both** the knob and the phone UI, with a knob that turns forever. That rules out a pot. A pot is *absolute*: it reads its physical angle as the value, so the moment the UI sets a rate the pot and screen disagree, and the next nudge of the knob snaps the rate back to wherever the pot happens to be sitting. Classic "parameter jump." No fixed set position works cleanly with a pot.

A **rotary encoder** is *relative*: it reports "turned N clicks CW/CCW", not an absolute position. It spins endlessly with no end stop. Both the encoder and the UI edit **one shared `rate` variable** in firmware: the encoder adds/subtracts deltas, the UI writes absolute values, and they never fight. Turn the knob → nudge rate up/down from wherever it currently is. That's exactly the continuous-knob behaviour Rob wants.

- **Two GPIOs per encoder** (A/B quadrature) instead of one ADC pin. Most EC11-type encoders also have a **push switch** — free per-side STOP or a mode toggle.
- No ADC noise, no calibration, no ADC1/ADC2-vs-WiFi gotcha. Debounce in firmware (interrupt on A/B, or a library like `ESP32Encoder`).
- Detented (clicky) encoder gives tactile steps — e.g. 1 click = ±0.1 ml/min. Firmware still clamps to the rate cap regardless of how far it's spun.
- The screen shows the live rate value, so the knob and UI always reflect the same number. Coarse tactile control on the knob, precise target + STOP on the phone.

## Control / firmware sketch

- Single shared `rate` per side, edited by **both** encoder deltas and UI writes; LEDC PWM duty derived from it (clamped to the rate cap).
- Closed-loop volume: read HX711, integrate/compare to target, stop pump at target.
- Web UI (async web server): per-side target ml, rate, start/stop, live ml + time, big STOP button.
- Firmware hard caps: max ml per side, max rate, max run time — independent of UI values.
- Prime/purge mode: run pump to fill lines with no volume counting toward the dose.

## Flow rate & pump sizing (target set 2026-08-14)

**Target: 1 litre per breast in 60 min.** Reference point: Aimee's bag/gravity runs did ~1L per breast in ~2h, so this is **double her previous pace**. Flag to Aimee before a run — the old rate was just whatever gravity gave, not a chosen comfort ceiling. Doubling it should be fine but it's her call.

- **Per-pump rate = 1000 ml/hr = ~16.7 ml/min** (each side independent, both run together).
- This is a **modest rate** for 12V peristaltics, which is good: we pick a pump whose *top* speed is well above 17 ml/min so 17 sits at a relaxed mid-throttle. Running a peristaltic near its floor (very low PWM) gets pulsatile and can stall — headroom keeps the flow smooth.

**Pump pick: Kamoer NKP (12V), silicone or PharMed BPT tube.**
- NKP range is ~1.2–90 ml/min depending on motor/tube bore, so 17 ml/min ≈ 20% of top end — smooth, controllable, never straining.
- Proper **food/medical-grade tube options** (PharMed BPT or silicone), which is the whole reason to pay for a Kamoer over a generic. This is the sterility-path part; don't cheap out here.
- Generic 12V "Adafruit/PMD-type" pumps (~100 ml/min top) would physically do it too, but tube quality is the unknown — fine as a fallback, not first choice.
- Higher-flow alt if we ever want faster: ATO 12V micro at ~150 ml/min.

At 17 ml/min the constraint isn't pump power at all — it's tube bore, needle gauge, and comfort. The pump is loafing.

## Needle gauge (sized for the top of the range, not the average)

Rob wants variable rate (~5 to 50 ml/min, dialled live) so Aimee can push it faster in a club. So size the needle for the **top** (50 ml/min), not the 17 ml/min average. Gauge sets how hard the pump has to shove before back-pressure fights it.

Back-pressure at 50 ml/min (Poiseuille, saline ≈ water, ~19mm metal cannula + ~30cm butterfly tubing @ ~0.8mm ID):

| Gauge | Needle ID | ~Back-pressure @ 50 ml/min | Verdict |
|---|---|---|---|
| **21G** (green) | 0.51 mm | **~5–6 psi total** | **Pick.** Huge headroom, pump never strains |
| 23G (blue) | 0.34 mm | ~12–13 psi | Works, finer/less noticeable, but pump leans on it |
| 25G (orange) | 0.26 mm | ~27+ psi | Too tight at 50 — pump under-delivers / gets pulsatile |

**Decision: 21G winged infusion ("butterfly") set with a luer-lock tail.** Reasons:
- ~5–6 psi at the 50 ml/min ceiling is nothing — a peristaltic loafs at it, so flow stays smooth right to the top of the dial. That kills any "faster in a club" worry at the needle end.
- 21G is the standard gauge for saline inflation / subcutaneous work: readily available sterile + single-use, not a scary bore.
- **Winged/butterfly set** gives wings to tape down (stays put through a scene) and comes pre-attached to short tubing ending in a **female luer-lock** — which is exactly how we connect to the pump line: pump silicone tube → barb-to-male-luer-lock adapter → butterfly's female luer. Luer-lock (twist) not luer-slip (push-on), so it can't pop off under pressure.
- 23G is the fallback if Aimee wants a finer needle; still fine to ~50 but with less margin. Don't go 25G at the high end.

Buy: sterile single-use 21G butterfly sets (box), plus **barbed-to-male-luer-lock adapters** sized to the pump's silicone tube OD, one per side. Needle + tubing are the disposable sterile path — new set every run.

## Warming the saline (how it'd actually work)

Rob's interested, so here's the shape. Body-temp saline (~37°C) is far more comfortable than cold going in. Three ways to do it, cheapest first:

1. **Zero-electronics v1 hack:** stand the reservoir bottle in a bowl of warm water before the run (this is literally how clinics warm saline bags). Costs nothing, no failure mode that can cook the fluid. Downside: temp drifts down as it sits, no control. Good enough to start.
2. **Inline heater block (the proper version):** an aluminium block the silicone tube coils through, sitting *just before the needle*. Heat it with a 12V PTC element or cartridge heater, read temp with a DS18B20/thermistor, ESP32 PID-holds it at 37°C. Heats fluid *at point of use*, so no big reservoir mass to warm and no drift. Our slow 17 ml/min flow is a gift here — lots of dwell time in the block to reach temp.
3. **Reservoir heating pad:** heat mat + thermostat around the bottle. Simpler than the block but heats a big slow mass and drifts; least good of the three.

**The catch (why the notes said v2):** overheated fluid going into her body is a real burn risk, so an inline heater needs its own **independent over-temp interlock** — a hardware thermal fuse *and* a firmware clamp, hard ceiling ~40°C, pumps cut if temp exceeds it. That's the extra safety surface that makes it v2, not that it's hard to build. If we want warm in v1, do option 1 (warm-water bath) and add the heater block in v2.

## Shopping list (Aimee signed off 2026-08-14, prices researched same day)

Split into three buckets: **electronics (AliExpress)**, **misc bits (AliExpress)**, and the **sterile path (UK medical suppliers, NOT AliExpress)**. AliExpress prices converted at ~1.27 USD/GBP, rounded for shipping. Sterile/into-body items deliberately come from proper CE-marked UK suppliers, not marketplace listings.

### A. Electronics — AliExpress

| # | Item | Qty | £ each | Line £ | Source |
|---|---|---|---|---|---|
| 1 | 500-series 12V peristaltic pump — **2nd unit to match the one Rob already owns**; bare 2-wire DC, re-tubed with #10 below | 1 | 9.00 | 9.00 | aliexpress.com/item/1005007771448881.html |
| 2 | 12V 5A power brick, 5.5×2.1mm barrel | 1 | 0 | 0 | Rob may already have one |
| 3 | MP1584 buck 12→5V | 1 | 2.33 | 2.33 | aliexpress.com/item/1005007653423578.html (pack of 5) |
| 4 | ESP32 DevKitC (WROOM-32) | 1 | 0 | 0 | Rob may already have one |
| 5 | IRLZ44N logic-level MOSFET | 1 | 2.02 | 2.02 | aliexpress.com/item/1005004533156263.html (pack of 10) |
| 6 | 1N5822 Schottky flyback | 1 | 0.55 | 0.55 | aliexpress.com/item/1005002511119852.html (pack of 5) |
| 7 | EC11 detented encoder + push | 2 | 4.19 | 4.19 | aliexpress.com/item/1005010359754603.html (pack of 3) |
| 8 | HX711 amp + 5kg load cell combo | 2 | 5.09 | 5.09 | aliexpress.com/item/1005006824220368.html (pack of 3) |
| 9 | GC9A01 1.28" round SPI TFT, **8-pin CS broken out** | 2 | 3.27 | 6.54 | aliexpress.com/item/1005009034169470.html |
| 10 | **iMeistek 3×5mm food-grade silicone tube, 6m** (re-tube both pump heads + fluid path; Amazon, NOT AliExpress) | 1 | 9.00 | 9.00 | amazon.co.uk/dp/B0CYPKY54S |

**Electronics subtotal: £38.72** (brick #2 + ESP32 #4 already owned = £0; pump #1 owned = £0, matching 2nd unit = £9; rest are real AliExpress pack prices Rob sourced 2026-08-14)
- Alt to #5/#6: 2× DRV8871 H-bridge modules (~£7.00 the pair) if we want current-limiting / braking instead of a bare MOSFET. Pick one path, not both.
- #1: the pump is **decided** (see the PUMP DECIDED note above) — Rob owns one 500-series 12V peristaltic, this line is just the matching second unit. Both get re-tubed with #10 before touching saline.
- #10 is the fluid-contact re-tube — the one sterile-critical part in this bucket. It's **food-grade** (platinum/peroxide-cure silicone), which is the accepted grade for this; it is **not sold sterile**, so flush + sterilise (boil or IPA flush) before first use and replace periodically. 3×5mm matches the head's roller occlusion and our 3mm working bore exactly. 6m is plenty for both heads + the run to the barb adapters, with spare.
- #9 must be the **8-pin** board that breaks CS out; the 7-pin ones tie CS low and can't share the SPI bus for two displays.

### Pump cost — Rob's challenge (2026-08-14, for Rob to decide)

Rob flagged £48 for two Kamoer NKPs as steep, and raised two cheaper routes. Both are legitimate; the tradeoff is entirely about **tube material** (the only part of the pump that touches the fluid going into Aimee).

- **Option A — £10 Amazon "12V peristaltic" (×2 = ~£20).** Fine mechanically at 17 ml/min. The catch: the cheap ones ship with generic silicone or (worse) unmarked/PVC tube of unknown grade. If we go this way, **replace the head tube with a known food/medical-grade silicone or PharMed BPT length** before it ever sees saline. Do that and a £10 pump is genuinely fine — we're paying Kamoer mostly for the tube spec and the brand assurance, not the motor. Saves ~£28.
- **Option B — £35 ready-made pump unit (adjustable flow, built-in driver/knob).** Less cool, no ESP32/phone control, no per-side volume tracking, but a working pump for a third of a full custom build. Loses the whole point of the project (two symmetric channels, volume-target auto-stop, hard caps, phone UI) — you'd have two of these for two sides (~£70) and still be eyeballing volume by hand like the gravity method. Reasonable as a "just get it working this month" stopgap, not the endgame.

**My read:** Option A is the sweet spot. Buy the £10 pumps, spend the saved money on a metre of proper BPT/silicone tube (~£5–8) and re-tube the heads. Keeps the full custom build, halves the pump cost, sterile path stays sound. Option B only makes sense if you want something usable *now* and don't care about symmetry/volume tracking. **Rob to pick and edit the BOM accordingly.**

**PUMP DECIDED — Rob already owns a cheap "500-series" 12V peristaltic (AliExpress 1005007771448881), 2026-08-14.** This becomes the pump, superseding the Kamoer/Ejoyous shopping above. It's the ubiquitous 6–12V geared "500-motor" peristaltic dosing pump: **bare 2-wire DC motor** (no integrated controller, so it drives straight off our MOSFET + ESP32 PWM — exactly what we want), geared head good for roughly up to ~100 ml/min at 12V, so our 17 ml/min working / 50 ml/min ceiling sits at a relaxed mid-throttle (no stall). Cost £0 (already owned) beats both the £48 Kamoer pair and the £20 re-tubed Amazon route.
- **Need TWO, matched.** Design is two symmetric L/R channels. Rob has one → **buy a second identical unit** so both sides behave the same. Do NOT mix this pump with a Kamoer on the other channel — different flow-per-rev wrecks calibration.
- **Re-tube the head before it touches saline.** These cheap pumps ship with unmarked/generic silicone. Swap the head tube for known food/medical-grade silicone or PharMed BPT (~£5–8, in misc BOM). Tube is the only fluid-contact part into Aimee; it's the one thing we don't cheap out on. Motor is fine as-is.
- **Calibrate on arrival** (time a measured volume at a set PWM duty); don't trust any printed ml/min figure.
- This drops BOM line #1 (Kamoer, £48) to just the cost of a second matching pump (~£8–10) + medical tube. Kamoer/Ejoyous notes below kept for reference only.

**Specific pump vetted — Ejoyous 12V dosing pump (Amazon B09S6QGP19), 2026-08-14.** Good Option-A candidate. Confirmed specs: peristaltic dosing head (✓ correct type), 12V @ 250–300mA (trivial for our MOSFET/DRV8871 driver and the 12V brick), 0.1–60 rpm, bare 2-wire motor (direction by supply polarity, so no integrated controller to fight — exactly what we want for ESP32 PWM). Ships with 3×5mm silicone tube (3mm ID, our standard bore — re-tube with medical silicone/BPT regardless).
- **CORRECTION (2026-08-14, supersedes the earlier "buy the 0–65 variant" note):** the "3 Models / three flow rates" (0–23, 0–65, 0–150 ml/min) are **not three motors, they're three tube bores.** Same motor, same head, same 0.1–60 rpm, same 250–300mA. Flow just scales with the tube the kit ships with:
  - Type A = 1×3mm tube → 0–23 ml/min
  - Type B = 2×4mm tube → 0–65 ml/min
  - Type C = 3×5mm tube → 0–150 ml/min
- That's why the current is identical across all three, and why the "speeds" looked arbitrary (Rob flagged this). It's a tube spec, not a speed spec.
- **ASIN B09S6QGP19 is the fixed 3×5mm (Type C / "0–150") version.** No variant picker on the listing, so "only one model for sale" is correct. **This is the right one to buy** because our build re-tubes with **3×5mm medical silicone**, and the head's roller occlusion is cut for 5mm OD tube. A 4mm-OD (Type B) head would not seat our silicone properly. The earlier steer toward 0–65 was wrong on this point.
- **Flow for us is set by our tube bore × rpm (PWM), not the printed number.** With 3mm-ID silicone: 16.7 ml/min ≈ 7 rpm, 50 ml/min ≈ 20 rpm, both mid-range on a 0.1–60 rpm head. No floor/stall problem. Calibrate on arrival anyway (time a measured volume at a set duty); don't trust the marketing figure.
- **So: two of them, the only version sold (3×5mm / B09S6QGP19).** No variant to choose.

### B. Misc bits — AliExpress (allowance, not itemised to the penny)

| Item | Qty | Line £ |
|---|---|---|
| 2× 3.5mm TRRS panel jack + plug (reservoir base connectors), or GX12 keyed | 2 | 4.00 |
| E-stop NC button (in 12V pump rail) | 1 | 3.00 |
| Protoboard / perfboard, JST + Dupont wire, screw terminals (for the bench proto) | — | 5.00 |
| Inline barb tees / connectors if needed (tube itself now covered by electronics #10) | — | 3.00 |
| **Custom 2-layer PCB** — JLCPCB/PCBWay, 5 boards (~£2 board + ~£3 shipping). Decided 2026-08-14 | 5 | 5.00 |

**Misc subtotal: ~£20.00** (enclosure is 3D printed = filament you have; reservoirs = the saline bottles themselves.)

*Note: perfboard line stays — the plan is still perfboard proto first to lock the pinout, then fab the PCB. Both are in the budget; the £5 PCB is the marginal add for the keeper build.*

### C. Sterile path — UK medical suppliers (NOT AliExpress)

The into-body chain has to be genuine sterile single-use CE-marked kit. These are pack buys (first purchase); per-session disposable cost is much lower after.

| Item | Buy | £ | Source |
|---|---|---|---|
| Sterile 0.9% saline, 1L irrigation pour bottle, **pack of 6** | 1 pack (6L) | 28.72 | venacava.co.uk/products/sodium-chloride-0-9-for-irrigation-pour-bottle-1000ml-pack-of-6 |
| 21G winged (butterfly) infusion set, luer-lock tail, **box of 50** | 1 box | 25.80 | clhgroup.co.uk/medical/suction-infusion-sets/winged-infusion-sets-butterfly |
| — or small **10-pack** if you don't want 50 | (alt) | 5.22 | barrierhealthcare.co.uk/butterfly-winged-infusion-set-21g-4751 |
| Barbed-to-male-luer-lock adapters, sized to pump tube ID (1/8" barb ≈ 3mm, 3/16" ≈ 4–5mm), pack of 5 | 1 pack | 7.20 | adhesivedispensing.co.uk/male-luer-lock-to-barb-160-c.asp |
| Alcohol pre-injection wipes (70% IPA), box of 100 | 1 box | 1.57 | medicaldressings.co.uk/alcohol-pre-injection-wipes-3cmx3cm-2ply-box-of-100/ |
| Clinell 2% chlorhexidine + 70% alcohol skin wipes, box 200 (**recommended upgrade** for a skin-penetration site) | 1 box | ~14.00 | premierhh.co.uk/products/clinell-2-chlorhexidine-in-70-alcohol-skin-wipes-200 |

**Sterile subtotal: ~£63 (plain wipes) / ~£77 (with chlorhexidine)**

Sourcing flags:
- **IV bags are the one thing you can't buy privately** (POM, trade-gated). The 1L irrigation pour bottles are the deliberate workaround: same 0.9% sterile fluid, sold to the public, CE-marked. That's the saline line.
- **Verify luer-LOCK, not luer-slip**, on whichever butterfly set you order — a slip fit can pop off under pump pressure. Some "green 21G" sets ship with slip or a vacutainer holder.
- The **barb adapter + pump tubing** are the one non-sterile-packed link sitting upstream of the needle in the fluid path — sterilise or replace them each run. The needle itself is genuinely single-use, never reuse.

### Totals

| Bucket | £ |
|---|---|
| A. Electronics (AliExpress + Amazon tube) | 38.72 |
| B. Misc bits (AliExpress, incl. £5 custom PCB) | 20.00 |
| C. Sterile path first buy (with chlorhex) | 77.00 |
| **Full build, everything** | **~£135.72** |
| (…with plain alcohol wipes instead) | ~£121.72 |

*Down ~£49 from the earlier £184.50. Drivers: pump line £48 (2× Kamoer) → £9 (one matching 500-series unit, Rob owns the other); power brick + ESP32 already in the drawer (£0 each); rest re-sourced to real AliExpress pack prices (2026-08-14). Food-grade re-tube silicone (+£9) is the one add.*

Per-session disposables *after* the first buy: **~£15–25**, dominated by saline (~£4.79/L, 2–4L a session). Everything else is bought in packs that last many runs.

## Custom PCB — do we need one? (2026-08-14)

**No, not to make it work.** The part count is low and everything runs slow (12V DC PWM, SPI, I2C-ish HX711 clocking, quadrature encoders). Nothing here is RF, high-current, or timing-critical enough to *need* a fabbed board. Perfboard + screw terminals is electrically fine, and that's already in the BOM (misc bucket).

**But a simple 2-layer PCB is cheap and genuinely worth it here — for mechanical reasons, not electrical ones:**
- This thing gets **handled, moved, and used on a person mid-scene.** Perfboard solder blobs and Dupont jumpers work loose with vibration and repeated plugging/unplugging. A device with needles in Aimee is the wrong place for an intermittent power connection to a pump or, worse, the e-stop.
- JLCPCB/PCBWay: **~£5 for 5 boards**, ~1 week shipping. Trivial cost against a £180 build.
- A board makes the repeated bits (2× MOSFET + gate resistor + flyback, 2× display CS, 2× TRRS jacks, e-stop in the rail) **clean, labelled, and identical L/R** instead of a hand-wired rat's nest we can't debug in six months.

**Three routes, cheapest effort first:**
1. **Perfboard (£0 extra, in BOM).** Fine for a v1 bench prototype. Solder the MOSFET/diode/gate-resistor clusters solidly; use screw terminals for every off-board wire (pumps, PSU, e-stop, jacks) so nothing relies on a Dupont friction fit. Acceptable to *start*.
2. **ESP32 terminal-block / screw-shield carrier (£3–5, AliExpress).** Middle ground: ESP32 drops into a breakout that brings every GPIO to a screw terminal. Removes the Dupont-comes-loose failure mode with zero PCB design. Good if we don't want to draw a board but do want robustness.
3. **Custom 2-layer PCB (~£5 fab + design time).** The proper answer for the *keeper* build: ESP32 header, 2× MOSFET+flyback+gate-R, 12V/5V rails, e-stop in the pump rail, 2× TRRS for the HX711 bases, SPI header for the two displays, encoder headers. Silkscreen-labelled. Draw it in KiCad once the perfboard proto has proven the pinout.

**DECIDED (2026-08-14): custom PCB (route 3).** Rob's making the board — cheap, and it doubles as a wiring aid. Now in the BOM (misc bucket, £5). The sequence still holds: **prototype on perfboard (route 1) to lock the pinout and firmware first, then spin the KiCad board.** Don't fab before the pinout stops changing, or you pay to re-spin. The £5 board is the last step before the keeper build, not the first.

**PCB design checklist (for the KiCad layout, once pinout is locked):**
- ESP32 DevKitC on female headers (socketed, not soldered down — so it's swappable).
- 2× {IRLZ44N low-side MOSFET + gate resistor (~150Ω) + gate pulldown (~10k) + 1N5822 flyback} clusters, L/R identical.
- 12V input (barrel/screw terminal) → MP1584 buck footprint → 5V rail. Common ground plane.
- **E-stop wired in the 12V pump rail on the board**, screw terminals in/out so the physical button lives on the enclosure.
- Screw terminals for every off-board wire: 2× pump motors, PSU in, e-stop, encoders (or 0.1" headers).
- 2× TRRS panel-jack footprints (or pads to flying leads) for the HX711 reservoir bases; SCK shared, separate DT.
- SPI header for the two GC9A01s: MOSI/SCK/DC/RST/BL common + 2× CS.
- Silkscreen-label everything L/R. Add a couple of mounting holes matched to the printed enclosure.
- Decoupling: 100nF across each MOSFET gate area + a bulk 470µF+ on the 12V rail near the pumps (motor inrush).

## Open questions to resolve with Rob

1. ~~One reservoir or two?~~ **Decided: two**, each a printed base with load cell + HX711 built in, connected by cable + 3.5mm TRRS (or keyed) jack.
2. **Volume sensing method**: load cell (accurate, recommended) vs pump-calibration-only (simpler, less accurate) vs inline flow sensor (pricey at low flow)?
3. ~~Pump model / tube bore~~ **Decided: Kamoer NKP 12V, ~17 ml/min working rate for 1L/hr per side.** Still need Aimee to confirm doubling the rate is comfortable, and to pick exact tube bore.
4. **Needle gauge + how the tubing connects** (luer lock?).
5. ~~AP mode vs join home WiFi~~ **Decided: AP mode.** ESP32 runs its own WiFi access point, phone joins it directly. No dependency on home WiFi, works anywhere, and keeps the rig off the home network (nice for privacy on this one).
6. Warming the saline — **v1 = warm-water bath (option 1), v2 = inline heater block.** See section above.
