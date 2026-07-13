# Craft ERP

Aimee's craft business (leatherwork, candles) inventory and sales app. Single user, local-first, no cloud.

## What it is

- Repo: `github-personal:NilSkilz/ERP-app` (private). Local clone: `~/projects/ERP-app` on the jarvis LXC.
- Stack: Electron + Angular 20 (PrimeNG) + better-sqlite3 + Drizzle + tRPC over IPC. The main process owns the DB and domain logic; the renderer is pure UI over a typed tRPC link. Money is integer pence (banker's rounding); stock movements are immutable. See the repo's `README.md` and `DECISIONS.md`, they're good.
- Started life as a Mac desktop app. The renderer already had an HTTP fallback link (for phones on the LAN), which is what made headless hosting cheap.

## Hosting (2026-07-13)

- **Live at `https://erp.cracky.co.uk`** (and `http://192.168.1.10:7273` direct on the LAN) on CT 116 (`craft-erp`), systemd `craft-erp.service`. Full detail (deploy steps, backups, gotchas) in `Context/Infrastructure.md`, Craft ERP section.
- The app has no login of its own, so the subdomain sits behind an NPM basic-auth gate (access list `craft-erp-lan-or-auth`): **user `aimee`, password `t5AMWCZ7Xyxu5IqyrXCJ`** (repo is private, Rob keeps creds in the vault). LAN IPs are configured to bypass, but hairpinned home traffic still shows the prompt once per browser. Worth a Vaultwarden entry.
- I added a headless server entry (`src/server/index.ts`) on branch `feat/headless-web-server`: same domain code and router, no Electron, serves API + built renderer from one port. PR open for Rob: https://github.com/NilSkilz/ERP-app/pull/new/feat/headless-web-server (no `gh` CLI on this box, so the PR needs creating from that compare link, or I retry when `gh` exists).
- The Electron desktop app still works unchanged; the two entries share everything below `src/main/`.
- On the Tide System page as a parents-only card ("Craft business stock & sales") linking to erp.cracky.co.uk. Kids' accounts don't see it.

## Watch-outs

- Anyone with the basic-auth creds (or on the LAN) has full read-write; there is no per-user model. If this ever grows beyond Aimee+Rob, the app needs real auth.
- The browser renderer talks to the API same-origin (fixed 2026-07-13 so the HTTPS subdomain works). The one exception is the Vite dev server on port 5173, which hops to `:7273`; if the dev port ever changes, `src/renderer/app/core/trpc.client.ts` needs to know.
- `npm install` in the repo rebuilds better-sqlite3 for Electron's ABI (postinstall hook). Run `npm rebuild better-sqlite3` after installing to run tests or the server under plain node.
- Migrations run on service start; schema changes just need the new `drizzle/` files shipped with the deploy.
