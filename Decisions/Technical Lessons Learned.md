# Technical Lessons Learned

**Key insights from development and system administration work**

> **Note (2026-07-02):** The development lessons here (TypeScript, git flow, Thread/Matter, browser sandboxing, cron executable bit) remain valid. Some infra items predate the Proxmox rebuild and reference the retired NUC/OpenClaw/Docker stack — treat those as historical. Current infra lives in `Context/Infrastructure.md`.

## System Infrastructure

### LVM Thin Pools Fill Silently and Pause VMs
**Problem:** `pve/data` thin pool hit 100% (2026-07-03): HAOS VM paused in io-error state, LXCs (Plex, Sonarr) took ext4 write errors. Root cause: LXC disks on lvmthin never TRIM, so deleted blocks stay allocated and the pool only ever grows. The 32G jarvis CT alone held 29G of reclaimable blocks.  
**Solution:** `pct fstrim <id>` on every CT reclaimed 100% → 64% in one pass. `qm resume` un-paused the VM cleanly. Prevention: weekly `/etc/cron.weekly/pct-fstrim` on the host + heartbeat checks Data% and alerts over 85%.  
**Result:** Full outage recovered in minutes with no data loss; pool now self-maintains  
**Date:** 2026-07-03

### UniFi Won't Reserve a Fixed IP a Container Only Ever Held via Proxmox Static
**Problem:** New CT (GlitchTip, CT 106) was given a Proxmox static IP (`.20`) from birth and never did DHCP. Trying to add the belt-and-braces DM reservation (`PUT/POST rest/user … use_fixedip,fixed_ip,network_id`) kept failing with `api.err.InvalidFixedIP` — even with the CT stopped and after `forget-sta`. UniFi keeps a sticky `IP ↔ MAC` client mapping for a wired host it has seen, and refuses to convert an address the client is "already at" (outside DHCP) into a fixed reservation. Distinct error from `api.err.FixedIpAlreadyUsedByClient` (that one = a *different* live client holds the IP).  
**Solution:** Break the catch-22 by giving the MAC a real DHCP lease first: `pct set <id> -net0 …,ip=dhcp`, start, let it lease a pool IP, then reserve **that** IP (reserving a client's current lease is the textbook flow → `rc:ok`). Then set the Proxmox static back to the reserved IP. Net result: the CT lands on whatever DHCP handed out (here `.62`, not the tidy `.20` I wanted), static + reservation both pinned. Diagnostic that localises it fast: try reserving a few IPs — `InvalidFixedIP` = the target is stuck to your own MAC; `FixedIpAlreadyUsedByClient` = someone else is live on it; `rc:ok` = free and reservable.  
**Result:** Reservation created cleanly on `.62`; don't burn an hour fighting the original number — reserve the lease and move on.  
**Date:** 2026-07-17

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

### Never Pass a bcrypt Hash on a Shell Command Line
**Problem:** Resetting the Uptime Kuma admin password by generating a bcrypt hash and passing it into a remote `sqlite3 ... "UPDATE user SET password='$HASH'"` failed silently. The stored value looked plausible (`$2a$10$...`) but login always returned "Incorrect username or password", even though `bcrypt.compareSync` against the stored hash returned `true` in isolation.  
**Why it hid:** A bcrypt hash contains multiple `$` sequences (`$2a$10$...`). Sent through `ssh host "..."` (and again through `pct exec`/`docker exec`), the *remote* shell performs variable expansion on `$2a`, `$10`, etc. before sqlite ever sees the string, silently corrupting the hash. The confusion: my verification hashed and compared in-container (bare strings, no shell), so it passed; only the through-ssh write path was mangling it.  
**Solution:** Never put a `$`-laden secret on a command line that crosses a shell boundary. Write the hash to a file *inside* the target, then read it back in SQL: `UPDATE user SET password=trim(readfile('/app/data/_h'))`. Generate the hash in-container too (`docker exec ... node -e '...bcryptjs.hashSync(process.argv[1],10)...'`), passing only the plaintext (alnum, shell-safe) as argv.  
**Result:** Clean, repeatable password resets. Kept the working approach in `~/Jarvis/kuma/`.  
**Date:** Jul 10, 2026

### restic `forget` Groups by Path: a mktemp Staging Dir Defeats Retention
**Problem:** The offsite crown-jewels backup staged files in a fresh `mktemp -d /var/tmp/offsite.XXXXXX` each run. Snapshots kept accumulating and `restic forget --keep-daily 7 ...` never pruned across runs, even though everything was same-host, same-tag, same-day.  
**Why it hid:** `restic forget` groups snapshots by `host,paths` **by default**, then applies the keep-policy *within each group*. A random staging path means every run is its own single-snapshot group, so the policy keeps 1-per-group and prunes nothing. The dry-run tell was `keep 1 snapshots` printed once *per group* (twice, thrice...) instead of one combined table.  
**Solution:** Two fixes, both applied: (1) use a **stable** staging path (`/var/tmp/offsite-stage`, cleaned each run) so snapshots share one path/series; (2) run `forget --group-by host,tags` so retention is computed across all same-tag snapshots regardless of path. Verified: multiple same-day runs then collapse to restic's newest+oldest-of-period (middle runs pruned), bounded correctly.  
**Aside:** restic keeps both the newest AND oldest snapshot of each retention window (reason shows `oldest daily snapshot`), so a lone extra snapshot at the boundary is normal, not a leak.  
**Date:** Jul 11, 2026

## Tags
#lessons-learned #technical #development #infrastructure #home-automation #ai-strategy #community-building

## Links
- [[Mission Control]] - Dashboard development lessons
- [[Haven]] - Container filesystem issues  
- [[Tethered]] - Community building and TypeScript practices
- [[Home Assistant]] - Thread/Matter commissioning
- [[Reddit Engagement]] - Community strategy insights