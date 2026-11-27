# Jarvis box credentials

Private to Rob. Aimee's sessions run as the `jarvis` user, so this must never live in a shared file.

## jarvis user (CT 110, 192.168.1.11)

- **Password:** `xjqXK24rZit3dCrv`
- Reset 2026-11-27 from the Proxmox host (`ssh proxmox "pct exec 110 -- chpasswd"`). The 2 July rebuild password was never recorded.
- This is also the sudo password on the box.
- Recovery if lost again: same `pct exec 110` route from the host (`~/.ssh/config` alias `proxmox`).
