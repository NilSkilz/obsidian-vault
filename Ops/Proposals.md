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

## Cloudflare DDNS broken — public *.cracky.co.uk domains down (2026-08-05)
**Problem:** ALL public `*.cracky.co.uk` domains (plex, ha, vault, mc, plausible, seerr, etc.) are currently unreachable from outside the LAN. Root cause: `~/.config/jarvis/cloudflare.env`'s `CF_API_TOKEN` (used by the `*/10` DDNS cron, `Jarvis/bin/cloudflare-ddns.sh`) is now scoped only to the `kernowlabs.co.uk` zone, not `cracky.co.uk` — confirmed via the CF API (`/zones` with this token lists only kernowlabs.co.uk; the cracky.co.uk zone call 403s with "Unauthorized to access requested resource"). The token itself is valid/active, just wrong scope. This lines up with the file's mtime (2026-07-30 20:14), right in the middle of the Kernow Labs custom-domain work — looks like that token overwrote the cracky.co.uk-scoped one in the same env file. Last successful DDNS update was 2026-07-15 (pointed everything at `86.181.171.46`); the DDNS cron has been silently erroring (`ERROR listing records: ...Authentication error`) since, with no visible symptom until the house's WAN IP actually changed. Confirmed today: real WAN IP is now `109.149.184.92`, but DNS still resolves to the stale `86.181.171.46` — so every public domain times out. Local/LAN access is unaffected (verified Plex serving fine on `192.168.1.3:32400`).
**Option:** Rob mints a Cloudflare API token scoped to `Zone.DNS:Edit` on `cracky.co.uk` specifically (separate from the kernowlabs Pages-deploy token) and drops it into `~/.config/jarvis/cloudflare.env`. Once in place I can verify the next `*/10` cron run updates the records and re-check all public domains resolve/serve.
**Risk:** Credential creation on Rob's Cloudflare account — not something I can self-serve. Flagging as urgent since it's an active outage (family's remote access to Plex/HA/Vaultwarden/Tide all down), not just a future risk like the other entries here.

## Plausible Docker image updates (2026-07-09)
**Problem:** `updates.sh` patches apt packages on the host + all 12 LXCs and HA, but Plausible runs as a Docker Compose stack, so its images (`plausible/community-edition`, the DB images) are never pulled by the update routine. They'll silently drift out of date, including security fixes.
**Option:** Add a small step to `updates.sh` (or a separate weekly job) that does `docker compose pull && up -d` in `/opt/plausible-ce` on CT 111, with a health check after.
**Risk:** A major Plausible version bump can need a schema migration; an unattended `pull && up -d` could break analytics. I'd pin to minor updates or gate majors behind a NEEDS-ROB line. Low stakes (analytics, not family-facing) but raising since it's an automation touching a running service.

