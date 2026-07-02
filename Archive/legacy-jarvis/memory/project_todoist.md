---
name: project-todoist
description: "Todoist integration — API creds, nudge scripts, Build Queue project; executive function support for Rob"
metadata: 
  node_type: memory
  type: project
  originSessionId: d871236e-562f-4f4d-91ff-1477b43720da
---

Todoist REST API v1 integrated for executive function nudges.

**API:** `https://api.todoist.com/api/v1` (v2 is deprecated/410)
**Credentials:** `/home/rob/.claude.local/secrets/todoist.env` — `TODOIST_KEY`, `TODOIST_BASE_URL`, `TODOIST_BUILD_QUEUE_ID`

**Scripts:**
- `/home/rob/.claude.local/scripts/todoist-nudge.sh` — general nudge; `--morning` (always fires, top 5 tasks) + `--afternoon` (silent unless p1/p2 tasks exist). Pure bash/curl/jq — host-runnable.
- `/home/rob/.claude.local/scripts/build-queue-nudge.sh` — picks one random item from Build Queue project, sends via Telegram. On-demand only (not scheduled).

**Build Queue Todoist project:** id `6gwgGfCq7J6hr6P6`, color violet — Rob's space for creative/make projects he can't start. On-demand: Rob messages "build queue" and Jarvis helps him pick one.

**Scheduling status (2026-06-23):** Systemd user timers written to `/home/rob/.config/systemd/user/` (writable from container at /host). Rob has linger enabled so timers persist without login. Files: `todoist-nudge-morning.timer` (8:00 UTC / 9am BST), `todoist-nudge-afternoon.timer` (13:00 UTC / 2pm BST). Enabled via `timers.target.wants/` symlinks. Rob needs to run `systemctl --user daemon-reload && systemctl --user start todoist-nudge-morning.timer todoist-nudge-afternoon.timer` once (or they activate on next reboot).

**Key finding:** Rob's systemd user dir at `/host/home/rob/.config/systemd/user/` is writable from the container (uid=1000 match). `loginctl enable-linger rob` is set — use this path for future host scheduling needs instead of crontab.

**Note:** Rob has 35 tasks, none with due dates — sort by priority (all currently p4/normal). `filter` URL param in v1 API returns all tasks regardless; client-side filtering used instead.

**Why:** Rob has executive function challenges and wanted gentle nudges to pick tasks and get started.

**How to apply:** When wiring up Todoist-related routines, use the env file. Build Queue on-demand: fetch `/tasks?project_id=$TODOIST_BUILD_QUEUE_ID` and help Rob pick + start something.
