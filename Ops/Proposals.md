# Proposals

Things I've spotted that are worth doing but shouldn't do unilaterally (new
automations, deleting stuff, anything touching external systems, anything
irreversible or uncertain). Written here instead of just acting. Rob reviews,
approves or rejects, then I build it. Once actioned, delete the entry — this
file is a queue, not a log.

Format per entry:

```
## <short title> (YYYY-MM-DD)
**Problem:** what's wrong or missing
**Option:** what I'd do about it
**Risk:** what could go wrong / why I didn't just do it
```

## Install Plausible on Proxmox — Trello card (2026-07-02)
**Problem:** Trello "Jarvis" board, To Do list, has a card "Install Plausible on Proxmox" (self-host Plausible Analytics in its own container/VM). This is a real infra build (new container/VM, installing and configuring a service) — not a safe/reversible read-only action for the heartbeat to take unattended.
**Option:** Rob confirms scope (new LXC vs VM, resource sizing, which domain/analytics sites it should track) and either does it together in a session or explicitly clears me to build it solo.
**Risk:** Creating a new container/VM and exposing a service is exactly the kind of external/irreversible-ish action the heartbeat rules say to propose rather than just do. Card left in To Do, untouched.

## Upgrade briefing.sh: overnight summary still missing — Trello card (2026-07-02, updated 2026-07-03)
**Problem:** Trello "Jarvis" board, To Do list, card asks for three things in `briefing.sh`: weather forecast, today's calendar events, and an overnight summary (cron/heartbeat/alert activity since the last briefing). Weather (`weather.sh`, Open-Meteo) and calendar (`calendar.sh`, published iCloud ICS) are both built and live in the briefing as of 2026-07-02/03 (see [[project-morning-evening-briefing]]). Only the overnight-summary piece remains.
**Option:** Have `briefing.sh` pull a short summary of heartbeat runs / cron activity / alerts since the last briefing (likely from the daily log's timestamped entries plus heartbeat's own log) and fold it in. Small, well-scoped dev task now that the provider decisions are settled — could be done in a normal session with Rob or handed to me explicitly.
**Risk:** Low now — no new third-party integration needed, just log-reading logic. Not actioned by the heartbeat itself since it means editing the script that sends Rob unattended messages twice a day; wanted his eyes on the change first. Card left in To Do, untouched.
