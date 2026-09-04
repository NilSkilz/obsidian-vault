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

### 4. Apply (fully automated since 2026-08-28)
- **Standing approval from Rob (28 Aug): "Those contracts might be worth a shot, I can always back out later, so in future send an application. No need to ask me. Just let me know in the evening what was done."**
- Flow: JobServe role scores 8+ in triage → `~/contract-hunt/auto-apply.sh` writes a tailored cover note (sonnet, modelled on the two sent examples, same wording rules: never imply employment, Superdry/Tethered anonymised, rate pitched mid-to-upper in the ad range, £450 if no rate, never under £400) → wording guard grep → `apply-jobserve.js` submits with the CV PDF → result logged to `~/.local/state/jarvis-contract-hunt-applied.log` (+ `applied-ids.txt` so nothing goes twice, screenshot `out/apply-result-<id>.png`).
- Evening brief reads the applied log and lists each application sent. No live Telegram ping for strong matches any more; only a FAILED submit pings, because that needs him.
- LinkedIn-alert roles can't be auto-applied (no full ad, portal login); they still show in the digest for Rob to eyeball.
- Triage told to be strict on 8+ (explicit outside IR35, remote, TS/React/Node/AWS core), since an 8 now sends.
- Triage judgment call (Rob, 2026-08-25): numeric bar stays, but Jarvis should weigh "would Rob plausibly take this if offered" alongside the score, not just the raw number. Seniority mismatch, sub-£40/hr, or portal-only (LinkedIn Easy Apply, no recruiter email) still get filtered without a ping even at 6-7. Rob's stance: "as a numbers game, more applications is generally better" but he trusts Jarvis's judgment on which numbers are worth it, and said to revisit the bar if scores stay low for a week.

### 5. Rob's irreducible bits
- Recruiter phone calls (the market runs on them, no way round it).
- Interviews.
- Contract review when an offer lands (IR35 status determination, working practices).

## Positioning (settled 2026-08-24, revised same day)
- **Overemployed setup.** The contract runs alongside Superdry in reality, but externally Rob presents as a normal fully-available contractor. Superdry is never named to recruiters or clients: the CV anonymises it as "major UK fashion retailer", cover notes never hint at concurrent work, availability is "immediate, fully remote". Legally fine on Rob's side (no moonlighting clause, confirmed 2026-08-24); discretion is the whole game.
- Rate history: started £375, last contract £425/day (the Nov 2021 to May 2023 test-automation contract at Superdry itself, per the 2024 CV; anonymised on the new CV as "major UK fashion retailer (same client)"). Pitch £400 to £450; private floor £200 (never advertised).
- **Availability wording (Rob, 2026-08-24, supersedes the earlier "mutually agreed exit" line):** Rob is not leaving Superdry, the contract runs alongside it. Cover notes and calls simply say "available immediately, fully remote". Never mention a current engagement, an exit, or a notice period; there is nothing to explain, so don't explain it. Also: robstokes.co.uk is dead, removed from the CV header (24 Aug).
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

