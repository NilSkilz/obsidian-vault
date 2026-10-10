# Little Yikes

**Status:** IDEA, parked 10 Oct 2026. Rob: "will come back to it later."

## The idea

Inspired by a r/BdsmDIY post (Oct 2026): **"My First Cattle Prod" by Little Yikes Toys**. A scary impact/shock toy styled like a 90s Little Tikes / Fisher-Price kids' toy, for maximum juxtaposition. The original was 3D printed, sanded to 2000 grit, high-gloss spray painted, with a printed label. Inside: an 18650 cell, a £5 "400kV" high-voltage module, a 12mm metal momentary button and two 2mm steel alignment pins as contacts. Half the effect is the sound: a loud, terrifying stun-gun crackle before it ever touches skin.

## LEGAL BLOCKER: don't build the original in the UK

Found 10 Oct 2026 (I missed it on the first pass). In England & Wales **a stun gun is a prohibited weapon** under s.5(1)(b) Firearms Act 1968: anything that discharges electricity counts (*Flack v Baldry* 1988; "it's non-lethal" was rejected in *R v Brereton* 2012). Up to 10 years. Worse, a stun gun **disguised as another object** is s.5(1A)(a), which carries a **mandatory minimum of 5 years**. A working HV discharge device styled as a children's toy is very close to the textbook disguised-weapon case. The parts are legal to buy separately; assembled into a handheld shock device is the problem. A BDSM purpose isn't a defence. Source: HJA Solicitors' stun-gun law piece (hja.net).

So the Little Yikes *styling* is the keeper, and the business end has to be something that isn't a weapon.

## Legal versions (pick one when we come back to it)

**A. "My First Zapper": Little Yikes shell around the e-stim kit we already have (recommended).** The printed toy body holds a 2-pin contact head wired to the Boots EM43 TENS (see `reference_estim_kit` memory and the e-stim notes). Real bite, from a medical device, nothing weapon-like. Add the menace back with **sound**: the button plays a stun-gun crackle sample through a small speaker (DFPlayer Mini + speaker), so you get the terror without the HV. Optional red LED that flashes with it. Same e-stim safety rule: below the waist only.

**B. "My First Violet Wand": Little Yikes sleeve around a cordless violet wand.** Violet wands are sold openly as erotic toys in the UK and you get real crackle and visible sparks. Cordless rechargeable models exist (XR Master Series Electra, Shockgasm 2.0 Unplugged). Costs more, and you're dressing up a bought product rather than building one.

## BOM: version A (My First Zapper)

Prices checked 10 Oct 2026 where marked ✓, the rest are typical UK prices, re-check before ordering.

| Part | Qty | Approx £ | Notes |
|---|---|---|---|
| PLA filament, bright primary colours | 1-2 × 1kg | £21 each ✓ (Bambu PLA Basic) | May already have suitable colours |
| Filler primer spray | 1 | £8-10 | Hides layer lines before sanding |
| Rust-Oleum Painter's Touch gloss, 400ml | 2-3 colours | £5.75-14 each ✓ | Red/yellow/blue = the Little Tikes palette |
| Gloss clear coat | 1 | £8-10 | Protects the label |
| Wet-and-dry paper, 240-2000 grit pack | 1 | £6-8 | |
| DFPlayer Mini MP3 module + microSD | 1 | £4-6 | Button triggers the track directly, no microcontroller needed |
| Small 3W 40mm speaker | 1 | £3-4 | |
| 18650 cell, protected | 1 | £6-9 | Powers the sound board only |
| TP4056 USB-C charge board with protection | 1 (packs of 5) | £5/pack | |
| Slide switch (arming) | 1 | £1-2 | |
| 12mm metal momentary button | 1 | £3-4 | Rob may have one |
| 2mm stainless pins or 4mm snap studs for contacts | 2 | £3-5 | Plus 2mm-pin or snap lead to the EM43 |
| Red LED + resistor | 1 | pennies | |
| Wire, heat-shrink, sticker paper for the label | | £5 | Probably in stock |

**Rough total: £60-90**, less whatever's already in the parts bin. The EM43 TENS is already owned. The big costs are paint and filament, and the electronics are about £20.

## BOM: version B (violet wand)

- Cordless violet wand: roughly £60-120 (not price-checked; corded kits ~£50-90).
- Filament and paint for the shell: ~£35-50 (same lines as above).
- **Total ~£100-170.**

## For reference: the original build

HV module (~$5-8), 18650 + holder, 12mm button, 2mm steel pins, printed shell. About £15 in electronics. **Not to be built in the UK**, see the legal blocker above.

## Non-negotiables whichever version

- **Lives locked away.** A convincing kids'-toy-styled kink device in a house with Dexter (15) and Logan (12) is the exact thing that gets picked up off a shelf. Locked box, not "tucked away". The kids don't know about any of this and that doesn't change.
- E-stim rule: nothing above the waist, never across the chest, not on anyone with a heart condition or pacemaker.
- Arming switch so it can't go off in a bag.
- Next step when Rob picks it up: model the handle in build123d (`~/.venvs/cad`), chunky enough for the cell, charge board, sound board and arming slide.
