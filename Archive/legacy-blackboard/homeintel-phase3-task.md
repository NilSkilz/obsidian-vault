# HomeIntel Phase 3: AI Analysis Engine

## Status: starting

## Task Overview
Implement Claude Opus integration for smart home gap analysis. Build the AI-powered analysis engine that examines entity assignments and provides intelligent recommendations for home automation improvements.

## Context
- **Project Location**: `/home/rob/Projects/Personal/HomeIntel/`
- **Service**: `homeintel` PM2 service on port 5173 (intel.cracky.co.uk)
- **Previous Phases**: Foundation setup (Phase 1) and UI Components (Phase 2) are complete
- **Current State**: Working React app with entity assignment, room capability detection, and UI components

## Phase 3 Requirements

### 1. Anthropic API Integration (src/services/anthropic.ts)

Create complete Claude Opus integration:

```typescript
interface AnalysisRequest {
  entities: Entity[];
  rooms: Room[];
  assignments: Record<string, string>; // entityId -> roomId
}

interface AnalysisResponse {
  overallScore: number; // 0-100
  roomScores: Record<string, number>; // roomId -> score 0-100
  gaps: AnalysisGap[];
  recommendations: Recommendation[];
  summary: string;
}

interface AnalysisGap {
  id: string;
  roomId?: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  category: 'security' | 'lighting' | 'climate' | 'presence' | 'energy' | 'automation';
  estimatedCost?: string; // "£50-100", "Free", etc.
  effort: 'low' | 'medium' | 'high';
}

interface Recommendation {
  id: string;
  title: string;
  description: string;
  type: 'software' | 'hardware';
  priority: number; // 1-5 for top 5 display
  estimatedCost?: string;
  implementation: string; // how to implement
}

// Main function:
export async function analyzeHomeSetup(data: AnalysisRequest): Promise<AnalysisResponse>
```

**API Configuration:**
- Model: `claude-3-opus-20240229` (Claude Opus-4-5)
- Anthropic API key from environment: `VITE_ANTHROPIC_API_KEY`
- Structured JSON response with validation
- Smart home consultant persona
- Focus on practical, actionable recommendations

### 2. Analysis Panel Component (src/components/AnalysisPanel.tsx)

Build comprehensive analysis UI with three states:

**Empty State:**
- Call-to-action design
- "Analyse Gaps" button (primary, prominent)
- Brief explanation of what analysis provides
- Requirements note (need some entity assignments)

**Loading State:**  
- Spinner/loading animation
- "Analysing your setup..." text
- Progress indication
- Cancel button (optional)

**Results State:**
- Overall home automation score (large, prominent)
- Room scores breakdown (grid of room cards with scores)
- Priority gaps list (filterable by room/category)
- Top 5 recommendations (software vs hardware)
- Re-analyze button

### 3. Analysis Hook (src/hooks/useAnalysis.ts)

Complete analysis state management:

```typescript
interface AnalysisState {
  isAnalyzing: boolean;
  lastAnalysis: AnalysisResponse | null;
  lastAnalyzedAt: number | null;
  error: string | null;
}

export function useAnalysis() {
  const [state, setState] = useState<AnalysisState>({
    isAnalyzing: false,
    lastAnalysis: null,
    lastAnalyzedAt: null,
    error: null
  });

  const analyzeSetup = async (entities: Entity[], rooms: Room[], assignments: Record<string, string>) => {
    // Trigger analysis with error handling
  };

  const clearAnalysis = () => {
    // Reset analysis state
  };

  return { ...state, analyzeSetup, clearAnalysis };
}
```

**Features:**
- Analysis trigger with loading states
- Error handling and retry logic  
- Result caching (persist to localStorage)
- Timestamp tracking for freshness
- Clear/reset functionality

### 4. JSON Response Validation

Use Zod for API response validation:

```typescript
import { z } from 'zod';

const AnalysisGapSchema = z.object({
  id: z.string(),
  roomId: z.string().optional(),
  title: z.string(),
  description: z.string(), 
  priority: z.enum(['high', 'medium', 'low']),
  category: z.enum(['security', 'lighting', 'climate', 'presence', 'energy', 'automation']),
  estimatedCost: z.string().optional(),
  effort: z.enum(['low', 'medium', 'high'])
});

const AnalysisResponseSchema = z.object({
  overallScore: z.number().min(0).max(100),
  roomScores: z.record(z.number().min(0).max(100)),
  gaps: z.array(AnalysisGapSchema),
  recommendations: z.array(RecommendationSchema),
  summary: z.string()
});

// Validate API responses before using
```

### 5. Error Handling & Retry Logic

Implement robust error handling:
- Network failures (retry up to 3 times)
- API quota/rate limiting (graceful degradation)
- Invalid responses (validation failures)
- Timeout handling (30 second limit)
- User-friendly error messages

