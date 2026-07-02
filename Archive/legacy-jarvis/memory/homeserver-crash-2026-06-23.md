---
name: homeserver-crash-2026-06-23
description: "HomeServer recurring crashes = kernel stack-protector panic (corruption in __schedule), NOT thermal/iGPU. Cause = memory corruption, likely bad RAM. memtest86+ pending."
metadata: 
  node_type: memory
  type: project
  originSessionId: d1d09aff-be71-4066-bf6c-499370f9d677
---

HomeServer (i3-8109U NUC, HA Supervised on Debian 12) hard-froze at **00:11:53 on 2026-06-23**, dead ~10 min until Rob power-cycled it at 00:21.

**Confirmed NOT thermal this time:** CPU package temp was 61–63°C at crash (recorder sensor `sensor.homeserver_cpu_package_temp`). This partially counters [[homeserver-thermal-problem]] — at least this crash was a lockup, not an overheat. (The 91°C reading right after reboot is just the cold-boot surge.)

**Signature = kernel panic, not app crash:** HA core logged normally until `00:11:53.959`, then total silence till 00:21 restart. Recorder temp sensor last point 00:11:47 (63°C), first post-boot point 00:22:59 (91°C surge, cooling). The systemd journal *is* persistent (`/var/log/journal/`); its apparent end at 20:50 is just idle silence on a quiet host — HA runs in Docker so its logs live in container json files, not the host journal. NOT a fsync issue.

**KEY CORRECTION to prior belief:** kernel logs ARE captured. `efi_pstore` backend is active; `systemd-pstore.service` archives each panic to `/var/lib/systemd/pstore/<id>/dmesg-efi-*` (root-owned, 0600). `journalctl -k` is empty only because journald doesn't ingest the kmsg buffer here — pstore is the real source.

**Recurring hard-panic pattern** (kernel-written timestamps from pstore dump file mtimes): 2026-06-11 18:06, 2026-06-17 13:17, 2026-06-19 20:28, 2026-06-23 00:12. 4 panics in 12 days, no time-of-day pattern (idle + active both). Box usually stays dead until Rob manually reboots (down 17–47h on earlier ones); last night caught in 8 min. **No working hardware watchdog** → no auto-recovery.

**Environment:** BIOS BECFL357.86A.0077 dated 2019-11-27 (old; NUC8 has newer). cmdline = `quiet`, no `intel_idle`/`i915`/C-state mitigations. Root on cheap DRAM-less SanDisk SSD Plus 120GB (`sda`); 11TB WD `sdb` for media.

**ROOT CAUSE FOUND (06-23 boot dump, read by Rob via sudo):**
```
Kernel panic - not syncing: stack-protector: Kernel stack is corrupted in: __schedule+0xa06/0xa20
```
Stack-canary smash caught in the scheduler at 12.3h uptime → **kernel memory corruption**, almost certainly **bad/flaky RAM**. The `i915` lines in the dump are stale boot-log (timestamp [6.6s]), NOT the cause — iGPU suspect retired. Thermal/C-state retired too. `__schedule` is just the hottest always-running fn, so it's where the canary check trips, not the corruption site.

**CONFIRMED hardware (cross-dump comparison done):** 3 DIFFERENT panic types at random uptimes — 06-11 `Fatal exception in interrupt` (68.6h up), 06-19 `Fatal exception in interrupt` (8.3h), 06-23 `stack-protector corrupted in __schedule` (12.3h). Different signatures + random uptimes = hardware, not a software bug. **Single 8GB SO-DIMM in SODIMM1** (SODIMM2/Channel B empty), SPD half-blank (`Manufacturer: 0000`, no part number = generic/no-name module). That one stick is the prime suspect.

**Fix plan (priority):** (1) reseat the SODIMM1 stick — free. (2) memtest86+ overnight = definitive. (3) best: swap in known-good RAM / add a 2nd 8GB (single 8GB also cramped for the container stack; gains dual-channel). (4) ✅ DONE 2026-06-23: watchdog/auto-recovery installed — `/etc/systemd/system.conf.d/watchdog.conf` (`RuntimeWatchdogSec=30s`, iTCO_wdt armed, verified `RuntimeWatchdogUSec=30s`) + `/etc/sysctl.d/99-panic-reboot.conf` (`kernel.panic=10`, `kernel.panic_on_oops=1`, both live). Box now self-reboots in 10–30s instead of sitting dead 17–47h. Still a safety net, NOT a fix — RAM (reseat + memtest86+) is the real job.
