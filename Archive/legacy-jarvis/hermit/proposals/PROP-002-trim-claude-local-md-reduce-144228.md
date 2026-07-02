---
id: PROP-002-trim-claude-local-md-reduce-144228
title: "Trim CLAUDE.local.md to reduce per-call seed token cost"
status: resolved
source: operator-request
session: S-NNN
created: 2026-06-25T14:42:28+01:00
accepted_date: 2026-06-25T15:33:58+01:00
resolved_date: 2026-06-25T15:36:00+01:00
related_sessions: [S-010]
category: improvement
tags: [cost-optimization, seed-context]
responded: true
self_eval_key: null
accepted_in_session: null
success_signal: null
---
# Proposal: PROP-002 — Trim CLAUDE.local.md to reduce per-call seed token cost

## Context

Surfaced from S-010 cost analysis (operator request, 2026-06-25). S-010 was a 9h always-on session with 511 API calls, producing 39M cache read tokens ($11.70) and 1.66M cache write tokens ($6.22). The seed context — injected into every API call — is ~3,500 tokens: CLAUDE.local.md (~2,500 tokens, 10,417 chars) + MEMORY.md index (~960 tokens). This seed is re-paid by every subagent dispatch as well.

## Problem

CLAUDE.local.md contains sections where the injected text is significantly more verbose than the operative rule requires. Specifically:

1. **Watches section (lines 18–29):** 12 lines of implementation notes (grep buffering, CLAUDE_PLUGIN_ROOT, Docker vs macOS, poll vs stream descriptions) that are already covered in the `/watch` skill docs. The seed-critical content is just: registry path, the two class names, and the `HEARTBEAT_EVALUATE` handler. The rest is redundant.

2. **Context hygiene rule (Rules § line 68):** The break-even rationale ("subagents inherit CLAUDE.md/CLAUDE.local.md, so each dispatch re-pays that seed as a fixed token tax…") is 5 dense lines. The operative decision rule is 3 conditions (a/b/c). The rationale could be condensed to one sentence.

3. **Knowledge Discipline — memory-first paragraph (line 53):** ~500 chars listing every skill that must consult memory. Could be stated as a single rule: "Before suggesting anything novel, check auto-memory and suppress if already covered."

4. **Operator Notification — channel-miss case (line 46):** The explanation of what "miss" means (`missing dm_channel_id`, `empty allowed_users`, `config_read_failed`) is verbose. The operative instruction is: fire push, log to SHELL.md, dedup issue.

**Secondary finding:** Five large memory files for resolved incidents may be unnecessarily large:
- `homeserver-thermal-problem.md` (6.7KB) — thermal issue resolved
- `rob-hermit-launcher-upgrade.md` (5.0KB) — upgrade complete
- `rob-hermit-auth-token-collision.md` (4.0KB) — collision resolved
- `homeserver-crash-2026-06-23.md` (3.9KB) — crash resolved

These files are loaded on demand (not auto-injected), so their impact is conditional — but they add noise to relevant-memory retrieval.

## Proposed Solution

**Part A — CLAUDE.local.md trim:**

1. **Watches section:** Replace lines 18–29 with two condensed lines:
   - Keep: registry path reference, two class names, `HEARTBEAT_EVALUATE` → heartbeat run
   - Remove: grep buffering note, `|| true` note, noisy-watch note, CLAUDE_PLUGIN_ROOT note, session-scoping note (all in watch skill docs)

2. **Context hygiene rule:** Trim the break-even rationale from 5 sentences to 1: "Each dispatch re-pays the seed — net win only when intermediate context >> conclusion."

3. **Knowledge Discipline:** Replace the "memory-first" paragraph (6 lines) with: "Before suggesting anything novel, check auto-memory; suppress with `covered-by-memory` if the pattern is already there."

4. **Operator Notification:** Trim the channel-miss definition parenthetical — keep the operative instruction, drop the diagnostic detail.

Estimated result: ~1,200 chars / ~300 tokens removed from seed.

**Part B — Memory file audit:**

Review the four large incident memory files listed above. For each: if the incident is fully resolved and the memory's "How to apply" guidance is no longer relevant to ongoing behaviour, archive or condense to a 3-line summary.

## Impact

**Direct cost saving:** ~300 tokens × 511 calls × $0.30/M = ~$0.05/session in cache reads. Modest. The real benefit is qualitative: a leaner seed means each context window has more headroom for task-relevant content, and the model's attention is less diluted by operational boilerplate it has already learned.

**Effort:** Low — text editing only. No behaviour change if the removed content is genuinely redundant with skill docs. Risk of behaviour regression is low but non-zero for the Watches trim (if the model relies on the grep-buffering reminder to get new watches right).

**Subagent compounding:** Each subagent dispatch re-pays the seed. 511 calls likely includes ~50 subagent dispatches — trimming the seed saves proportionally on those too.

## Verification

1. After applying the trim, run `/claude-code-hermit:watch start` and verify both config monitors register correctly — confirms the Watches trim didn't remove necessary context.
2. Run one heartbeat tick manually (`/claude-code-hermit:heartbeat run`) — confirms HEARTBEAT_EVALUATE handler is still recognised.
3. Trigger one operator notification (e.g. via a test Telegram message) — confirms notification routing still works.
4. Check `wc -c CLAUDE.local.md` before and after — confirm ≥1,000 chars removed.

## Success Signal

<!-- benefit is qualitative: direct cost saving (~$0.05/session) is below session-to-session variability; cannot be reliably measured with avg_session_cost_usd predicate -->

## Operator Decision
Accepted on 2026-06-25T15:33:58+01:00.
PROCEED — /home/rob/CLAUDE.local.md (all 4 sections confirmed present at cited lines)
Resolved on 2026-06-25T15:36:00+01:00. Removed 2,108 bytes (from 10,417 to 8,309). HEARTBEAT_EVALUATE preserved. Memory files: homeserver-thermal and hermit-launcher-upgrade condensed; auth-collision and homeserver-crash left as-is (ongoing constraints).
