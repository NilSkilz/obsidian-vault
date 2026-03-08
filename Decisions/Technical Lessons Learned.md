# Technical Lessons Learned

**Key insights from development and system administration work**

## System Infrastructure

### OpenClaw Cron Reliability
**Problem:** OpenClaw cron unreliable for critical scheduled tasks  
**Solution:** Migrate to system crontab + `openclaw system event`  
**Result:** Much better reliability for DDNS updates, monitoring, autonomous work  
**Date:** Early 2026

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
**Best practice:** Use internal IP (192.168.1.2) not localhost  
**Context:** [[Mission Control]] dashboard monitoring  
**Reason:** More reliable for cross-container communication

### System Reliability
**DDNS:** Every 5 min with fallback IP sources  
**PodPoint monitoring:** Direct Telegram alerts for reliability  
**Overnight work:** System cron more reliable than OpenClaw cron

## Tags
#lessons-learned #technical #development #infrastructure #home-automation #ai-strategy #community-building

## Links
- [[Mission Control]] - Dashboard development lessons
- [[Haven]] - Container filesystem issues  
- [[Tethered]] - Community building and TypeScript practices
- [[Home Assistant]] - Thread/Matter commissioning
- [[Reddit Engagement]] - Community strategy insights