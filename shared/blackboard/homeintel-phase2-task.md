# HomeIntel Phase 2: UI Components Implementation

## Status: starting

## Task Overview
Build the complete React component library for Home Intelligence entity organization interface. Phase 1 foundation is complete with working data flow, hooks, and mock data.

## Context
- **Project Location**: `/home/rob/Projects/Personal/HomeIntel/` 
- **Current State**: Phase 1 complete - working foundation with useEntities hook, mock data (67 entities), capability mapping
- **Service**: `homeintel` PM2 service on port 5173 (intel.cracky.co.uk)
- **Foundation Available**: Mock entities, useEntities/useAnalysis hooks, localStorage persistence working

## Phase 2 Requirements

### 1. Header Component (src/components/Header.tsx)
**Features:**
- App branding: House icon (⌂) + "Home Intelligence" + subtitle "Entity Organiser & Gap Analyser"
- Progress bar showing "X/Y entities assigned" with amber fill as completion increases
- Count badge for unassigned entities
- Primary "✦ Analyse Gaps" button for Phase 3 integration
- Connection status indicator (🟢 Connected / 🔴 Disconnected / 🟡 Connecting)
- "Demo Mode" pill if VITE_DEV_MODE=true

**Design:**
- Dark theme with GitHub-style colors from Tailwind config
- DM Sans font family
- Responsive layout with proper spacing

### 2. UnassignedPanel Component (src/components/UnassignedPanel.tsx)
**Features:**
- Fixed 280px width left sidebar, scrollable
- Title "Unassigned" with count badge
- Domain filter pills row: "All" + one pill per domain (using domain icons/colors)
- Scrollable list of EntityCard components
- Empty state: "✓ All entities assigned" when count is 0
- Hide IGNORED_DOMAINS entities completely

**Filter Behavior:**
- "All" shows all unassigned entities
- Domain pills filter to show only entities of that domain
- Use domain metadata for pill styling (icon + color from domainMeta utility)

### 3. EntityCard Component (src/components/EntityCard.tsx)
**Features:**
- Domain badge with icon + label (colored using domain metadata)
- Entity friendly name (medium weight)
- Entity ID in monospace, muted, small text
- Room assignment dropdown: "Assign to room..." placeholder
- Dropdown lists all available rooms
- Assignment triggers entity movement to room

**Design:**
- Clean card layout with proper spacing
- Hover states for interactivity
- Dropdown styling consistent with dark theme

### 4. RoomsGrid Component (src/components/RoomsGrid.tsx)
**Features:**
- 2-column responsive grid layout
- "Add Room" button that opens inline input
- Grid of RoomCard components
- Proper spacing and responsive behavior

**Add Room Flow:**
- Button click shows inline text input
- User types room name + Enter or "Add" button
- Room ID derived: `name.toLowerCase().replace(/\s+/g, "_")`
- New room appears in grid, input hides

### 5. RoomCard Component (src/components/RoomCard.tsx)
**Features:**
- Room name as heading
- Row of CapabilityBadge components (6 capabilities)
- List of assigned entity chips: `[icon] Entity name [×]`
- Click × to unassign entity (returns to unassigned panel)
- Empty state: "No entities assigned — use the panel on the left"
- Subtle left border: amber if entities assigned, gray if empty

**Entity Chips:**
- Domain icon + entity friendly name + remove button
- Clean, removable chip design
- Proper spacing in flow layout

### 6. CapabilityBadge Component (src/components/CapabilityBadge.tsx)
**Features:**
- Green dot if capability present, red/muted if missing
- Hover tooltip showing capability name + description
- 6 capability types: occupancy, lighting, temperature, entry, media, climate_control
- Uses capability mapping logic from Phase 1
- Smooth hover states and transitions

**Visual Design:**
- Small circular badges in a row
- Clear visual distinction between present/missing
- Informative tooltips with proper positioning

