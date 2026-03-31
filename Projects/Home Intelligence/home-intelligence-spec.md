# Home Intelligence — Entity Organiser & Gap Analyser
## Implementation Specification for Claude Code

---

## Overview

Build a React web application that connects to a local Home Assistant instance, pulls all entities and areas, lets the user organise entities into rooms, derives a capability map, and uses the Anthropic API to analyse automation gaps and recommend sensors/devices.

The app has two modes:
- **Dev mode** — uses mock data so it can be built and tested without a live HA instance
- **Live mode** — connects to a real Home Assistant instance via its REST/WebSocket API

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | React 18 + Vite |
| Language | TypeScript (strict) |
| Styling | Tailwind CSS |
| HTTP client | Native `fetch` |
| HA WebSocket | `home-assistant-js-websocket` |
| AI | `@anthropic-ai/sdk` |
| State | React `useState` / `useReducer` (no external state lib needed) |
| Config | `.env` file |

---

## Environment Variables

```env
VITE_HA_URL=http://homeassistant.local:8123
VITE_HA_TOKEN=your_long_lived_access_token
VITE_ANTHROPIC_API_KEY=your_anthropic_api_key
VITE_DEV_MODE=true
```

> **Note:** In production, the Anthropic API key must NOT be in the frontend. For now, treat this as a local dev tool only. Add a note in the README about this.

---

## Project Structure

```
src/
├── main.tsx
├── App.tsx
├── types/
│   └── index.ts              # All shared TypeScript types
├── data/
│   └── mockEntities.ts       # Realistic mock HA entities for dev mode
├── services/
│   ├── homeAssistant.ts      # HA REST + WebSocket connection
│   └── anthropic.ts          # Anthropic API calls
├── hooks/
│   ├── useEntities.ts        # Entity state + assignment logic
│   └── useAnalysis.ts        # Gap analysis trigger + result state
├── components/
│   ├── Header.tsx
│   ├── UnassignedPanel.tsx   # Left sidebar
│   ├── EntityCard.tsx        # Single unassigned entity
│   ├── RoomsGrid.tsx         # Main room grid
│   ├── RoomCard.tsx          # Single room with capabilities + entities
│   ├── AnalysisPanel.tsx     # Gap analysis results
│   ├── CapabilityBadge.tsx   # Green/red capability indicator dot
│   └── AddRoomModal.tsx
└── utils/
    ├── capabilityMap.ts      # Logic to derive capabilities from entities
    └── domainMeta.ts         # Icon/colour metadata per HA domain
```

---

## Core TypeScript Types

```typescript
// src/types/index.ts

export type HaDomain =
  | "light"
  | "switch"
  | "binary_sensor"
  | "sensor"
  | "climate"
  | "media_player"
  | "device_tracker"
  | "camera"
  | "alarm_control_panel"
  | "lock"
  | "cover"
  | "automation"
  | "script"
  | string;

export interface HaEntity {
  id: string;           // e.g. "light.bedroom_main"
  name: string;         // friendly_name from HA
  domain: HaDomain;
  deviceClass?: string; // e.g. "motion", "temperature", "door"
  area: string | null;  // area/room ID, null if unassigned
  state?: string;       // current state value from HA (optional, for display)
  attributes?: Record<string, unknown>;
}

export interface Room {
  id: string;           // e.g. "living_room"
  name: string;         // e.g. "Living Room"
  haAreaId?: string;    // original HA area ID if imported from HA
}

export type CapabilityKey =
  | "occupancy"
  | "lighting"
  | "temperature"
  | "entry"
  | "media"
  | "climate_control"
  | "presence";

export interface Capability {
  key: CapabilityKey;
  label: string;
  icon: string;
  description: string;
  has: boolean;
}

export interface RoomCapabilityMap {
  roomId: string;
  roomName: string;
  capabilities: Capability[];
  entities: HaEntity[];
}

// --- Analysis types (from Anthropic API response) ---

export interface GapItem {
  label: string;         // e.g. "Occupancy Detection"
  suggestion: string;    // e.g. "Add a PIR or mmWave motion sensor"
  priority: "high" | "medium" | "low";
  cost: string;          // e.g. "~£15" or "free"
}

export interface RoomAnalysis {
  name: string;
  score: number;         // 0-100
  canDo: string[];
  gaps: GapItem[];
}

export interface Priority {
  action: string;
  reason: string;
  cost: string;
  type: "software" | "hardware";
}

export interface AnalysisResult {
  summary: string;
  overallScore: number;
  rooms: RoomAnalysis[];
  topPriorities: Priority[];
}
```

---

## Mock Data

