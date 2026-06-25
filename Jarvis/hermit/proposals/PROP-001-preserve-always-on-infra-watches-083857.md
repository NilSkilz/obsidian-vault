---
id: PROP-001-preserve-always-on-infra-watches-083857
title: "Preserve always-on infra watches across daily-auto-close"
status: resolved
source: manual
session: S-006
created: 2026-06-11T08:38:57+01:00
accepted_date: "2026-06-22T20:26:00+01:00"
resolved_date: "2026-06-22T20:26:00+01:00"
related_sessions: [S-005, S-006]
category: improvement
tags: [reliability, infra]
responded: true
self_eval_key: null
accepted_in_session: S-008
---
# Proposal: PROP-001 — Preserve always-on infra watches across daily-auto-close

## Context
Surfaced during S-006 (2026-06-11 08:30). After the midnight `daily-auto-close` archived S-005, the heartbeat-restart routine re-armed the heartbeat monitor and the routine crons — but the three config watches (`telegram-poll`, `telegram-inbox`, `cloudflare-ddns`) stayed **stopped** from ~00:37 until 08:30 UTC (~8h). They only came back because a `NEXT-TASK.md` happened to exist, which triggered heartbeat idle-agency → `session-start` → `/watch start`.

## Problem
`session-close --auto` stops **all** watches before archiving (per the session-close preamble, not skipped on `--auto`), and nothing re-registers them until a new session starts. For an always-on daemon this is a reliability gap with two concrete failure modes:

1. **Deaf to the operator (circular).** The `telegram-inbox` watch that captures Rob's messages is itself stopped by auto-close. An inbound Telegram message cannot trigger a session-start because the thing that detects it is offline. The hermit can stay deaf until an unrelated trigger (a queued NEXT-TASK, or a routine that happens to start a session) fires. If neither exists, it stays deaf indefinitely.
2. **DNS goes stale.** The `cloudflare-ddns` watch stops polling. If the home dynamic IP drifts while it's down, `*.cracky.co.uk` points at a dead IP — this is exactly the outage that took down Plausible in S-005 (IP moved .207 → .236). On 2026-06-11 the IP happened not to drift during the 8h window, so there was no harm — but that was luck, not design.

The current safety net (heartbeat idle-agency re-registering watches via NEXT-TASK pickup) is incidental: it only works when a NEXT-TASK is queued, and it cannot work for the inbound-message case because the trigger channel is the very thing that's down.

## Proposed Solution
Pick one (operator's call — listed cheapest-first):

- **(a) `survive_auto_close` flag on config monitors.** Add an opt-in field to `config.json` `monitors[]` entries (e.g. `"survive_auto_close": true` on `telegram-poll`, `telegram-inbox`, `cloudflare-ddns`). `session-close --auto` skips stopping flagged watches; operator-invoked `/session-close` still stops everything. Smallest change, keeps the watches alive continuously. **Caveat:** session-start step 3b clears the registry unconditionally — flagged survivors would need their registry entries preserved or the survivors reconciled on next start to avoid orphaned/duplicate Monitors.
- **(b) Heartbeat self-heal.** On each EVALUATE tick, if the daemon is alive and any enabled config watch is not in `monitors.runtime.json`, re-register it. Bounds the outage to one heartbeat interval (≤2h) regardless of NEXT-TASK presence. More robust than (a) but still leaves a gap up to one interval.
- **(c) Re-register after archive in daily-auto-close.** After `session-close --auto` archives, immediately `/watch start` the config infra watches. Closes the gap at the source, but only for the daily-auto-close path (not other close paths).

(a)+(b) together would be belt-and-suspenders: continuous survival plus a self-heal backstop.

## Impact
- **Benefit:** removes a silent single-point reliability gap on the two most important always-on channels (operator comms + dynamic DNS). Directly prevents recurrence of the S-005 outage class and prevents the daemon going unreachable.
- **Effort:** low–moderate. (a) is a config field + two conditionals in session-close and the registry-clear step. (b) is a reconciliation block in the heartbeat EVALUATE flow. Both touch plugin skill files (operator implements; agent must not self-modify plugin internals).
- **Security:** none — re-registers already-approved config monitors; no new network/permission surface.

## Operator Decision
Accepted on 2026-06-22T20:26:00+01:00. Implement options (a) survive_auto_close flag + (b) heartbeat self-heal reconciliation.
Falsification gate: PROCEED. All insertion points verified. Files: session-close/SKILL.md, session-start/SKILL.md, heartbeat/reference.md, heartbeat/SKILL.md, config.json. Note: no cloudflare-ddns entry in current config.
Resolved on 2026-06-22T20:26:00+01:00.
