---
name: homeserver-thermal-problem
description: "HomeServer (i3-8109U NUC) thermal context — turbo disabled, watchdog live; root cause of crashes later confirmed as bad RAM"
metadata: 
  node_type: memory
  type: project
  originSessionId: 4c0c1f9b-fd3f-4f30-a1c3-c2c6c379f430
---

HomeServer runs `disable-turbo.service` (writes `intel_pstate/no_turbo=1` on boot, caps CPU at 3.0GHz). Thermal watchdog cron runs every minute, logs to `~/.claude.local/logs/thermal.log`, Telegram-alerts at pkg ≥98°C. HA sensors `sensor.homeserver_cpu_package_temp` / `sensor.homeserver_pch_temp` with automation alert >95°C for 2 min. Root cause of the Jun 2026 crash series was bad RAM (kernel stack-protector panics), not thermal — see `homeserver-crash-2026-06-23` memory.
