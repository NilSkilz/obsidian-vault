# Play Room Speakers (Snapcast Pis)

Two Raspberry Pis in the play room, each driving an amp, running as Snapcast clients of Music Assistant on Home Assistant. Multi-room audio from the NUC era, rediscovered 2026-08-22, fully documented and tidied 2026-08-25. See [[Home Assistant]] for the HA side and `Context/Infrastructure.md` for the network map.

## The two Pis

| | Main speakers | Ambient speakers |
|---|---|---|
| Hostname | `play-room-main-speakers` | `play-room-ambient-speakers` |
| IP | 192.168.1.219 | 192.168.1.108 |
| MAC | b8:27:eb:a5:b3:a8 | b8:27:eb:38:f0:e0 |
| Hardware | Raspberry Pi 3 Model B (arm64) | Raspberry Pi Zero W (armv6l) |
| OS | Debian 13 trixie, kernel 6.12 rpi-v8 | Raspbian 13 trixie, kernel 6.12 rpi-v6 |
| Audio out | onboard `bcm2835 Headphones` (card 0) | `USB PnP Sound Device` (card 0, USB DAC) |
| Snapclient | v0.31.0 | v0.31.0 |

Both IPs are DHCP, not reserved (they've been stable, but if one moves, look them up by MAC on the UDM).

## Access

- SSH user **`rob`**, password **`F0rsak3n229!`** (same on both). No `pi` user.
- My ed25519 key (`jarvis@192.168.1.11`) is in `~/.ssh/authorized_keys` on both, so from this box `ssh rob@192.168.1.219` / `ssh rob@192.168.1.108` is passwordless. `rob` has sudo (password prompt).

## How snapclient is configured

The server address is **hardcoded in the systemd unit**, not in `/etc/default/snapclient` (that file exists but `SNAPCLIENT_OPTS` is empty):

```
/etc/systemd/system/snapclient.service
ExecStart=/usr/bin/snapclient -h 192.168.1.4
User=rob, Restart=always
```

Since 2026-08-25 both point **directly at `192.168.1.4:1704`**, the builtin snapserver in Music Assistant on HA (Snapcast provider enabled). Before that they pointed at `192.168.1.2` (the dead NUC's IP, now the Proxmox host) and a DNAT forwarder on the host bridged the gap; that forwarder (`snapcast-forward.service`) is now disabled. The unit file is still on the host, harmless, delete if it offends.

To change the server again: `sudo sed -i 's|-h .*|-h NEW.IP|' /etc/systemd/system/snapclient.service && sudo systemctl daemon-reload && sudo systemctl restart snapclient`, then confirm with `ss -tn | grep 1704`.

## Health checks

- `systemctl is-active snapclient` on each Pi.
- `ss -tn | grep 192.168.1.4:1704` should show one ESTAB connection.
- Both appear as players in Music Assistant on HA; if HA reboots they reconnect on their own (`Restart=always`, 5s).
- SD cards ~5-6% used as of 2026-08-25.

## History

- 2026-08-22: found the Pis, worked out they were pointing at the dead NUC, stood up the host-side DNAT forwarder as a stopgap, enabled Snapcast in Music Assistant.
- 2026-08-25: Rob remembered the password, key installed, snapclient repointed at `.4`, forwarder retired.
