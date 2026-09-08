# Evil Scientist Kit

**Status:** idea, noted 7 Sept 2026. Cheap/no-solder builds queued while the soldering iron (saline pump) and rope dye tests are on hold. Not greenlit individually, just the standing shortlist.

## Why

[[Mary]]'s stated ideal top is "evil scientist... gadgets, toys, machines" (her own Fet profile). Rob wanted low-cost builds, ideally from parts already owned, that fit that framing and can be remote-controlled.

## Shortlist (priority order, 7 Sept 2026)

1. **Dinner vibe.** ESP32 + MOSFET + coin vibe motor (or gutted toy/toothbrush) + USB power bank. Joins Mary's phone hotspot, driven from a web page over MQTT. Solderless (headers/screw terminals/Dupont), under a fiver. Directly matches her bucket-list line "a romantic dinner with secret vibrator." Works once she's back in Oxford in October.
2. **Remote keyholding box.** 3D-printed box + ESP32 + small servo latch (~£3 if not already owned). Only Rob's phone opens it.
3. **Leather chastity shield.** Riverqueer-style design: leather wings + rivets, metal bars forming the arch, gap between bars ~10-13mm (blocks fingers, allows tongue). Rob has **50mm saddle clamps, full width** (confirmed 7 Sept 2026) — flanges eat ~10-12mm each side, leaving an arch span of ~25-30mm, comfortably inside the working range. Verdict: not too wide, good to build. Watch-outs: saddle clamps are pipework hardware, check for press burrs and prefer stainless over zinc/galvanised (plating doesn't hold up to fluids); flange spacing at rivet time sets the finger-block gap, lay out on a cardboard mock-up first. Zero-cost fit test before cutting: cardboard mock-up at full width, held in place, legs together, sit and walk — if it digs at the thigh creases it's too wide for that body. Fit test should be Mary's, not a guess, since vulva-to-thigh geometry varies more than hardware.

## Shared backbone

All three (plus [[Fuck-io]] eventually) want the same control plane: MQTT broker + authed web panel + hard local stop. Pure software, buildable any time at £0, not blocked on any hardware arrival.

## Deliberately parked

Remote-hacking the EM43 TENS ([[E-stim - EM43 sensation map + TENS 08 recipe]]) — needs the proper soldering iron anyway, and remote e-stim wants real interlocks. Pinecil-era project, not this batch.
