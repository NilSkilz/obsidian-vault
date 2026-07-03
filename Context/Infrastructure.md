# Infrastructure

The current, verified picture of where I live and what's around me, after the July 2026 Proxmox rebuild. Everything marked **verified** was checked against the running box on 2026-07-02. Everything marked **inherited** is carried over from pre-rebuild memory and is probably still true (external/cloud resources) but has NOT been re-confirmed on the new setup.

## Where I run (verified 2026-07-02)

- I'm in an **LXC container named `jarvis` at `192.168.1.11`**. Home dir `/home/jarvis`.
- The **memory vault is `/data/memory`** (this repo). It is NOT at the old `/home/rob/obsidian-vault` path, and there is no `/home/rob` on this box.
- **Proxmox host** is `192.168.1.2` (per CLAUDE.md). I'm a guest on it, not the host itself. No `/host` mount into this container.
- **Home Assistant** answers on **`http://192.168.1.4:8123`** (HTTP 200 confirmed). Any older reference to HA on `.2:8123` is stale.
- The vault was root-owned on first boot and had to be `chown`ed to `jarvis:jarvis` (2026-07-02) before I could write to my own memory. If a future rebuild leaves memory read-only to me, that's the fix.
- **Vault backup (set up 2026-07-02):** git remote is `github-personal:NilSkilz/obsidian-vault.git` (private) via an SSH deploy key at `~/.ssh/github-personal` (no passphrase, so cron can push). Backup is two-layer: **per-change** commits+pushes as work happens, plus a **nightly safety net** via `Jarvis/bin/git-sync.sh` (pull-rebase → commit → push) on a **`jarvis` user cron at 02:30**, logging to `~/.local/state/memory-git-sync.log`. Script hardcodes `VAULT=/data/memory`; don't move it without updating the crontab.
- No systemd `--user` bus / linger yet (no `/run/user/1000`), so always-on *services* still need a one-time root action. Cron works fine as `jarvis` without it.

## Home network map

| Host | Address | Notes |
|---|---|---|
| Proxmox host | https://192.168.1.2:8006 | Hypervisor. No SSH key for `jarvis` by design — host-level work goes through Rob. |
| Plex | http://192.168.1.3:32400 | Media server |
| Home Assistant | http://192.168.1.4:8123 | Whole-house automation |
| Prowlarr | http://192.168.1.5:9696 | Indexer manager |
| SABnzbd | http://192.168.1.7:7777 | Usenet downloader |
| Sonarr | http://192.168.1.8:8989 | TV |
| Radarr | http://192.168.1.9:7878 | Movies |
| Homepage dashboard | http://192.168.1.10:3000 | Home dashboard (not port 80 — corrected 2026-07-03) |
| **Jarvis (me)** | 192.168.1.11 | This LXC |

## Media stack API keys

Repo is private and Rob is fine with these living here. Used for media status/suggestions (north-star feature). All verified reachable from this container 2026-07-02.

