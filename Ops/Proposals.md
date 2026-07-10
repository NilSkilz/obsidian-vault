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

## local-lvm thin pool headroom (2026-07-09)
**Problem:** On 2026-07-03 the `local-lvm` thin pool hit 100% and caused real damage: HAOS paused on write errors, and SABnzbd's config file was zeroed to null bytes (recovered from backup). It's the tightest constraint on the box. Mitigations since (weekly `pct-fstrim`, heartbeat alert >85%, new disks routed to `data1-backups`) are keeping it around 75-80%, but they're reactive: the pool still creeps and a bad day could refill it.
**Option:** Move the fattest existing guest disks off `local-lvm` onto `data1-backups` (the 460GB disk) to buy permanent headroom, and/or grow the thin pool. I'd audit which guests are heaviest and propose specifics before touching anything.
**Risk:** Moving a live guest disk needs the guest stopped briefly (short downtime, scheduled). Not doing it risks a repeat of the 3 Jul corruption event. Raising rather than acting because it's downtime + irreversible-ish disk moves.

## GitHub PAT for self-serve PRs (2026-07-09)
**Problem:** No `gh` CLI or GitHub token on the jarvis LXC. Every PR on non-Tide repos (Tethered especially, which uses the branch+PR workflow) needs Rob to click a compare link manually. Came up repeatedly during the Tide build. (Tide itself no longer needs it: Rob's directive is commit to `feature/tide-build` + `deploy-tide.sh` straight to live, no PR.)
**Option:** Drop a fine-grained PAT (repo scope, mission-control + tethered) into `~/.config/jarvis/github.env` so I can open PRs end to end.
**Risk:** A token on the box widens blast radius if the LXC is compromised. Fine-grained + scoped to the two repos keeps it contained. Raising because it's a credential Rob has to mint and decide the scope of.

## Plausible Docker image updates (2026-07-09)
**Problem:** `updates.sh` patches apt packages on the host + all 12 LXCs and HA, but Plausible runs as a Docker Compose stack, so its images (`plausible/community-edition`, the DB images) are never pulled by the update routine. They'll silently drift out of date, including security fixes.
**Option:** Add a small step to `updates.sh` (or a separate weekly job) that does `docker compose pull && up -d` in `/opt/plausible-ce` on CT 111, with a health check after.
**Risk:** A major Plausible version bump can need a schema migration; an unattended `pull && up -d` could break analytics. I'd pin to minor updates or gate majors behind a NEEDS-ROB line. Low stakes (analytics, not family-facing) but raising since it's an automation touching a running service.

