# Work Context

**Rob's professional life and work environment**

## Current Employment
- **Employer:** Superdry
- **Role:** Software developer
- **Location:** Remote from Cornwall, with office in Cheltenham
- **Schedule:** Supposed to be 2 days/fortnight in office (but flexible)
- **Work style:** Prefers remote work from home in Crackington Haven

## Communication Preferences
- **Style:** Casual, sharp-witted, no fluff
- **Platform:** Telegram preferred (moved from WhatsApp)  
- **Approach:** Direct communication - Rob doesn't want hand-holding
- **Feedback:** Appreciates honest, straightforward responses

## Work-Life Integration
### ENM Context
- **[[Tash]]** — Rob's partner in Cinderford (visits when at office)
- **Office visits** often combined with partner time
- **Family understanding:** [[Aimee]] supportive of work travel + partner visits

### Side Projects Priority
- **Time allocation:** Significant focus on [[Tethered]], [[Mission Control]], [[Haven]]
- **Goal:** Build side income to eventually reduce reliance on employment
- **Approach:** Evenings and weekends dedicated to personal projects

## Professional Skills
- **Primary:** Software development  
- **Stack experience:** TypeScript, React, various web technologies
- **Deployment:** AWS Amplify Gen2, Docker, various cloud platforms
- **Philosophy:** Clean code, well-tested, proper PR workflows

## Remote Work Setup
- **Location:** Home office in Crackington Haven, Cornwall
- **Equipment:** Full development environment
- **Network:** Reliable internet for remote work and development
- **Flexibility:** Allows for intensive side project work

## Career Goals
- **Short term:** Maintain stable income while building side projects
- **Long term:** Transition to entrepreneurship with successful SaaS products
- **Strategy:** [[Tethered]] as potential primary income source
- **Backup:** Consulting/freelance development if needed

## Work Schedule Coordination
- **Calendar management:** Integrated with family calendar system
- **Travel planning:** Office visits coordinated with [[Aimee]]'s schedule
- **Project time:** Evenings after family time, weekends for major work
- **Communication:** Available during business hours via Telegram

## Jira (added 2026-08-24)
- Site: supergroupbt.atlassian.net, project **DGF (DigiForce)**, the shared cross-team project
- Rob's team board: **board 305** (https://supergroupbt.atlassian.net/jira/software/c/projects/DGF/boards/305)
- Rob's team in Jira is **Digital** (team custom field customfield_10114); DGF also holds Data, Core Technology, DevOps, Commercial Wholesale/PLM, Logistics
- The Data team's board 668 has a zombie "Data Sprint 8" open since Nov 2025, so `sprint in openSprints()` on DGF returns their stale sprint, not Rob's board. Query board-ish views with `project = DGF AND statusCategory != Done` plus the team field instead
- Project-wide open ticket count is huge (1,100+); only the recently-updated slice is real activity
- 2026-08-24: cleaned Rob's assigned tickets down to 8 real DGF items (EP/Straightline closed by Chaz, DIGI relics unassigned)
- **DGF-2757 (Bloomreach Experiments SDK), 2026-09-01:** unrefined intake ticket from Jan, March deadline dead. Charlotte's meeting with Bloomreach/Claire only produced "they still want the feature". Agreed plan: Rob does a timeboxed feasibility spike (Engagement JS SDK is client-side, unrelated to the existing server-side feed cartridge; needs anti-flicker approach, identity matching, cookie-consent handling), then uses that to force a properly refined ticket with real requirements before any build work is scheduled.
- **Working pattern with Isaac and Charlotte:** Isaac has a habit of not reading docs/investigating himself and outsourcing his own tickets upward; Charlotte's tickets tend to land unrefined (no requirements). Push back by closing out evidence on the ticket itself and handing next-steps back explicitly, rather than leaving an open-ended "let me know if you need help".

## Tags
#work #superdry #remote #software-development #career #employment

## Links
- [[Rob]] - Personal context
- [[Aimee]] - Family coordination  
- [[Tash]] - ENM partner near office
- [[Tethered]] - Primary side project
- [[Mission Control]] - Side project
- [[Haven]] - Side project
## Secure Properties tool
- Working URL: https://secure-properties-api-ch.us-e2.cloudhub.io/ (the us-e1 host in older Slack threads 504s, ignore it)
- Fallback: MuleSoft secure-properties-tool.jar locally, Blowfish/CBC default
