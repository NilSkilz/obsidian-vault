# Twisted Boudoir Website (lead)

**Status:** Lead, first conversation 30 Sep 2026. Owner may want a new website.
**Contact:** Owner of Twisted Boudoir (Rob talking to them directly).

## What the business is

Kink-friendly studio rental in the Southwest (between Bristol and Exeter). "More than just a studio": photography/video studio hire with props, professional lighting, custom-built structures (steel truss, gothic posing cross, industrial swing), impact/sensory prop collections, event hosting with an on-site bar ("The Boudoir Bar"), workshops, private hire with tiered pricing.

## Current site audit (30 Sep 2026)

- **Stack:** WordPress. Plugins detected: **Amelia** (booking) and Newsletter. No WooCommerce, no page builder detected.
- **Pain point (their words via Rob):** they don't understand WordPress. They need an admin backend they can actually use to edit content.
- **Pages:** Home, Make a Booking, Private Hire Prices, Events and Workshops, plus footer pages (Find Us, Privacy, Terms, Rules, Contact, Customer Panel).
- **Design:** functional but dated. Long bulleted lists, weak hierarchy, galleries poorly integrated. The physical space is clearly impressive and the site doesn't sell it.
- **Booking:** Amelia plugin handles it. That's the one functional piece worth preserving or replacing carefully. No visible payment integration.
- **Oddities:** stray "Pink Apple Studios" branding mid-page (possibly the previous studio name or a copy-paste leftover, worth asking).

## Scope thinking

The real requirement is: owner edits content + working bookings, without touching WordPress.

