# Inspiration Log

Wild ideas hunted from the internet, curated for us. Fed by the weekly inspiration scout (`Jarvis/bin/inspiration.sh`, Sundays 09:30) plus ad-hoc hunts. Rob asked for this on 22 Sep 2026: "I wanna be blown away with awesome ideas." Standard: would a jaded senior dev raise an eyebrow? If not, it doesn't go in.

## 2026-09-22 (founding hunt: all four themes at once)

### AI assistants: what people are actually building

- **GLaDOS Personality Core** (dnhkng): fully local, low-latency voice persona with custom-trained voice, interruption handling, long-term memory, vision, and 3D-printed animatronics with an eye that tracks you. Modular enough to reskin as any persona. The obvious riff: a physical Jarvis face on the wall. https://github.com/dnhkng/GLaDOS
- **Latent Reflection** (Rootkid): art piece. A 3B model trapped on a Pi with an LED text display, told at boot it lives inside finite RAM; its monologue about its own mortality consumes memory until OOM kills it, then it reboots and starts again. Parts-bin buildable, genuinely unsettling. https://rootkid.me/works/latent-reflection
- **LLM Vision for Home Assistant**: camera streams + multimodal LLM = notifications like "courier left a parcel behind the bin" instead of "motion detected", with an event memory you can query later ("who came to the door while I was out?"). HACS install, would drop straight onto our HA at .4. https://github.com/valentinfrlch/ha-llmvision/wiki
- **zclaw**: an entire AI assistant runtime in 888KB on a bare ESP32, talking over Telegram, monitoring and actuating its own GPIO. An AI employee whose body is a microcontroller. Crossover with the saline-pump class of rigs. https://hackaday.com/2026/02/27/ai-assistant-uses-esp32/
- **Pocket Tank**: a 14M-param LLM running a virtual aquarium on an ESP32-S3 with a screen; the model decides fish behaviour. Riff: ambient desk creatures whose mood reflects house state. https://www.hackster.io/news/this-virtual-aquarium-is-driven-by-a-tiny-llm-3ce0ccd30813
- **Plant Intelligence / BioAgent AI**: self-watering garden where the AI looks at camera frames of the sky (and whether someone already watered by hand) before deciding. Vision-as-sensor is the 2026 move: one camera + a model replaces a fleet of dedicated sensors. https://www.hackster.io/sbis04/plant-intelligence-self-watering-garden-that-checks-the-sky-407900
- **AI Marketplace Monitor**: browser-driving watcher that has an LLM judge each Facebook Marketplace listing against your criteria and pings only the good ones. The reusable pattern: scraper does volume, model does taste. Direct upgrade path for the car-hunt script. https://pypi.org/project/ai-marketplace-monitor/
- **OpenClaw ecosystem**: the self-hosted personal-AI phenomenon (0 to 100k stars in a month). We already ARE this architecture, but the user patterns are worth raiding: supervisor agent managing worker fleets over tmux, marketplace price negotiation, gift tracking. Security record is a mess (341 malicious skills, an RCE), so watch, don't adopt. https://news.ycombinator.com/item?id=46838946
- Also noted: claude-homelab (Claude Code skills/hooks for homelab ops, https://github.com/jmagar/claude-homelab), ESP32-S3 voice puck with local MCP execution (https://hackaday.io/project/204691-esp32-ai-voice-assistant-with-mcp-integration).

### Kink software we'd never heard of

- **Chaster's Extensions API**: the chastity platform ships a public API where third parties build lock extensions (dice games, pillory, task lists) that act on other people's locks. The only "app store" in kink software. Someone built an ESP32 physical key-safe unlocked by the Chaster API: https://github.com/bdsm-spuddy/esp8266-chaster-safe. Docs: https://docs.chaster.app/api/extensions-api/getting-started/
- **Kneel** (getkneel.com): newest and closest Tethered competitor. Tasks with photo proof and auto-consequences, scheduled check-ins, keyholding countdowns, a "petition" system (sub formally requests, Dom rules on it), one shared couple subscription. Aggressive SEO. Worth a proper teardown.
- **Obedience** (obedienceapp.com) and **SubTasks** (subtasksapp.com): the D/s habit-tracker cluster. Obedience frames kink as habit science and is doing serious content marketing in exactly Tethered's space; SubTasks is squeezing from below with a free tier.
- **buttplug.io / Intiface + XToys.app**: the open-source spine of toy control (750+ devices, new REST API). XToys has block-style visual scripting AND a custom-device path: any ESP32 gadget can present itself over BLE/MQTT/ESPHome. Map of the ecosystem: https://awesome-buttplug.io (Beadi node-based toy programming, FunGen AI funscript generation, a chess engine that vibrates moves in morse code).
- **Restim + Coyote 3 scene**: open-source e-stim signal generator, multi-electrode, syncs to funscript/video/games. https://github.com/diglet48/restim
- **OpenShock**: open ESP32 firmware + self-hosted API for cheap RF shock collars; £15 AliExpress collar replaces PiShock's cloud subscription. https://openshock.app
- **ChastiSafe**: free community-run keyholding with BOT keyholders that co-manage a lock alongside a human. https://chastisafe.com
- **Plura** (heyplura.com): YC-backed kink/ENM events platform, the only serious challenger to FetLife's events monopoly.
- Local-first consent tools worth idea-mining: https://github.com/kdirectoryxo/kinkdirectory, https://github.com/petaurora/kink-profile (privacy by browser-only storage).

**Gaps Tethered could own** (from the sweep, nobody is doing these):
1. Kink-native safety check-ins still barely exist. The safecall space is entirely vanilla (Kitestring etc); dead-man-switch safecalls with kink context remain Tethered's open founding premise.
2. Rope/rigging logs and suspension safety tools: literally nothing exists. Tie log, nerve-check outcomes, incident notes. Zero competitors.
3. Aftercare/drop tracking as a product doesn't exist; every app blogs about it, none instrument it (mood-after-scene, drop alerts to the partner).
4. A public check-in/task API a la Chaster's extensions, so hardware (ESP32 locks, Coyote, OpenShock) can hook Tethered events. Obedience/SubTasks/Kneel are all closed boxes; nobody in the D/s cluster has a platform play.

### DIY / mad scientist kink hardware

- **OSSM + KinkyMakers**: THE reference open fucking machine (ESP32, belt linear rail, up to 1 m/s), with a mod ecosystem, an open wireless remote (OSSM-M5-Remote), and a Discord that's the real R&D floor. Rob's stepper machine done by a thousand people first: steal the architecture. https://github.com/KinkyMakers/OSSM-hardware, https://ossm.tech
- **Edge-o-Matic 3000 / Endless Orgasm Machine**: automated edging via inflatable plug + £10 pressure sensor detecting involuntary pelvic floor contractions; algorithm cuts stimulation before the point of no return. The ESP32-only fork: https://github.com/RubberyFun/endless-orgasm-machine. Pairs beautifully with a machine: speed governed by the bottom's own arousal signal. This is basically Fuck-io's orgasm-detect plug, already built and MIT licensed.
- **FOC-Stim**: current-controlled e-stim from a £20 ST motor-driver dev board, any-to-any electrode topology so sensation can be STEERED spatially across 3-4 electrodes. Controlled by Restim. The obvious upgrade path from the EM43. Scope + dummy load before skin, below the waist only. https://github.com/diglet48/FOC-Stim (also NeoDK, the other serious open design, great reading on output stages: https://github.com/Onwrikbaar/NeoDK)
- **T-Code + funscript as the lingua franca**: one .funscript can now drive a stroker, e-stim, vibe and machine simultaneously. Highest-leverage firmware decision for anything we build: speak T-Code, get the whole scripting/VR ecosystem free. https://osr.wiki/books/osr2/page/overview
- **Strain-Paddle** (KinkyMakers): impact paddle with a strain gauge. Quantified spanking: force telemetry per stroke, HX711 + load cell (kitchen scale parts). Impact play with a live force graph is very us. https://github.com/KinkyMakers
- **Fail-open maglock predicament engineering**: 12V electromagnetic door holders release on ANY power loss (timer, battery death, crash), which makes them the only safe electronic bondage release. ESP32 + dead-man logic + mechanical backup in reach. No commercial market can touch this for liability reasons.
- **Peltier thermal play**: research VR haptics has solved scriptable hot/cold pads (H-bridge flips a TEC between heat and cool); no kink product exists at all. Firmware thermal limits + thermistor + hardware fuse. https://medium.com/@SomaticLabs/temperature-feedback-with-the-thermoelectric-peltier-effect-c2e86e1cb4f1
- **Milking machine conversions**: a £60 agricultural milking pulsator is the same mechanism as a £1,200 Venus 2000; ESP32-controlled pulse valves give software-defined patterns no commercial unit offers. Pressure relief valve non-negotiable.

**Underserved kinks where homemade wins**: predicament bondage electronics (biggest open lane, zero commercial products), closed-loop biofeedback (HR/GSR-fused arousal dashboards, unbuilt outside academia, and Rob builds dashboards for a living), sensation-mapping multi-electrode e-stim, quantified impact play, scriptable thermal play, medical play instrumentation (real ECG/SpO2 into theatrical displays; the saline pump is already this category).

### Household apps worth stealing from

- **Donetick**: self-hosted chores with auto-rotation strategies, parental approval before points count, and an API so HA sensors can complete/trigger chores (dishwasher finished = chore due). https://github.com/donetick/donetick
- **ChoreOps**: chore gamification living INSIDE Home Assistant; every point balance, badge and streak is an entity you can automate against (no WiFi until chores approved). https://github.com/ccpk1/choreops
- **OpenSkyLight**: open-source Skylight family wall calendar clone; the tile grid + star-balance economy is the whole product, prime idea-mining for Tide. https://github.com/hukunokina/OpenSkyLight
- **Warracker**: warranty/receipt tracker organised around EXPIRY DATES rather than documents; alerts before warranties lapse so you claim instead of shrug. https://github.com/sassanix/Warracker
- **DVLA Vehicle Enquiry for HA**: MOT/tax become HA sensors straight off the reg plate; renewal nagging becomes an automation. Directly relevant to the Fiesta/Dacia dates we track by hand. https://github.com/jonwilliams84/ha-dvla-vehicle (pairs with LubeLogger for service history: https://lubelogger.com)
- **Advanced Energy Card**: the best of the 2025-26 HA energy-flow cards (animated flows, liquid-fill battery viz). The front-end for the energy dashboard idea once the solar clamp is fixed. https://github.com/ratava/advanced-energy-card
- **Dawarich**: self-hosted Google Timeline replacement; a private family "where did we go this year" map. https://github.com/Freika/dawarich
- **HortusFox**: collaborative plant care with a shared warning queue, so plants become household responsibility rather than one person's guilt. https://github.com/danielbrendel/hortusfox-web
- **Pet-care-tracker's one great trick**: reminders delivered as an ICS calendar subscription. Zero apps, zero push infra, lands in everyone's native calendar. Worth stealing for Tide reminders. https://github.com/AlexDreamien/pet-care-tracker

**Recurring mechanics in the good 2025-26 stuff**: approval-gated points economies for kids, expiry-date-first data models for life admin, ICS subscriptions as the zero-friction notification channel, and (from the AI pile) vision-as-sensor plus LLM-as-taste-filter in dumb pipelines.

### The cross-theme mashups (my picks)

1. **Arousal-governed machine**: Endless Orgasm Machine pressure sensing + the stepper machine + T-Code. Fuck-io's core loop already exists as open source; we'd be integrating, not inventing.
2. **Scene telemetry dashboard**: bottom's live HR (BLE chest strap) + GSR + EoM pressure on a Grafana-style display, with rules attached. Nobody has built it, it's dashboards + ESP32, and it feeds Tethered's aftercare-instrumentation gap.
3. **Tethered platform play**: a Chaster-style extensions/webhook API, positioned by the rigging-log and aftercare gaps nobody else is touching.
4. **Tide life-admin layer**: DVLA sensors + Warracker-style expiry model + ICS-subscription reminders.
5. **House with a face**: LLM Vision narrating the cameras + a GLaDOS-style local voice persona. The homelab already has the brain; this gives it eyes and a mouth.
