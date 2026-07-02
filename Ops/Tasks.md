# Tasks

Owned by the heartbeat (`Jarvis/bin/heartbeat.sh`, runs every 2h 7am-11pm via cron).
Each run picks up items from **Now**, does relevant checks, and acts on anything
safe. Recurring items get checked every run. Backlog/Ideas are NOT touched by
the heartbeat — they're just a parking lot for later, reviewed with Rob manually.

Each run also checks the **"To Do" list** on the Trello "Jarvis" board
(via `Jarvis/bin/trello.sh cards "To Do"`) and treats those cards the same way
as items here — same safe/reversible rule, Proposals.md if not. Ideas/Backlog
lists on the board are not triaged, heartbeat never touches them.

## Now

_(empty — add stuff here for the heartbeat to pick up)_

## Recurring

- Check all Proxmox LXC containers/VMs are up (`pct list` / `qm list` on 192.168.1.2, or `ssh` there if not local). Flag anything stopped that shouldn't be — don't restart without asking unless it's obviously safe (e.g. a known-flaky non-critical service).

## Backlog / Ideas

_(heartbeat ignores this section entirely)_
