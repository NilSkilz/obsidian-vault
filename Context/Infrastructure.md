# Infrastructure

The current, verified picture of where I live and what's around me, after the July 2026 Proxmox rebuild. Everything marked **verified** was checked against the running box on 2026-07-02. Everything marked **inherited** is carried over from pre-rebuild memory and is probably still true (external/cloud resources) but has NOT been re-confirmed on the new setup.

## Where I run (verified 2026-07-02)

- I'm in an **LXC container named `jarvis` at `192.168.1.11`**. Home dir `/home/jarvis`.
- The **memory vault is `/data/memory`** (this repo). It is NOT at the old `/home/rob/obsidian-vault` path, and there is no `/home/rob` on this box.
- **Proxmox host** is `192.168.1.2` (per CLAUDE.md). I'm a guest on it, not the host itself. No `/host` mount into this container.
- **I have root SSH to the Proxmox host** (granted by Rob 2026-07-03): `ssh proxmox` (alias in `~/.ssh/config`, key `~/.ssh/proxmox-root`). Host is PVE 9.2.3, 39GB RAM. I can create/manage LXCs myself now; the old "host goes through Rob" rule is retired. Storage note: `local-lvm` thin pool is ~79% full, so new LXC disks go on `data1-backups` (460GB dir storage, rootdir content enabled 2026-07-03).
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
| **Jarvis (me)** | 192.168.1.11 | This LXC (CT 110) |
| Seerr | http://192.168.1.12 | Media requests (CT 107, was missing from this map) |
| Tdarr | http://192.168.1.13 | Transcoding (CT 109, was missing from this map) |
| Nginx Proxy Manager | http://192.168.1.14:81 | Reverse proxy (CT 108, static IP, installed 2026-07-03) |
| Plausible | http://192.168.1.15:8000 | Web analytics (CT 111, static IP, installed 2026-07-03) |

Anything else on the LAN gets its address from the BT hub's DHCP pool (which starts above these; NPM originally leased .177 before I pinned it static).

## Media stack API keys

Repo is private and Rob is fine with these living here. Used for media status/suggestions (north-star feature). All verified reachable from this container 2026-07-02.

