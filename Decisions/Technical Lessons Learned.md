# Technical Lessons Learned

**Key insights from development and system administration work**

> **Note (2026-07-02):** The development lessons here (TypeScript, git flow, Thread/Matter, browser sandboxing, cron executable bit) remain valid. Some infra items predate the Proxmox rebuild and reference the retired NUC/OpenClaw/Docker stack — treat those as historical. Current infra lives in `Context/Infrastructure.md`.

## System Infrastructure

### LVM Thin Pools Fill Silently and Pause VMs
**Problem:** `pve/data` thin pool hit 100% (2026-07-03): HAOS VM paused in io-error state, LXCs (Plex, Sonarr) took ext4 write errors. Root cause: LXC disks on lvmthin never TRIM, so deleted blocks stay allocated and the pool only ever grows. The 32G jarvis CT alone held 29G of reclaimable blocks.  
**Solution:** `pct fstrim <id>` on every CT reclaimed 100% → 64% in one pass. `qm resume` un-paused the VM cleanly. Prevention: weekly `/etc/cron.weekly/pct-fstrim` on the host + heartbeat checks Data% and alerts over 85%.  
**Result:** Full outage recovered in minutes with no data loss; pool now self-maintains  
**Date:** 2026-07-03

### Auth "Disabled for Local Addresses" Is Meaningless Behind a Same-LAN Reverse Proxy
**Problem:** Sonarr/Radarr/Prowlarr with auth "disabled for local addresses" were login-free from the INTERNET once proxied, because the proxy's LAN IP is the client and X-Forwarded-For is not trusted  
**Solution:** Flip to auth-required-everywhere before exposing; always spoof-test with `curl -H "X-Forwarded-For: 8.8.8.8" https://host/` and expect a login wall  
**Result:** Caught before anyone found it; SABnzbd (no auth at all) got credentials the same way  
**Date:** 2026-07-03

### System Cron Over Agent-Managed Scheduling
**Problem:** Agent-/daemon-managed scheduling was unreliable for critical tasks (they die with the session/container)  
**Solution:** Use the host's own crontab/systemd timers for anything that must run regardless of whether an agent is up  
**Result:** Much better reliability for DDNS updates, monitoring, autonomous work  
**Date:** Early 2026 (learned on the old OpenClaw/hermit stack; principle still applies)

### Docker Container Limitations
**Problem:** Dev subagent can't access host filesystem (Docker sandbox)  
**Impact:** Manual migration required for [[Haven]] family features  
**Lesson:** Plan for container filesystem limitations in agent delegation  
**Project:** [[Haven]] development

### Browser Sandboxing Issues
**Problem:** Browser sandboxing blocks iframe + `srcDoc` for HTML rendering  
**Solution:** Serve HTML files directly instead of inline content  
**Context:** [[Mission Control]] dashboard development  
**Date:** Feb 2026

## Home Automation

### Thread/Matter Commissioning
**Problem:** Docker containers can't access BLE for Thread device pairing  
**Solution:** Use HA Companion app on phone for commissioning  
**Requirements:** IPv6 forwarding enabled (`net.ipv6.conf.all.forwarding=1`)  
**Troubleshooting:** Restart OTBR if "NoBufs" errors appear  
**Status:** Working as of Mar 2026  
**Devices:** IKEA KAJPLATS bulbs, BILRESA switch paired successfully  
**Note:** BILRESA scroll wheel not fully exposed in Matter yet (button works)

### Matter Installation Complexity
**Alternative considered:** Native Python Matter Server install  
**Assessment:** Possible but complex and still has issues  
**Decision:** Stick with OTBR approach for stability

## AI/LLM Strategy

### Model Usage Optimization
**Strategy:** Tiered approach - Haiku → Sonnet → Opus based on complexity  
**Problem:** llama-free rate-limited frequently  
**Solution:** Always have Sonnet fallback available  
**Goal:** Maximize subscription value without exceeding limits  
**Date:** Feb 2026

