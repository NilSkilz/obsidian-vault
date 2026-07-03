# Mission Control

**Jarvis/system monitoring dashboard with terminal/sci-fi aesthetic**

## Overview
- **Repo:** `github-personal:NilSkilz/mission-control` (branch `master`; dev clone at `~/projects/mission-control` on the jarvis LXC)
- **Stack:** Vite + React + Tailwind + Express API
- **Status:** REDEPLOYED 2026-07-03 on Proxmox — CT 112 at `192.168.1.16:3001`, `https://mc.cracky.co.uk` (LAN open, external basic-auth; creds in `Context/Infrastructure.md`)

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