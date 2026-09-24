# The Programme (MK Ultra fear play rig)

**Status:** concept, 24 Sep 2026. Intended bottom: **Aimee**. Moved out of `Projects/Evil Scientist Kit.md` the moment that became true, because her sessions read that file and a fear play scene loses everything if she can read the script. This file never reaches her sessions.

**Origin:** the MK Ultra scene in Manhunt: Unabomber (flashing lights, scope traces, dials, clinical menace). Concept: an interrogation/conditioning-lab scene where the *machine* is the top's proxy. The fear engine is that a machine can't be read, charmed or negotiated with; the bottom watches dials move and a trace spike and knows something is coming but not what or when.

## The polygraph pivot (24 Sep, Rob's idea)

Rob's refinement: head restraint with electric wires coming off it, feeding a polygraph-style tracing machine. This is *better* than the scope version for one big reason: **the trace can be partly real.**

- **GSR (galvanic skin response):** two finger contacts (velcro straps + coins or blank snap electrodes), a voltage divider, an ESP32 ADC pin. Microamp sensing currents, completely safe, and it genuinely reads skin conductance, which spikes with stress and arousal. The pen jumps because *she* reacted.
- **Pulse:** a PPG ear/finger clip sensor, ~£3, same ESP32.
- Result: the machine isn't bluffing. "It can tell" is literally true. That's scarier than any fake trace, and it's also *fairer*: less of the scene rests on deception because the core claim is honest.

## Build sketch

**The tracer (pick one):**
1. **Thermal receipt printer** (TTL serial type, £15-25, ESP32-driven): continuous slow feed printing live traces + timestamped "readings". Cheapest, and the theatre of tearing off a strip, reading it silently, and writing something on a clipboard is worth the whole build.
2. **Pen chart recorder** (most authentic): servo waggling a fibre-tip pen over paper pulled by a stepper + rollers (till-roll paper). More build effort, but the servo chatter is free menace and it looks exactly like the films.
3. Scope/CRT trace as per the original sketch, still valid as a second display.

**The head end:**
- Swim cap or leather head harness with snap studs, EEG-style dummy electrode discs, curly wires running to the panel. **The head-side wires are 100% theatrical: they terminate in a dummy connector that physically cannot mate with any powered output.** Nothing electrically live above the waist, ever (standing e-stim rule). The only real sensors are the GSR finger strap and pulse clip, both passive.
- Restraint: padded headband/halo on a high-backed chair, velcro or side-release buckles, **releasable in under 2 seconds**. Nothing across or near the throat. Nothing rigid that loads the neck if she slumps or drops. Hands stay free enough to use the non-verbal out.