Create `src/data/mockEntities.ts` with at least 50 realistic entities. The mock should include a realistic mix with some entities already assigned to areas (to show the UI in a useful state on first load), and many unassigned to demonstrate the problem being solved.

Include entities across these domains:
- `light` — at least 10 (bedroom, kitchen, living room, hallway, bathroom, office, garden front/rear)
- `binary_sensor` — at least 12, with `deviceClass` values: `motion`, `door`, `window`, `smoke`, `co`, `garage_door`
- `sensor` — at least 8, with `deviceClass` values: `temperature`, `humidity`, `energy`, `power`
- `switch` — at least 4 (smart plugs for TV, kettle, washing machine, monitor)
- `climate` — 2 (thermostat, TRV)
- `media_player` — 3 (TV, Echo in bedroom, Echo in kitchen)
- `device_tracker` — 2 (owner's phone, partner's phone)
- `camera` — 2 (front door, garden)
- `alarm_control_panel` — 1
- `lock` — 1
- `cover` — 2 (blinds)
- `automation` — 2 (these should be in a separate "ignored" list, not shown in the assignable panel)
- `script` — 1

Pre-assign about 8–10 entities to `living_room` (lights, motion sensor, temperature sensor, TV, one blind) and 2–3 to `kitchen` so the UI isn't completely empty on first load.

---

## Home Assistant Service

```typescript
// src/services/homeAssistant.ts

// Fetches entities from HA REST API and maps to HaEntity[]
export async function fetchHaEntities(baseUrl: string, token: string): Promise<HaEntity[]>

// Fetches HA areas (their equivalent of rooms) and returns Room[]
export async function fetchHaAreas(baseUrl: string, token: string): Promise<Room[]>

// Fetches entity-area registry (which entity belongs to which area in HA)
export async function fetchHaEntityRegistry(baseUrl: string, token: string): Promise<Record<string, string>>
// returns map of entityId -> areaId

// Calls HA REST API to perform an action (e.g. turn off a light)
// Used later when the AI layer executes actions — stub this for now
export async function callHaService(
  baseUrl: string,
  token: string,
  domain: string,
  service: string,
  target: { entity_id: string },
  data?: Record<string, unknown>
): Promise<void>
```

**Endpoints to use:**
- `GET /api/states` — all entity states
- `GET /api/config/area_registry/list` — all areas
- `GET /api/config/entity_registry/list` — entity registry (includes area assignments)
- `POST /api/services/{domain}/{service}` — call a service

**Headers for all requests:**
```
Authorization: Bearer {VITE_HA_TOKEN}
Content-Type: application/json
```

**Error handling:** If the HA URL is unreachable, fall back to mock data and show a banner: `"Could not connect to Home Assistant — showing demo data"`.

---

## Capability Map Logic

```typescript
// src/utils/capabilityMap.ts

// Maps HA entities for a room to a list of Capability objects
export function deriveCapabilities(entities: HaEntity[]): Capability[]

// Definition of each capability and how to detect it:
const CAPABILITY_DEFINITIONS = [
  {
    key: "occupancy",
    label: "Motion Detection",
    icon: "👁",
    description: "Can detect if someone is in the room",
    // detect if any entity has domain=binary_sensor AND deviceClass=motion or deviceClass=occupancy
  },
  {
    key: "lighting",
    label: "Lighting Control",
    icon: "💡",
    description: "Can control lights in this room",
    // detect if any entity has domain=light
  },
  {
    key: "temperature",
    label: "Temperature",
    icon: "🌡",
    description: "Can read room temperature",
    // detect if any entity has deviceClass=temperature OR domain=climate
  },
  {
    key: "entry",
    label: "Door/Window Sensor",
    icon: "🚪",
    description: "Knows if doors or windows are open",
    // detect if any entity has domain=binary_sensor AND deviceClass in [door, window, garage_door]
  },
  {
    key: "media",
    label: "Media Device",
    icon: "📺",
    description: "Can detect/control media activity",
    // detect if any entity has domain=media_player
  },
  {
    key: "climate_control",
    label: "Climate Control",
    icon: "❄",
    description: "Can control heating or cooling",
    // detect if any entity has domain=climate
  },
]
```

---

## Domain Metadata

```typescript
// src/utils/domainMeta.ts

// Returns display info for a given HA domain
export function getDomainMeta(domain: HaDomain): {
  label: string;
  icon: string;
  color: string;        // hex colour for text/badge
  bgColor: string;      // semi-transparent version for badge background
}

// Domains to define metadata for:
// light, binary_sensor, sensor, switch, climate, media_player,
// device_tracker, camera, alarm_control_panel, lock, cover
// Anything unknown gets a generic grey "⚙" icon
```

---

## Anthropic Service

