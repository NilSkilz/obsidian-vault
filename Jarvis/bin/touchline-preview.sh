#!/usr/bin/env bash
# Serve the Touchline built dist on :4173 (vite preview).
# Public at https://touchline.cracky.co.uk via NPM (host on .14) -> 192.168.1.11:4173.
# Cron: @reboot as jarvis. Safe to re-run; kills any existing preview first.
set -euo pipefail

cd /home/jarvis/projects/touchline
pkill -f "vite preview" 2>/dev/null || true
sleep 1
setsid npx vite preview >>"$HOME/.local/state/touchline-preview.log" 2>&1 &
