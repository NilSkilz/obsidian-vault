---
title: OpenClaw-Era Projects Review
created: 2026-06-04T00:00:00+00:00
source: jarvis-agent
tags: [infrastructure, review, docker]
---

# OpenClaw-Era Projects Review

Survey conducted 2026-06-04. All projects found under `/home/rob/Projects/Personal/apps/`.

---

## Projects Surveyed

### 1. Mission Control
**Path:** `/home/rob/Projects/Personal/apps/mission-control`  
**Port:** 3001 (API), 3003 (Frontend)  
**Status:** Active — most recently developed app  
**Last commit:** 2026-03-09 (`Merge branch 'feature/time-ambient-themes-final'`)  
**Git:** Yes (49 commits since 2024)  
**Docker:** Yes — Dockerfile + in docker-compose.yml  

**Stack:**
- Frontend: React + Vite + Tailwind CSS + Radix UI
- Backend: Express 4 (Node.js) serving on port 3001
- Database: AWS Amplify Gen2 + DynamoDB (eu-west-1) for chores/users; JSON flat-files in `db/` for meals, shopping, presence, videos
- Integrations: Home Assistant (WebSocket + REST), iCloud CalDAV, Todoist CLI, wttr.in weather

**Features:**
- Chore management with earnings tracking (DynamoDB-backed)
- Meal planning with ~200-recipe database
- Shopping lists
- Calendar (iCloud CalDAV)
- Home Assistant dashboard widgets
- Video library (TheDuchy media mount)
- Agents page, timeline, seasonal/ambient themes
- OpenClaw route (`/api/openclaw`) still present

**Assessment:** The flagship family app. Actively developed and Dockerised. The chores/earnings system lives in AWS DynamoDB/Amplify which creates a hard external dependency and requires AWS credentials for local dev. The video library requires a bind mount from the host filesystem (`/usr/share/hassio/media/Media/TheDuchy`).

**Recommendation: KEEP — primary family app, maintenance mode is appropriate.**

---

### 2. Haven
**Path:** `/home/rob/Projects/Personal/apps/haven`  
**Port:** 3004  
**Status:** Active but partially complete — no git history, files last modified April 2026  
**Git:** No  
**Docker:** Yes — Dockerfile + in docker-compose.yml  

**Stack:**
- Frontend only: React + Vite + TypeScript + Tailwind v4
- No backend of its own — calls Mission Control's API (`localhost:3001/api` or `api.cracky.co.uk/api`)
- Data: Meals/shopping/recipes backed by Mission Control's `/api/haven/*` routes (flat JSON files in `db/haven/`); chores fall back to localStorage

**Features:**
- Home dashboard with family member selector (Rob, Aimee, Dexter, Logan)
- Weekly meal planner
- Shopping list
- Chores tracker with earnings (localStorage fallback — no server-side persistence yet)
- Calendar (calls Mission Control `/api/calendar/events`)
- Presence awareness (calls Mission Control `/api/presence`)

**Assessment:** Haven is a **warm-aesthetic family frontend** that delegates all data to Mission Control. It is essentially Mission Control's family-facing UI — complementary rather than competing. The chores system uses localStorage fallback, meaning chore data does not persist across devices or sessions when Mission Control is unreachable.

**Key gap:** Haven chores/completions/earnings have no server-side endpoints. Mission Control's haven routes only cover meals/recipes/shopping.

**Recommendation: KEEP — but clarify its role. Two options:**
- **Option A (Merge):** Fold Haven's pages into Mission Control as a `/family` route subset with the warm aesthetic. Eliminates the separate deployment and the chores localStorage gap.
- **Option B (Extend):** Add chores/completions/earnings endpoints to Mission Control's `/api/haven/` routes, aligning Haven with Mission Control's DynamoDB backend. Haven remains a separate Docker container (warm UI) talking to Mission Control (the API).

Option B is lower risk and keeps the aesthetic separation intact. Priority: add server-side chores persistence to Haven.

---

### 3. HomeIntel
**Path:** `/home/rob/Projects/Personal/apps/HomeIntel`  
**Port:** 5173 (via `proxy.mjs`), internal server also on 3001  
**Status:** Partial — Phase 4 README present, no git history, files last modified April 2026  
**Git:** No  
**Docker:** No Dockerfile found  

**Stack:**
- Frontend: React + Vite + TypeScript + Tailwind CSS + Radix UI
- Backend: TypeScript Express server (`server/index.ts`) with WebSocket support
- Dependencies: `@anthropic-ai/sdk` (Claude AI for gap analysis), `home-assistant-js-websocket`
- Proxy: `proxy.mjs` serves on port 5173, proxies HA calls

**Features:**
- Connects to Home Assistant to fetch all entities
- Drag-and-drop entity assignment to rooms
- Capability gap analysis using Claude AI (Anthropic API)
- Real-time HA state sync via WebSocket
- Note: `insightsRouter` disabled in server (has syntax errors)