```typescript
// src/services/anthropic.ts

import Anthropic from "@anthropic-ai/sdk";

export async function analyseGaps(
  roomMaps: RoomCapabilityMap[],
  globalContext: {
    hasPresenceDetection: boolean;
    hasAlarm: boolean;
    hasCameras: boolean;
    unassignedCount: number;
    totalEntities: number;
  }
): Promise<AnalysisResult>
```

**Model to use:** `claude-opus-4-5` (high quality for analysis)

**System prompt to use:**

```
You are a smart home consultant analysing a Home Assistant setup. The homeowner wants to build an AI reasoning layer that can:
- Infer when everyone has left the house
- Automate lighting based on occupancy
- Manage heating efficiently  
- Handle security arming/disarming
- Detect anomalies (device left on, unusual patterns)

Return ONLY valid JSON (no markdown fences, no commentary) matching this exact TypeScript type:
{
  summary: string,          // 2–3 sentence overview
  overallScore: number,     // 0–100, how capable the setup is for AI automation
  rooms: Array<{
    name: string,
    score: number,          // 0–100
    canDo: string[],        // things currently possible
    gaps: Array<{
      label: string,        // capability name
      suggestion: string,   // specific sensor/device to add
      priority: "high" | "medium" | "low",
      cost: string          // e.g. "free", "~£15", "~£30", "~£50+"
    }>
  }>,
  topPriorities: Array<{
    action: string,
    reason: string,
    cost: string,
    type: "software" | "hardware"
  }>
}

Priority definitions:
- high: blocks a key automation goal entirely
- medium: significantly reduces intelligence/reliability
- low: nice to have improvement

topPriorities: max 5 items. Software/free fixes first. Only include rooms that have at least one entity assigned.
```

**Error handling:** Wrap in try/catch. On parse failure, retry once with an explicit "fix your JSON" message. On second failure, throw a user-readable error.

---

## UI Layout

### Overall Structure

```
┌─────────────────────────────────────────────────────────┐
│ HEADER: Logo | Title | Progress bar | Analyse button     │
├──────────────┬──────────────────────────────────────────┤
│              │ [Rooms & Areas] [Gap Analysis]  [+Room]  │
│  UNASSIGNED  ├──────────────────────────────────────────┤
│  PANEL       │                                          │
│              │   ROOMS GRID (2 cols)                    │
│  Filter by   │   or                                     │
│  domain      │   ANALYSIS PANEL                         │
│              │                                          │
│  Entity      │                                          │
│  cards with  │                                          │
│  room        │                                          │
│  dropdown    │                                          │
└──────────────┴──────────────────────────────────────────┘
```

**Left panel width:** 280px fixed, scrollable  
**Content area:** flex-1, scrollable  

---

### Header

- Left: House icon (⌂), app title "Home Intelligence", subtitle "Entity Organiser & Gap Analyser"
- Right: Progress bar showing `X/Y entities assigned`, count badge for unassigned entities, primary "✦ Analyse Gaps" button
- Progress bar fills amber as more entities are assigned
- If VITE_DEV_MODE=true, show a subtle "Demo Mode" pill

---

### Left Panel — Unassigned Entities

- Title "Unassigned" with count badge
- Row of filter pills: "All" + one pill per available domain (using domain icon from `getDomainMeta`)
- Scrollable list of `EntityCard` components
- Empty state: "✓ All entities assigned" when count is 0
- Domains in `IGNORED_DOMAINS` list are hidden entirely from this panel

**EntityCard:**
- Domain badge (icon + label, coloured)
- Entity friendly name (medium weight)
- Entity ID (monospace, muted, small)
- Room dropdown select: "Assign to room..." as placeholder, lists all rooms

**IGNORED_DOMAINS** (never shown in the unassigned panel):
```typescript
const IGNORED_DOMAINS = [
  "automation", "script", "input_boolean", "input_number",
  "input_select", "group", "zone", "sun", "weather",
  "persistent_notification", "scene", "timer", "counter"
]
```

---

### Rooms Grid

- 2-column grid of `RoomCard` components
- "Add Room" button opens an inline input row at the top of the grid

**RoomCard:**
- Room name (heading)
- Capability badges row: one dot per capability, green if present, red/muted if missing, with tooltip on hover showing capability name and status
- Assigned entity chips: `[icon] Entity name [×]` — clicking × unassigns the entity (returns it to the unassigned panel)
- Empty state within card: "No entities assigned — use the panel on the left"
- Card has a subtle left border that is amber if at least one entity is assigned, dark grey if empty

---

### Analysis Panel

Three states:

1. **Empty (no analysis run yet):**  
   Centred icon (✦), "Ready to analyse" heading, short description, "Analyse Gaps" button

