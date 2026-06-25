---
id: S-008
status: completed
date: 2026-06-22T19:45:00+01:00
duration: 18d
cost_usd: 159.6555
tokens: 62008000
tags: [watches, infra]
proposals_created: [PROP-001]
task: "Implement PROP-001: Preserve always-on infra watches across daily-auto-close"
escalation: balanced
operator_turns: 0
closed_via: operator
---
# Session Report: S-008

## Overview
Implement PROP-001: Preserve always-on infra watches across daily-auto-close

## Completed
- Implemented `survive_auto_close` flag (option a) on monitor config entries — telegram-poll and telegram-inbox both marked `survive_auto_close: true` in config.json
- Implemented heartbeat self-heal reconciliation (option b) in heartbeat/SKILL.md and heartbeat/reference.md — on each heartbeat tick, missing config-defined monitors are re-registered
- Updated session-close/SKILL.md and session-start/SKILL.md to respect the flag
- Diagnosed cost leak: always-on session was running on claude-opus-4-8; every scheduled wake re-read full context on Opus ($13-22/wake). Fixed by switching config.model to claude-sonnet-4-6
- Identified stale watchdog as root cause of context never clearing; Docker rebuild (`hermit-docker update`) identified as unifying fix (pending Rob action)
- Verified Radarr + Sonarr API keys stored and auth-verified; end-to-end movie suggest→approve→add→search→grab flow proven

## Changed
- `/home/claude/.claude/plugins/cache/claude-code-hermit/claude-code-hermit/1.2.8/skills/session-close/SKILL.md` (modified)
- `/home/claude/.claude/plugins/cache/claude-code-hermit/claude-code-hermit/1.2.8/skills/session-start/SKILL.md` (modified)
- `/home/claude/.claude/plugins/cache/claude-code-hermit/claude-code-hermit/1.2.8/skills/heartbeat/reference.md` (modified)
- `/home/claude/.claude/plugins/cache/claude-code-hermit/claude-code-hermit/1.2.8/skills/heartbeat/SKILL.md` (modified)
- `/home/rob/.claude-code-hermit/config.json` (modified)
- `db/presence.json` (modified)
- `db/theduchy-videos.json` (modified)
- `server/index.js` (modified)
- `server/websocket/haWebSocket.js` (modified)
- `src/App.jsx` (modified)
- `src/components/AmbienceProvider.jsx` (modified)
- `src/components/HomeAssistantWidget.jsx` (modified)
- `src/hooks/useHAWebSocket.js` (modified)
- `src/lib/api.tsx` (deleted)
- `src/pages/Home.jsx` (deleted)

## Artifacts

## Blockers

## Lessons
- Always-on sessions accumulate very large token counts over multi-day spans (62M tokens here) — the model choice matters enormously; Opus on a long-running always-on session is cost-prohibitive
- Watchdog stall silently prevents context-clear from firing; the symptom is `state/clear-requested.json` sitting unconsumed with no watchdog state updates

## Proposals Created
- PROP-001 (Preserve always-on infra watches across daily-auto-close)

## Next Start Point
Items waiting on Rob:

0. **NEW PROJECT: weekly movie suggestions + on-demand downloads** — RECON DONE. Media stack: Radarr :7878, Sonarr :8989, Plex (creds in .claude.local/secrets/plex.env). Keys in .claude.local/secrets/radarr.env and sonarr.env (RADARR_KEY/SONARR_KEY). End-to-end flow proven (Sicario test). Still to build: weekly-suggestion routine (taste from Plex library+history → Telegram suggestions → pick → add). NZBGet queue was paused — check if Rob resolved.
1. **Docker rebuild pending** — `hermit-docker update` activates Sonnet model switch + restarts watchdog + clears bloated context.
2. **Biothane posture collar** — Rob hasn't answered whether he wants the steel-boned design consolidated into a clean v1 spec. If yes: 3 bands of 20mm biothane, corset-steel-bone risers in sandwich-and-rivet channels, back closure. Full design in S-007-REPORT.md Progress Log [20:18-20:34]. Don't write to Obsidian vault without explicit yes.
