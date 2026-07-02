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

## Set up SSH access from jarvis container to Proxmox host (2026-07-02, updated 21:0x)
**Problem:** The "check all LXC/VMs are up" recurring heartbeat task needs `pct list`/`qm list` on 192.168.1.2. Status has moved twice now: first host-key verification failure (no known_hosts entry), then a full port-22 timeout (host/port unreachable). As of this run, the host is reachable again and SSH is answering — but `ssh root@192.168.1.2` now fails on auth: "Permission denied (publickey,password)". The jarvis container has no local keypair (`~/.ssh` has no `id_ed25519`/`id_rsa`) to offer, and root password login isn't set up for it either.
**Option:** Rob's call on the approach: (a) generate a keypair in the jarvis container and add the pubkey to the Proxmox host's `root` `authorized_keys`, or (b) create a dedicated non-root user on the host with sudo for just `pct list`/`qm list`, or (c) skip SSH entirely and expose container/VM status some other way (e.g. Proxmox API token). Whichever way, needs a decision + action on the host side that I can't do from inside the container.
**Risk:** Nothing risky actioned. Flagging the auth failure is now the actual blocker (network path is fine) so the next fix attempt goes straight to credentials, not the network.

## Install Plausible on Proxmox — Trello card (2026-07-02)
**Problem:** Trello "Jarvis" board, To Do list, has a card "Install Plausible on Proxmox" (self-host Plausible Analytics in its own container/VM). This is a real infra build (new container/VM, installing and configuring a service) — not a safe/reversible read-only action for the heartbeat to take unattended.
**Option:** Rob confirms scope (new LXC vs VM, resource sizing, which domain/analytics sites it should track) and either does it together in a session or explicitly clears me to build it solo.
**Risk:** Creating a new container/VM and exposing a service is exactly the kind of external/irreversible-ish action the heartbeat rules say to propose rather than just do. Card left in To Do, untouched.
