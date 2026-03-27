# Task: Haven Family App Development Roadmap
## Status: planning-phase
## Chain: Dev (standalone)
---

**Objective:** Create comprehensive development roadmap for Haven family app improvements and backend integration

**Current Haven Status:**
- **Running:** Docker container on port 3004
- **Stack:** Vite + React + TypeScript + Tailwind v4
- **Features:** Weekly meal planner, chores tracker with earnings, family member selector
- **Data:** Currently localStorage-based (needs backend)
- **Aesthetic:** Warm family-friendly (cream/terracotta/sage colors)
- **Location:** `/home/rob/Projects/haven`

**Development Priorities:**

### Phase 1: Backend Foundation (Q2 2026)
1. **Data Persistence Strategy**
   - Replace localStorage with proper database (SQLite or PostgreSQL?)
   - API design for meal planning, chores, family data
   - Consider serverless vs traditional backend approach

2. **Family Member Management**
   - User authentication system
   - Family group creation and management
   - Role-based permissions (parents vs kids)

### Phase 2: Enhanced Features (Q3 2026)
3. **Chores System Improvements**
   - Recurring task templates
   - Photo verification for completed chores
   - Earnings tracking and spending history
   - Reward redemption system

4. **Meal Planning Evolution**
   - Recipe database integration
   - Grocery list generation
   - Dietary preference handling
   - Calendar sync for presence awareness

### Phase 3: Smart Features (Q4 2026)
5. **Home Assistant Integration**
   - Chore completion via HA sensors
   - Presence detection for meal planning
   - Smart notifications and reminders
   - Automatic scheduling based on family calendar

**Technical Questions to Address:**
- Best backend approach for family use case (privacy-focused)
- Mobile app vs PWA for notifications
- Offline capability requirements
- Multi-family deployment vs single-family focus

**Deliverables:**
- Complete development roadmap: `obsidian-vault/shared/blackboard/haven-roadmap.md`
- Technical architecture recommendations
- Timeline with milestones and dependencies
- Resource requirements (development time, infrastructure costs)