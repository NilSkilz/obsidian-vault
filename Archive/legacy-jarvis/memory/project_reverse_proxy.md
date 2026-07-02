---
name: project_reverse_proxy
description: Remote access to containers is via Nginx Proxy Manager (HA add-on) on domain cracky.co.uk
metadata: 
  node_type: memory
  type: project
  originSessionId: 59525ed8-0f57-4031-ace5-c2957da221b0
---

Rob's remote access to home containers runs through **Nginx Proxy Manager (NPM)** — the `a0d7b954_nginxproxymanager` Home Assistant add-on (`ghcr.io/hassio-addons/nginxproxymanager`), NOT hand-rolled nginx. Domain is **cracky.co.uk**.

- **Admin UI / API:** port 81 (80/443 are the proxy). API health: `GET http://127.0.0.1:81/api/` → `{"status":"OK"}`.
- **Data:** container `/data` ← host `/usr/share/hassio/addons/data/a0d7b954_nginxproxymanager`. Proxy configs at `/data/nginx/proxy_host/N.conf` (NPM-owned — regenerated from `/data/database.sqlite`; **do not hand-edit**). Certs at `/data/letsencrypt/live/npm-N/`.
- **Existing subdomains (as of 2026-06-08):** ha, plex, sonarr, radarr, nzb, portainer, api, nginx (admin) — all `*.cracky.co.uk`.
- **SSL:** per-host Let's Encrypt (no wildcard). NPM auto-requests a cert when a proxy host is created (HTTP-01; port 80 is open). Wildcard would need DNS-01 + a DNS-provider API token.

**To add a subdomain (the right way):** drive the NPM REST API — auth (admin email+password) → JWT → `POST /api/nginx/proxy-hosts` with domain, forward host/port, SSL flags. **Needs:** NPM admin creds (hashed in DB, unrecoverable — ask Rob) AND a DNS record for the new subdomain pointing at the public IP (DNS provider TBC — asked Rob: Cloudflare vs registrar). I reach the container via `docker exec` (docker socket is mounted; `docker`/`docker compose` allow-listed). See also [[project_infra]].
