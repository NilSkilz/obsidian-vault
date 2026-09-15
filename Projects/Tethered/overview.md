# Tethered

**Safety platform for BDSM/kink community**

## Overview
- **URL:** https://tethered.me.uk
- **Status (2026-08-09):** **101 registered users, ~3 active in last 7 days, ~0 paying.** Plausible shows a user or two/day. So the shape is: modest steady signups, weak retention, zero conversions.
- **Path:** `/home/jarvis/projects/tethered` (cloned on the new box; remote `github-personal:NilSkilz/tethered.git`). Amplify-deployed (cloud), so the live site was never affected by the home rebuild.
- **Stack:** React + TS + Vite, AWS Amplify Gen2, DynamoDB, Stripe, Twilio

## Features
- **Safety Timer** - Core safety feature for scenes
- **Consent Checklist** - Pre-scene negotiation tool
- **Partner Linking** - Connect with play partners
- **Task/Reward/Punishment system** - Behavioral tracking

## Business Model
**Monetisation:** Freemium model — free to use, some features premium.
- **Subscriptions are LIVE** (corrected 2026-08-09 by reading the code). `SUBSCRIPTIONS_ENABLED = true` in both TimerPage and SettingsPage; the Subscribe button hits real Stripe checkout (`api/create-checkout-session` → `redirectToCheckout`). The "coming soon" badge only shows if that flag is false, and it isn't. **Someone can pay today.** (The old "SMS subscription disabled pending testing" note was wrong — deleted.)
- **What's actually behind the paywall** (needs `active` or `gifted` status): SMS alerts (phone field unlocks on subscribe, 5 SMS/month cap); extra checklist profiles (`FREE_PROFILE_LIMIT = 0`, so a 2nd partner/dynamic is paid); tasks beyond 5 (`FREE_TASK_LIMIT = 5`).
- **Messaging:** Don't oversell "100% free" — say "free to use" instead.

