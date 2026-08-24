# Contract Hunt

**Goal:** supplement Superdry income with outside-IR35 contract work. Rob does as close to nothing as possible; Jarvis runs the pipeline. Started 2026-08-24, planning stage.

## The key insight

UK contract recruitment does not run on application portals, it runs on **recruiters and email**. JobServe applications are literally emails with a CV attached. Recruiter ads carry email addresses. LinkedIn/CWJobs alerts arrive by email. So the "anti-bot" problem mostly doesn't exist for this market: the high-converting channel (fast, tailored email replies to recruiters) has no CAPTCHA in the way, and Jarvis already has full iCloud mail access.

What we deliberately skip: scripting around bot detection on portals (LinkedIn Easy Apply, Workday etc). Two reasons: Jarvis won't build CAPTCHA evasion, and it's the low-value channel anyway. Portal spray-and-pray converts terribly for contracts; recruiter email + speed of response is what wins. Zero loss.

## Pipeline

### 1. One-time setup (the only real Rob effort)
- [x] Check Superdry employment contract for exclusivity / conflict-of-interest clause. **Cleared 2026-08-24: no moonlighting clause** (Rob confirmed).
- [x] Contractor CV: master written and career history backfilled from Rob's 2024 CV (received 2026-08-24). Timeline: Redsource/Redware iOS 2013-15, LimeNinja (own consultancy) 2015-19, Headforwards 2019-21, then retail contract 2021-23 → perm 2023-now. Needs one Rob review; only LinkedIn/GitHub URLs and the education line still open.
- [x] Day rate decision, 2026-08-24: pitch at market (£400 to £450, last rate was £425, verify against live ads per application). Rob's private walk-away floor is £200 since this is supplemental income, but we never advertise low; a cheap rate on a senior CV reads as junior, not bargain.
- [ ] Ltd company: needed for outside IR35. Agreed: incorporate when the first offer lands (takes 24h, ~£12 Companies House), not before. Parked until then.
- [ ] Set up email alerts: JobServe saved-search alerts, LinkedIn job alerts, CWJobs/Technojobs. All land in iCloud inbox which Jarvis already reads hourly.

### 2. Sourcing (fully automated)
- Email alerts from the boards land in the inbox; the hourly email check picks them up.
- **Live 2026-08-24:** `Jarvis/bin/contract-hunt.sh` on cron (every 2h, 08:20 to 20:20). Headless-Chrome scrape of public JobServe search (`~/tools/contract-hunt/scrape-jobserve.js`, searches: typescript / react contract / node aws, last 2 days), dedupe on job id (`~/.local/state/jarvis-contract-hunt-seen.txt`), sonnet triage scores 0-9. 8+ pings Telegram immediately, everything lands in `jarvis-contract-hunt-digest.log` which the evening brief summarises. Log: `~/.local/state/jarvis-contract-hunt.log`.

### 3. Triage (Jarvis, zero Rob effort)
- Extend the email-judge pattern: score each role against profile (stack match, remote, outside IR35 explicitly stated, rate floor, contract length).
- Dedupe across boards (same role gets posted by 5 agencies).
- Daily digest line in the evening brief; instant Telegram ping only for strong matches.

### 4. Apply (Jarvis drafts, Rob one-taps)
- Tailored short cover note (3 lines, rate, availability, right CV variant attached).
- Telegram ping: role summary + draft. Rob replies "send" and Jarvis sends from his mail.
- Once the pattern is trusted, Rob can grant standing approval for auto-send within tight rules (explicit outside-IR35, rate above floor, remote). Ask-first until then.

### 5. Rob's irreducible bits
- Recruiter phone calls (the market runs on them, no way round it).
- Interviews.
- Contract review when an offer lands (IR35 status determination, working practices).