### 6. UI Integration

Wire analysis into the main app:
- Add AnalysisPanel to main layout (prominent position)
- Connect to useEntities data (entities, rooms, assignments)
- Disable analysis if insufficient data (< 5 entity assignments)
- Show analysis freshness (last analyzed X minutes ago)
- Auto-refresh option when assignments change significantly

## Technical Implementation Details

### Claude Prompt Design
Create a sophisticated prompt that:
- Establishes smart home consultant persona
- Explains Home Assistant entity types and room assignments
- Requests structured JSON output matching our schema
- Focuses on AI automation goals (presence, lighting, security, climate)
- Provides realistic cost estimates and implementation guidance
- Balances software automations vs hardware additions

### Analysis Features Specification

**Room Capability Scoring (0-100):**
- Basic room functions: lighting, temperature monitoring
- Advanced: presence detection, entry monitoring, climate control
- Bonus points: media integration, security, energy monitoring

**Gap Identification:**
- Missing motion sensors in frequently used rooms
- Rooms without temperature monitoring
- Entry points without sensors
- No automation between related devices
- Security gaps (unmonitored doors/windows)

**Recommendation Prioritization:**
- Safety/security issues: high priority
- Daily comfort improvements: medium priority  
- Energy efficiency: medium/low priority
- Entertainment/convenience: low priority

### API Response Structure
```json
{
  "overallScore": 75,
  "roomScores": {
    "living_room": 85,
    "bedroom": 60,
    "kitchen": 70
  },
  "gaps": [
    {
      "id": "motion_bedroom",
      "roomId": "bedroom", 
      "title": "Missing Motion Detection",
      "description": "Bedroom has lighting but no motion sensor for automation",
      "priority": "medium",
      "category": "presence",
      "estimatedCost": "£25-40",
      "effort": "low"
    }
  ],
  "recommendations": [
    {
      "id": "bedroom_motion_auto",
      "title": "Add Bedroom Motion Automation",
      "description": "Install motion sensor and create automation for automatic lighting",
      "type": "hardware",
      "priority": 1,
      "estimatedCost": "£30",
      "implementation": "Install Aqara motion sensor, create HA automation: motion detected → turn on lights if dark"
    }
  ],
  "summary": "Your home automation is well-established with good lighting control. Main opportunities are adding motion detection to bedrooms and improving climate monitoring."
}
```

## Environment Setup

Add to `.env.local`:
```
VITE_ANTHROPIC_API_KEY=sk-ant-api03-...
```

## File Structure
```
src/
├── services/
│   └── anthropic.ts (new)
├── components/
│   └── AnalysisPanel.tsx (new) 
├── hooks/
│   └── useAnalysis.ts (enhance existing)
├── types/
│   └── analysis.ts (new types)
└── utils/
    └── analysisValidation.ts (Zod schemas)
```

## Testing Strategy

**Manual Testing:**
- Test with minimal data (few entities assigned)
- Test with comprehensive data (most entities assigned)
- Test error conditions (no API key, network failures)
- Test response validation (malformed API responses)

**Error Scenarios:**
- API key missing/invalid
- Network timeout
- Invalid JSON response
- Missing required fields
- Rate limiting

## Success Criteria

1. **Working Analysis**: Click "Analyse Gaps" → get structured recommendations
2. **Three UI States**: Empty, loading, and results display properly
3. **Error Handling**: Network failures show user-friendly messages
4. **Validation**: API responses validated, invalid data handled gracefully
5. **State Management**: Analysis results persist across component re-renders
6. **Performance**: Analysis completes within 30 seconds
7. **Integration**: Seamlessly integrated with existing entity assignment workflow

## Expected Deliverables

1. **Anthropic Service**: Complete API integration with Claude Opus
2. **Analysis Panel**: Full UI component with all three states
3. **Enhanced Hook**: useAnalysis with complete state management
4. **Validation Layer**: Zod schemas for response validation
5. **Error Handling**: Robust error handling with retry logic
6. **Documentation**: Comment code and update main README

## Notes for Implementation

- Focus on practical, actionable recommendations over theoretical analysis
- Ensure analysis feels valuable - users should get insights they wouldn't think of themselves
- Keep the UI clean and scannable - lots of information to display effectively
- Test with real Home Assistant entity data to ensure prompt generates useful insights
- Consider analysis caching to avoid repeated API calls for same data

## Next Phase Preview
Phase 4 will connect to live Home Assistant REST APIs, replacing mock data with real entity states and enabling service calls for automation implementation.

## File Locations
- **Work in**: `/home/rob/Projects/Personal/HomeIntel/`
- **Output results**: `obsidian-vault/shared/blackboard/homeintel-phase3-results.md`