# Infrastructure

The current, verified picture of where I live and what's around me, after the July 2026 Proxmox rebuild. Everything marked **verified** was checked against the running box on 2026-07-02. Everything marked **inherited** is carried over from pre-rebuild memory and is probably still true (external/cloud resources) but has NOT been re-confirmed on the new setup.

## Where I run (verified 2026-07-02)

- I'm in an **LXC container named `jarvis` at `192.168.1.11`**. Home dir `/home/jarvis`.
- The **memory vault is `/data/memory`** (this repo). It is NOT at the old `/home/rob/obsidian-vault` path, and there is no `/home/rob` on this box.
- **Proxmox host** is `192.168.1.2` (per CLAUDE.md). I'm a guest on it, not the host itself. No `/host` mount into this container.
- **I have root SSH to the Proxmox host** (granted by Rob 2026-07-03): `ssh proxmox` (alias in `~/.ssh/config`, key `~/.ssh/proxmox-root`). Host is PVE 9.2.3, 39GB RAM. I can create/manage LXCs myself now; the old "host goes through Rob" rule is retired. Storage note: new LXC disks go on `data1-backups` (460GB dir storage, rootdir content enabled 2026-07-03), NOT the `local-lvm` thin pool. **The pool hit 100% on 2026-07-03 and paused the HAOS VM with io-errors** (LXCs never trim, deleted blocks accumulate). Fixed with `pct fstrim` on all CTs (100% → 64%); prevention: weekly host cron `/etc/cron.weekly/pct-fstrim` + heartbeat alerts at 85%.
- **Home Assistant** answers on **`http://192.168.1.4:8123`** (HTTP 200 confirmed). Any older reference to HA on `.2:8123` is stale.
- The vault was root-owned on first boot and had to be `chown`ed to `jarvis:jarvis` (2026-07-02) before I could write to my own memory. If a future rebuild leaves memory read-only to me, that's the fix.
- **Vault backup (set up 2026-07-02):** git remote is `github-personal:NilSkilz/obsidian-vault.git` (private) via an SSH deploy key at `~/.ssh/github-personal` (no passphrase, so cron can push). Backup is two-layer: **per-change** commits+pushes as work happens, plus a **nightly safety net** via `Jarvis/bin/git-sync.sh` (pull-rebase → commit → push) on a **`jarvis` user cron at 02:30**, logging to `~/.local/state/memory-git-sync.log`. Script hardcodes `VAULT=/data/memory`; don't move it without updating the crontab.
- No systemd `--user` bus / linger yet (no `/run/user/1000`), so always-on *services* still need a one-time root action. Cron works fine as `jarvis` without it.

## Home network map

> **Service-CT IP addressing (belt-and-braces):** **most CTs already have DHCP reservations on the Dream Machine** (Rob confirmed) — which is why they stayed on their low IPs. Seerr was the exception (no reservation → drifted on DHCP → seerr.cracky.co.uk 502'd, 2026-07-03). Fix: on top of the DM reservations, **all service CTs are now also pinned static in their `/etc/pve/lxc/<id>.conf`** (`net0 ... ip=192.168.1.X/24,gw=192.168.1.1`). Having both is fine and intended — a CT with a static config never asks DHCP, so the reservation is just a matching record; the Proxmox static always wins. (I couldn't add a DM reservation for Seerr via API — the key hits a 301/redirect wall on client writes, needs a controller session — so Seerr is held by the Proxmox static alone, which is sufficient.) `.conf` edits apply at next boot; running leases already matched so no restart was needed except Seerr (rebooted off its pool address). Backups at `*.conf.bak-ipfix`.

