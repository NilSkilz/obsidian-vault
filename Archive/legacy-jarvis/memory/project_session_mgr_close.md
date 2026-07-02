---
name: project_session_mgr_close
description: "session-mgr subagent pauses before the final runtime.json atomic swap on auto-close — recurring, needs the main loop to finish it"
metadata: 
  node_type: memory
  type: project
  originSessionId: d7fa0582-0e72-4447-9534-f4978d33ef55
---

On `/session-close --auto` (daily-auto-close path), the `claude-code-hermit:session-mgr` subagent archives the report and resets SHELL.md to the fresh template, but **returns/pauses before completing the final runtime.json atomic swap**. It leaves runtime.json mid-transition (`transition: "cleaning"`, old `session_id`, `shutdown_completed_at: null`) and emits a "use SendMessage to continue this agent" handoff instead of finishing.

**Observed twice:** S-003 close (2026-06-08) and S-004 close (2026-06-09) — both archived reports exist as evidence. SendMessage is not available to the main loop, so each time I finished the swap manually: write runtime.json with `session_state: idle`, next `session_id`, `transition: null`, fresh `shutdown_completed_at`+`updated_at`, then `rm -f pending-close.json`.

**Why it matters:** if the main loop weren't present to finish, the session would be stuck in `transition: "cleaning"` and the next session-start would have to run interrupted-transition recovery (or leave a stale lifecycle clock). Borderline-proposal-worthy as a Component Health issue — let `reflect` gate it through triage/judge using the two archived sessions as `archived-session` evidence. Candidate label: `session-mgr-incomplete-close-swap`. Related: [[project_telegram_bridge]].
