# Proposals

Things I've spotted that are worth doing but shouldn't do unilaterally (new
automations, deleting stuff, anything touching external systems, anything
irreversible or uncertain). Written here instead of just acting. Rob reviews,
approves or rejects, then I build it. Once actioned, delete the entry — this
file is a queue, not a log.

Format per entry:

```
## <short title> (YYYY-MM-DD)
**Problem:** what's wrong or missing
**Option:** what I'd do about it
**Risk:** what could go wrong / why I didn't just do it
```

## GitHub PAT for self-serve PRs (2026-07-09)
**Problem:** No `gh` CLI or GitHub token on the jarvis LXC. Every PR on non-Tide repos (Tethered especially, which uses the branch+PR workflow) needs Rob to click a compare link manually. Came up repeatedly during the Tide build. (Tide itself no longer needs it: Rob's directive is commit to `feature/tide-build` + `deploy-tide.sh` straight to live, no PR.)
**Option:** Drop a fine-grained PAT (repo scope, mission-control + tethered) into `~/.config/jarvis/github.env` so I can open PRs end to end.
**Risk:** A token on the box widens blast radius if the LXC is compromised. Fine-grained + scoped to the two repos keeps it contained. Raising because it's a credential Rob has to mint and decide the scope of.

## Delete stale old Cloudflare zone for cracky.co.uk (2026-08-06)
**Problem:** This morning's DDNS fix moved `cracky.co.uk` to a new Cloudflare account (new token, new zone id `da56…`), and Nominet now delegates the domain to that zone's nameservers (meg/owen) correctly. But the OLD account's zone for `cracky.co.uk` (nameservers edna/john) is still live and still answering with the dead `86.181.171.46`. Any resolver that still had the old edna/john delegation cached (or re-queries it before its own NS-record TTL expires) gets the stale answer, which caused the ~16:00 today "site is slow/not loading" flakiness. Confirmed as of this heartbeat run (19:07) it's now cleared everywhere I can check (1.1.1.1, 8.8.8.8, and the house router's resolver all return the correct proxied IPs, and all five public subdomains served 200/302 directly) — so it's not urgent, but the old zone is still sitting there as a landmine for the next resolver that hasn't refreshed.
**Option:** Rob deletes the old `cracky.co.uk` zone from the OLD Cloudflare account (the one before the account migration). My DDNS token only has access to the new account (zones: cracky `da56…` + kernowlabs), so I can't reach the old zone to remove it myself.
**Risk:** Account-level deletion I have no credentials for anyway — genuinely needs Rob, not just a caution. Low urgency now that the symptom has cleared, but worth closing out so it can't recur.

## HA core_ssh add-on stuck failing to update (2026-08-21)
**Problem:** `ha addons update --backup core_ssh` has now failed three heartbeat runs (2026-08-20, 2026-08-21, 2026-08-23), stuck at 10.3.0 while 10.4.0 is available. HA core/OS and everything else update clean (host + all 17 LXCs upgraded fine on 2026-08-23, HA core went to 2026.8.3). HA itself is fully up. Already flagged to Rob via Telegram on 2026-08-20, so not re-pinging for the same unresolved issue, but this is now three-for-three, not a blip.
**Option:** Rob checks the add-on update manually from the HA UI (Settings > Add-ons > Terminal & SSH > Update) to see the actual error, since the CLI update call doesn't surface one.
**Risk:** None from waiting, core_ssh at the old version still works. Just don't want this to become a silent recurring failure nobody looks at.

## Plausible Docker image updates (2026-07-09)
**Problem:** `updates.sh` patches apt packages on the host + all 12 LXCs and HA, but Plausible runs as a Docker Compose stack, so its images (`plausible/community-edition`, the DB images) are never pulled by the update routine. They'll silently drift out of date, including security fixes.
**Option:** Add a small step to `updates.sh` (or a separate weekly job) that does `docker compose pull && up -d` in `/opt/plausible-ce` on CT 111, with a health check after.
**Risk:** A major Plausible version bump can need a schema migration; an unattended `pull && up -d` could break analytics. I'd pin to minor updates or gate majors behind a NEEDS-ROB line. Low stakes (analytics, not family-facing) but raising since it's an automation touching a running service.

