# Work Context

**Rob's professional life and work environment**

## Current Employment
- **Employer:** Superdry
- **Role:** Software developer
- **Location:** Remote from Cornwall; contract says the Cheltenham office is the workplace
- **Schedule:** Written exemption (Rob + a couple of others) to 1 day/week or 2 days/fortnight in office, vs the standard 3 days/week RTO mandate. Originally a gentleman's agreement at hire (Cornwall), formalised in writing post-COVID. Keep a personal copy of that exemption off work systems.
- **The exemption evidence (found 21 Sep 2026):** Slack DM from Ryan Williams (manager), 16 Oct 2024 09:12: "the business have accepted that for you they are happy to accept on average one working day a week, this can be split however you'd like so if you wanted to do 2 days a fortnight, or 4 days in a single week and not come back for another 3 weeks, that's fine too... It was exactly what you'd proposed before so I'm glad the business have accepted it." Rob accepted in writing 17 Oct 2024 08:48 ("That is much more achievable and a huge relief"). Permalink: https://superdry-it.slack.com/archives/D02NR4FHMFD/p1729066330453019 . Negotiation trail also in that DM, 19-20 Sep 2024 (Ryan discussed with Mark). Screenshots saved 21 Sep 2026 (plus copies on Rob's phone): Ryan's offer message at `Context/attachments/ryan-rto-exemption-slack-2024-10-16.jpg`, and the full thread including Rob's acceptance of 17 Oct 08:48 and Ryan's confirmation ("Brilliant, no worries at all", 17 Oct 08:49) at `Context/attachments/rto-exemption-slack-full-thread-2024-10-16-17.jpg`. Evidence set is complete: offer, acceptance, confirmation.
- **Work style:** Prefers remote work from home in Crackington Haven
- **Pension:** Superdry workplace scheme is with **Standard Life**, plan number D4431472000 (confirmed 25 Sep 2026 from Standard Life enrolment emails, Aug-Oct 2024). Payslip line "SS Pension" = salary sacrifice: Rob £300.42/month + employer £240.33 = £540.75 total. As of Sep 2026 Rob had never registered for the online account (standardlife.co.uk, needs the plan number). Separate from his personal PensionBee pot (old pensions consolidated there Dec 2024).

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
- **What it's costing him (2026-09-01, his words):** he is "so bored of replying to people". The job has quietly become being the reading comprehension for the rest of the team, which is the one part of the craft that gives nothing back, and it is a direct driver of the contract hunt. Read his flat work moods through this lens rather than treating them as general low mood. See `Projects/Contract Hunt.md` ("Why Rob wants this").

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
