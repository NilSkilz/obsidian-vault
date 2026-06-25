---
name: rob-hermit-launcher-upgrade
description: "rob-hermit container upgraded from 1.1.9→1.2.8 (py→ts); autoUpdate locked off, running on known-good commit c474926"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6469ca69-bf43-46ef-9328-d39ec86eb4cb
---

Hermit plugin auto-upgraded 1.1.9→1.2.8 (Python→TypeScript, bun runtime) during Jun 2026. Fixed bin wrappers, ran hermit-evolve to align. `autoUpdate: false` set on both `claude-code-hermit` and `claude-plugins-official` in the container volume's `settings.json` — marketplace frozen at commit `c474926`. Risk: a full config-volume reset would re-clone main HEAD (no entrypoint pinning). Rollback breadcrumbs: `*.bak-v1.1.9-20260620` in bin/, `installed_plugins.json.bak-20260620`.
