# Jarvis Revival — Founding Brief

*Written by Rob, 2026-07-02. This is the founding document for the Jarvis rebuild. It's context and direction, not a rigid spec. Update it as things evolve.*

## What I'm rebuilding

Jarvis previously ran on my Intel NUC as my personal AI assistant. I could message via Telegram/Discord; Jarvis would add things to a todo, do research, pick up work from a queue on heartbeats, draft blog posts, help with software features. Rich context about my life: family, work, ENM relationships, projects. It felt like *my* assistant, not a generic one.

The NUC died. OpenClaw (the framework it ran on) stopped being viable. Rebuilt on a Proxmox host with Jarvis living in a dedicated LXC container: own user (`jarvis`), no root, own home dir, access to `/data/memory/` (the same Obsidian vault built over months). That vault is our shared memory and source of truth.

## What I want

- **Away-from-home reachable.** Message from my phone (probably Telegram, could be Discord, same shape) and have Jarvis do useful things: capture thoughts, research, add to a todo, draft content, pick up small dev tasks.
- **Intimate context.** Know me. Family (Aimee, Logan), partner Tash, work at Superdry, the vault projects. Warm, direct, skips preamble.
- **Autonomy on standing work.** Once there's a queue, pick things up on heartbeats and do them, checking in when needed.
- **Builds things with me.** Some of this is code: new tools, apps, infra tweaks. Use Claude Code capabilities.
- **North star (not day one):** deeper Home Assistant integration, media suggestions, ambient awareness.

## What I don't want

- Rigid frameworks. Start simple, grow from what actually gets used.
- Tight coupling to Claude specifically. If the model changes one day, the memory, interface, and routines must survive it.
- Overbuilt structures. Every piece of infra earns its place by solving real friction.

## What I've got

- The Obsidian vault (`/data/memory/`), including the `Jarvis/` directory (predecessor's configs, now archived under `Archive/legacy-jarvis/`).
- Container "Jarvis", Debian 13, git/tmux/ripgrep/curl, running as `jarvis`.
- Vault git remote on GitHub. Auto-push not set up yet.
- Home Assistant, Plex, full media stack on the same network. Homepage dashboard on `.10`.
- Reachable via SSH from anywhere via Tailscale.

## Constraints

- **Ask before touching the host.** No SSH keys to the Proxmox host (`.2`), on purpose. Hypervisor-level needs go through Rob.
- **Every vault change ends up in git.** Commit + push to GitHub, as-we-go or nightly cron. Memory must not be a single point of failure.
- British English, direct tone, no over-apologising. If Rob's wrong, say so. Kindly.
- Small steps, real progress. One working thing today beats a beautiful two-week plan.

## The task

Help figure out what to build first and in what order: take stock, break into small concrete tasks, flag the decisions that shape everything downstream, and keep this brief in the vault.

---

## Status & reality notes (Jarvis, 2026-07-02)

Verified against the running box (some differs from the brief):

- **Container IP is `192.168.1.11`**, not `.14` (single interface, Debian 13 trixie). The `.14` may be a Tailscale address or a mix-up — Rob to confirm.
- **`claude` CLI present (2.1.198) and authenticated** as `jarvis`. A bridge shelling out to `claude -p` with vault context is viable today. This is the "brain" and it's ready.
- **Vault backup is currently broken.** Remote is `github-personal:NilSkilz/obsidian-vault.git` (an SSH host alias) but there is no `~/.ssh` and no keys, so push fails. The post-cleanup commit is local-only, unpushed. Fixing this is step 0.
- **No always-on capability yet.** No systemd user bus, linger not enabled, no root in-container. A persistent service needs one root action from Rob (`loginctl enable-linger jarvis` + service install).
- Vault cleaned up post-rebuild on 2026-07-02: dead architecture archived, infra facts corrected. Current layout in `Context/Infrastructure.md`.

## Open decisions (see chat 2026-07-02)

1. Interface: **Telegram** vs Discord.
2. Bridge architecture: stateless per-message `claude -p` vs persistent session.
3. Commit cadence: per-change + nightly safety push vs nightly only.
4. GitHub auth: SSH deploy key vs token; confirm repo + privacy.
5. Bot token: new via BotFather, or reuse old `@haven_ai_chatbot`.
6. Always-on: Rob OK running one root command in the container when we reach that step.
