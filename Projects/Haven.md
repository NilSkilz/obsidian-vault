# Haven

**Family home management app named after Crackington Haven**

## Overview
- **Path:** not migrated to the new Proxmox box yet (was `/home/rob/Projects/haven` on the old NUC) — TBD
- **Stack:** Vite + React + TypeScript + Tailwind v4
- **Status:** In development as of Feb 2026 (split from [[Mission Control]]); not currently running post-rebuild

> **Post-rebuild note (2026-07-02):** deployment details below (Docker port, IPs like `192.168.1.2`, PM2) are pre-rebuild and no longer live. See `Context/Infrastructure.md`.

## Features
- **Weekly meal planner** with family preferences
- **Chores tracker** with kid earnings system
- **Family member selector** for personalization
- **Presence-aware meal suggestions** based on who's home

## Design Aesthetic
**Warm, family-friendly:**
- Cream/terracotta/sage color palette
- Approachable interface
- Family-focused UX

## Technical Architecture
- **Data storage:** Currently localStorage-based
- **Backend:** Can wire to database later
- **PM2 service:** `haven`
- **Health endpoint:** `/health`

## Home Assistant Integration
- **Sensors:** `sensor.haven`, `binary_sensor.haven_online`
- **Presence integration** via Mission Control API presence refresh
- **URL:** http://192.168.1.2:3004

## Family Context
**Named after:** Crackington Haven, Cornwall (family location)
**Users:**
- [[Rob]] - Setup and configuration
- [[Aimee]] - Meal planning and chores assignment  
- [[Dexter]] - Chore tracking and earnings
- [[Logan]] - Chore tracking and earnings

## Development Notes
**Lesson learned:** Dev subagent can't access host filesystem (Docker sandbox) — migration done manually

## Presence System
- **Daily refresh:** Mission Control presence API parses shared calendar
- **Away events** detection for meal planning
- **Command:** `curl -X POST http://localhost:3001/api/presence/refresh`

## Requests feature — build cards (2026-07-09)

New feature: a family "requests" board. Someone posts a request (needs a lift, needs a job covered, needs a hand), others see it and can accept it. First accept wins. Notify via web push. Cards below are self-contained so any session can pick one up cold. Move to Trello once the link is rebuilt.

> **BUILT (2026-07-09):** Cards 1-3 shipped as the **Lifts tab** in Tide (live on cracky.co.uk). Built **server-side** (SQLite `liftRequests` table + `/api/family/lifts`, race-guarded accept/deny), NOT localStorage — the old card assumed a single-device app, but kids and parents are on different devices so it has to be shared state. Spec followed Rob's lift-specific version (day defaults today, 15-min slots ≥30 min out, GPS "here", extras e.g. bike rack, note; parents accept/deny with note; first-response-wins). Verified end-to-end against the live API. **All 4 cards now done, including web push (2026-07-09):** VAPID keys generated + persisted at `db/.vapid.json` on CT 112 (gitignored, client fetches public key at runtime), `pushSubscriptions` table, `/api/family/push/{key,subscribe,unsubscribe}`, service worker `public/sw.js` (push + notificationclick → /lifts, no fetch caching), opt-in "turn on lift alerts" button in the tab. New request → notifies parents; accept/deny → notifies the kid. Files: `src/tide/TideLifts.jsx`, `src/lib/push.js`, `public/sw.js`, `server/routes/family.js` (lifts + push), `server/lib/push.js`, `server/lib/familyDb.js`, `src/lib/data.js`. **iOS caveat:** web push on iPhone/iPad only works when Tide is installed to the Home Screen (PWA) and alerts are enabled from *inside* the installed app — a plain Safari tab won't subscribe. Android Chrome + desktop work in-browser. **PWA manifest + app icons added 2026-07-09** (family is all-iPhone, so this is required): `public/manifest.webmanifest`, `public/icon.svg` (coral→rose gradient + white waves) rasterised via `sharp` to `icon-192/512.png` + `apple-touch-icon.png` (180), apple-mobile-web-app meta in `index.html`. So "Add to Home Screen" gives a clean Tide icon + standalone app, and push works once installed. Open q for Rob: a deny currently *closes* the request; could instead leave it open for the other parent (per-parent denials, small change).

- [x] **CARD 1 — Data model + storage for Requests** (done — server SQLite, not localStorage)
  - Add a `Request` type: `id`, `createdBy` (family member id), `title`, `dateTime` (ISO), `location`, `extras` (free text, optional), `note` (optional), `status` (`open` | `accepted` | `cancelled`), `acceptedBy` (member id | null), `acceptedAt` (ISO | null), `acceptNote` (optional), `createdAt`.
  - Persist in localStorage under a `haven.requests` key (matches existing localStorage pattern, see "Technical Architecture"). Keep a thin data layer (`getRequests`, `saveRequest`, `updateRequest`) so we can swap to a backend later without touching UI.
  - Reuse the existing family-member selector for `createdBy` / `acceptedBy` identity. No new auth.
  - Done when: requests can be created, read, updated in localStorage and survive refresh.

- [x] **CARD 2 — Request form (create a request)** (done)
  - Fields: date/time, location, extras, note. Title too (short summary). `createdBy` comes from the current selected family member.
  - Validate: date/time and location required; extras/note optional.
  - On submit: write an `open` Request via CARD 1's data layer, then show it in the list.
  - Warm family aesthetic (cream/terracotta/sage), matches rest of Haven. Mobile-first — this gets used on phones.
  - Done when: filling the form creates a visible open request.

- [x] **CARD 3 — Accept / deny flow** (done — atomic first-response-wins guard)
  - List view of open requests. Each shows who asked, when, where, extras.
  - A member (not the creator) can **Accept**. First accept wins: on accept, set `status=accepted`, `acceptedBy`, `acceptedAt`, optional `acceptNote`. If already accepted, block and show who took it.
  - Creator can **Cancel** their own open request (`status=cancelled`).
  - Guard the race: re-check status from the data layer at the moment of accept, not just from stale UI state.
  - Done when: two members can't both accept the same request; accepted/cancelled states render correctly.

- [x] **CARD 4 — Web push wiring** (done — VAPID + service worker + opt-in, graceful fallback)
  - Depends on CARDS 1–3. Notify relevant people: new open request → notify other members; request accepted → notify the creator.
  - Service worker + Push API. Needs a VAPID key pair and a tiny push endpoint (this is the one card that needs backend, not just localStorage — flag to Rob before starting, ties into the infra rebuild).
  - Graceful fallback: if push isn't granted, feature still works, just no notifications.
  - Done when: accepting a request pushes a notification to the creator's device.

## Tags
#project #haven #family #meal-planning #chores #react #typescript #docker #requests

## Links
- [[Mission Control]] - Sister project and presence provider
- [[Aimee]] - Primary user for meal planning
- [[Dexter]] - Chores and earnings tracking
- [[Logan]] - Chores and earnings tracking  
- [[Home Assistant]] - Smart home integration