**More real instrumentation (Rob's additions, 24 Sep evening):**
- **Blood pressure cuff:** buy a cheap off-the-shelf wrist or arm monitor (£15-25), don't build one. It's already a certified medical device, the readings are real, and the dread beat is free: the machine "decides" to take a reading and the cuff tightens on its own. A basic model can be ESP32-triggered by wiring a relay/optocoupler across its start button; the cuff and pump stay stock and untouched. Rules: standard cuff use only, never left inflated, never on a limb with circulation play happening.

### Cuff automation (specced 24 Sep evening)

Two tiers.

**Tier 1, button hack (do this first):** optocoupler (PC817) across the monitor's start button, driven from an ESP32 GPIO over the usual MQTT backbone. One solder joint each side of the button's PCB pads, everything medical stays stock. The monitor runs its own certified inflate/measure/deflate cycle, so there is nothing to get wrong pneumatically. Bonus theatre: most cheap ones beep before inflating, which becomes a conditioned dread cue for free. Limit: no control over timing or hold, it does its ~30s cycle and dumps.

**Tier 2, custom pneumatic loop (the creepy one):** keep only the cuff itself, replace the guts.

- Parts: 6V diaphragm micro air pump (the same type inside BP monitors, £4-6), **normally-open** solenoid dump valve (£5-8), MPX5050GP pressure sensor (0-50 kPa, ~375 mmHg range, £6) teed into the line, MOSFET drivers, ESP32. All standard fittings on 4mm silicone air line.
- What it buys: slow-creep inflation (a cuff that tightens over 60 seconds instead of 10 is far worse in the good way), hold-at-pressure, and a real physiological channel: hold ~40 mmHg and the pressure sensor picks up the pulse as oscillations, so the chart gets a live heart-rate trace from the cuff itself. Arousal channel and cuff share one sensor design (same MPX family as the probe line).
- **Hard safety interlocks, all mandatory:** dump valve is normally open, so any power loss or crash = instant deflate. Firmware pressure ceiling 160 mmHg, no override path in code. Hardware backstop: mechanical relief valve or a fixed bleed. Watchdog auto-dump on any hold longer than 90 seconds, and a scene rule of at least a couple of minutes recovery between cycles. Upper arm or wrist only, over clothing or bare, never anywhere else, and the existing rule stands: never on a limb with circulation play happening. Prolonged or repeated inflation risks nerve compression (radial/ulnar), which is why the 90s watchdog is not negotiable.
- Physical out: she can rip the cuff's velcro herself even restrained at the head, so cuff arm stays free enough to reach it.

Tier 1 ships the scene. Tier 2 is the upgrade once the rest of the panel exists.
- **"Arousal probe":** an insertable inflatable, and this one converges with [[Fuck-io]]'s orgasm-detect plug idea. **Never DIY the insertable itself**: commercial body-safe inflatable plug, flared base, stock hand bulb. The clever bit goes in the AIR LINE: a T-fitting with a small pressure sensor (BMP-type or an MPX air pressure sensor, £3-8) teed in, reading squeeze. Pelvic floor contractions show up as clean pressure pulses, so the trace channel labelled AROUSAL is genuinely live, and orgasm is unmistakable on the chart. Sensor never touches the body, it only reads air. Hard rules: inflation stays on the hand bulb in the top's hand, no motorised or compressor inflation ever, bleed valve in the circuit, inflate to comfort not to spec.

**Panel + control plane:** plywood face, chunky toggles, rotary dials, indicator lamps, mechanical relays purely for the clunk. ESP32 reads the controls and drives trace/lamps/printer, same MQTT backbone as the rest of the kit. Sound is half the scene: low drone or tape hiss under the relay clicks.

**Sensation output:** manual, timed to the trace (ice, wartenberg, drips, scratches). Two or three honest pairings of ramp-then-sensation, and a dry ramp gets a full flinch off nothing. TENS integration stays parked; fear play + electro + new interlocks is too many new variables at once.

**Cost:** printer £20ish, sensors under £10, panel furniture £15-20 from the surplus bins, ESP32 owned. Under £50 without a scope.

## Safety, non-negotiable

- Fear play means **negotiating the deception itself** ("I consent to not knowing what the machine does or when"). She consents to the concept, not the script. Double the normal aftercare, and debrief the tricks afterwards; showing the wizard behind the curtain is part of landing it well.
- Non-verbal out agreed in advance (dropped object, tap pattern) alongside traffic lights; someone deep in dread may not find words.
- No strobing without an explicit photosensitivity check; slow red pulse and a flickering desk lamp are creepier anyway.
- Head restraint rules above: quick release, throat clear, neck never loaded.

## The Aimee question (answered 24 Sep)

Rob confirms: **she loves fear and dread.** So this is the straight version, not the half-camp one. Delivery notes that follow from that:

- Play it cold and clinical throughout. No winks, no breaking character to check she's enjoying it (that's what the non-verbal out and traffic lights are for). The top-as-technician reads the chart, makes notes, and treats her reactions as data.
- Dread is built in the gaps, not the events: long silences on the trace, the printer feeding slowly, the cuff inflating unprompted mid-silence. Under-deliver on sensation relative to the threat and the anticipation does the work.
- Because she genuinely feeds on dread, the pre-negotiation matters MORE, not less: she consents to the concept and the not-knowing, plus a real out she trusts. Heavier aftercare and a full debrief-the-tricks afterwards still stand.

Fen remains ruled out for this rig (visual overwhelm, blindfold-dependent drop).
