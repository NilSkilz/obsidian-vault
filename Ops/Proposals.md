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

## `/data` disk shows 364GB used with only 12MB of actual files (2026-08-24)
**Problem:** `/data` (dedicated disk `/dev/sdb`, ext4, 447GB) has read `88%` used across every heartbeat check today, logged each time as "steady, not climbing." Dug into it properly this run: `df -i` shows only 2973 inodes used and `du -sh /data/*` finds just the `memory` vault at 12MB — there's nothing else visible on the mount (no other dirs, no `lost+found`, no stacked mounts). But `stat -f /data` shows the filesystem's own block bitmap has ~95.4M of 115M blocks (4K each) marked used, i.e. ~364GB accounted for at the ext4 level that doesn't correspond to any file I can find. Checked for the obvious explanation (deleted-but-still-open file handles via `lsof`) and ruled it out — the only deleted-and-open files on the box are tiny npm/tmp logs (<2KB), nowhere near 364GB. This looks like either a stale/corrupt block bitmap (possible from however this disk was provisioned/attached to the LXC) or something genuinely using space I don't have visibility into from inside the container.
**Option:** Needs `fsck`/`e2fsck -f` to actually diagnose, which requires unmounting `/data` first — not something to do unattended on the live memory vault disk. Rob (or a scheduled maintenance window) should: back up `/data/memory` first (it's only 12MB, trivial), unmount, run `e2fsck -f /dev/sdb` from the Proxmox host or a rescue context, see what it finds/fixes, remount. Alternative if fsck comes back clean: check from the Proxmox host side whether this disk image itself is oversized/thin-provisioning weirdness rather than a guest-side ext4 issue.
**Risk:** Unmounting `/data` briefly takes the memory vault offline for me (low stakes, it's small and easy to re-verify after). Running fsck unattended carries a small risk of it "fixing" things in a way that loses data if the bitmap corruption is masking something real, so I didn't do it myself. Not urgent (53GB still free, hasn't grown across 5 checks today) but worth closing out since an unexplained 364GB gap is the kind of thing that could either be nothing or a slow-motion problem.

## Plausible Docker image updates (2026-07-09)
**Problem:** `updates.sh` patches apt packages on the host + all 12 LXCs and HA, but Plausible runs as a Docker Compose stack, so its images (`plausible/community-edition`, the DB images) are never pulled by the update routine. They'll silently drift out of date, including security fixes.
**Option:** Add a small step to `updates.sh` (or a separate weekly job) that does `docker compose pull && up -d` in `/opt/plausible-ce` on CT 111, with a health check after.
**Risk:** A major Plausible version bump can need a schema migration; an unattended `pull && up -d` could break analytics. I'd pin to minor updates or gate majors behind a NEEDS-ROB line. Low stakes (analytics, not family-facing) but raising since it's an automation touching a running service.