| Host | Address | Notes |
|---|---|---|
| UniFi Dream Machine | https://192.168.1.1 | Router/DHCP/port forwards. API key in `~/.config/jarvis/unifi.env` (`X-API-KEY` header, works on both `/proxy/network/integration/v1/` and legacy `/proxy/network/api/s/default/`), granted 2026-07-03. |
| Proxmox host | https://192.168.1.2:8006 | Hypervisor. `ssh proxmox` (root, key `~/.ssh/proxmox-root`) works — granted 2026-07-03, see above. |
| Plex | http://192.168.1.3:32400 | Media server |
| Home Assistant | http://192.168.1.4:8123 | Whole-house automation |
| Prowlarr | http://192.168.1.5:9696 | Indexer manager |
| SABnzbd | http://192.168.1.7:7777 | Usenet downloader |
| Sonarr | http://192.168.1.8:8989 | TV |
| Radarr | http://192.168.1.9:7878 | Movies |
| ~~Homepage dashboard~~ | ~~192.168.1.10~~ | **Removed 2026-07-10** (CT 106 destroyed, superseded by Tide/Mission Control). `.10` now free. Final backup on `data1-backups` (`vzdump-lxc-106-2026_07_10`). |
| **Jarvis (me)** | 192.168.1.11 | This LXC (CT 110) |
| Seerr | http://192.168.1.12:5055 | Media requests (CT 107). **Was on plain DHCP and drifted (.111/.119/.133) → seerr.cracky.co.uk 502'd; pinned static .12 in the CT config 2026-07-03 and NPM repointed.** |
| Tdarr | http://192.168.1.13:8265 | Transcoding (CT 109) |
| Nginx Proxy Manager | http://192.168.1.14:81 | Reverse proxy (CT 108, static IP, installed 2026-07-03) |
| Plausible | http://192.168.1.15:8000 | Web analytics (CT 111, static IP, installed 2026-07-03) |
| Vaultwarden | http://192.168.1.17:8080 | Password manager (CT 113, static IP, installed 2026-07-10). Public: **https://vault.cracky.co.uk** (NPM host 12, cert 2, websockets on). |
| Mission Control | http://192.168.1.16:3001 | Family site (Tide), CT 112, static IP. **Running the Tide build (`feature/tide-build`) as of 2026-07-03**, `/opt/mission-control`, systemd `mission-control.service`, single port (API + built dist). Public: **https://mc.cracky.co.uk (no basic-auth)** — the NPM access list was removed once real server-side auth landed (`app.use('/api', authGuard)`: scrypt passwords in the users table, HMAC bearer token; only `/api/auth` + the Plex art proxy are unauthenticated). Login is the app's own (starter passwords family123 / dexter1 / logan1, changeable via `/api/auth/change-password`). Auth token secret persists at `db/.auth_secret`. Local SQLite store at `db/family.sqlite` (better-sqlite3); recipe book seeded (16 meals), `CALENDAR_ICS_URL` in `.env` feeds the calendar. **Served at three domains, all → .16:3001 on cert 2, no access list (app login only):** apex **`cracky.co.uk`** (NPM host 11), **`mc.cracky.co.uk`** (host 9), **`tide.cracky.co.uk`** (host 10, repointed off the old .11:3010 preview 2026-07-03). Apex resolves because the DDNS cron patches every A record in the zone. Dev preview when needed: `http://192.168.1.11:3002` (vite) + `:3010` (built) on the jarvis LXC. |

Anything else on the LAN gets its address from the UDM's DHCP pool (which starts above these; NPM originally leased .177 before I pinned it static). Note 2026-07-03: the router is a **UniFi Dream Machine**, not a BT hub as older notes assumed (the WAN is still BT residential, hence the dynamic IP).

## Media stack API keys

Repo is private and Rob is fine with these living here. Used for media status/suggestions (north-star feature). All verified reachable from this container 2026-07-02.

