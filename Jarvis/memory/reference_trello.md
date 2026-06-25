---
name: reference-trello
description: "Trello board \"Jarvis-v2\" is Rob's task pipeline for Jarvis work — how to access it"
metadata: 
  node_type: memory
  type: reference
  originSessionId: f648f305-92f5-4c9c-b505-25d0e8ca6e15
---

Rob tracks tasks for Jarvis on Trello board "Jarvis-v2" at https://trello.com/b/YkZEamyj/jarvis-v2.

**Credentials:** `/home/rob/.claude.local/secrets/trello.env` (mode 0600, gitignored). Contains `TRELLO_KEY`, `TRELLO_TOKEN`, `TRELLO_BOARD_SHORTLINK`, `TRELLO_BOARD_ID`.

**CLI:** `/home/rob/Projects/Personal/tools/jarvis-tools/trello/trello.mjs` (was at Personal/jarvis-tools/ before 2026-06-04 reorg) — run via `node trello.mjs <cmd>`. Commands: `lists`, `cards [filter]`, `read <id>`, `add <list> <title> [desc]`, `move <id> <list>`, `comment <id> <text>`, `check <id> <text>`. List name matching is fuzzy/substring so `move xyz Done` works.

**Lists (kanban):** Inbox → Todo → In Progress → Blocked → Done.

**How to apply:** On idle ticks or when Rob says "what's on the board?", `node trello.mjs cards Todo` to see what's pickable. Move cards through the flow as work progresses. Always comment progress before moving to In Progress / Done / Blocked. Cards in Todo can be picked up autonomously; cards in Inbox are not yet triaged by Rob.

**Autonomous pickup:** Heartbeat tick (every 2h) runs `pickup.mjs` (max 2 cards/tick, 6h staleness recovery). For each claimed card, the heartbeat spawns a background subagent using template at `/home/rob/Projects/Personal/tools/jarvis-tools/trello/SUBAGENT-BRIEF.md`. Subagent comments progress to the card and moves to Done/Blocked, then calls `release.mjs <id> <outcome>` to clear in-flight state at `/home/rob/.claude-code-hermit/state/trello-pickup.json`. Heartbeat checklist item is in `.claude-code-hermit/HEARTBEAT.md`.
