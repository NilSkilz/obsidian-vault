# HomeIntel Phase 1: Foundation Setup

## Status: starting

## Task Overview
Implement the core foundation components for Home Intelligence - mock data, utility functions, and React hooks. The project scaffolding is already complete and working.

## Context
- **Project Location**: `/home/rob/Projects/Personal/HomeIntel/` 
- **Current State**: Basic Vite + React + TypeScript + Tailwind project is running on PM2
- **Service**: `homeintel` on port 5173 (accessible via intel.cracky.co.uk)
- **Previous Phase**: Project setup completed, all dependencies installed, basic structure exists

## Phase 1 Requirements

### 1. Enhanced Mock Data (src/data/mockEntities.ts)
Create realistic Home Assistant entity data with **50+ entities** across domains:

**Required Entities by Domain:**
- **light** (10+): bedroom_main, kitchen_ceiling, living_room_main, hallway, bathroom, office, garden_front, garden_rear, etc.
- **binary_sensor** (12+): motion sensors, door/window sensors, smoke/CO detectors, garage door
  - deviceClass values: motion, door, window, smoke, co, garage_door
- **sensor** (8+): temperature, humidity, energy, power sensors
  - deviceClass values: temperature, humidity, energy, power  
- **switch** (4+): smart plugs for TV, kettle, washing machine, monitor
- **climate** (2): thermostat, TRV
- **media_player** (3): TV, Echo bedroom, Echo kitchen
- **device_tracker** (2): owner phone, partner phone
- **camera** (2): front door, garden
- **alarm_control_panel** (1)
- **lock** (1)
- **cover** (2): blinds
- **automation/script** (3): these go in IGNORED_DOMAINS

**Entity Pre-assignment:**
- 8-10 entities assigned to `living_room` (lights, motion sensor, temperature sensor, TV, blind)
- 2-3 entities assigned to `kitchen`
- Rest unassigned to demonstrate the organizing workflow

### 2. Capability Mapping Logic (src/utils/capabilityMap.ts)
Implement the `deriveCapabilities()` function with detection logic:

```typescript
const CAPABILITY_DEFINITIONS = [
  {
    key: "occupancy",
    label: "Motion Detection", 
    icon: "👁",
    description: "Can detect if someone is in the room",
    // detect: domain=binary_sensor AND deviceClass=motion or occupancy
  },
  {
    key: "lighting",
    label: "Lighting Control",
    icon: "💡", 
    description: "Can control lights in this room",
    // detect: domain=light
  },
  {
    key: "temperature",
    label: "Temperature",
    icon: "🌡",
    description: "Can read room temperature", 
    // detect: deviceClass=temperature OR domain=climate
  },
  {
    key: "entry",
    label: "Door/Window Sensor",
    icon: "🚪",
    description: "Knows if doors or windows are open",
    // detect: domain=binary_sensor AND deviceClass in [door, window, garage_door] 
  },
  {
    key: "media", 
    label: "Media Device",
    icon: "📺",
    description: "Can detect/control media activity",
    // detect: domain=media_player
  },
  {
    key: "climate_control",
    label: "Climate Control", 
    icon: "❄",
    description: "Can control heating or cooling",
    // detect: domain=climate
  }
];
```

### 3. Domain Metadata Enhancement (src/utils/domainMeta.ts)
Already exists but may need refinement. Ensure it covers all domains in mock data with proper colors/icons.

### 4. Core React Hooks

#### useEntities Hook (src/hooks/useEntities.ts)
Implement entity state management with:
- Entity loading (from mock data initially)
- Room assignment/unassignment functions  
- Progress tracking (assigned vs total entities)
- localStorage persistence (`"hi_assignments_v1"`)
- Room creation functionality

#### useAnalysis Hook (src/hooks/useAnalysis.ts)  
Create placeholder hook structure for Phase 3:
- Analysis trigger function (stub for now)
- Loading states
- Result storage
- Error handling structure

### 5. Enhanced App Structure (src/App.tsx)
Wire up the foundation components with:
- useEntities hook integration
- Basic layout structure with placeholder components
- Entity assignment workflow demonstration
- Progress bar functionality

## Technical Requirements

### Mock Data Realism
- Realistic entity IDs: `light.bedroom_main`, `binary_sensor.living_room_motion`
- Proper device classes for sensors
- Mix of friendly names: "Bedroom Main Light", "Living Room Motion Sensor"
- Some entities with existing area assignments (to show populated state)

### localStorage Persistence
- Key: `"hi_assignments_v1"`  
- Store room assignments as `{ entityId: roomId }` mapping
- Load on app start, save on every assignment change
- Handle edge cases (malformed data, missing entities)

### TypeScript Compliance
- All functions properly typed with existing interfaces
- No `any` types
- Strict mode compliance
- Export all public functions/hooks

### Component Integration
- Components should receive data via props (no direct hook usage yet)
- App.tsx orchestrates data flow
- Proper React patterns (keys, effects, memoization where needed)

## Expected Deliverables

1. **Working Mock Data**: 50+ realistic HA entities with proper pre-assignment
2. **Capability Detection**: Room capability badges updating based on assigned entities  
3. **Entity Assignment**: Working assignment/unassignment with localStorage persistence
4. **Progress Tracking**: Progress bar showing X/Y entities assigned
5. **Room Management**: Add/remove rooms functionality
6. **Foundation Hooks**: useEntities with full state management, useAnalysis placeholder

## Success Criteria
- Navigate to intel.cracky.co.uk and see populated entity list
- Assign entities to rooms and see capability badges update
- Refresh page and see assignments persist
- Progress bar reflects assignment state accurately
- No TypeScript compilation errors
- Clean console (no runtime errors)

## Notes for Implementation
- Focus on data flow and state management, not UI polish
- Use existing component structure from previous setup
- Test assignment workflow thoroughly
- Ensure room capability detection is accurate
- Mock data should feel realistic and demonstrate all features

## File Locations
- Work in: `/home/rob/Projects/Personal/HomeIntel/`
- Reference spec: `./home-intelligence-spec.md`
- Output results: `obsidian-vault/shared/blackboard/homeintel-phase1-results.md`

## Phase 2 Preview
Next phase will implement the UI components (Header, UnassignedPanel, RoomCard, etc.) using the foundation built in this phase.