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
- **Trello:** board "Jarvis-v2" — https://trello.com/b/YkZEamyj/jarvis-v2. Kanban: Inbox → Todo → In Progress → Blocked → Done. Needs `trello.env` creds + CLI to drive (both gone, rebuild if wanted).
- **Todoist:** "Build Queue" project id `6gwgGfCq7J6hr6P6` (violet) — Rob's creative/make-projects list he picks from on demand.
- **Tethered** is AWS Amplify-deployed (cloud), live at https://tethered.me.uk — unaffected by the home rebuild.

## Projects (not migrated to this box yet, 2026-07-02)

Mission Control, Haven and Tethered source were on the old NUC at `/home/rob/Projects/...` and are **not on this container**. Paths are TBD until Rob migrates them or tells me where they now live. See `Projects/Mission Control.md`, `Projects/Haven.md`, `Projects/Tethered/overview.md`.

## History

The old NUC ("HomeServer", i3-8109U) ran HA Supervised on Debian 12 with a Docker Compose + PM2 + "hermit" always-on-daemon stack. It suffered a run of hard kernel panics in June 2026 (root cause: bad/flaky RAM, a single no-name 8GB SO-DIMM) and was retired. Everything moved to Proxmox in July 2026. The full pre-rebuild operational memory (hermit daemon architecture, session reports, the crash investigation) is preserved under `Archive/legacy-jarvis/`.
