# Tethered

**Safety platform for BDSM/kink community**

## Overview
- **URL:** https://tethered.me.uk
- **Status:** ~20 users from Reddit/FetLife  
- **Path:** `/home/rob/Projects/Personal/tethered`
- **Stack:** React + TS + Vite, AWS Amplify Gen2, DynamoDB, Stripe, Twilio

## Features
- **Safety Timer** - Core safety feature for scenes
- **Consent Checklist** - Pre-scene negotiation tool
- **Partner Linking** - Connect with play partners
- **Task/Reward/Punishment system** - Behavioral tracking

## Business Model
**Monetisation:** Freemium model — free to use, some features may be premium
- SMS subscription planned ($1.99/mo for 5 SMS alerts)
- **Messaging:** Don't oversell "100% free" — say "free to use" instead
- SMS subscription currently disabled pending testing

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