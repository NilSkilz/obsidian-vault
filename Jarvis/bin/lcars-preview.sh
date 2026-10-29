#!/usr/bin/env bash
# Serve the LCARS Home Assistant dashboard mockup on :3080.
# Public at https://lcars.cracky.co.uk via NPM (host on .14) -> 192.168.1.11:3080.
# Cron: @reboot as jarvis. Safe to re-run; kills any existing server first.
set -euo pipefail
pkill -f "^python3 -m http\.server 3080"  2>/dev/null || true
sleep 1
setsid python3 -m http.server 3080 --directory /home/jarvis/projects/lcars-mockup >>"$HOME/.local/state/lcars-preview.log" 2>&1 < /dev/null &