## Positioning (settled 2026-08-24, revised same day)
- **Overemployed setup.** The contract runs alongside Superdry in reality, but externally Rob presents as a normal fully-available contractor. Superdry is never named to recruiters or clients: the CV anonymises it as "major UK fashion retailer", cover notes never hint at concurrent work, availability is "immediate, fully remote". Legally fine on Rob's side (no moonlighting clause, confirmed 2026-08-24); discretion is the whole game.
- Rate history: started £375, last contract £425/day (the Nov 2021 to May 2023 test-automation contract at Superdry itself, per the 2024 CV; anonymised on the new CV as "major UK fashion retailer (same client)"). Pitch £400 to £450; private floor £200 (never advertised).
- **Tethered/Tide stay anonymous on the CV** (Rob, 2026-08-24): neutral descriptions, no product names or URLs. He doesn't want the BDSM SaaS surfacing in a recruitment context.
- Triage preference order (private, capacity is still real even if we don't say so): part-time / flexible / deliverable-based gigs first, then full-time remote outside-IR35 where the working pattern is async enough to juggle. Skip anything onsite-heavy, rigid-hours, or with heavy synchronous meeting load.

## Overemployment risk notes (for Rob, not for anyone else)
- **LinkedIn is the mismatch point.** Recruiters cross-check the CV against LinkedIn within minutes, and Rob's presumably names Superdry. Either blur it there too (title + "UK fashion retail", no company page link) or accept that anyone who looks will connect the dots. Decide before the first application goes out.
- **References:** don't offer current-employer references. Use the prior contract client and/or the SaaS products as proof of work.
- **Client-side exclusivity:** some contracts include an exclusivity or "declare other engagements" clause. Read for it at offer stage (already on the contract-review checklist). Outside-IR35 actually helps here: a genuine business-to-business supplier having multiple clients is normal and supports the IR35 position.
- **Tax is a non-issue:** PAYE at SD plus Ltd dividends/salary is standard and legal; HMRC seeing both is fine. Just means the Ltd accountant should know about the PAYE income for tax-band planning.

## Status
- 2026-08-24: plan agreed with Rob (via Telegram). Contract gate cleared (no moonlighting clause). Rate + positioning settled (above). CV draft written at `Projects/Contract Hunt CV.md`, awaiting Rob's gap-fill + one review.
- 2026-08-24 (later): Rob switched positioning to overemployed. Superdry scrubbed from CV and cover-note template (anonymised as "major UK fashion retailer"), risk notes added above.
- 2026-08-24 (evening): Rob sent his 2024 CV as PDF. Career history backfilled into the master CV (13+ years: Redsource/Redware → LimeNinja → Headforwards → retail contract → retail perm). Rob decided Tethered/Tide stay anonymous. Bonus finds: the £375/£425 contract was at Superdry itself (test automation, Nov 2021 to May 2023, converted to perm), and he ran his own Ltd (LimeNinja) for four years, so the outside-IR35 setup is familiar ground, not a first rodeo.

- 2026-08-24 (late): sourcing pipeline built and live (see step 2). First dry run: 61 ads scraped, 1 strong hit (Forward Deployed Engineer, TechShack, £400-450 outside IR35, remote, TypeScript/Next.js, Sept to Dec, http://www.jobserve.com/guYtY). JobServe's public site scrapes fine headless, no login or CAPTCHA involved. Apply step (4) still manual: Rob says "draft it" and Jarvis writes the cover note.

- 2026-08-24 (22:30): **first application ready to send.** TechShack FDE (JSBH-11959, contact Louis DaSilva). JobServe apply is a plain ASP.NET form (email, UK status, CV upload, cover text), no CAPTCHA, no login needed. Built `~/contract-hunt/apply-jobserve.js` (fills + submits; `--dry` previews to `out/apply-preview.png`) and a md→PDF renderer (`~/contract-hunt/topdf.js`, 2-page A4 at `out/Rob Stokes CV.pdf`, strips internal notes). Cover note at `out/cover-techshack-JSBH-11959.txt`, pitched £450. Dry run verified, awaiting Rob's "send". Hourly-rate dropdown mapped to £50-65/h (≈£400-520/day).

## Open questions
- ~~LinkedIn~~ resolved 24 Aug: profile names Superdry, Rob accepts the connectable dots. URL on CV header. Don't re-raise.
- ~~GitHub~~ omitted (Rob: half-finished projects, nothing worth showing).
- ~~Education~~ omitted.
- LinkedIn job alerts: only Rob can create these (in his LinkedIn app, 2 minutes: search "TypeScript contract remote", toggle Set alert). They already pass the email judge unbinned once they arrive.
- Standing auto-send approval for applications: still ask-first (step 4 above), revisit once the drafts prove trustworthy.
- 2026-08-24 (22:50): **TechShack FDE application SENT** via JobServe (JSBH-11959, Louis DaSilva, £450/day pitched). Confirmation email to rob_stokes@me.com. Cover note reworded on Rob's request: no "day job" or "current work" language, nothing that implies employment; use "most recent engagement" / "work I've been doing for years". Apply script fix: with JS enabled the visible submit is `#btn2`, not `#btn2NoJS`. Apply form URL pattern: `https://www.jobserve.com/gb/en/W<JOBID>.jsap`.