- **Plex:** `jLzjydWMj6xzykLFPyKp` — `X-Plex-Token` query param, e.g. `/identity?X-Plex-Token=`
- **Sonarr:** `dfbacfa36ecc4d70b1acdf44f33ef421` — API v3, `/api/v3/...?apikey=` (v4.0.19)
- **Radarr:** `74b3d479445e4e19b26bd11197d006e2` — API v3 (v6.2.1)
- **Prowlarr:** `24ad1e0e672c422b80f3573cb382b8be` — API v1 (v2.4.0)
- **SABnzbd:** `2d17dc736dfa47f491e0dc2aa918c00a` — `/api?mode=...&output=json&apikey=` (v5.0.4; note it's `/api`, not `/sabnzbd/api`)

## Nginx Proxy Manager (CT 108, installed 2026-07-03)

- LXC at **192.168.1.14** (static), built with the community-scripts helper, NPM v2.15.1 running natively (systemd `npm.service`, no Docker). 2 CPU / 2GB / 8GB on `data1-backups`.
- Admin UI: `http://192.168.1.14:81`. Login **rob@cracky.co.uk / Ylgb3sPlGzEWl4JeD5285Rrx** (set via API on install day; repo is private, Rob is fine with creds here).
- Replaces the old HA add-on NPM from the pre-rebuild setup. Proxy hosts so far: `plausible.cracky.co.uk` → `192.168.1.15:8000` (no SSL cert yet, see blockers below).
- **Blocked on Rob for external access:** (1) BT hub port forwards 80/443 → 192.168.1.14, (2) Cloudflare DNS for `*.cracky.co.uk` still points at the OLD home IP `109.148.234.141`; current WAN is `86.145.166.218`. DDNS rebuild needs a Cloudflare API token. Until both are done, Let's Encrypt issuance and all remote access stay dead.

## Plausible Analytics (CT 111, installed 2026-07-03)

- LXC at **192.168.1.15** (static), hostname `plausible`, 2 CPU / 4GB / 20GB on `data1-backups`, unprivileged with `nesting=1,keyctl=1`.
- Runs **Plausible CE v3.2.1** via the official Docker Compose stack (only supported install method) at `/opt/plausible-ce` inside the container. Docker 29.6.1. Three containers (app, Postgres, ClickHouse), all `restart=always`.
- `BASE_URL=https://plausible.cracky.co.uk`, listens on `:8000`, TLS terminates at NPM. `SECRET_KEY_BASE` is in `/opt/plausible-ce/.env`.
- **First user not yet registered** — whoever hits `/register` first owns the instance, so do this soon after external access works (or locally via `http://192.168.1.15:8000`).
- Upgrades: `cd /opt/plausible-ce && git pull && docker compose pull && docker compose up -d`.

## Tooling that did NOT survive the migration (needs rebuilding)

None of the old operational scripts or secrets are present on this box (`/home/jarvis/.claude.local` does not exist). If Rob wants any of these capabilities back, they're a rebuild job, not a config tweak. What used to exist (from pre-rebuild memory, now archived under `Archive/legacy-jarvis/`):

- **HA control** — `ha-api.sh` helper + `ha.env` (bearer token). HA REST pattern: `GET /api/states`, `POST /api/services/<domain>/<service>` with `{"entity_id": "..."}`. Rebuild target: reach HA at `192.168.1.4:8123`.
- **Telegram bridge** — custom `telegram-notify.sh` / `telegram-poll.sh` scripts (NOT the MCP plugin). Bot `@haven_ai_chatbot`, chat id `7331133695`, token was in `telegram-bridge.env`. **Durable lesson:** Telegram allows only ONE `getUpdates` consumer, so the `telegram@claude-plugins-official` plugin and a custom poller fight over the bot token (409 Conflict) and inbound silently dies. Keep the plugin disabled if the custom bridge is rebuilt.
- **Cloudflare DDNS** — `cloudflare-ddns.sh` kept `*.cracky.co.uk` pointed at the dynamic home IP. Needed because the domain points DIRECTLY at Rob's BT residential IP (not Cloudflare-proxied).
- **Todoist nudges** — `todoist-nudge.sh` (morning/afternoon executive-function nudges) + `build-queue-nudge.sh`. Creds in `todoist.env`.
- **DAKboard alerts** — `dakboard-notify.sh` posted notable alerts to the wall display (was `localhost:3006`, will differ on the new setup).

## External / cloud resources (inherited, likely still valid)

These live outside the box so the rebuild didn't touch them, but confirm before relying on them:

- **Domain:** `cracky.co.uk` — wildcard `*.cracky.co.uk` A record at Rob's dynamic home IP, **currently stale** (points at old IP `109.148.234.141` as of 2026-07-03; DDNS rebuild pending, needs Cloudflare API token). Remote access now proxied by the **standalone NPM LXC at 192.168.1.14** (the old `a0d7b954_nginxproxymanager` HA add-on is gone). Subdomains seen pre-rebuild: ha, plex, sonarr, radarr, nzb, portainer, api — none recreated yet. Adding one = NPM REST API + DNS record.
- **Trello:** wired back up 2026-07-02, creds in `/home/jarvis/.config/jarvis/trello.env` on the jarvis LXC. Live board is **"Jarvis"** — https://trello.com/b/IMUJxUvx/jarvis (board id `6981c75edb5758a1a2d689e7`, lists: Ideas, Backlog, To Do, In Progress, Review, Done). CLI is `Jarvis/bin/trello.sh` (curl+jq, no node on this box — `lists`/`cards <list>`/`move <id> <list>`/`comment <id> <text>`). Heartbeat checks the **To Do** list every run and treats cards like `Ops/Tasks.md` items. Note: the old "Jarvis-v2" board (https://trello.com/b/YkZEamyj/jarvis-v2) is now **closed/archived**, not in use. Other boards visible: PRISM (open), Order Injector, Framework v2.5 (both closed).
- **Todoist:** "Build Queue" project id `6gwgGfCq7J6hr6P6` (violet) — Rob's creative/make-projects list he picks from on demand.
- **Tethered** is AWS Amplify-deployed (cloud), live at https://tethered.me.uk — unaffected by the home rebuild.

## Projects (not migrated to this box yet, 2026-07-02)

Mission Control, Haven and Tethered source were on the old NUC at `/home/rob/Projects/...` and are **not on this container**. Paths are TBD until Rob migrates them or tells me where they now live. See `Projects/Mission Control.md`, `Projects/Haven.md`, `Projects/Tethered/overview.md`.

## History

The old NUC ("HomeServer", i3-8109U) ran HA Supervised on Debian 12 with a Docker Compose + PM2 + "hermit" always-on-daemon stack. It suffered a run of hard kernel panics in June 2026 (root cause: bad/flaky RAM, a single no-name 8GB SO-DIMM) and was retired. Everything moved to Proxmox in July 2026. The full pre-rebuild operational memory (hermit daemon architecture, session reports, the crash investigation) is preserved under `Archive/legacy-jarvis/`.
