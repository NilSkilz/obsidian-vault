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


## 2026-10-19: HA add-on core_ssh update failed
**Problem:** updates.sh heartbeat could not update core_ssh (10.4.0 -> 10.5.0); everything else in the HA sweep succeeded.
**Option:** retry from the HA UI (Settings > Add-ons > Terminal & SSH), or check the add-on log for why. Probably transient, will see whether tomorrow's run clears it.
**Risk:** low. Add-on is only the SSH/terminal access; but updates.sh itself may rely on it, so worth a look if it keeps failing.

## 2026-10-20: core_ssh add-on update needs the HA UI (root cause found)
**Problem:** core_ssh 10.4.0 -> 10.5.0 failed two days running. Cause: "App core_ssh can't update itself" (the add-on is the SSH path updates.sh uses), so it will never succeed from the script.
**Option:** Rob clicks Update in HA (Settings > Apps > Terminal & SSH). updates.sh now skips it with a note instead of raising NEEDS-ROB every day.
**Risk:** none, cosmetic. Only 0.1 minor version behind.
