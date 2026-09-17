# House

Durable facts about the property, gathered during the heat pump research (Sep 2026).

## Heating & hot water
- **Currently heating oil**, no mains gas. No hot water cylinder at all (combi-style setup) — any heat pump/cylinder quote needs a full new cylinder, no "keep existing" discount applies.
- Boiler sits inside the **garage**, which juts ~1m forward of the house at the front.
- Has **solar PV** installed.
- Village is in an **AONB**, not a conservation area, not listed. Confirmed via GPDO Class G that AONB carries no extra permitted-development restriction for ground-mounted heat pump units (only conservation areas/World Heritage Sites do) — front garden by the garage is PD-legal, pending the surveyor's noise calc and no Article 4 direction on the village.

## Energy monitoring & solar (17 Sep 2026)
- **Shelly EM** on the incoming supply at `192.168.1.100` (UniFi name "Shelly Electricity Monitor"), feeding HA as `sensor.shellyem_34945470ed50_*`.
- **Channel 1 = grid.** Lifetime at 17 Sep 2026: 18,339 kWh imported, 8,049 kWh exported. The export figure proves the PV exports plenty (battery-relevant).
- **Channel 2 = solar feed, clamp is DEAD.** 14,692 kWh lifetime vs the generation meter's 15,099.86 kWh (close match = it clamps the PV circuit), but it read 0.00 W at 13:10 BST 17 Sep while the inverter display showed ~660 W and the grid channel showed 75 W export. Clamp has fallen off, failed, or been disconnected; ~408 kWh drift vs the gen meter suggests it died a while back (or the Shelly was fitted after the PV went live). Physical check needed. Shelly firmware also ancient (v1.10.4, v1.14.0 pending).
- **Inverter: Solis S6-GR1P3.6K** (side label photo 17 Sep). Single-phase string inverter, 3.6 kW rated output (16 A), dual MPPT (2x14 A input, 90-520 V), non-isolated, IP66, S/N 1802020226190414. Not a hybrid (hybrids are the EH1P line), so a battery means **AC-coupled** (Powerwall / GivEnergy AC / Sunsynk retrofit etc.) or an inverter swap to hybrid. AC-coupled leaves the PV side untouched. Solis WiFi datalogger dongle fitted underneath. DC rotary isolator (IS4P20) + small PV consumer unit alongside.
- **DNO note:** 3.6 kW is the classic G98 connect-and-notify size (16 A/phase limit). Any AC-coupled battery inverter adds generation capacity on top, taking the property over the G98 limit, so the install needs a **G99 application to the DNO** (installer handles it, but it adds lead time and is worth asking quotes about up front). Array is probably ~4 kWp given the dual-MPPT 3.6 kW pairing; MCS cert will confirm.
- **Generation meter:** Emlite ECA2, serial EML2231754961, 15,099.86 kWh at 17 Sep 2026. Serial prefix "22" suggests 2022 manufacture, so install likely 2022/23 — post-FIT (closed Mar 2019), so **SEG or nothing**, which simplifies a battery (no FIT deeming to protect).
- **Electrical layout (photo 17 Sep):** everything on one garage wall: main consumer unit (older cream/yellowed plastic split-load board, main switch + RCD-protected and non-RCD sections, "Solar PV System" warning label fitted), Emlite gen meter below it, IMO DC isolator + red rotary AC isolator, then the Solis inverter. Washing machine/dryer on the same wall. This is close to ideal for an AC-coupled battery: short cable runs, garage location (PAS 63100 prefers non-habitable spaces), and installers typically feed the battery inverter from Henley blocks + a small dedicated CU, so the old plastic board being full isn't a blocker (though an installer may push a board upgrade; plastic CU is legal to keep, new circuits just need RCD protection). Inverter OPERATION LED green in the photo = generating fine, reconfirming the Shelly ch2 clamp is dead, not the PV.
- **Still needed from Rob:** array kWp (MCS cert), current tariff + whether SEG is actually registered. Then sizing/payback maths. (Inverter model + consumer unit both captured 17 Sep.)

## Heat pump decision (open, as of 10 Sep 2026)
- Octopus quote: **£2,749 fully installed** after £9,000 BUS grant, includes new cylinder, assumes existing radiators kept (extras £250/radiator fitted). Survey lead time 2-6 months.
- Value case: UK data puts a heat-pump premium at ~1.7-3% of house value, but the bigger driver is removing the oil tank — oil-heated homes take ~40% longer to sell, and losing it should also lift the EPC band.
- Solar match: mismatch is seasonal (panels weakest exactly when heating demand peaks, Dec-Feb), but strong for hot water — heating water via the heat pump on solar surplus gets ~3x the yield of an immersion diverter (COP effect), covering most of the household's hot water roughly March-October.
- Running cost estimate: ~£1,100-1,300/yr on Octopus Cosy to hold 21°C (4-bed, 4 occupants), vs ~£2,000/yr for the same heat via oil at Sep 2026 prices (~94p/L) — heat pump ~£700-900/yr cheaper before solar.
- Sizing ask for the survey: state 4 occupants + daily showers explicitly so they spec a 200-250L cylinder (not 200L default); MCS requires the installer to agree reheat expectations with the customer.
- Full research/reasoning trail (microbore pipework, siting, value impact, solar match) logged in `Daily/2026-09-09.md` and `Daily/2026-09-10.md`.
- Rob was leaning positive (off-oil economics, solar/cylinder synergy, PD-legal siting) but hadn't decided whether to book the survey as of 10 Sep. Follow up on this.
