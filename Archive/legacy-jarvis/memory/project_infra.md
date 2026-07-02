---
name: project-infra
description: "Local projects — Mission Control, Haven, smart home infrastructure"
metadata: 
  node_type: memory
  type: project
  originSessionId: f648f305-92f5-4c9c-b505-25d0e8ca6e15
---

**Mission Control** — Jarvis/system monitoring dashboard (terminal/sci-fi aesthetic). Completed Feb 2026, maintenance mode. Path: `/home/rob/Projects/mission-control`. Stack: Vite + React + Tailwind + Express API. Docker ports 3001 (API), 3003 (UI). Design: mono fonts, `// PREFIX` headers, blue SVG icons, no emojis, animated thinking circles.

**Haven** — Family home management app (warm aesthetic). In development Feb 2026. Path: `/home/rob/Projects/haven`. Stack: Vite + React + TypeScript + Tailwind v4. Docker port 3004. Users: Aimee (meals), Dexter + Logan (chores/earnings). Design: cream/terracotta/sage palette.

**Home Assistant:** http://192.168.1.2:8123 (Supervised Debian 12). Devices: Tesla "Timmy", Nanoleaf Aurora, IKEA Matter/Thread, Alexa (7 devices), OctoPrint, climate. Alexa announcements preferred by Aimee over push notifications.

**Infrastructure:** Docker Compose orchestration, PM2 services, Obsidian vault at `/home/rob/obsidian-vault` as memory/source of truth (git-synced to Mac).

**Old OpenClaw removed.** Bridge server remnants at `/home/rob/Projects/openclaw-bridge` — can be cleaned up.
