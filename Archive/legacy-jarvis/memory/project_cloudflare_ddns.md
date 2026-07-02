---
name: project_cloudflare_ddns
description: "cracky.co.uk uses Cloudflare DDNS for Rob's dynamic home IP; updater script rebuilt 2026-06-10 and runs as a hermit watch"
metadata: 
  node_type: memory
  type: project
  originSessionId: d7fa0582-0e72-4447-9534-f4978d33ef55
---

`cracky.co.uk` DNS points **directly at Rob's home IP** (BT residential, dynamic — NOT Cloudflare-proxied / grey-cloud), so a Dynamic-DNS updater must keep the records current or every service behind the domain goes dark. Served via a **wildcard** `*.cracky.co.uk` A record (covers all subdomains incl. plausible, etc.) plus the apex `cracky.co.uk`.

The original updater (part of the old "openclaw" setup) was **deleted**, the home IP rotated (86.145.166.207 → .236), and on 2026-06-10 everything on the domain went unreachable until rebuilt. Symptom signature: services healthy locally, but `cracky.co.uk` resolves to a stale IP — check current public IP (`curl https://api.ipify.org`, which exits via Rob's home line from the hermit container) against `getent hosts cracky.co.uk`.

**Rebuilt updater:** `/home/rob/.claude.local/scripts/cloudflare-ddns.sh` — sources the CF API key from `/home/rob/.claude.local/secrets/cloudflare.creds` internally (var `CF_API_KEY`; never put it in a shell command — deny-listed and the outbound scanner blocks it too, see [[project_telegram_bridge]]), looks up the zone id, PATCHes only changed A records, idempotent, logs to `.claude.local/logs/cloudflare-ddns.log`. Records default `*.cracky.co.uk cracky.co.uk` (override with `CF_RECORDS`). Runs every 5 min as the hermit watch `cloudflare-ddns` (in `config.json` monitors → auto-starts each session). Host-cron backup offered (`*/5 * * * * <script>`) — independent of the hermit being up. Related: [[project_reverse_proxy]], [[project_infra]].
