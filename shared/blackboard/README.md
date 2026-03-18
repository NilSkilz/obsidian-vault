# Blackboard - Agent Collaboration

This is the shared workspace where agents collaborate on multi-step tasks.

## Structure

- `current-task.md` — Active task brief, status, and chain definition
- `research-output.md` — Scout's research findings  
- `draft.md` — Scribe's content drafts
- `dev-notes.md` — Dev's implementation notes, PR descriptions
- `house-log.md` — House agent's action log

## Usage

1. Main agent writes task plan to `current-task.md`
2. First agent reads plan, executes, writes results to appropriate file
3. Next agent reads previous results and continues the chain
4. Final agent or main agent reads results and reports back

Always clean up completed task files before starting new chains.