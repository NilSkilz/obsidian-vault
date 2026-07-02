---
name: ""
metadata: 
  node_type: memory
  title: "Project: DAKboard Alert Surface"
  slug: project_dakboard_alerts
  type: project
  created: 2026-06-08T00:00:00+00:00
  tags: 
    - dakboard
    - monitoring
    - alerts
    - wall-display
  originSessionId: e6e7d446-30d0-4e98-9622-82f8d4ba5ead
---

# DAKboard Alert Surface

## Overview
DAKboard running at `http://localhost:3006` is used as a proactive alert display for notable events — service down, disk low, etc.

## How to Post
Use `/home/rob/.claude.local/scripts/dakboard-notify.sh`:

```bash
dakboard-notify.sh "<text>" [info|alert|success]
```

## Rule
Jarvis decides what's worth posting. When heartbeat or monitoring detects something notable (not routine), POST to DAKboard in addition to any Telegram notification.

## Why
Rob has DAKboard on his wall display and wants Jarvis to surface important alerts there — not just in Telegram. It's a passive, always-visible surface for at-a-glance status.