### 7. AnalysisPanel Component (src/components/AnalysisPanel.tsx)
**Three States:**
1. **Empty:** Centered ✦ icon, "Ready to analyse" heading, description, "Analyse Gaps" button
2. **Loading:** Centered spinner, "Analysing your home setup..." text  
3. **Results:** Summary card with score + breakdown (stub for Phase 3)

**Design:**
- Clean state transitions
- Proper loading animations
- Results layout ready for Phase 3 data integration

### 8. App.tsx Integration
**Wire Up Complete Flow:**
- Header with real progress tracking
- UnassignedPanel with working entity filtering
- RoomsGrid with functional room creation
- Entity assignment/unassignment working end-to-end
- Real-time capability badge updates
- AnalysisPanel in empty state (ready for Phase 3)

**Layout Structure:**
```
┌─────────────────────────────────────────────────────────┐
│ HEADER: Progress + Buttons                              │
├──────────────┬──────────────────────────────────────────┤
│              │ MAIN CONTENT AREA                        │
│  UNASSIGNED  │                                          │
│  PANEL       │   ROOMS GRID (2-col)                     │
│  (280px)     │   or                                     │
│              │   ANALYSIS PANEL                         │
│              │                                          │
└──────────────┴──────────────────────────────────────────┘
```

## Technical Requirements

### Styling & Design
- **Theme:** GitHub Dark colors from existing Tailwind config
- **Fonts:** DM Sans (UI), JetBrains Mono (entity IDs only)
- **Layout:** 280px fixed left panel, flex-1 main content
- **Responsiveness:** 2-column room grid, mobile considerations
- **Interactions:** Hover states, smooth transitions, loading states

### Integration Points
- **useEntities Hook:** Assignment/unassignment functions
- **Domain Metadata:** Icons, colors for entity badges  
- **Capability Mapping:** Real-time capability detection
- **localStorage:** Persist assignments across refreshes
- **Mock Data:** Use existing 67 entities with pre-assignments

### Component Architecture
- **Props-based:** Components receive data via props, minimal direct hook usage
- **TypeScript:** Strict typing with existing interfaces
- **React Patterns:** Proper keys, useEffect usage, memoization where beneficial
- **Modular:** Each component focused, reusable, well-structured

## Expected Deliverables

1. **Complete Component Library:** All 7 components implemented and integrated
2. **Working Assignment Flow:** Drag entities between unassigned panel and rooms
3. **Real-time Updates:** Capability badges, progress bar, counts update immediately  
4. **Visual Polish:** Clean dark theme, proper spacing, smooth interactions
5. **Room Management:** Add rooms, assign/unassign entities, remove entities from rooms
6. **Filtering System:** Domain-based entity filtering in unassigned panel
7. **Responsive Layout:** Works on various screen sizes, proper component spacing

## Success Criteria
- Navigate to intel.cracky.co.uk and see polished interface
- Assign entities to rooms via dropdown, see capability badges update
- Filter entities by domain in left panel
- Add new rooms and assign entities to them
- Remove entities from rooms, see them return to unassigned panel
- Progress bar accurately reflects assignment completion
- All interactions feel smooth and responsive
- No TypeScript errors, clean console output

## Notes for Implementation
- Build on existing Phase 1 foundation (don't recreate hooks/utilities)
- Focus on UI/UX polish and component interactions
- Test assignment workflow thoroughly across all components
- Use existing color/typography system from Tailwind config
- Ensure mobile responsiveness for various screen sizes
- Phase 3 will integrate AI analysis using the AnalysisPanel empty state

## File Locations
- Work in: `/home/rob/Projects/Personal/HomeIntel/`
- Use existing: useEntities, useAnalysis hooks, domain metadata, capability mapping
- Output: `obsidian-vault/shared/blackboard/homeintel-phase2-results.md`

## Next Phase Preview
Phase 3 will implement the AI analysis engine using Anthropic API, filling in the AnalysisPanel with real gap analysis and recommendations.