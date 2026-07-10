# Mission Control

**Jarvis/system monitoring dashboard with terminal/sci-fi aesthetic**

## Overview
- **Repo:** `github-personal:NilSkilz/mission-control` (branch `master`; dev clone at `~/projects/mission-control` on the jarvis LXC)
- **Stack:** Vite + React + Tailwind + Express API
- **Status:** LIVE on Proxmox running the **Tide** family site — CT 112 at `192.168.1.16:3001`, `https://mc.cracky.co.uk` (no basic-auth; **real server-side login**, starter passwords in `Context/Infrastructure.md`). Runs `feature/tide-build`.

> **DEPLOY — read this before touching the app (2026-07-09).** The live site (`cracky.co.uk` / `mc.` / `tide.`) is served by **CT 112 (192.168.1.16)** from **`/opt/mission-control`** via systemd `mission-control.service`, serving the **built** `dist/`. The `~/projects/mission-control` checkout on the jarvis LXC is **only a dev preview (`:3002`)** — editing it does NOT change the live site. To ship: commit + push to `feature/tide-build`, then run **`Jarvis/bin/deploy-tide.sh`** (reaches CT 112 via the Proxmox host with the `proxmox-root` key + `pct exec`, runs `/root/deploy-tide.sh`: pull → `npm run build` → restart service → verify). ~10s. Rob's directive (2026-07-09): **no branches, no PRs — commit straight to `feature/tide-build` and deploy.** (Supersedes the "single Tide PR awaiting review" note below.)
> **Rename (2026-07-09):** the app is now just **"Tide"** everywhere user-facing — browser title, favicon 🌊, header/login/loading wordmark (was "stokeshq"). Server-side `mission_control` identifiers/health keys left as-is (functional, not user-facing).

> **Tide build (2026-07-03 →):** MC is now the family's home surface (replaces [[Haven]]), Tide design signed off. **Cards 1-10 built** on branch `feature/tide-build` (stacks card 1's SQLite store; the single Tide PR, awaiting Rob's review/merge; not yet deployed to CT 112). Card 11 (hallway display) parked. Built: Tide shell (theme tokens + real-sun day/night crossfade for Crackington Haven, nav, login, sci-fi pages relocated to `/system`), home, chores/wallet/approvals, notes (targeting/pin/expiry/receipts), calendar (ICS backend `server/lib/icsCalendar.js` + `/api/family/calendar`), meals+shopping (16-meal catalogue carried over — the "~200" was aspirational), cinema (real Plex + local film-request approval + Seerr deep link), house (config-driven HA allow-list `src/tide/houseConfig.js`; HA is sparse — only living/snug lights exist), jarvis chat (grounded, no LLM). Design system in `src/tide/tide.css`. **Live preview:** http://192.168.1.11:3002 (LAN) / https://tide.cracky.co.uk (TLS). Still no `gh`/token on the LXC (PR via compare link).

> **Redeploy notes (2026-07-03):** runs the `feature/proxmox-redeploy` branch (PR open) — service health checks moved to per-LXC IPs (env-overridable), Express serves the built frontend on one port, Amplify made optional. The AWS Amplify backend (DynamoDB, family chores/meals data) is STUBBED — those pages fall back to mocks. The repo README/CLAUDE.md still describe the pre-pivot family-dashboard era; trust the code, not the docs. Old-NUC deployment details below are historical.

## Features
- **Environment cards** with sparkline graphs (temp/power/solar)
- **Tesla widget** with charge status for "Timmy"
- **Weather + calendar** integration
- **Service health monitoring** (Plex, Radarr, Sonarr, Overseerr, PM2 services)
- **Network stats** from Dream Machine (devices, uptime, cumulative traffic)
- **Agent control page** (`/agents`) showing sub-agent sessions
- **Animated concentric circles** for "AI thinking" visual

## Design Aesthetic
**Terminal/sci-fi style:**
- `// PREFIX` headers
- Mono fonts
- Blue SVG icons
- No emojis
- Animated thinking circles

## Technical Notes
- **Service health checks** use internal IP (192.168.1.2) not localhost
- **Docker orchestration** via `/home/rob/Projects/docker-compose.yml`
- **Health checks** on `/health` endpoints
- **Credentials** in `/home/rob/Projects/.env`

## Home Assistant Integration
- **Sensors:** `sensor.mission_control_api`, `binary_sensor.mission_control_online`
- **URL:** http://192.168.1.2:3003

## Evolution
### Feb 2026 - System Dashboard Overhaul
**Pivot:** Changed from family dashboard to Jarvis/system monitoring
- Family features moved to [[Haven]]
- Focus on system health and monitoring
- Terminal aesthetic implementation

## Tags
#project #mission-control #dashboard #monitoring #react #typescript #docker

## Links
- [[Haven]] - Family app (split from Mission Control)
- [[Home Assistant]] - Integration and sensors
- [[Tethered]] - Sister project
- [[Docker]] - Container orchestration