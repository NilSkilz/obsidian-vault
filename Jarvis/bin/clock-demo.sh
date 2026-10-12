#!/bin/sh
# Static server for the clock demo page (https://clock.cracky.co.uk, NPM host 20 -> .11:4180)
cd /home/jarvis/projects/clock-demo && exec python3 -m http.server 4180 --bind 0.0.0.0