2. **Loading:**  
   Centred spinner animation, "Analysing your home setup..." text

3. **Results:**
   - Summary card with overview text and overall score (displayed as a circle/ring with the number)
   - "Top Priorities" section: cards showing action, reason, cost, type badge (Software = green, Hardware = amber)
   - "Room Breakdown" section: one card per room with score, "can do" list (green checkmarks), and gaps list (colour-coded by priority: red=high, amber=medium, grey=low)

---

## Colour Palette & Design Tokens

Use Tailwind's config or CSS variables. Target this palette:

```
Background:       #0d1117
Surface:          #161b22
Surface elevated: #1c2128
Border:           #21262d
Border subtle:    #30363d

Text primary:     #e6edf3
Text muted:       #8b949e
Text faint:       #484f58

Accent amber:     #f0b429
Accent amber dim: rgba(240,180,41,0.15)

Success green:    #3fb950
Warning amber:    #d29922
Error red:        #f85149
Info blue:        #58a6ff
```

**Typography:**  
Import from Google Fonts:
- `DM Sans` — UI text (weights 400, 500, 600)
- `JetBrains Mono` — entity IDs only (weights 400, 500)

---

## Key Behaviours

**Assignment flow:**
1. User selects a room from the dropdown on an `EntityCard`
2. Entity immediately moves from the unassigned panel to the room card
3. Room card's capability badges update in real time
4. Progress bar in header updates

**Unassignment flow:**
1. User clicks × on an entity chip inside a room card
2. Entity returns to the unassigned panel (at the top of its domain group)
3. Progress bar updates

**Add room flow:**
1. User clicks "+ Add Room"
2. An inline text input appears at the top of the grid
3. User types name and presses Enter or clicks "Add"
4. Room ID is derived: `name.toLowerCase().replace(/\s+/g, "_")`
5. New room card appears in the grid
6. Input hides

**Persistence:**
- Save entity-to-room assignments to `localStorage` on every change using key `"hi_assignments_v1"`
- On load, rehydrate assignments from `localStorage` before applying mock/live data
- This means assignments survive page refreshes

**HA live connection:**
- On mount, if `VITE_DEV_MODE !== "true"`, attempt to connect to HA
- Show a connection status indicator in the header (🟢 Connected / 🔴 Disconnected / 🟡 Connecting)
- Import existing HA areas as rooms automatically
- Import existing entity-area assignments from HA entity registry as initial assignments

---

## Implementation Phases

### Phase 1 — Foundation
- [ ] Scaffold Vite + React + TypeScript + Tailwind project
- [ ] Create all type definitions in `src/types/index.ts`
- [ ] Create mock entity data in `src/data/mockEntities.ts`
- [ ] Implement `capabilityMap.ts` and `domainMeta.ts` utilities
- [ ] Build `useEntities` hook with assignment logic and localStorage persistence

### Phase 2 — UI
- [ ] Build `Header` component with progress bar
- [ ] Build `UnassignedPanel` with filter pills and `EntityCard`
- [ ] Build `RoomsGrid` and `RoomCard` with capability badges
- [ ] Build `AddRoomModal` (inline input)
- [ ] Wire everything together in `App.tsx` — ensure assignment/unassignment works end to end

### Phase 3 — Analysis
- [ ] Implement `src/services/anthropic.ts`
- [ ] Build `AnalysisPanel` component (all three states)
- [ ] Build `useAnalysis` hook
- [ ] Wire up "Analyse Gaps" button

### Phase 4 — HA Integration
- [ ] Implement `src/services/homeAssistant.ts`
- [ ] Add connection status to header
- [ ] Merge live HA entity data with existing state
- [ ] Fall back gracefully to mock data on connection failure

---

## README Requirements

The generated README should include:
1. What the app does (1 paragraph)
2. Prerequisites (Node 18+, a HA instance, an Anthropic API key)
3. Setup instructions (`cp .env.example .env`, fill in values, `npm install`, `npm run dev`)
4. Security warning: this is a local dev tool — do not expose the Anthropic API key or HA token publicly
5. How to get a HA Long-Lived Access Token (Profile → Long-Lived Access Tokens)
6. Dev mode explanation

---

## Notes for Claude Code

- Use `strict: true` in `tsconfig.json`
- All components should have explicit prop types (no implicit `any`)
- Keep components focused — if a component file exceeds ~150 lines, split it
- The `analyseGaps` function serialises only the room capability map and a minimal global context — do NOT send all raw entity state to the API
- The Anthropic response must be validated — use a type guard or Zod schema to ensure the JSON matches `AnalysisResult` before using it in state
- Add a simple Zod validation for the API response (`npm install zod`)
- All async operations should have loading + error states
