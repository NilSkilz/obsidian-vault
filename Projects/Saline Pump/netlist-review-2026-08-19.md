# Saline Pump — Netlist Review (2026-08-19)

Deep review of Rob's exported netlist (`.enet`, EasyEDA/JLCEDA v2.0.0) against the locked v1 pinout in `hardware.md`. Traced all 26 nets, every pin, both power domains. Context: last export missed GND to the buck; Rob asked for a thorough pass so nothing else slips.

## Verdict
GND-to-buck is **fixed**. Topology is sound and matches the documented v1 pinout. Two things must be fixed before fab (one serious), plus a design-intent gap and a part-number check.

## Must fix before fab

### 1. R2 & R3 value is wrong in the file — says 10kΩ, must be 150Ω (SERIOUS) — RESOLVED (2026-08-20 redraw)
R2 (gge7_4) and R3 (gge7_3) are the **gate series resistors** (D26→Q2 gate, D25→Q1 gate). Their schematic `Name` reads "150Ω" but their `Value` property reads **"10kΩ"**. R1/R4 (the 10k gate pulldowns) are correctly 10k.
- If the BOM/assembly pulls the `Value` field, both series resistors become 10k. With the 10k gate pulldown that's a **10k/10k divider**: gate sees only ~1.65V from a 3.3V GPIO, **below the IRLZ44N Vgs(th) (2.5V typ)**. MOSFETs never fully turn on → linear-region heating, pumps barely run.
- Fix: set R2 and R3 `Value` to **150Ω** so it matches the `Name` and the checklist ("150Ω series + 10k pulldown").

### 2. No bulk cap on the pump rail — RESOLVED (2026-08-20 redraw)
The netlist has the flyback diodes (good) but **no bulk electrolytic** on the pump feed and no input cap. `hardware.md` PCB checklist explicitly calls for "bulk 470µF+ on the 12V rail near the pumps (motor inrush)." Absent here.
- Motor inrush/stall transients will sag the rail; with the buck tapping the same input, that risks browning out the ESP32.
- Fix: add **470µF+ across $1N41→GND** near the pumps, and a small input cap near the MP1584 IN+ ($1N37). (The MP1584 module and ESP32 devkit carry their own local caps, so the ESP rail itself is OK — this is specifically the motor-transient bulk.)

## Design-intent gap

### 3. ESTOP_SENSE (D16) not wired — RESOLVED: wire it (Rob 2026-08-20)
The stated goal is "ESP32 stays alive to show STOPPED when pumps are killed." But nothing senses the pump rail, so **firmware can't tell the e-stop was hit** — it'll keep showing "running" while pumps are dead. **Decision: add the sense.** Wire in EasyEDA:
- **R5 = 100k** from +12V_SW ($1N41) to a new node (call it ESTOP_SENSE).
- **R6 = 33k** from ESTOP_SENSE to GND.
- **C = 100nF** from ESTOP_SENSE to GND (noise immunity).
- Net ESTOP_SENSE → ESP32 **GPIO16 (D16)**.
- Math: rail live → 12 × 33/133 = **2.98V** (clean HIGH, under 3.3V); e-stop open → rail dead → 33k pulls node to **0V** (LOW). Firmware: HIGH = running, LOW = STOPPED. Now locked as v1 in `hardware.md`.

### 4. Reservoir connector part vs footprint
gge20/gge21 (Reservoir1/2) have device name **"HDR2.54-LI-2x4P" (8-pin)** but `FootprintName` is **4P** and only 4 pins are used (3V3/SCK/DT/GND — correct for the HX711 digital side). Verify the ordered part (C9900020145) is physically a **4-pin** header, or it won't seat on the 4-pin footprint.

