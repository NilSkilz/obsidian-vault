# Illuminated Suspension Hoop

Tangent idea, raised 27 Nov 2026 (not a gift). No off-the-shelf lit shibari suspension ring exists (searched: only aerial-lyra lamps, plain rings, a glowing-frisbee patent), so it's DIY or nothing.

**How commercial lit aerial hoops work** (Firetoys spec): rated steel tube (25mm, 3mm wall, TIG-welded, 128kg WL) + LED strip + hard clear coat + grip tape. The lighting is just a layer over a hoop already rated; the steel never knows the LEDs are there.

## Two directions, depending on what Rob means by "hoop"

**A. Big lyra-style hoop (tied into/onto):** buy a rated single-point aerial hoop or suspension ring, never drill/weld/heat it. SK6812/WS2812B addressable strip + ESP32 running WLED (familiar territory from the saline pump) for effects/phone control. Power: 18650 pack at the top tab (least-movement point). Protect with clear epoxy or heatshrink over the strip. Leave tie zones (top + anchor wraps) bare, light only the spans between.

**B. Small hardpoint ring (30-40cm), "halo" look:** LEDs round the outside edge since load sits on the inside. Caveat: the outside edge isn't rope-free either, lark's heads/half hitches/frictions on the upline all cross it, just pressure-light rather than load-bearing. Diffusion: addressable neon flex (WS2812B/silicone-sealed, search "WS2812B neon flex") not a DIY epoxy layer, waterproof/IP67, shrugs off rope dragging far better than hard coatings which crack. Check bend direction (light faces outward when wrapped round the ring), bend radius (15-20cm radius on a 30-40cm ring, most 6x12/8x16mm flex handles it fine), density (60+ LEDs/m). Fix with neutral-cure silicone/VHB or 3D-printed clip-on saddles, never drilled/clamped into the steel. Leave ~5-8cm gap at the top for upline + battery pod (one 18650, WLED brightness capped ~40%). Leave fixed tie spots bare if wraps are consistent; otherwise run the neon all the way round and accept scuffing.

**Sourcing:** not available on any UK high street (B&Q/Homebase Twinkly Flex is wrong shape/mains-only; Screwfix/Range/Argos neon flex is single-colour, no WLED effects). For effects: BTF-Lighting addressable neon flex off Amazon, 5V, 60 LEDs/m, 1m covers a 30-40cm ring with spare. For a plain warm-white halo (Rob's/Jarvis's pick as "the classy option anyway"): single-colour neon flex works and can be bought same-day.

**27 Nov, IKEA KABBLEKA:** Rob is buying one to try, planning to cut it for parts. Not addressable: 5V DC, max 15W, cut only at the marked black lines. Dimmable version = single warm white; adjustable-colour version changes the whole strip at once, no chasing effects. Offcuts are usable: solder onto the copper pads at the cut mark, reseal with clear neutral-cure silicone if sleeved. 5V suits an 18650+boost or a power bank directly. For the dimmable version, ESP32 + one logic-level MOSFET (IRLZ44N-class) gives WLED single-channel PWM dimming/breathing. Adjustable-colour offcuts are riskier, channel count at the cut (2 = single colour, 3-4 = channels) needs checking in person before planning around it.

Rough budget either way: ~£25-40 with the ESP32.
