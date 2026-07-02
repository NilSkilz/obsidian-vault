# Rob's Memory Vault

This vault is the **source of truth** for all memory, project context, and decision logs.

## 🗂️ Structure Overview

- **[[Daily]]** - Daily memory logs and activities
- **[[Projects]]** - Active project documentation and progress
- **[[People]]** - Family, partners, and important relationships  
- **[[Decisions]]** - Technical lessons learned and decision logs
- **[[Context]]** - Domain-specific knowledge and system references
- **[[Archive]]** - Completed projects and historical information

## 🚀 Current Projects

### Primary Focus
- **[[Tethered]]** - BDSM safety platform (~20 users, freemium model)
- **[[Mission Control]]** - System monitoring dashboard (terminal aesthetic)
- **[[Haven]]** - Family management app (meals, chores, presence)

### Development Context
- **[[Jarvis Working Relationship]]** - AI collaboration standards
- **[[Technical Lessons Learned]]** - Key insights from development

## 👨‍👩‍👧‍👦 Family & People

### Core Family
- **[[Aimee]]** - Wife, home management, Alexa enthusiast
- **[[Dexter]]** - Son (15yo), chores tracker, own Echo Dot
- **[[Logan]]** - Son (12yo), family activities, calendar management

### ENM Network
- **[[Tash]]** - Rob's partner (Cinderford, office visit coordination)
- **[[Sean]]** - Aimee's Dom (Andover, ~3 week visits)

### Professional
- **[[Work Context]]** - Superdry employment, remote work balance

## 🏠 Technical Infrastructure

### Smart Home
- **[[Home Assistant]]** - Automation hub (192.168.1.4:8123)
  - Thread/Matter: IKEA devices working (ZBT-2 border router)
  - Alexa integration across all rooms
  - Tesla "Timmy" integration

### Project Architecture
- Rebuilt on Proxmox July 2026. Current layout, IPs, and what tooling still needs rebuilding: see **[[Infrastructure]]** (`Context/Infrastructure.md`). The old Docker Compose + PM2 + hermit-daemon stack is retired (archived under `Archive/legacy-jarvis/`).

## 📈 Community Building

### Reddit Strategy
- **Username:** u/RiggerWhoCodes on r/BDSMcommunity
- **Approach:** 90% helpful advice, 10% natural [[Tethered]] mentions
- **Success:** 108 upvotes on rope safety advice, building credibility

### Growth Strategy
- **FetLife presence:** TetheredApp account in 6+ groups
- **Munch organizer outreach:** Cornwall/Devon → Bristol expansion
- **Content creation:** Safety-first positioning, fire play guides

## 🔧 Development Standards

### Code Quality
- **Always:** `npx tsc --noEmit` before commits
- **Workflow:** Feature branches → PRs → Rob review → merge
- **Testing:** Well-tested, clean code, proper error handling

### AI Collaboration
- **Operating spine:** `CLAUDE.md` (voice, hard rules, working defaults, knowledge sources)
- **Communication:** Async for build tasks, responsive for quick questions

## 📊 Recent Activity

### Latest Daily Logs
- **[[2026-03-08]]** - Obsidian vault setup, wax play research, Yale lock troubleshooting
- **[[2026-03-07]]** - Major Reddit engagement session, community building

### Key Decisions
- **Migration to Obsidian:** Git-based sync for memory management
- **System cron over OpenClaw:** Better reliability for critical tasks
- **Thread/Matter:** Working setup with IPv6 forwarding

---

## 🔄 Sync Status
- **Location:** `/data/memory` in the `jarvis` LXC on Proxmox (`192.168.1.11`)
- **Workflow:** Git-versioned; edits committed here, nightly sync job commits automatically
- **Backup:** Full version history in Git

*Vault migrated to Obsidian: 2026-03-08. Moved to Proxmox: July 2026.*