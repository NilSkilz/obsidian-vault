#!/usr/bin/env bash
# Serve the Twisted Boudoir website mockup (built dist) on :4620.
# Public at https://twisted.cracky.co.uk via NPM (host on .14) -> 192.168.1.11:4620.
# Cron: @reboot as jarvis. Safe to re-run; kills any existing server first.
set -euo pipefail
pkill -f "http\.server 4620" 2>/dev/null || true
sleep 1
setsid python3 -m http.server 4620 --directory /home/jarvis/projects/twisted-boudoir-mockup/dist >>"$HOME/.local/state/twisted-preview.log" 2>&1 < /dev/null &
