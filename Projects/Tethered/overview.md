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
### [[Obedience]]
- **Price:** $60/yr
- **Focus:** Habit/task tracking, rewards/punishments, point system
- **Issues:** Buggy, no safety features

### [[BeMoreKinky]]
- **Rating:** 4.8★
- **Focus:** Discovery/compatibility, 600+ activities, scene planning
- **Gap:** No safety timer functionality

## Differentiation
**Tethered owns "safety-first" positioning** - neither competitor addresses "meeting someone new safely" use case

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
- **Always run** `npx tsc --noEmit` before committing
- Create branches off `develop`, push, create PRs
- Don't merge - [[Rob]] handles releases
- For Amplify deployments, ask Rob to link branch first

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