### Reddit Engagement Formatting
**Critical finding:** Double `\n\n` line breaks required for proper paragraphs  
**Editor preference:** Markdown mode over Rich Text for clean formatting  
**Style:** Avoid AI language ("I understand", diplomatic hedging)  
**Credibility:** Personal anecdotes add authenticity

## Development Workflows

### TypeScript Quality Control
**Mandate:** Always run `npx tsc --noEmit` before committing  
**Reason:** No TS errors in PRs  
**Process:** Create branches off `develop`, push, create PRs  
**Rule:** Don't merge - [[Rob]] handles releases  
**Amplify:** Ask Rob to link branch first for deployments

### Git Branch Management
**Standard:** Feature branches off `develop`  
**PR process:** Always create PRs for review  
**Testing:** Everything should be well-tested before PR  
**Code quality:** Clean code, proper error handling

## Community Building

### Reddit Engagement Strategy
**Effective approach:** 90% helpful advice, 10% natural product mentions  
**Timing:** First comments on posts get better engagement  
**Credibility:** Build through expertise sharing before any promotion  
**Quality over quantity:** Better to be genuinely helpful than frequent

### Growth Strategy Insights
**Effective:** Munch organizers > influencers (trusted community gatekeepers)  
**Reason:** Less pitch fatigue, more authentic trust relationships  
**Geographic approach:** Cornwall/Devon → Bristol → expand  
**FetLife tactics:** Auto-accept requests, RSVP "interested", join safety groups

### Content Creation
**Focus:** Safety-first positioning for [[Tethered]]  
**Success:** Fire play guide completed and well-received  
**Approach:** Educational content builds credibility for product mentions

## Memory Organization

### Documentation Cleanup
**Problem:** Duplicate session logs, scattered information  
**Solution:** Consolidated documentation structure  
**Result:** Better searchability and reduced redundancy  
**Date:** Feb 15, 2026  
**Migration:** To [[Obsidian]] vault structure (Mar 2026)

## Infrastructure Monitoring

### Service Health Checks
**Best practice:** Use the service's actual internal LAN IP, not `localhost`  
**Context:** [[Mission Control]] dashboard monitoring  
**Reason:** `localhost` inside a container resolves to the container, not the host/other services; the real internal IP is reliable for cross-host checks

### System Reliability
**DDNS:** Every 5 min with fallback IP sources  
**PodPoint monitoring:** Direct Telegram alerts for reliability  
**Overnight work:** System cron more reliable than OpenClaw cron

### Cron Direct-Exec Needs the Executable Bit
**Problem:** Host cron DDNS line never actually ran — `*/5 * * * * /path/cloudflare-ddns.sh` fired on schedule (journal confirmed `(rob) CMD`) but the script died instantly with EACCES (exit 126) before it could log anything. Script was mode 644 (no `+x`). Symptom: empty DDNS log with multi-day gaps despite a healthy cron daemon (pid 589) and a correctly-installed crontab.  
**Why it hid:** Cron invokes the script *directly*, which requires the executable bit. Testing with `bash script.sh` runs fine *without* `+x`, so "verified working for cron" checks missed it.  
**Solution:** `chmod +x` the script (or change the cron line to `bash /path/script.sh`).  
**Result:** Host cron DDNS now runs every 5 min independently of any agent session — closes the stale-DNS outage where `*.cracky.co.uk` went dead because coverage relied on an in-container watch that died with the session.  
**Date:** Jun 19, 2026

## Tags
#lessons-learned #technical #development #infrastructure #home-automation #ai-strategy #community-building

## Links
- [[Mission Control]] - Dashboard development lessons
- [[Haven]] - Container filesystem issues  
- [[Tethered]] - Community building and TypeScript practices
- [[Home Assistant]] - Thread/Matter commissioning
- [[Reddit Engagement]] - Community strategy insights