- **Plex:** `jLzjydWMj6xzykLFPyKp` — `X-Plex-Token` query param, e.g. `/identity?X-Plex-Token=`
- **Sonarr:** `dfbacfa36ecc4d70b1acdf44f33ef421` — API v3, `/api/v3/...?apikey=` (v4.0.19)
- **Radarr:** `74b3d479445e4e19b26bd11197d006e2` — API v3 (v6.2.1)
- **Prowlarr:** `24ad1e0e672c422b80f3573cb382b8be` — API v1 (v2.4.0)
- **SABnzbd:** `2d17dc736dfa47f491e0dc2aa918c00a` — `/api?mode=...&output=json&apikey=` (v5.0.4; note it's `/api`, not `/sabnzbd/api`)

## Tooling that did NOT survive the migration (needs rebuilding)

None of the old operational scripts or secrets are present on this box (`/home/jarvis/.claude.local` does not exist). If Rob wants any of these capabilities back, they're a rebuild job, not a config tweak. What used to exist (from pre-rebuild memory, now archived under `Archive/legacy-jarvis/`):

- **HA control** — `ha-api.sh` helper + `ha.env` (bearer token). HA REST pattern: `GET /api/states`, `POST /api/services/<domain>/<service>` with `{"entity_id": "..."}`. Rebuild target: reach HA at `192.168.1.4:8123`.
- **Telegram bridge** — custom `telegram-notify.sh` / `telegram-poll.sh` scripts (NOT the MCP plugin). Bot `@haven_ai_chatbot`, chat id `7331133695`, token was in `telegram-bridge.env`. **Durable lesson:** Telegram allows only ONE `getUpdates` consumer, so the `telegram@claude-plugins-official` plugin and a custom poller fight over the bot token (409 Conflict) and inbound silently dies. Keep the plugin disabled if the custom bridge is rebuilt.
- **Cloudflare DDNS** — `cloudflare-ddns.sh` kept `*.cracky.co.uk` pointed at the dynamic home IP. Needed because the domain points DIRECTLY at Rob's BT residential IP (not Cloudflare-proxied).
- **Todoist nudges** — `todoist-nudge.sh` (morning/afternoon executive-function nudges) + `build-queue-nudge.sh`. Creds in `todoist.env`.
- **DAKboard alerts** — `dakboard-notify.sh` posted notable alerts to the wall display (was `localhost:3006`, will differ on the new setup).

## External / cloud resources (inherited, likely still valid)

These live outside the box so the rebuild didn't touch them, but confirm before relying on them:

- **Domain:** `cracky.co.uk` — wildcard `*.cracky.co.uk` A record at Rob's dynamic home IP. Remote access proxied by **Nginx Proxy Manager** (the `a0d7b954_nginxproxymanager` HA add-on), per-host Let's Encrypt SSL. Subdomains seen pre-rebuild: ha, plex, sonarr, radarr, nzb, portainer, api. Adding one = drive the NPM REST API (admin creds) + a DNS record.
- **Trello:** wired back up 2026-07-02, creds in `/home/jarvis/.config/jarvis/trello.env` on the jarvis LXC. Live board is **"Jarvis"** — https://trello.com/b/IMUJxUvx/jarvis (board id `6981c75edb5758a1a2d689e7`, lists: Ideas, Backlog, To Do, In Progress, Review, Done). CLI is `Jarvis/bin/trello.sh` (curl+jq, no node on this box — `lists`/`cards <list>`/`move <id> <list>`/`comment <id> <text>`). Heartbeat checks the **To Do** list every run and treats cards like `Ops/Tasks.md` items. Note: the old "Jarvis-v2" board (https://trello.com/b/YkZEamyj/jarvis-v2) is now **closed/archived**, not in use. Other boards visible: PRISM (open), Order Injector, Framework v2.5 (both closed).
- **Todoist:** "Build Queue" project id `6gwgGfCq7J6hr6P6` (violet) — Rob's creative/make-projects list he picks from on demand.
- **Tethered** is AWS Amplify-deployed (cloud), live at https://tethered.me.uk — unaffected by the home rebuild.

## Projects (not migrated to this box yet, 2026-07-02)

Mission Control, Haven and Tethered source were on the old NUC at `/home/rob/Projects/...` and are **not on this container**. Paths are TBD until Rob migrates them or tells me where they now live. See `Projects/Mission Control.md`, `Projects/Haven.md`, `Projects/Tethered/overview.md`.

## History

The old NUC ("HomeServer", i3-8109U) ran HA Supervised on Debian 12 with a Docker Compose + PM2 + "hermit" always-on-daemon stack. It suffered a run of hard kernel panics in June 2026 (root cause: bad/flaky RAM, a single no-name 8GB SO-DIMM) and was retired. Everything moved to Proxmox in July 2026. The full pre-rebuild operational memory (hermit daemon architecture, session reports, the crash investigation) is preserved under `Archive/legacy-jarvis/`.