Likely shape of a rebuild:
- Custom front-end (same TS stack as Rob's other projects) with a simple purpose-built admin: edit page copy, pricing tiers, gallery uploads, events list. Small fixed surface beats a general CMS for a non-technical owner.
- Booking: either keep/embed Amelia, or swap to Cal.com embed, or build a simple slot-request flow that emails them. Ask how they use Amelia today (paid bookings? approvals?) before deciding.
- Content is small (roughly 8 pages), so migration is an afternoon, the admin is the real build.

## Open questions for the owner

1. What do they actually edit most often? (Prices, events, gallery?)
2. How do bookings work today end to end: does Amelia take payment, or is it request-and-confirm?
3. What's the "Customer Panel" in the footer, is anything behind a login?
4. Hosting/domain: who controls the registrar and current hosting?
5. Budget/expectation: paid gig or favour?

## Deal shape (30 Sep 2026)

Rob's plan: build it himself, likely in exchange for free venue hire sometime, plus possibly a small monthly hosting charge. Not chasing a big invoice.

## Mockup (built 30 Sep 2026)

- Repo: `/home/jarvis/projects/twisted-boudoir-mockup` (local git only; renamed 19 Nov when the real build took the `twisted-boudoir` name). Vite + React + TS, single-page marketing mock. Target stack per Rob: React/Vite on Amplify.
- Design: near-black plum background, violet/fuchsia/pink gradients (Tide-adjacent but its own look), Fraunces display serif + Outfit body. Real photos pulled from their current site into `public/photos/`.
- Sections: hero (playroom wide shot), The Space feature grid, private-hire pricing tiers (sample prices), events/workshops list (sample), Boudoir Bar split, gallery, booking CTA, footer with an "Owners: edit site content" teaser for the custom-admin pitch.
- Served on LAN at http://192.168.1.11:4620 (python http.server on the dist build). Screenshots sent to Rob 30 Sep.
- **Public since 19 Nov 2026: https://twisted.cracky.co.uk** (NPM host 25, `Jarvis/bin/twisted-preview.sh` @reboot) so Rob can share it with the owner. Sample events now compute rolling future dates (next few weekends from whenever it's opened), and both the prices and events sections carry a "sample for the mock-up" note. Rebuild after edits: `npm run build` in the repo, the server picks up `dist` live.

## Owner's brief (19 Nov 2026, after seeing the mockup)

- Loves the colour scheme, wants a few visual tweaks.
- **Main need is bookings**, "what we have now but less complicated": automatic bookings into a calendar she can see and adjust, her existing payment gateways (which ones still unknown), automatic emails to customers with instructions + the "unmanaged" (unsupervised hire) info (she has or can write the copy).
- **Events: list only, no purchasing.** Tickets stay on Fet.
- Asked: same domain or start again? (Answer: same domain, swap over at launch, keep old URLs redirecting so traffic/Google rank carries over.)
- Asked: would Rob be paid emergency tech support? Not a novice, not techy.
- Asked for cost, "business is business".

### Price I suggested to Rob (19 Nov)
- Build: about **£1,500** (site + admin + booking/calendar/payments/emails), half up front, half at launch. Option to knock some off for venue-hire credit (the original swap idea).
- Ongoing: about **£35/month** for hosting, backups, keeping bookings/payments working, emergency support and small edits; bigger changes quoted separately.
- Caveat: custom booking with payments is the real build and the real support liability, so it's priced in, not a freebie. Need her gateway list before committing.

## Follow-ups

- Rob to continue the conversation; next step is the open questions above.
- If the owner bites: real prices/events from their current site, decide Amelia vs replacement booking flow, then scope the admin backend (the actual build).

## The build (started 19 Nov 2026)

Rob asked for the TB backend: Google Calendar-linked bookings, owner-set availability (e.g. Mon-Thu 08:00-20:00), settable prices, hardcoded login on `/admin`, Amplify Gen 2.

- **Repo:** `NilSkilz/twisted-boudoir` (private, Rob created it 19 Nov; pushed to `main`). Local: `/home/jarvis/projects/twisted-boudoir`. First commit went straight to main (empty repo); since then branch + PR (Rob hasn't said otherwise).
- **Shape:** Liaisons pattern. All logic in `shared/engine.ts`, one Lambda behind an AppSync `read` query + `call` mutation (API key), DynamoDB single table (pk/sk, RETAIN + PITR). LAN dev server runs the same engine with `.data/db.json`.
- **Availability** = weekly hours (multiple windows per day) minus closed dates, existing bookings + buffer, Google Calendar busy times (owner blocks time by adding an event in Google), notice period, max days ahead. London wall time, UTC storage, clock change tested.
- **Prices** = "hire options": name, length, price, optional deposit, show/hide, order.
- **Bookings** start `pending` (tentative in Google), owner marks confirmed / cancels / moves / notes them from a week-view calendar in `/admin`. Every change syncs to Google.
- **Google:** service account JWT via node:crypto (no googleapis dep). Needs the `TB_GOOGLE_SERVICE_ACCOUNT` Amplify secret (or `none`) before the first deploy, calendar shared with the SA email, calendar ID set in /admin Settings. README has the steps.
- **Admin login:** hardcoded in `shared/adminCredentials.ts`, username `admin`. Replace before the owner relies on it.
- **Verified:** 12 vitest tests, both typechecks, vite build, offline `cdk synth`, puppeteer flow (`/home/jarvis/tools/browser-check/tb-flow.js`, needs `TB_PW`): customer books on a phone, owner confirms in /admin.
- **LAN preview:** http://192.168.1.11:3020 (and /admin), `Jarvis/bin/twisted-bookings-preview.sh` @reboot. Not public on purpose (hardcoded password).
- **Public site wired in (19 Nov, PR #1, branch `feature/public-site`):** mockup is now `/`, booking moved to `/book` inside the same nav/footer, homepage prices pulled live from /admin, "Book this" goes to `/book?package=<id>`. Events are display only with "On FetLife" links (placeholder events, `FETLIFE_URL` still generic `fetlife.com`). Per-page CSS chunks; gotcha: a ternary of `import()`s made Vite give every page the homepage's CSS preloads, so the imports are separate functions.
- **Her current setup (pulled from the live WordPress/Amelia site, 19 Nov):** gateways **PayPal + Square** (Stripe/Mollie off). Hours 7 days 10:00-23:30. Amelia charges 1h £45, 2h £70, 3h £105, 4h £140, 5h £175, 6h £210, 8h £280 (standard, up to 4 people); group bookings same prices +£10 per extra person over 4. These are now the defaults. **Mismatch to flag to her:** her "Private hire prices" page says £55 for 1 hour and £45/h for 2h+ (so 2h = £90), but Amelia actually charges £35/h-ish. Also her Amelia "8 Hour Booking" is set to 6 hours long (bug).
- **Not built yet:** payments (PayPal + Square), group pricing (guest count), customer/owner emails (SES, she has the unmanaged-hire copy), pulling edits made directly in Google back into bookings, real events + FetLife URL.
- **Rob to do:** connect the repo in the Amplify console, set the secret, add the SPA rewrite for /admin (in README).
