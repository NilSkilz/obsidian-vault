#!/usr/bin/env bash
# Serve "The Mobile Vet" static website mockup on :3070.
# Public at https://mobilevet.cracky.co.uk via NPM (host on .14) -> 192.168.1.11:3070.
# Cron: @reboot as jarvis. Safe to re-run; kills any existing server first.
set -euo pipefail
pkill -f "^python3 -m http\.server 3070"  2>/dev/null || true
sleep 1
setsid python3 -m http.server 3070 --directory /home/jarvis/projects/mobile-vet >>"$HOME/.local/state/mobile-vet-preview.log" 2>&1 < /dev/null &
