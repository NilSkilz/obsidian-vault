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
cheaply by feeding recent `conversation.log` context into each prompt — no
persistent Claude process, so it's model-agnostic and doesn't rack up context
cost ("stateless engine, stateful memory").

## Topic-threaded context (2026-09-01)

Rob's design (see `topic-context-design.md`): the flat 16-line tail wasted
context when conversations bounce between topics. Now every entry in Rob's
`conversation.log` carries a topic slug prefix (`[rope]`, `[work]`,
`[jarvis-dev]`...). A quick haiku call (`JARVIS_CLASSIFY_MODEL`, ~6-8s) tags
each incoming message against the live thread list, minting new slugs for new
subjects; on any failure it falls back to the current topic, so classification
can never break the exchange. Fold-ins skip the classifier and inherit the live
run's topic.

Context per reply is three layers: the matched topic's thread (last ~20
entries, the priority context), a flat cross-topic tail (last ~8 lines, keeps
"yeah do that" working right after a switch), and a one-line index of parked
threads with last-touched stamps (plus a grep recipe to pull any of them back).
Family logs stay on the plain flat buffer.

**Memory promoter** (Rob's addition): when the classifier detects a topic
switch, a background `claude -p` run (`JARVIS_PROMOTE_MODEL`, Sonnet) sweeps
the parked thread and promotes anything durable to the vault, then commits and
pushes (with git-lock retries, since the main run may be working too). One
sweep at a time; `topics-promoted.json` tracks line counts so an unchanged
thread isn't re-swept. "general" never gets swept.

History was backfilled with `backfill_topics.py` (one-off, batched haiku,
atomic rewrite with a growth check so live appends survive; `.bak` kept).

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

- `JARVIS_MODEL` env (default `claude-fable-5`) — anything that messages Rob runs Opus-class or higher; background/subagent work can stay on Sonnet.
- `JARVIS_PROGRESS_MODEL` env (default `claude-sonnet-5`) — the heartbeat summarizer.
- `JARVIS_CLASSIFY_MODEL` env (default Haiku 4.5) — the topic tagger.
- `JARVIS_PROMOTE_MODEL` env (default `claude-sonnet-5`) — the topic-switch memory promoter.

## Family privacy: shared vault, private pockets (2026-08-29)

Anyone who isn't Rob runs in `/home/jarvis/family/<name>/`, not the vault, with a `CLAUDE.md`
copied from `family/_template/` on first use and a generated `.claude/settings.json` deny list.

- **Kids:** no tools at all, cwd `/tmp`. Pure text.
- **Adults (Aimee):** `Read,Write,Edit,Glob,Grep,WebSearch,WebFetch`. The vault `/data/memory` is
  **shared household context**: she can read and write People/, Projects/, Context/, Reference/ etc.
  Denied (read and write): `Private/Rob/`, `Daily/`, `Weekly/`, `Archive/`, `Jarvis/`, `CLAUDE.md`,
  `.git/`, other family members' `Private/<Name>/` and workspaces, plus everything else on the box
  (`~/.local`, `~/.claude`, `~/projects`, `/etc`...). Not skip-permissions, so a denied path is refused.
- **Private pockets:** `/data/memory/Private/<Name>/` per person. Rob's prompt says to put anything
  Aimee shouldn't see in `Private/Rob/` and to announce it in chat; Aimee's prompt says the same for
  `Private/Aimee/`. Rob's sessions never read `Private/Aimee/`, her workspace, or any
  `conversation-<name>.log`. Daily logs get at most "<name> used the bot".

Agreed by Rob and Aimee together on 2026-08-29 (replaces the full two-way wall from earlier that day,
which cost Aimee the Craft ERP / Saline Pump context).
