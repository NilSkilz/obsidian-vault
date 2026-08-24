# Jarvis Telegram bridge

The phone loop. Stateless engine, stateful memory (see `Jarvis/founding-brief.md`).

## How it works

`bridge.py` long-polls Telegram. The poll loop never blocks: each message is
queued and run by a single background worker, so Telegram stays responsive while
a job runs. Every message is acked fast (typing indicator kept alive, plus a
text ack for anything that takes more than a few seconds), then handed to an
**agentic** `claude -p` run **inside `/data/memory`** (so `CLAUDE.md` persona +
vault context load for free). That run has full tools and skip-permissions, so
it actually DOES the work (edits code in `/home/jarvis/projects`, runs commands,
pushes, updates the vault) end to end, then replies with a short summary. When
it says it did something, it did.

Jobs run **one at a time**, so two agentic runs never fight over the same git
repo. Timeout is 15 min per job (reset by fold-ins). Continuity is faked
cheaply by feeding the last ~16 lines of `conversation.log` into each prompt —
no persistent Claude process, so it's model-agnostic and doesn't rack up
context cost ("stateless engine, stateful memory").

## Fold-ins (2026-08-24)

A plain text message that lands while a job is running is **folded into the
live run**, not parked behind a holding message: the prompt goes in over stdin
(`--input-format stream-json`) and stdin stays open, so the poll loop can write
Rob's mid-job message straight into the running claude process as a new user
message. The model sees it inside the current turn and adjusts, exactly like
typing into Claude Code while it works. The ack slot reopens on a fold-in so
the model's next streamed line reaches Rob as the reaction to it. Media
(voice/photo/file) still queues with the holding line (needs download or
transcription first), as does anything arriving once the run is winding down
(stdin closes at the first result) or when a queue has already formed.

The old design was one-shot chat-only: it could talk but not act, so every "on
it, give me a few" was a dead end (the process died the instant it replied).
Rebuilt agentic + async on 2026-07-09.

## Config

`~/.config/jarvis/telegram.env` (mode 600, outside the vault — never committed):
```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ALLOWED_CHAT=...   # Rob's chat id; bridge ignores everyone else
```

## State (not in git)

`~/.local/state/jarvis-bridge/`: `offset` (last update processed),
`conversation.log` (rolling buffer), `bridge.log` (activity).

## Run

`run.sh` launches it in tmux, idempotently:
```
/data/memory/Jarvis/bridge/run.sh          # start if not already up
tmux attach -t jarvis-bridge               # watch it
```

**Reboot-proof via cron** (no root needed): the `jarvis` crontab has
`@reboot run.sh` plus a `*/5 * * * * run.sh` watchdog that relaunches it if it
ever dies. Survives container reboots. (A systemd user service would be tidier
but needs a one-time root `enable-linger` — cron does the job without it.)

## Autonomy

The bridge's `claude` calls run with `--dangerously-skip-permissions` (Rob's
call, 2026-07-02), so phone-Jarvis can actually *act* — write the vault, run
commands, hit the media/HA APIs — not just chat. Blast radius is the `jarvis`
user (no root) and is locked to Rob's chat id. **Any message from that chat can
trigger arbitrary autonomous action** — that's the deal, eyes open.

## Progress heartbeats (2026-08-24)

On runs past 3 min (and again at 10), the beat is no longer a canned "still on
it": the worker run's tool calls are logged as they stream past, and a quick
no-tools `claude -p` (Sonnet) summarizes them into one natural line ("typecheck's
clean, running the tests now"). Canned wording survives only as the fallback if
the summarizer fails. Same reason the canned ack pool got demoted: canned
one-liners read as uncanny to Rob; real voice or nothing.

## Knobs

- `JARVIS_MODEL` env (default `claude-opus-4-8`) — anything that messages Rob runs Opus 4.8 or higher; background/subagent work can stay on Sonnet.
- `JARVIS_PROGRESS_MODEL` env (default `claude-sonnet-5`) — the heartbeat summarizer.
