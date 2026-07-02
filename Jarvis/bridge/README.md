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

Today it runs manually in tmux (survives logout, not reboot):
```
tmux new -d -s jarvis-bridge 'python3 /data/memory/Jarvis/bridge/bridge.py'
tmux attach -t jarvis-bridge     # watch it
```

The reboot-proof version (systemd user service + `enable-linger`) needs a
one-time root action in the container — a later step.

## Knobs / follow-ups

- `JARVIS_MODEL` env (default `sonnet`) — chat runs on Sonnet for cost; bump for heavier work.
- v1 is conversational + vault-read. Letting it take **actions** (write todos,
  run commands autonomously) is the next permission dial, and a deliberate
  decision for Rob — headless `claude -p` needs a permission mode set for that.
