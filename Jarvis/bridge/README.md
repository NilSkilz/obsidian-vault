# Jarvis Telegram bridge

The phone loop. Stateless engine, stateful memory (see `Jarvis/founding-brief.md`).

## How it works

`bridge.py` long-polls Telegram. Each of Rob's messages is run through
`claude -p` **inside `/data/memory`** (so `CLAUDE.md` persona + vault context
load for free), and the reply goes back. Continuity is faked cheaply by feeding
the last ~16 lines of `conversation.log` into each prompt — no persistent Claude
process, so it's model-agnostic and doesn't rack up context cost.

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

## Knobs

- `JARVIS_MODEL` env (default `claude-opus-4-8`) — anything that messages Rob runs Opus 4.8 or higher; background/subagent work can stay on Sonnet.
