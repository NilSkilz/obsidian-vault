# Haven

**Family home management app named after Crackington Haven**

## Overview
- **Path:** `/home/rob/Projects/haven`
- **Stack:** Vite + React + TypeScript + Tailwind v4
- **Running:** Docker container `haven` on port 3004
- **Status:** NEW Feb 2026 (split from [[Mission Control]])

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

## Tags
#project #haven #family #meal-planning #chores #react #typescript #docker

## Links
- [[Mission Control]] - Sister project and presence provider
- [[Aimee]] - Primary user for meal planning
- [[Dexter]] - Chores and earnings tracking
- [[Logan]] - Chores and earnings tracking  
- [[Home Assistant]] - Smart home integration