**Assessment:** A developer/diagnostic tool — not a daily-use family app. Useful for auditing and improving the HA setup, but not something that needs to run 24/7. The server has a conflicting port (defaults to 3001 — same as Mission Control). It has no Dockerfile, no docker-compose entry, and no git history.

**Recommendation: LOW PRIORITY — do not run as a permanent service.**  
- When needed: run locally (`npm run dev` + `npm run server:dev`)
- If you want it permanently available: Dockerise on port 3006 and add to docker-compose
- Fix the `insightsRouter` syntax errors before next use
- No consolidation opportunity — it's a standalone HA admin tool, not a family-facing app

---

### 4. Dakboard
**Path:** `/home/rob/Projects/Personal/apps/dakboard`  
**Port:** 3005  
**Status:** Recently created — files dated 2026-06-04 (today), no git history  
**Git:** No  
**Docker:** Yes — Dockerfile present and **already added to docker-compose.yml**  

**Stack:**
- Node.js + Express (minimal, single `server.js` file)
- No frontend framework — serves a static `public/index.html`
- SSE (Server-Sent Events) for real-time notification push

**Features:**
- Notification display server for Dakboard wall display
- `POST /message` — Jarvis/agent sends notifications here
- `GET /events` — SSE stream for the wall display to subscribe to
- In-memory message history (last 20 messages), no persistence
- Already has a health endpoint

**Assessment:** Simple, purpose-built, and already Dockerised. Already added to docker-compose.yml (port 3005). Very lightweight — no database dependency, no auth, no complexity.

**Recommendation: KEEP and deploy — it's ready.**  
- Already Dockerised and in docker-compose. Just needs a `docker compose up -d --build dakboard`.
- Consider adding the `dakboard` network to the compose default network so Mission Control can reach `http://dakboard:3005/message` without going through the host.

---

## Docker Compose Summary

Current `docker-compose.yml` (in `/home/rob/Projects/Personal/apps/`):

| Service | Container | Ports | Status |
|---|---|---|---|
| mission-control | mission-control | 3001 (API), 3003 (UI) | Defined + Dockerised |
| haven | haven | 3004 | Defined + Dockerised |
| dakboard | dakboard | 3005 | Defined + Dockerised (just added) |
| HomeIntel | — | 5173/3001 | Not in compose, no Dockerfile |

All three defined services share the `home-apps` Docker network, meaning they can reach each other by container name (e.g. `http://mission-control:3001`).

**Port conflict risk:** HomeIntel server defaults to port 3001 — same as Mission Control. If HomeIntel is ever Dockerised, use port 3006.

---

## Port Assignment Recommendations

| Service | Current Port | Recommended |
|---|---|---|
| Mission Control API | 3001 | 3001 (keep) |
| Mission Control UI | 3003 | 3003 (keep) |
| Haven | 3004 | 3004 (keep) |
| Dakboard | 3005 | 3005 (keep) |
| HomeIntel (if Dockerised) | — | 3006 |

---

## Overlap / Consolidation Opportunities

**Chores + Shopping in Haven vs Mission Control:**
Both apps have chores and shopping pages. Haven was built as a warm-aesthetic complement to Mission Control's sci-fi aesthetic, targeting Aimee and the kids rather than Rob's monitoring dashboard. The distinction is intentional — they serve different audiences. The problem is data duplication/divergence: Haven's chores use localStorage, Mission Control's use DynamoDB/Amplify.

**Recommended consolidation path:**
1. Add Haven chores/completions/earnings endpoints to Mission Control's `/api/haven/` routes (using the existing flat-JSON pattern already used for meals/shopping)
2. Haven's `lib/api.ts` already has the right structure — just needs the try/catch removed so it hits the API instead of falling back to localStorage
3. This keeps both UIs alive but unifies the data backend (Mission Control API)

**HomeIntel vs Mission Control:**
Mission Control already has HA integration (WebSocket, REST, presence detection). HomeIntel is specifically for entity-to-room assignment and AI gap analysis — not something Mission Control covers. No consolidation needed; they don't overlap.

**OpenClaw remnants:**
- `/api/openclaw` route exists in Mission Control's server — check `server/routes/openclaw.js` to see if it's used or can be removed
- No `openclaw-bridge` directory found at `/home/rob/Projects/` — already cleaned up per memory notes

---

## Action Priority List

1. **Deploy dakboard** — already done in compose, just needs `docker compose up -d --build dakboard`
2. **Add Haven chores API endpoints** — add `/api/haven/chores`, `/api/haven/completions`, `/api/haven/earnings` routes to Mission Control server using the same flat-JSON pattern as meals/shopping
3. **Clean up openclaw route** — review `mission-control/server/routes/openclaw.js`, remove if unused
4. **HomeIntel — fix insights syntax errors** if you plan to use it again; otherwise leave as a run-on-demand tool
5. **Haven backend data** — the `db/haven/` directory lives inside Mission Control's Docker container. Consider whether it should be a named volume for persistence across rebuilds
6. **HomeIntel Dockerfile** (optional/low priority) — if wanted permanently, Dockerise on port 3006 and add to compose
