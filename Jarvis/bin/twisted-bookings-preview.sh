#!/usr/bin/env bash
# Serve the Twisted Boudoir bookings app (vite preview + dev/server.ts LAN backend) on :3020. LAN only.
# Cron: @reboot as jarvis. Safe to re-run. Data lives in the project's .data/db.json.
set -euo pipefail
cd /home/jarvis/projects/twisted-boudoir
pkill -f "projects/twisted-boudoir/node_modules/.bin/vite preview" 2>/dev/null || true
sleep 1
setsid npx vite preview --host 0.0.0.0 --port 3020 --strictPort >>"$HOME/.local/state/twisted-bookings-preview.log" 2>&1 < /dev/null &
