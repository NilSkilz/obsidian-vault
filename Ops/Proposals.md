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

## Backup retention will fill the data1 disk (2026-08-25)
**Problem:** the "364GB phantom usage on `/data`" (yesterday's proposal, now withdrawn) was never a filesystem fault. `/data` is a bind mount of `/mnt/data1/jarvis` on the Proxmox host, so `df` inside my container reports the whole 447GB `data1` disk, not my 13MB folder. The 374GB is the host's `data1-backups` storage: 287GB of weekly vzdump dumps + 87GB of CT rootfs images (incl. mine). Disk is now at 90% (43GB free) and it is climbing ~36GB a week (18 guests, Sunday 01:00 job). The job's retention is `keep-last=3, keep-daily=7, keep-weekly=4, keep-monthly=3`, which on a weekly-only job means 7 "dailies" are really 7 more weeks: steady state is ~17 dumps per guest, roughly 600GB. The disk is 440GB. It will run out around mid-September, and a full backup disk also breaks the Sunday job and anything else on data1 (my rootfs lives there).
**Option:** change the vzdump job retention to `keep-last=1, keep-weekly=3, keep-monthly=2` (6 per guest, ~215GB worst case, still 6 weeks of restore points). One command on the host: `pvesh set /cluster/backup/backup-cf999020-84ea --prune-backups keep-last=1,keep-weekly=3,keep-monthly=2`. Old dumps beyond the policy get pruned on the next Sunday run (or immediately with `vzdump --prune-backups ... --storage data1-backups` per guest). Optionally also move the offsite restic target to cover the dumps if you want longer history off-box.
**Risk:** it deletes ~4 of the 10 existing restore points per guest (the July 1-12 rebuild-era ones and some mid-July). Nothing else. I didn't do it unattended because deleting backups is exactly the kind of thing you should say yes to first.