- **Plex:** `jLzjydWMj6xzykLFPyKp` — `X-Plex-Token` query param, e.g. `/identity?X-Plex-Token=`
- **Sonarr:** `dfbacfa36ecc4d70b1acdf44f33ef421` — API v3, `/api/v3/...?apikey=` (v4.0.19)
- **Radarr:** `74b3d479445e4e19b26bd11197d006e2` — API v3 (v6.2.1)
- **Prowlarr:** `24ad1e0e672c422b80f3573cb382b8be` — API v1 (v2.4.0)
- **SABnzbd:** `2d17dc736dfa47f491e0dc2aa918c00a` — `/api?mode=...&output=json&apikey=` (v5.0.4; note it's `/api`, not `/sabnzbd/api`). Web UI login **rob / Tlwts46t2bApn2plc4** (set 2026-07-03 before exposing nzb.cracky.co.uk; UI had no auth before). **SAB is CT 103 at .7**, config `/root/.sabnzbd/sabnzbd.ini`. **2026-07-03: that ini (and its `.bak`) were found zeroed to null bytes — collateral from the local-lvm disk-full io-error event earlier that day — so SAB crash-looped and nzb.cracky.co.uk 502'd. Restored the ini from the 2026-07-01 vzdump (`data1-backups`), which had the intact provider creds + the same api_key; re-set the web login via `set_config`. Lesson: that fs-corruption event can silently zero a running LXC's files; the weekly vzdump is the recovery path.**

## Nginx Proxy Manager (CT 108, installed 2026-07-03)

- LXC at **192.168.1.14** (static), built with the community-scripts helper, NPM v2.15.1 running natively (systemd `npm.service`, no Docker). 2 CPU / 2GB / 8GB on `data1-backups`.
- Admin UI: `http://192.168.1.14:81`. Login **rob@cracky.co.uk / Ylgb3sPlGzEWl4JeD5285Rrx** (set via API on install day; repo is private, Rob is fine with creds here).
- Replaces the old HA add-on NPM from the pre-rebuild setup. Proxy hosts (all on wildcard cert 2, SSL forced, HTTP/2, websockets): plausible→.15:8000, ha→.4:8123, plex→.3:32400, sonarr→.8:8989, radarr→.9:7878, prowlarr→.5:9696, nzb→.7:7777, seerr→.12:5055. **Deliberately NOT exposed:** Tdarr (no auth of any kind), Proxmox UI.
- **Exposure hardening (2026-07-03):** the *arrs had auth "disabled for local addresses", and NPM's LAN IP counts as local (X-Forwarded-For is NOT trusted), so externally they were wide open — flipped all three to `authenticationRequired: enabled` via their APIs (login now required on LAN too; API keys unaffected). SABnzbd UI had no auth at all — set rob + password (see API keys section). Lesson: **"disabled for local addresses" is meaningless behind a same-LAN reverse proxy; always spoof-test with `X-Forwarded-For: 8.8.8.8` before exposing.**
- `ha.cracky.co.uk` verified working after adding NPM to HA's `trusted_proxies` (2026-07-03).
- **Wildcard cert** `*.cracky.co.uk` + apex (cert id 2, expires 2026-10-01, auto-renews) issued via **Let's Encrypt DNS-01 with the Cloudflare token**, so renewal never depends on port forwards. Future subdomains just need a proxy host attached to cert 2 — no new cert, no DNS work (wildcard A record covers them).
- **External path verified working 2026-07-03:** UDM forwards 80/443 → 192.168.1.14 (repointed the stale rules that aimed at .2), DNS current, `https://plausible.cracky.co.uk` serves publicly with valid TLS. The old UDM rule exposing port 81 (NPM admin) to WAN was **disabled deliberately** — admin UI stays LAN-only.

## Plausible Analytics (CT 111, installed 2026-07-03)

- LXC at **192.168.1.15** (static), hostname `plausible`, 2 CPU / 4GB / 20GB on `data1-backups`, unprivileged with `nesting=1,keyctl=1`.
- Runs **Plausible CE v3.2.1** via the official Docker Compose stack (only supported install method) at `/opt/plausible-ce` inside the container. Docker 29.6.1. Three containers (app, Postgres, ClickHouse), all `restart=always`.
- `BASE_URL=https://plausible.cracky.co.uk`, listens on `:8000`, TLS terminates at NPM. `SECRET_KEY_BASE` is in `/opt/plausible-ce/.env`.
- **First user not yet registered** — whoever hits `/register` first owns the instance, so do this soon after external access works (or locally via `http://192.168.1.15:8000`).
- Upgrades: `cd /opt/plausible-ce && git pull && docker compose pull && docker compose up -d`.

## Vaultwarden (CT 113, installed 2026-07-10)

- LXC at **192.168.1.17** (static in `/etc/pve/lxc/113.conf`), hostname `vaultwarden`, 2 CPU / 1GB / 8GB on `data1-backups`, unprivileged with `nesting=1,keyctl=1`.
- Runs the official **`vaultwarden/server:latest`** Docker image (the supported deployment) via Compose at `/opt/vaultwarden` inside the container. Data volume `/opt/vaultwarden/data` (SQLite + attachments + RSA keys — **this is the backup-critical dir**). `restart: always`.
- Listens `:8080` → container `:80`; TLS terminates at NPM (host 12, wildcard cert 2, `allow_websocket_upgrade` on — Vaultwarden needs WS for live sync). `DOMAIN=https://vault.cracky.co.uk`.
- Config in `/opt/vaultwarden/vaultwarden.env` (chmod 600): `ADMIN_TOKEN` is an **argon2 PHC hash** (not plaintext) — the `/admin` password is in the daily log 2026-07-10, not stored here. `SIGNUPS_ALLOWED=false` (Rob registered 2026-07-10, then locked down). Add users via `/admin` invite. To reopen: flip the env, `docker compose up -d`.
- Upgrades: `cd /opt/vaultwarden && docker compose pull && docker compose up -d`. Not covered by `updates.sh` (Docker images, same as Plausible).

## Tooling that did NOT survive the migration (needs rebuilding)

None of the old operational scripts or secrets are present on this box (`/home/jarvis/.claude.local` does not exist). If Rob wants any of these capabilities back, they're a rebuild job, not a config tweak. What used to exist (from pre-rebuild memory, now archived under `Archive/legacy-jarvis/`):

- ~~**HA control**~~ — **rebuilt 2026-07-03, with full Supervisor control**:
  - `Jarvis/bin/ha-api.sh` (states / state / call / raw) — REST, long-lived token in `~/.config/jarvis/ha.env`, 43 entities.
  - `Jarvis/bin/ha_ws.py` — stdlib websocket client. **The REST Supervisor proxy (`/api/hassio/*`) 401s even for admin tokens on HA 2026.6, but the websocket `supervisor/api` command works fully.** Usage: `ha_ws.py '{"type":"supervisor/api","endpoint":"/supervisor/info","method":"get"}'`. Long ops need `HA_WS_TIMEOUT=300`. Add-on options POSTs must send the COMPLETE options object (missing keys = validation error).
  - **SSH into HAOS**: `ssh -i ~/.ssh/ha-root root@192.168.1.4` — Terminal & SSH add-on (`core_ssh`), installed/configured by me via the websocket API, boot=auto, port 22 mapped. Gives `ha` CLI + `/config`. This is the durable path for add-ons, config edits, core restarts.
  - `configuration.yaml` now has the `http:` block trusting NPM (`192.168.1.14`, X-Forwarded-For on), added 2026-07-03, backup at `/config/configuration.yaml.bak-20260703`. `ha.cracky.co.uk` works.
- **Fleet updates (new 2026-07-03):** `Jarvis/bin/updates.sh` (`check` / `apply` / `heartbeat`). Covers the Proxmox host (apt dist-upgrade), every Debian LXC (apt upgrade via `pct exec`), and HA (add-ons, core, OS via the `ha` CLI over SSH, `--backup` on add-ons/core; an OS update reboots the HAOS VM and the script waits for it to return). Heartbeat runs it once a day via the `heartbeat` mode (20h stamp at `~/.local/state/jarvis-updates.stamp`). It never reboots the Proxmox host or LXCs itself; pending reboots and failures come out as `NEEDS-ROB:` lines. Plausible's Docker images are NOT covered (see upgrade one-liner above).
- **Telegram bridge** — custom `telegram-notify.sh` / `telegram-poll.sh` scripts (NOT the MCP plugin). Bot `@haven_ai_chatbot`, chat id `7331133695`, token was in `telegram-bridge.env`. **Durable lesson:** Telegram allows only ONE `getUpdates` consumer, so the `telegram@claude-plugins-official` plugin and a custom poller fight over the bot token (409 Conflict) and inbound silently dies. Keep the plugin disabled if the custom bridge is rebuilt.
- ~~**Cloudflare DDNS**~~ — **rebuilt 2026-07-03**: `Jarvis/bin/cloudflare-ddns.sh`, cron every 10 min as `jarvis`, token in `~/.config/jarvis/cloudflare.env`, logs to `~/.local/state/cloudflare-ddns.log`. Keeps apex + wildcard A records on the dynamic BT IP (not Cloudflare-proxied).
- **Todoist nudges** — `todoist-nudge.sh` (morning/afternoon executive-function nudges) + `build-queue-nudge.sh`. Creds in `todoist.env`.
- **DAKboard alerts** — `dakboard-notify.sh` posted notable alerts to the wall display (was `localhost:3006`, will differ on the new setup).

## External / cloud resources (inherited, likely still valid)

These live outside the box so the rebuild didn't touch them, but confirm before relying on them:

- **Domain:** `cracky.co.uk` — wildcard `*.cracky.co.uk` A record at Rob's dynamic home IP, kept current by the rebuilt DDNS cron (see above). Remote access proxied by the **standalone NPM LXC at 192.168.1.14** (the old `a0d7b954_nginxproxymanager` HA add-on is gone). Live subdomains: plausible, vault, ha, plex, sonarr, radarr, prowlarr, nzb, seerr, mc/tide/apex. Pre-rebuild ones (ha, plex, sonarr, radarr, nzb, portainer, api) not recreated yet — adding one is a single NPM proxy-host API call attached to wildcard cert 2, nothing else.
- **Trello:** wired back up 2026-07-02, creds in `/home/jarvis/.config/jarvis/trello.env` on the jarvis LXC. Live board is **"Jarvis"** — https://trello.com/b/IMUJxUvx/jarvis (board id `6981c75edb5758a1a2d689e7`, lists: Ideas, Backlog, To Do, In Progress, Review, Done). CLI is `Jarvis/bin/trello.sh` (curl+jq, no node on this box — `lists`/`cards <list>`/`move <id> <list>`/`comment <id> <text>`). Heartbeat checks the **To Do** list every run and treats cards like `Ops/Tasks.md` items. Note: the old "Jarvis-v2" board (https://trello.com/b/YkZEamyj/jarvis-v2) is now **closed/archived**, not in use. Other boards visible: PRISM (open), Order Injector, Framework v2.5 (both closed).
- **Todoist:** "Build Queue" project id `6gwgGfCq7J6hr6P6` (violet) — Rob's creative/make-projects list he picks from on demand.
- **Tethered** is AWS Amplify-deployed (cloud), live at https://tethered.me.uk — unaffected by the home rebuild.

## Projects (not migrated to this box yet, 2026-07-02)

Mission Control, Haven and Tethered source were on the old NUC at `/home/rob/Projects/...` and are **not on this container**. Paths are TBD until Rob migrates them or tells me where they now live. See `Projects/Mission Control.md`, `Projects/Haven.md`, `Projects/Tethered/overview.md`.

## Jarvis family chat bridge (2026-07-03)

The Mission Control family chat ("jarvis" screen) is wired to a real LLM **through my own Claude Code subscription**, not an API key (Rob's choice — no per-use cost). How it works:
- **`Jarvis/bin/jarvis_chat_bridge.mjs`** on the jarvis LXC (CT 110) — a tiny LAN-only HTTP service (`:3040`), **systemd `jarvis-chat-bridge.service`** (enabled, User=jarvis so it inherits my Claude Code auth). Token in `~/.config/jarvis/bridge.env`; model `claude-sonnet-5` (configurable there). It shells out to `claude -p` headless with **no tools** and cwd `/tmp` — a pure text generator, so the family (incl. kids) can't reach the filesystem or any tool through it.
- The MC server (CT 112) posts `{name, role, context, message}` to the bridge with the shared token (`JARVIS_BRIDGE_URL`/`JARVIS_BRIDGE_TOKEN` in its `.env`). It builds a compact family context (dinner, calendar, the person's chores/wallet, notice board, shopping) so replies are grounded and per-person scoped (kids get "I'll check with a grown-up"). Actions stay deterministic in the MC server (add-to-shopping writes; a kid's "can I…" logs a parent note); grounded responder is the fallback if the bridge is down.
- Uses my Claude subscription quota; gated by login + LAN + token. Restart: `ssh proxmox "pct exec 110 -- systemctl restart jarvis-chat-bridge"`.

## History

The old NUC ("HomeServer", i3-8109U) ran HA Supervised on Debian 12 with a Docker Compose + PM2 + "hermit" always-on-daemon stack. It suffered a run of hard kernel panics in June 2026 (root cause: bad/flaky RAM, a single no-name 8GB SO-DIMM) and was retired. Everything moved to Proxmox in July 2026. The full pre-rebuild operational memory (hermit daemon architecture, session reports, the crash investigation) is preserved under `Archive/legacy-jarvis/`.