## Confirmed correct (incl. the prior miss)
- **GND is one clean common net**: MP1584 IN- (pin3) + OUT- (pin6), ESP32 GND, both MOSFET sources, CN1, resistors, all connectors. The previous buck-GND miss is fixed.
- **Both flyback diodes correct**: U1 across Pump1 (A=$1N10 drain, K=$1N41 +rail), U2 across Pump2 (A=$1N19, K=$1N41). Cathode to +supply = right.
- **Low-side MOSFET drive**: Q1 gate←D25 via 150Ω(R3)+10k pulldown(R4); Q2 gate←D26 via 150Ω(R2)+10k pulldown(R1). Textbook.
- **E-stop ("On/Off" connector) is wired exactly as intended**: bridges raw +12V ($1N37) to the switched pump rail ($1N41); the buck taps raw $1N37 *before* the switch, so the ESP32 stays powered when pumps are cut. Good safety design.
- **Peripherals match the locked pinout**: encoders on 3V3, CLK/DT/SW = 32/33/27 (L) and 14/13/22 (R); displays SPI-shared (MOSI23/SCK18/DC19/RES15) with per-screen CS (L=5, R=4), BLK+VCC on 3V3; HX711 bases share SCK=21, DT_L=34, DT_R=35, powered 3V3 (so DT is safe into input-only pins).
- **Strapping pins clear**: GPIO0/2/12 and serial 1/3 unused; GPIO15 (display RES) is the safe strapping pin, idles high. No boot conflicts.

## Build-time notes (not netlist errors)
- **Trim the MP1584 to 5.0V BEFORE connecting the ESP32 VIN.** Adjustable bucks ship untrimmed; feeding a wrong voltage into VIN can kill the devkit regulator.
- Silkscreen: label the "On/Off" connector as **E-STOP (pump kill)** so it isn't mistaken for master power (it doesn't cut the ESP32, by design).
- Layout: keep the pump-current ground return away from the ESP32/HX711 ground (star-ground) so motor noise doesn't wreck the load-cell readings.

## 2026-08-20 redraw re-review

Rob re-exported the netlist after moving pins around for easier PCB routing. Re-traced the whole thing. Net numbers reshuffled (switched pump rail is now **$1N49**, was $1N41; pump-1 drain **$1N50**, was $1N10). Topology unchanged and still sound.

**Resolved since the 08-19 pass:**
- **R2/R3 now 150Ω** (Value field) — the serious one, fixed.
- **Bulk cap present:** C1 across the switched rail ($1N49→GND) is part **TLR471M1EG13RT9 = 470µF / 25V** electrolytic. (Its Value *text* still shows the `={Value}` placeholder, but the actual part is correct.)
- **Bonus:** C2 + U4 = **100nF / 50V film caps** (FA28X8R1H104K) across each pump as motor snubbers. Not asked for, sensible add.

**Pins moved (docs updated in `hardware.md`):**
| Function | Old | New |
|---|---|---|
| Pump L gate | 25 | **14** |
| Pump R gate | 26 | **13** |
| Enc L CLK/DT/SW | 32/33/27 | **27/26/25** |
| Enc R CLK/DT/SW | 14/13/22 | **34/35/32** |
| HX711 SCK | 21 | **33** |
| HX711 DT_L / DT_R | 34 / 35 | **36 (VP) / 39 (VN)** |
| Displays | 23/18/19/15, CS 5/4 | **unchanged** |

**New must-look-at before fab (from the move):**
1. **Pump L gate is on GPIO14, which outputs a PWM burst at boot** → Pump L can twitch briefly at every power-on/reset. Safety-relevant on a needle device. Fix: swap Pump L gate to **27** (boot-clean, adjacent to 14 on the header) and put the freed encoder line on 14. Pump R (13) is fine.
2. **Enc R lands on input-only 34/35/32.** 34/35 have no internal pull-up — OK for CLK/DT (KY-040 has onboard pull-ups) but **SW must go to 32**, not 34/35, or it floats. Control2 is a bare 5-pin header, so this is a wiring instruction, not a schematic error — just get SW onto the pin routed to 32.
3. **ESTOP_SENSE still not drawn.** GPIO16 (the RX2-labelled pin) is present and free; the 100k/33k/100nF divider off $1N49 still needs adding in EasyEDA. Design is locked in `hardware.md`, it just isn't in the netlist yet.
4. **Dangling net:** $1N28 hangs off ESP32 D22 with nothing on the other end (vestige of the old Enc R SW on 22). Delete it to keep the ERC clean.
5. **Cosmetic:** set the Value text on C1/C2/U4 so the BOM and silk read 470µF / 100nF instead of `={Value}`.

**Still open from 08-19:** item 4 (Reservoir device is "HDR2.54-LI-2x4P" 8-pin name on a 4-pin footprint — verify the ordered part is physically 4-pin). Unchanged in this redraw.
