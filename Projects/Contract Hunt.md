# Contract Hunt

**Goal:** supplement Superdry income with outside-IR35 contract work. Rob does as close to nothing as possible; Jarvis runs the pipeline. Started 2026-08-24, planning stage.

## The key insight

UK contract recruitment does not run on application portals, it runs on **recruiters and email**. JobServe applications are literally emails with a CV attached. Recruiter ads carry email addresses. LinkedIn/CWJobs alerts arrive by email. So the "anti-bot" problem mostly doesn't exist for this market: the high-converting channel (fast, tailored email replies to recruiters) has no CAPTCHA in the way, and Jarvis already has full iCloud mail access.

What we deliberately skip: scripting around bot detection on portals (LinkedIn Easy Apply, Workday etc). Two reasons: Jarvis won't build CAPTCHA evasion, and it's the low-value channel anyway. Portal spray-and-pray converts terribly for contracts; recruiter email + speed of response is what wins. Zero loss.

## Pipeline

### 1. One-time setup (the only real Rob effort)
- [ ] Contractor CV: Jarvis drafts from known profile (TS/React, AWS incl. Amplify Gen2, Docker, e-commerce/retail domain from Superdry), Rob reviews once. Keep a master + tailor per application.
- [ ] Day rate decision: research current outside-IR35 rates for senior TS/React remote (ballpark £450 to £550/day as of mid-2026, verify against live ads before fixing).
- [ ] Check Superdry employment contract for exclusivity / conflict-of-interest clause **before** anything goes out. This is the one genuine legal gate.
- [ ] Ltd company: needed for outside IR35. Standard play is to incorporate when the first offer lands (takes 24h, ~£12 Companies House), not before. Park until then.
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

## Status
- 2026-08-24: plan agreed with Rob (via Telegram). Next concrete step: draft the contractor CV and confirm the Superdry contract check.

## Open questions
- Rate floor and minimum contract length Rob will get out of bed for.
- How many hours/week is realistic alongside Superdry + Tethered? (Affects whether to target part-time/overlap-friendly gigs or full contracts as a Superdry replacement.)
