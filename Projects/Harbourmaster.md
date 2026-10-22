# Harbourmaster (work PR bot)

Rob's "work version of Jarvis", started 22 Oct 2026. A small zero-dependency Node daemon that runs **on Rob's work Mac** (his call, 22 Oct: keeps Superdry code off the home Proxmox and inside his work Claude Code login). Walled off from me: no vault, no personal context, its own Telegram bot.

- **Code:** `~/projects/harbourmaster` on CT 110 (authoring copy only, never pointed at Superdry repos from here). GitHub: `NilSkilz/harbourmaster` (private).
- **Runs:** launchd agent `uk.co.cracky.harbourmaster` on the Mac, state/config/logs in `~/.harbourmaster/`.
- **UI:** Telegram (own bot, Approve / Diff / Skip buttons, reply-to-revise) + local dashboard at `http://localhost:4848`.

## What it does
1. Comments on Rob's PRs: waits 3 min for comments to settle, Claude fixes in a throwaway worktree, runs typecheck/tests, drafts a reply per comment. Push + post only on approve.
2. Review requested: drafts overview + verdict + body + inline comments. Re-requests review only the delta since the last reviewed sha.
3. Discussion on PRs Rob reviewed: drafts replies only when something needs him, otherwise silent.
4. Slack (off by default): ported from `Jarvis/bin/slack-check.sh`, read-only, uses the claude.ai Slack connector on his work Claude account.

## Guardrails
- Claude can't commit/push/gh (`--disallowedTools`), code jobs get `--strict-mcp-config` (no MCP).
- Non-force pushes only, refuses if the branch moved; forks + main/master/develop/release are reply-only.
- Big diffs (>400 lines) or sensitive paths need a second confirm.
- Repo allowlist; "Drafted with AI, reviewed and approved by Rob" footer on everything posted; `Co-Authored-By: Claude` on commits.
- Dashboard loopback-only, Host check + custom header (no CSRF/DNS rebinding).

## Status
- 22 Oct: v0.1 built and smoke-tested here (local bare repo as origin, real Claude run: fix, commit, push, replies with footer, review draft, dashboard screenshots). Dry-run poll against NilSkilz repos worked.
- Waiting on: Rob creates the empty private repo `NilSkilz/harbourmaster` (my PAT can't create repos), then I push. Then on the Mac: BotFather bot, `./install.sh`, fill `~/.harbourmaster/config.json` (token, chat id, `repos` allowlist), `./install.sh` again.
- Open question for Rob: does Superdry have an AI-tools / code policy? Worth a look before it posts at volume.

## Ideas, not built
- Auto-post reviews once Rob has approved ~20 unedited.
- Pull Jira ticket context into reviews (Atlassian connector, read-only).
