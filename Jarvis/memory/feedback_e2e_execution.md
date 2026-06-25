---
name: feedback-e2e-execution
description: "Rob wants tasks completed end-to-end without requiring his manual involvement — if it can be done autonomously, do it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b1bf6ab7-442f-4aab-97cb-f2012c9ebf13
---

When Rob asks for something to be done, complete it end-to-end without requiring his manual involvement, if it is technically feasible to do so.

**Why:** Rob explicitly said "I'm fed up of having to do stuff like that — when I ask something to be done I need it actually done, end-to-end." He's comfortable with Jarvis having broad permissions and does not want to be asked to run daemon-reloads, apply scripts, or perform other manual implementation steps.

**How to apply:** Before presenting a solution that requires Rob to run a command or take an action, first exhaust all autonomous paths (hermit routines, CronCreate, direct API calls, writing scripts that run themselves). Only involve Rob if there is a genuine blocker (e.g., requires physical access, a credential only he holds, or a classifier restriction that prevents the action). If blocked, be explicit about exactly why the autonomous path failed.
