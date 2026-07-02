---
name: rob-hermit-auth-token-collision
description: rob-hermit container keeps losing its OAuth refresh token (forced re-login) because it shares one Claude subscription login with the host; rotating single-use tokens collide.
metadata: 
  node_type: memory
  type: project
  originSessionId: 6469ca69-bf43-46ef-9328-d39ec86eb4cb
---

**Symptom:** the `rob-hermit-1` container periodically prompts for login despite a "valid refresh token" — its `/home/claude/.claude/.credentials.json` ends up with an expired `accessToken` and NO `refreshToken`.

**Root cause (confirmed via docs + anthropics/claude-code#54443):** the host CLI (`/home/rob/.claude`) and the container (named volume `rob_claude-config`) are signed into the **same Claude Team subscription account**. Claude Code subscription OAuth uses **single-use rotating refresh tokens** — when one client refreshes, the other's stored refresh token goes stale; the next refresh on the other client gets a 400/401, Claude discards the dead token, and forces `/login`. Two concurrent logins on one account is not officially supported and they invalidate each other.

**Immediate recovery (no interactive login):** the host `/home/rob` is bind-mounted into the container and both `rob`/`claude` are UID 1000, so copy the host's currently-valid creds in:
`docker exec rob-hermit-1 cp /home/rob/.claude/.credentials.json /home/claude/.claude/.credentials.json && docker exec rob-hermit-1 chmod 600 …` then restart. Done 2026-06-20 (backup left at `.credentials.json.broken-20260620`). This is a patch — recurs whenever host & container both refresh.

**Durable fix NOT taken (loses Remote Control):** `claude setup-token` mints a 1-year `CLAUDE_CODE_OAUTH_TOKEN` immune to the collision and still billed to the subscription — BUT it's inference-only and cannot do Claude Code Remote Control. Rob needs RC (`/rc active`), so we did NOT switch. (An `ANTHROPIC_API_KEY` is a separate pay-as-you-go pool AND also no RC — avoid.)

**Mitigation IN PLACE (2026-06-20):** host cron heals the container instead. Script `/home/rob/.claude-code-hermit/bin/hermit-cred-sync` (host cron `*/15 * * * *`, log `state/cred-sync.log`) copies host creds into the container ONLY when the container is broken (no refreshToken / expired) AND host creds are valid — guarded so it never clobbers a healthy/freshly-rotated container token. Tested end-to-end. Heals host-induced breakage within ~15 min; the running session picks up healed creds on its next auth cycle (restart for immediate effect). Does NOT eliminate the collision (shared login + rotation is fundamental) — just auto-recovers. If the cron ever logs "host creds also invalid", run `claude /login` on the host.

**RECURRED 2026-06-22 (silent >24h outage):** Both host AND container creds expired together ~Jun 21 03:30, so cred-sync had no valid source and kept logging "container creds broken AND host creds invalid" for over a day — the daemon sat wedged at `401 Invalid authentication credentials` the whole time, unnoticed (no heartbeat, no watchdog, clear flag unconsumed → looked like the cost/watchdog bug but was really auth). Surfaced only during crash-recovery investigation. Resolution confirmed the documented path exactly: Rob's host `/login` (11:59) minted valid creds → cred-sync copied them in (12:00, hashes matched) → but running daemon still showed 401 until `hermit-docker restart` made it re-read the file → came up authenticated on Sonnet, `/rc active`, bootstrap ran. **Lesson:** when the always-on hermit looks dead (stale watchdog, unconsumed clear flag, no heartbeat), check the daemon pane for a 401 *first* (`docker exec rob-hermit-1 tmux capture-pane -pt hermit-rob`) — auth wedging masquerades as the cost/watchdog bug. The shared-login expiry can be silent for a long time when host creds lapse too. Strengthens the case for the [[rob-hermit-auth-token-collision]] durable fix if RC ever becomes optional.

Related: [[rob-hermit-launcher-upgrade]].
