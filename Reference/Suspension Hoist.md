# Suspension Hoist

Rob and Aimee use a PA-series 300kg electric wire rope hoist (TEENO-clone, [Amazon link](https://www.amazon.co.uk/dp/B0CNGVS8B5?th=1)) for suspension play.

## Fault, reported 18 Sept 2026
Jams intermittently: motor makes noise but spool doesn't move. Manual nudge on the spool sometimes frees it, works for a while, then randomly jams again (often the next day). Diagnosis pending Rob confirming whether the motor hums (no spin) or audibly spins with no spool movement.

- **Hum, no spin** (most likely given the pattern): failing start capacitor (CBB60-type, ~£8, under side cover) or a sticking motor brake (spring brake gummed/corroded, frees with a manual turn).
- **Spins but spool doesn't move**: stripped gear or sheared drive key, hoist is scrap.

## Safety rule (non-negotiable)
Nobody goes in the air on this hoist until it starts cleanly from cold, consistently, and the fault is actually fixed, not just currently free. Don't hold the button while it hums, it cooks the motor windings. Keep a rescue plan for "jammed with someone up" regardless, since it's shown it can do that mid-scene.

## Open
Waiting on Rob to open it up and report hum vs spin (and ideally a photo of the capacitor label) before a fix is confirmed.

**18 Sept 2026:** fix on hold for a few days, the hoist is currently doing duty tensioning the freshly dyed rope while it dries. Diagnosis resumes once the rope comes off it. Safety rule above still stands in the meantime.

**15 Nov 2026:** hoist on the bench downstairs, diagnosis resumed. Bench checklist sent: rule out extension lead first (wall socket direct), reproduce cold with short taps up AND down, with and without ~20kg; then unplugged inspection of capacitor (bulge/leak/µF test, ±5% of label), all spade connections, the **pendant switch contacts** (on PA hoists the pendant switches motor current and the capacitor directly, worn contacts give exactly a hum-no-start, intermittent), and the brake end (rust/glazing/oil, look don't dismantle the spring). Verdict rule: cap or pendant/connection fault = cheap fix + 20 clean cold starts before anyone flies; brake or gearbox fault = retire it.

**15 Nov 2026 ~14:35: FOUND.** Rob traced it to a loose **yellow wire**; reseating it fixed the hum-no-start. Connection fault, so the cheap-fix branch: still owed 20 clean cold starts (up and down, some under load) before anyone goes up on it. If it recurs, crimp a fresh spade rather than just pushing the old one back on.

**15 Nov 2026 ~16:30: rewiring the crimps.** Rob is re-terminating rather than reseating. Two terminal types in there: insulated female spade (6.3mm Faston, yellow wire) and an uninsulated fork (black wire, tired crimp with strands flaring). Shopping list given: ratchet crimper for insulated terminals (red/blue/yellow dies), red (0.5 to 1.5mm²) insulated 6.3mm female spades, preferably fully-insulated nylon; red insulated forks sized to the stud (measure the screw, M3/M4/M5); proper wire strippers. Tug-test every crimp. Then the 20 clean cold starts still apply.
