#!/usr/bin/env bash
# Serve the Liaisons LAN build (vite preview + the dev/server.ts game backend) on :3010.
# Public at https://liaisons.cracky.co.uk via NPM (host on .14) -> 192.168.1.11:3010.
# Cron: @reboot as jarvis. Safe to re-run; kills only the existing Liaisons preview first.
# Rooms persist in the project's .data/rooms.json, so a restart doesn't end a game.
set -euo pipefail

cd /home/jarvis/projects/liaisons
pkill -f "projects/liaisons/node_modules/.bin/vite preview" 2>/dev/null || true
sleep 1
setsid npx vite preview --host 0.0.0.0 --port 3010 --strictPort >>"$HOME/.local/state/liaisons-preview.log" 2>&1 < /dev/null &
