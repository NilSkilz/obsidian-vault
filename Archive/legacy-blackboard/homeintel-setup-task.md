# HomeIntel Project Setup Task

## Status: starting

## Task Overview
Set up the Home Intelligence React web application project from scratch. This is a Home Assistant entity organizer and automation gap analyzer that uses Claude AI for intelligent recommendations.

## Context
- **Project Location**: `/home/rob/Projects/Personal/HomeIntel/` (already created)
- **Implementation Spec**: Already copied to project directory as `home-intelligence-spec.md`
- **Purpose**: React web app that connects to Home Assistant, organizes entities into rooms, derives capabilities, and uses Anthropic API for gap analysis
- **Tech Stack**: React 18 + Vite + TypeScript (strict) + Tailwind CSS + Anthropic SDK

## Detailed Requirements

### 1. Project Initialization
- Initialize Vite React project with TypeScript template
- Configure TypeScript with strict mode enabled
- Set up Tailwind CSS with custom dark theme color palette
- Install all required dependencies

### 2. Required Dependencies
**Core:**
- react (18+)
- react-dom
- typescript
- vite
- @vitejs/plugin-react

**Styling:**
- tailwindcss
- @tailwindcss/forms
- autoprefixer
- postcss

**API & Data:**
- @anthropic-ai/sdk
- home-assistant-js-websocket
- zod (for response validation)

**Fonts:**
- Configure Google Fonts: DM Sans (400,500,600) + JetBrains Mono (400,500)

### 3. Project Structure
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

### 4. Environment Configuration
Create `.env.example`:
```env
VITE_HA_URL=http://homeassistant.local:8123
VITE_HA_TOKEN=your_long_lived_access_token
VITE_ANTHROPIC_API_KEY=your_anthropic_api_key
VITE_DEV_MODE=true
```

### 5. Tailwind Configuration
Custom color palette (GitHub Dark theme):
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

### 6. Documentation Requirements

#### README.md Structure:
1. **Overview** (1 paragraph) - what the app does
2. **Prerequisites** - Node 18+, HA instance, Anthropic API key
3. **Setup Instructions** - env file, install, dev server
4. **Security Warning** - API keys, local dev tool only
5. **Getting HA Token** - how to create Long-Lived Access Token
6. **Dev vs Live Mode** - explanation of modes

#### Security Warnings to Include:
- Anthropic API key should never be exposed publicly
- This is a local development tool only
- HA token security considerations
- Do not deploy with API keys to public servers

### 7. TypeScript Configuration
- Enable strict mode
- Configure proper module resolution
- Set up path aliases for clean imports
- Include all necessary type definitions

### 8. Initial File Stubs
Create placeholder files for all components/services/hooks with basic TypeScript interfaces and exports. Don't implement full functionality yet - just structure.

## Expected Deliverables
1. Working Vite project with dev server running
2. All dependencies installed and configured
3. Complete project structure with placeholder files
4. Comprehensive README.md with setup instructions
5. Environment configuration examples
6. TypeScript strict mode working
7. Tailwind CSS configured with custom theme
8. Google Fonts integration working

## Notes for Implementation
- Focus on project setup and configuration first
- Create comprehensive documentation
- Ensure all file structure is in place
- Prioritize security warnings in documentation
- Make sure dev server starts without errors
- All TypeScript files should compile without errors

## File Locations
- Work in: `/home/rob/Projects/Personal/HomeIntel/`
- Reference spec: `./home-intelligence-spec.md` (already present)
- Output results to: `obsidian-vault/shared/blackboard/homeintel-setup-results.md`

## Success Criteria
- `npm run dev` starts development server successfully
- All TypeScript compiles without errors
- Tailwind CSS is working with custom theme
- README.md provides clear setup instructions
- Project structure matches specification exactly
- Environment examples are complete and documented