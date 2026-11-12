# Harbourmaster (work PR bot)

Rob's "work version of Jarvis", started 22 Oct 2026. A small zero-dependency Node daemon that runs **on Rob's old iMac** (his personal machine, used only for work right now; 12 Nov) (his call, 22 Oct: keeps Superdry code off the home Proxmox and inside his work Claude Code login). Walled off from me: no vault, no personal context, its own Telegram bot.

- **Code:** `~/projects/harbourmaster` on CT 110 (authoring copy only, never pointed at Superdry repos from here). GitHub: `NilSkilz/harbourmaster` (private since 12 Nov; must STAY private, the memory seed has colleague names and Jira details).
- **Runs:** launchd agent `uk.co.cracky.harbourmaster` on the Mac, state/config/logs in `~/.harbourmaster/`.
- **UI:** Telegram (own bot, Approve / Diff / Skip buttons, reply-to-revise) + local dashboard at `http://localhost:4848`.

## What it does
1. Comments on Rob's PRs: waits 3 min for comments to settle, Claude fixes in a throwaway worktree, runs typecheck/tests, drafts a reply per comment. Push + post only on approve.
2. Review requested: drafts overview + verdict + body + inline comments. Re-requests review only the delta since the last reviewed sha.
3. Discussion on PRs Rob reviewed: drafts replies only when something needs him, otherwise silent.
4. Slack (off by default): ported from `Jarvis/bin/slack-check.sh`, read-only, uses the claude.ai Slack connector on his work Claude account.

## Memory (v0.2, PR #1, 12 Nov)
- Rob asked for it to remember things "the same way you do", but in its own files. `~/.harbourmaster/memory/` on the Mac: `rob.md`, `team.md`, `lessons.md`, `repos/<repo>.md`, its own git repo. Fed into every fix/review/reply/Slack prompt as private context.
- Free text to the bot = chat: answers from notes, saves what's worth keeping. `/remember`, `/memory`. Approving a revised/hand-edited draft runs a learn step (saves lasting preferences only, pings what it noted).
- Seeded from `seed/memory/` with WORK-ONLY facts from `Context/Work Context.md`: role/stack, Rob's writing voice, review style, "don't be the team's reading comprehension" reply style, Jira (supergroupbt, DGF, board 305, Digital team, zombie-sprint gotcha), Slack id, Ryan/Charlotte/Isaac/Tim phrased as working patterns, Secure Properties URL, DGF-2757 spike. Deliberately left out: RTO exemption, pension/pay, contract hunt, anything personal or partner-related, all credentials (incl. the Cherwell cert password).
- Memory Claude runs (learn step): no Bash/web/MCP, refuses personal details (tested).

## Conversational chat (PR #2, 12 Nov)
- Rob, once installed: "chat doesn't act like a chat the way you do". Cause: free text was a one-shot, no-history, no-tools run told to answer only from notes.
- Now: `claude --resume` session per conversation (state in `~/.harbourmaster/chat-session.json`, resets after 3 idle hours or `/new`), persona prompt (warm/dry/direct/opinionated), notes injected into the system prompt each turn, read-only lookups (gh, PR checkouts via `--add-dir workDir`, Jira/Confluence/Slack MCP, web). Writes blocked via `--disallowedTools` (git commit/push, gh api/pr writes/issue/repo, Slack send/react/canvas, Atlassian create/edit/comment/transition). Replying to a non-draft message continues the chat.
- Both tests pass (memory test now checks it remembers the previous turn).

## Full work agent (PR #2 second commit, 12 Nov)
- Rob: "I want it to be just like you, a mini-Jarvis that only deals with work". So chat is now `mode: 'agent'` (`runAgent` in claude.js): no-prompt shell as his user, clones any repo gh sees into `~/.harbourmaster/work/chat/`, branch, code, test, commit (trailer), push branch, `gh pr create` with `agentFooter` ("Opened by Harbourmaster (AI) at Rob's request"). Research via web/Confluence/Jira/Slack. Jira create/edit/transition allowed.
- My call, kept blocked at CLI (`agentBlocked(cfg)`): merge, `gh pr review`, force-push, push to protected branches, repo delete/edit/archive, releases, `gh api -X/--method`, Slack send/schedule/react/canvas, Jira comments, Confluence writes. Slack `send_message_draft` allowed. Prefix-matching, so a seatbelt not a vault. Sudo: prompt says ask first (needs NOPASSWD anyway).
- Streams via `--output-format stream-json`: ack line, work, summary, each text block sent to Telegram in order. 2h turn cap (`claude.agentTimeoutMinutes`), `/stop` aborts running + queued turns and keeps the session for "carry on". `test/agent.js` added; all 3 suites pass.

## Guardrails
- Claude can't commit/push/gh (`--disallowedTools`), code jobs get `--strict-mcp-config` (no MCP).
- Non-force pushes only, refuses if the branch moved; forks + main/master/develop/release are reply-only.
- Big diffs (>400 lines) or sensitive paths need a second confirm.
- Repo allowlist; "Drafted with AI, reviewed and approved by Rob" footer on everything posted; `Co-Authored-By: Claude` on commits.
- Dashboard loopback-only, Host check + custom header (no CSRF/DNS rebinding).

## Status
- 22 Oct: v0.1 built and smoke-tested here (local bare repo as origin, real Claude run: fix, commit, push, replies with footer, review draft, dashboard screenshots). Dry-run poll against NilSkilz repos worked.
- 12 Nov: Rob created the repo, v0.1 pushed to `main` (04be3d7). Scanned first: no secrets, only Superdry mentions are the example config allowlist + Jira URL. Repo is public; Rob to flip it private (Settings > Danger Zone).
- 12 Nov: memory PR #1 merged to `main`, both tests pass. Installed and running on the iMac ~13:00. PR #2 (conversational chat, then full work agent) open, waiting on Rob to merge + `git pull && ./install.sh`.
- Next, on the Mac: install `gh` first (`brew install gh && gh auth login`, HTTPS + browser login, account that can see Superdry repos) or `./install.sh` fails with "Missing gh on PATH". Then BotFather bot, `git pull`, `./install.sh`, fill `~/.harbourmaster/config.json` (token, chat id, `repos` allowlist), `./install.sh` again.
- Open question for Rob: does Superdry have an AI-tools / code policy? Worth a look before it posts at volume.

## Ideas, not built
- Auto-post reviews once Rob has approved ~20 unedited.
- Pull Jira ticket context into reviews (Atlassian connector, read-only).
- 27 Oct: Rob floated moving this to an always-on EC2 box instead of his work Mac, for PR review + Slack + repo/Confluence knowledge. My take: a t3.micro (1GB) won't hold a Claude Code session plus a repo checkout and tsc/test run; floor is t3.medium/t4g.medium (4GB, ~$25-30/mo) with 30-50GB disk. It's a port of this bot (always-on version), not a rebuild. Open question before spinning anything up: needs to sit on Superdry's own AWS account with security sign-off, not a personal shadow box with prod code on it. Nothing built yet, pending Rob's decision.