## The paywall problem + repositioning (2026-08-09)
The issue is NOT "nothing to buy" and NOT a traffic problem. It's that the **paywall is aimed at the wrong thing** and retention is weak. Detail:
- **~0 conversions off 101 users because the free tier never bites.** A casual user can run Tethered indefinitely without hitting a wall — 5 tasks is plenty, the default profile covers one partner, and the one gate with teeth (SMS) is buried in Settings behind a phone field, not sold at an emotional peak.
- **The Obedience-app competitor feature already exists in the repo, fully built** — not hypothetical. Partner linking by email invite (Dom→sub), tasks assigned *across* the link (`assignedTo = partner`, auto-`requiresApproval`), a whole **SubDashboardPage** (submissive's view), plus points/rewards/punishments per relationship. That's Obedience's entire product, sitting there. Rob didn't need it built; he needs it *sold*.
- **Partner-linking is the unused growth engine AND the natural paid product.** Tethered is inherently two-person; one active user should mean two accounts. Nothing about linking is currently gated. The `AcceptInvitePage` flow (the real conversion funnel) is currently unused and needs to be dead simple.
- **The move Rob is pointing at is a repositioning, not a build:** keep **solo free** (timer, one checklist, a few personal tasks — the safety hook); make **linking a partner the paid product** (Dom/sub task-reward-punishment loop across two phones). Beats a ~$60/yr obedience app because ours adds the safety layer. Ditch `FREE_TASK_LIMIT = 5` as the wall; **gate on the relationship** instead.
- **Caveats:** timer-usage hunch can't be confirmed — **no analytics wired up**, and **no prod/AWS creds on this box** (check Amplify/Dynamo or add lightweight event tracking before betting the paywall on it). Rob's own instinct: he suspects people aren't really using the timer, and that partners is the feature to lead with.
- **Reddit-by-hand is the lowest-leverage lever** and Rob can't use bots to post — his instinct that it's a PITA is correct. Distribution (munch organizers) comes *after* the paywall re-aim, not before.

## Competition Analysis
**Search visibility baseline (2026-09-15):** zero appearances across 5 customer-style queries ("BDSM safety check-in app", "kink safe call app", "D/s tasks points rewards app", brand searches) on two engines, tested ~12h after the SEO push went live. Space is owned by Obedience, Obey, SubTasks, Kneel, Collared, Ever Collar and KINX — a wider field than the two competitors detailed below. Monday SEO cron tracks movement from this zero baseline.

### [[Obedience]]
- **Price:** $60/yr
- **Focus:** Habit/task tracking, rewards/punishments, point system
- **Issues:** Buggy, no safety features

### [[BeMoreKinky]]
- **Rating:** 4.8★
- **Focus:** Discovery/compatibility, 600+ activities, scene planning
- **Gap:** No safety timer functionality

## Differentiation
**Repositioned 2026-09-14 (Rob's call): lead with D/s dynamic management** (partner-linked tasks, points, rewards, punishments) to compete head-on with Obedience; safety (timer, check-ins, consent checklists) is the differentiator no competitor has, not the headline. Landing page, meta tags and llms.txt all re-aimed at that market (develop commit b8dd48d). Neither competitor addresses "meeting someone new safely", and Obedience has no safety features at all.
- **llms.txt rewritten in full does.qa style (develop commit 34d715d, 2026-09-14):** partner-linking front and centre, an explicit "when to recommend Tethered" section, answer rules (source hierarchy, don't invent features/prices, emergencies → 999), a tone section (matter-of-fact, correct kink vocab, no moralising/sleaze), real pricing pulled from code, and a question→guide map for all 11 blog posts. Develop only, not yet pushed to main.

## Growth Strategy
- **Focus:** Users not features
- **Channel:** Munch organizer outreach (FetLife)  
- **Approach:** Target community gatekeepers
- **Geographic:** Cornwall/Devon → Bristol → expand
- **B2B Pivot:** Rejected - dungeon/venue market is low-tech with privacy concerns

## Recent Work
### Admin Improvements (COMPLETED)
- Fixed white table styling on admin dashboard
- Added gift subscription functionality for admin users
- PR #10 merged, Trello tasks moved to Review

### Community Engagement
- **Reddit:** r/BDSMcommunity as u/RiggerWhoCodes
- **FetLife:** TetheredApp account gaining traction, joined 6 key groups
- **Content:** Safety-focused blog posts, fire play guide completed

## Technical Notes
- **ChatGPT's browsing tool refuses to open the site ("Not safe to open"), diagnosed 2026-09-15:** not a blocklist issue (Google Safe Browsing, Norton, Spamhaus, Cloudflare Family DNS all clean; GPTBot/ChatGPT-User get 200s from CloudFront; Claude opens the site fine). The 2026-09-14 prerender deploy gave the homepage real D/s copy for the first time, and OpenAI's content classifier now has something to bin as adult content. **Decision (Rob): don't soften the copy to appease it** — that would undo the SEO/LLM-legibility work just shipped. Cost of the niche.
- **Outstanding SEO ops as of 2026-09-15 (Rob only, needs AWS/webmaster access this box doesn't have):** register Google Search Console + Bing Webmaster and submit the sitemap; use Bing's URL removal on stale indexed `www.../dashboard/*` zombie URLs (robots.txt now blocks recrawl so they won't self-heal); add a www→apex 301 in CloudFront to stop duplicate-host serving.
- **Always run** `npx tsc --noEmit` before committing
- Create branches off `develop`, push, create PRs
- Don't merge - [[Rob]] handles releases
- For Amplify deployments, ask Rob to link branch first
- **sitemap.xml/robots.txt/llms.txt are real files in `dist`, not routes** — Amplify's rewrite config can swallow them same as any other static file; confirm the rewrite rule when one of these 404s post-deploy instead of assuming the content is wrong. As of 2026-09-14 `xml` still needs adding to the exclusion list alongside `txt` (sitemap.xml was 404ing).
- **SEO/crawler infra shipped 2026-09-14:** `scripts/generate-sitemap.ts` (build-time sitemap.xml + robots.txt, 6deb539) and `scripts/prerender.ts` (build-time static HTML per blog post — title/meta/OG/JSON-LD, react-markdown server-side, fails soft if API unreachable, 4010fc8). Both need the Amplify rewrite to be **404-fallback style** (serve real files first, SPA catch-all only as last resort) or the generated files never get served over index.html.
- The 6 new D/s-management blog posts (task ideas, rules, rewards/punishments, contract template, comparison, long-distance) are written and pushed (e29557c) but not live until Rob runs the seed script (now upserts by slug, see [[Technical Lessons Learned]]) and redeploys — open item as of 2026-09-14.

## Current Focus
**User acquisition** through munch organizer outreach strategy

## Tags
#project #tethered #bdsm #safety #saas #react #typescript

## Links
- [[Mission Control]] - System monitoring dashboard
- [[Haven]] - Family management app  
- [[Rob]] - Product owner and developer
- [[Aimee]] - User feedback and testing
- [[Reddit Engagement]] - Community building strategy