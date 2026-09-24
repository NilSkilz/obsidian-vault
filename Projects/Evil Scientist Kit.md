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

## Scene concept: "The Programme" (MK Ultra fear play rig, idea 24 Sep 2026)

Sparked by the MK Ultra scene in Manhunt: Unabomber (flashing lights, oscilloscope traces, dials, clinical menace). Concept: an interrogation/conditioning-lab scene where the *machine* is the top's proxy. The fear engine is that a machine can't be read, charmed or negotiated with the way a human top can; the bottom watches dials move and a trace spike and knows something is coming but not what or when.

**Why it works as theatre:** almost none of it has to be real. The scope trace, the dial panel, the clicking relays are set dressing; the only live output is whatever sensation the top actually delivers by hand (or a TENS unit later). The bottom's brain does the heavy lifting: visible trace ramps up, relay clunks, *then* the sensation lands. Classic anticipation conditioning, and after two or three honest pairings you can run a dry ramp and get a full flinch off nothing.

**Build sketch (mostly owned or cheap):**
- Old analogue oscilloscope, eBay £30-60, fed by a signal generator or an ESP32 DAC so the trace "responds" to dial turns. Even a CRT telly with a scope screensaver works at a pinch.
- Panel of chunky toggle switches, rotary dials and indicator lamps on a plywood face. ESP32 reads them and drives the scope trace + lamp patterns, so the panel *feels* live. Same MQTT control plane as the rest of the kit.
- Mechanical relays purely for the clunk. Sound is half the scene: add a low drone or tape-hiss loop.
- Lighting: a single flickering desk lamp or slow red pulse beats a strobe (see safety).
- Sensation output: manual at first (ice, wartenberg wheel, scratches, drips timed to the trace). EM43 TENS integration stays parked with the rest of the remote e-stim work; fear play plus electro plus new interlocks is too many new variables at once.

**Safety notes, non-negotiable:**
- Fear play is psychologically heavy: negotiate the deception itself ("I consent to not knowing what the machine does") and plan double the normal aftercare. Debrief the tricks afterwards; showing the wizard behind the curtain is part of landing it well.
- A bottom deep in fear may not find words: agree a non-verbal out (dropped object, hand tap pattern) alongside traffic lights.
- No actual strobing without an explicit photosensitivity check; slow pulses and flicker get the aesthetic without the seizure risk.
- Below-waist e-stim rule stands whenever the TENS eventually joins.

**Casting note:** this is NOT a Fen scene. Her sheet says visual input overwhelms her and blindfolds are what let her sink in; a flashing-light panel is her profile inverted. This is a build for a partner who feeds on dread and spectacle. Fits the original evil-scientist framing this file was born from.

## Deliberately parked

Remote-hacking the EM43 TENS ([[E-stim - EM43 sensation map + TENS 08 recipe]]) — needs the proper soldering iron anyway, and remote e-stim wants real interlocks. Pinecil-era project, not this batch.
