# Contract Hunt

**Goal:** supplement Superdry income with outside-IR35 contract work. Rob does as close to nothing as possible; Jarvis runs the pipeline. Started 2026-08-24, planning stage.

## The key insight

UK contract recruitment does not run on application portals, it runs on **recruiters and email**. JobServe applications are literally emails with a CV attached. Recruiter ads carry email addresses. LinkedIn/CWJobs alerts arrive by email. So the "anti-bot" problem mostly doesn't exist for this market: the high-converting channel (fast, tailored email replies to recruiters) has no CAPTCHA in the way, and Jarvis already has full iCloud mail access.

What we deliberately skip: scripting around bot detection on portals (LinkedIn Easy Apply, Workday etc). Two reasons: Jarvis won't build CAPTCHA evasion, and it's the low-value channel anyway. Portal spray-and-pray converts terribly for contracts; recruiter email + speed of response is what wins. Zero loss.

## Pipeline

### 1. One-time setup (the only real Rob effort)
- [x] Check Superdry employment contract for exclusivity / conflict-of-interest clause. **Cleared 2026-08-24: no moonlighting clause** (Rob confirmed).
- [ ] Contractor CV: draft written (`Projects/Contract Hunt CV.md`), needs Rob to fill career-history gaps and review once. Keep a master + tailor per application.
- [x] Day rate decision, 2026-08-24: pitch at market (£400 to £450, last rate was £425, verify against live ads per application). Rob's private walk-away floor is £200 since this is supplemental income, but we never advertise low; a cheap rate on a senior CV reads as junior, not bargain.
- [ ] Ltd company: needed for outside IR35. Agreed: incorporate when the first offer lands (takes 24h, ~£12 Companies House), not before. Parked until then.
- [ ] Set up email alerts: JobServe saved-search alerts, LinkedIn job alerts, CWJobs/Technojobs. All land in iCloud inbox which Jarvis already reads hourly.

### 2. Sourcing (fully automated)
- Email alerts from the boards land in the inbox; the hourly email check picks them up.
- Optionally add a direct JobServe RSS/search poll on cron for faster-than-alert pickup.

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
- Rate history: started £375, last contract £425/day. Pitch £400 to £450; private floor £200 (never advertised).
- Triage preference order (private, capacity is still real even if we don't say so): part-time / flexible / deliverable-based gigs first, then full-time remote outside-IR35 where the working pattern is async enough to juggle. Skip anything onsite-heavy, rigid-hours, or with heavy synchronous meeting load.

## Overemployment risk notes (for Rob, not for anyone else)
- **LinkedIn is the mismatch point.** Recruiters cross-check the CV against LinkedIn within minutes, and Rob's presumably names Superdry. Either blur it there too (title + "UK fashion retail", no company page link) or accept that anyone who looks will connect the dots. Decide before the first application goes out.
- **References:** don't offer current-employer references. Use the prior contract client and/or the SaaS products as proof of work.
- **Client-side exclusivity:** some contracts include an exclusivity or "declare other engagements" clause. Read for it at offer stage (already on the contract-review checklist). Outside-IR35 actually helps here: a genuine business-to-business supplier having multiple clients is normal and supports the IR35 position.
- **Tax is a non-issue:** PAYE at SD plus Ltd dividends/salary is standard and legal; HMRC seeing both is fine. Just means the Ltd accountant should know about the PAYE income for tax-band planning.

## Status
- 2026-08-24: plan agreed with Rob (via Telegram). Contract gate cleared (no moonlighting clause). Rate + positioning settled (above). CV draft written at `Projects/Contract Hunt CV.md`, awaiting Rob's gap-fill + one review.
- 2026-08-24 (later): Rob switched positioning to overemployed. Superdry scrubbed from CV and cover-note template (anonymised as "major UK fashion retailer"), risk notes added above. Open: Rob to decide LinkedIn treatment.

## Open questions
- Rob's pre-Superdry career history for the CV (employers, dates, roles). See TBC markers in the CV draft.
- Whether to name Tethered on the CV or describe it neutrally (see note in CV draft).
- LinkedIn: blur the Superdry name there to match the CV, or leave it and accept the connectable dots?