- 2026-08-28 (evening): **auto-apply live.** Rob granted standing approval; `auto-apply.sh` built and dry-run tested (cover generation + form preview OK on a live ad). Poll now applies to 8+ JobServe roles itself and the evening brief carries the receipt. Applications so far: TechShack FDE (24 Aug, £450), Smart-Sourcer JS-SS-124 (27 Aug, £650). No replies yet.
- 2026-08-31 (13:20): **auto-apply bar lowered to 7+** on Rob's instruction ("lower the bar to 7+"). Judge prompt reworked: 8-9 reserved for TS/React/Node/AWS bullseyes, 7 = strong-but-imperfect fit (adjacent stack, rate at edge, minor ambiguity); deal-breakers (inside IR35, umbrella, hybrid/onsite, wrong stack) stay capped at 6. Threshold changed in `contract-hunt.sh` (judge prompt + apply loop).
- 2026-08-31 (13:25): **TechShack chase sent.** One week of silence after the 24 Aug application and the 1 Sept start is tomorrow, so a short follow-up went to the role's contact address (apply.a4lq2e2hbr9y@aptrack.co, routes to Louis DaSilva), CV re-attached, sent as Rob from rob_stokes@me.com via iCloud SMTP and filed to Sent Messages. The aptrack address came out of the JobServe confirmation email (Deleted Messages, uid 1867); JobServe confirmations carry the recruiter contact block, useful for future chases.
- 2026-09-03 (14:12): **scoreboard: 4 applications sent, 0 replies.** TechShack FDE (24 Aug, £450, chased 31 Aug, still silent), Smart-Sourcer JS-SS-124 (27 Aug, £650), plus Ventula and GBV (auto-applied under the 7+ bar, exact dates not logged here). September wave so far is mostly dross (inside-IR35 London hybrid, DV-clearance, thin aggregator ads); nothing scored above 5-6 in the three 3 Sept polls.
- 2026-09-04 (22:00): **bar lowered to 6+ on Rob's instruction ("just apply to them all if they near suitable").** Judge prompt reworked: 6 = near suitable and now auto-applies (hybrid ≤2 days/week with fitting stack/rate, or IR35/remote unstated but plausible); 5 = too thin/ambiguous to apply blind (email-only listings); hard deal-breakers (stated inside IR35, umbrella, 3+ days onsite, wrong stack, rate under £350) now capped at 4 since 6 sends. Cover-note rule updated: hybrid ads get "remote-first, happy to cover the advertised onsite days" instead of a flat fully-remote claim (per Rob 2 Sept). New tool `~/tools/contract-hunt/fetch-job.js` fetches a single JobServe ad by permalink for retro-applies.
- 2026-09-04 (22:05): **retro-applied to the recent 6s: 4 more sent** (Dcoded Go/TS Manchester hybrid £465; SR2 Frontend Agentic AI London hybrid £450; RecOps Senior Node/TS Leeds 1-2d/wk £480; Scope AT Senior UI Dev, Tier 1 investment bank, 1d/wk London, pitched £1140). Skipped: La Fosse "fully remote £500-525" turned out inside IR35 in the full ad; GCS £300/day is under the £350 floor. Plus two auto-applies under the old 7+ bar this week not previously logged here: ARC React Native Tech Lead (3 Sept, £680) and IO Associates Senior Node/TS (4 Sept, £530). **Scoreboard: 10 sent, 0 replies.**

## Open questions
- ~~LinkedIn~~ resolved 24 Aug: profile names Superdry, Rob accepts the connectable dots. URL on CV header. Don't re-raise.
- ~~GitHub~~ omitted (Rob: half-finished projects, nothing worth showing).
- ~~Education~~ omitted.
- ~~LinkedIn job alerts~~ done 24/25 Aug: Rob created "TypeScript Contract Remote" (Bristol + Bude). Since 25 Aug the poll consumes them: `mail-tool.py jobmail` pulls alert mail (senders in `~/.config/jarvis/mail-job-senders.txt`, last 3 days only), LinkedIn job ids dedupe via the seen file (`li-<id>`), triaged alongside the JobServe scrape, then the emails are binned. The hourly email judge never sees those senders, so it cannot bin them first (Rob's worry on 25 Aug; it hadn't happened, but nothing prevented it). `SKIP_SCRAPE=1 DRYRUN=1 contract-hunt.sh` = quick email-only test.
- ~~Standing auto-send approval~~ granted 2026-08-28, see step 4.
- 2026-08-24 (22:50): **TechShack FDE application SENT** via JobServe (JSBH-11959, Louis DaSilva, £450/day pitched). Confirmation email to rob_stokes@me.com. Cover note reworded on Rob's request: no "day job" or "current work" language, nothing that implies employment; use "most recent engagement" / "work I've been doing for years". Apply script fix: with JS enabled the visible submit is `#btn2`, not `#btn2NoJS`. Apply form URL pattern: `https://www.jobserve.com/gb/en/W<JOBID>.jsap`.
- 2026-08-24 (21:40): funnel widened. Searches now: typescript, react contract, node aws, next.js, full stack javascript, test automation playwright, react native (was 3 terms; tonight's 21:17 pass was mostly Python/DevOps/data noise, nothing above 3/9 bar TechShack). A poll takes ~3 min per search term, so ~20 min per run; fine on the 2h cron but too long to run inline in a chat turn. Next real step is Rob's: LinkedIn job alerts (2 min in the app) and answering Louis when he rings.
