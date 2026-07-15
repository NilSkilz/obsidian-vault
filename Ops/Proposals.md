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

## local-lvm thin pool headroom (2026-07-09, recurred worse 2026-07-14, still critical 2026-07-15)
**Problem:** On 2026-07-03 the `local-lvm` thin pool hit 100% and caused real damage: HAOS paused on write errors, and SABnzbd's config file was zeroed to null bytes (recovered from backup). It's the tightest constraint on the box. Mitigations since (weekly `pct-fstrim`, heartbeat alert >85%, new disks routed to `data1-backups`) were keeping it around 75-80%, but on 2026-07-14 the heartbeat found it back at **100%** despite the weekly cron. Ran `pct fstrim` across all 15 running LXCs manually, which only brought it down to **95.26%**. On 2026-07-15's heartbeat it was back at **95.99%** — trim across all 15 LXCs this run only clawed back 0.09 points (95.34% -> 95.25% mid-run reading, settled at 95.99%). This confirms it's no longer a "reclaim slack" problem: there isn't meaningfully more trimmable space, the pool is genuinely full of live data. Worst individual volumes: vm-100 (Plex) 79.17% of its own 24G disk, vm-105 (Radarr) 84.42% of its own 4G disk. The VG (`pve`) still has 14.75GB unallocated that could extend the thin pool directly, no disk-move needed.
**Option:** Either (a) extend the `data` thin pool using the 14.75GB free in VG `pve` (`lvextend -L +14G pve/data`, quick, no guest downtime, buys maybe 1 more cycle given trim is no longer reclaiming much), or (b) the original plan — move the fattest guest disks (vm-100 Plex, vm-105 Radarr) off `local-lvm` onto `data1-backups` for permanent headroom, or (c) actually shrink usage — Radarr/Plex library housekeeping, since this looks like real growth, not slack.
**Risk:** (a) alone is a stopgap, not a fix, given trim is no longer buying real headroom — next growth cycle likely hits 100% again and repeats the July 3rd HAOS/SABnzbd damage. Escalating this one now (pushed a notification) rather than just logging it, since two consecutive daily heartbeats have found it critical and the standard quick fix stopped working.

**Update (2026-07-15, later heartbeat run):** Checked again — pool at 96.02% pre-trim, ran `pct fstrim` across all 15 running LXCs, only came down to 95.25%. Same story as this morning: trim is basically tapped out, still sitting critical. Still needs Rob's call on (a)/(b)/(c) above — not actioning any of them unilaterally since (a) is a filesystem-level change and (b)/(c) touch live disks/data.

**Update (2026-07-15, 18:xx — after the host crash/reboot):** Two things changed the picture. (1) Post-reboot `pct fstrim` reclaimed ~20 points (96.99% → 77.29%) — so "trim is tapped out" only holds on long uptime; a reboot frees a lot of untrimmed deleted blocks. (2) **Actioned option (a): `lvextend -L +13G pve/data`** — pool is now **66.93G, 62.4% used**, zero downtime. So the immediate crisis is over. BUT the VG is now nearly exhausted (**1.75G free**), so (a) can't be repeated — the SSD (`sda`, 119G) is fully allocated. **Confirmed: `sdb` / `data1-backups` is also an SSD (rota=0) with 328G free.** So the durable fix (b) is clean and has no perf penalty: move fat guest disks off `local-lvm` onto `data1-backups`. Recommended set: **HAOS VM 101 (live move via `qm move-disk`, no downtime), Plex CT 100, Tdarr CT 109, Seerr CT 107** (brief per-guest stop during rootfs move, all perf-tolerant). Frees ~30G+ of thin-pool allocation permanently. Leaving jarvis CT 110 (can't stop myself mid-session) and the *arrs in place. **Awaiting Rob's go-ahead on doing the disk moves** (touches live guest disks + brief blips).

## GitHub PAT for self-serve PRs (2026-07-09)
**Problem:** No `gh` CLI or GitHub token on the jarvis LXC. Every PR on non-Tide repos (Tethered especially, which uses the branch+PR workflow) needs Rob to click a compare link manually. Came up repeatedly during the Tide build. (Tide itself no longer needs it: Rob's directive is commit to `feature/tide-build` + `deploy-tide.sh` straight to live, no PR.)
**Option:** Drop a fine-grained PAT (repo scope, mission-control + tethered) into `~/.config/jarvis/github.env` so I can open PRs end to end.
**Risk:** A token on the box widens blast radius if the LXC is compromised. Fine-grained + scoped to the two repos keeps it contained. Raising because it's a credential Rob has to mint and decide the scope of.

## Plausible Docker image updates (2026-07-09)
**Problem:** `updates.sh` patches apt packages on the host + all 12 LXCs and HA, but Plausible runs as a Docker Compose stack, so its images (`plausible/community-edition`, the DB images) are never pulled by the update routine. They'll silently drift out of date, including security fixes.
**Option:** Add a small step to `updates.sh` (or a separate weekly job) that does `docker compose pull && up -d` in `/opt/plausible-ce` on CT 111, with a health check after.
**Risk:** A major Plausible version bump can need a schema migration; an unattended `pull && up -d` could break analytics. I'd pin to minor updates or gate majors behind a NEEDS-ROB line. Low stakes (analytics, not family-facing) but raising since it's an automation touching a running service.

