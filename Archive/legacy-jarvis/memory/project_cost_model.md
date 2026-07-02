---
name: project_cost_model
description: Always-on daemon runs on Sonnet (not Opus) for cost; escalate to Opus for real interactive work
metadata: 
  node_type: memory
  type: project
  originSessionId: 6c622af6-f583-4cb8-ad34-def63598447a
---

The always-on hermit daemon's session model was switched from Opus (`claude-opus-4-8`) to **Sonnet 4.6** (`claude-sonnet-4-6`) on 2026-06-21 to cut cost.

**Why:** Every scheduled wake (heartbeat every 2h, briefs, reflect) re-reads the full conversation context in the main loop. On Opus that was $13-22 per wake (one heartbeat tick = $12.52; a 3am re-arm = $22.61), driving daily spend to ~$46. Most of that is automated housekeeping, not useful work. The headline token count is misleading: ~94% is cheap cache reads.

**How to apply:**
- Baseline routine/automated wakes run on Sonnet (handles them fine).
- When Rob and I do real interactive/creative work together, bump back to Opus with `/model opus` so quality isn't lost, then it reverts on next daemon relaunch.
- Second cost driver: context bloat. The Docker entrypoint runs a ~5min watchdog loop that consumes `state/clear-requested.json` to `/clear` context after the midnight auto-close. If that loop stalls (check `state/watchdog-state.json last_run`), context grows unbounded and every wake pays to re-read it. Fix = Docker rebuild (`bin/hermit-docker update`), which relaunches the daemon + restarts the watchdog loop + clears context. See [[project_infra]].
