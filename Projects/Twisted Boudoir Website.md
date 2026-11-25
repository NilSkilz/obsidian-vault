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

- **Repo:** `NilSkilz/twisted-boudoir` (private, Rob created it 19 Nov; pushed to `main`). Local: `/home/jarvis/projects/twisted-boudoir`. **Rob, 19 Nov: commit straight to `main` for now** (no branch/PR). PR #1 was merged into main the same afternoon.
- **Shape:** Liaisons pattern. All logic in `shared/engine.ts`, one Lambda behind an AppSync `read` query + `call` mutation (API key), DynamoDB single table (pk/sk, RETAIN + PITR). LAN dev server runs the same engine with `.data/db.json`.
- **Availability** = weekly hours (multiple windows per day) minus closed dates, existing bookings + buffer, Google Calendar busy times (owner blocks time by adding an event in Google), notice period, max days ahead. London wall time, UTC storage, clock change tested.
- **Prices** = "hire options": name, length, price, optional deposit, show/hide, order.
- **Bookings** start `pending` (tentative in Google), owner marks confirmed / cancels / moves / notes them from a week-view calendar in `/admin`. Every change syncs to Google.
- **Google:** service account JWT via node:crypto (no googleapis dep). Needs the `TB_GOOGLE_SERVICE_ACCOUNT` Amplify secret (or `none`) before the first deploy, calendar shared with the SA email, calendar ID set in /admin Settings. README has the steps.
- **Admin login:** hardcoded in `shared/adminCredentials.ts`, username `admin`. Replace before the owner relies on it.
- **Verified:** 12 vitest tests, both typechecks, vite build, offline `cdk synth`, puppeteer flow (`/home/jarvis/tools/browser-check/tb-flow.js`, needs `TB_PW`): customer books on a phone, owner confirms in /admin.
- **LAN preview:** http://192.168.1.11:3020 (and /admin), `Jarvis/bin/twisted-bookings-preview.sh` @reboot. Not public on purpose (hardcoded password).
- **Public site wired in (19 Nov, PR #1, now merged to main):** mockup is now `/`, booking moved to `/book` inside the same nav/footer, homepage prices pulled live from /admin, "Book this" goes to `/book?package=<id>`. Events are display only with "On FetLife" links (placeholder events; FetLife link now admin-editable, see social links). Per-page CSS chunks; gotcha: a ternary of `import()`s made Vite give every page the homepage's CSS preloads, so the imports are separate functions.
- **Her current setup (pulled from the live WordPress/Amelia site, 19 Nov):** gateways **PayPal + Square** (Stripe/Mollie off). Hours 7 days 10:00-23:30. Amelia charges 1h £45, 2h £70, 3h £105, 4h £140, 5h £175, 6h £210, 8h £280 (standard, up to 4 people); group bookings same prices +£10 per extra person over 4. These are now the defaults. **Mismatch to flag to her:** her "Private hire prices" page says £55 for 1 hour and £45/h for 2h+ (so 2h = £90), but Amelia actually charges £35/h-ish. Also her Amelia "8 Hour Booking" is set to 6 hours long (bug).
- **Group pricing + emails (19 Nov, commit a1841c1 on main):** booking page has a people stepper with a live total (hire price + £10 a head over 4, max 12, all editable in /admin > Prices); homepage states the group rate. Emails via SES: customer on book / confirm / move / cancel, owner alert on every new booking with Reply-To set to the customer; per-change "email the customer" tickbox in admin; sender, owner address and the instructions/unmanaged-hire text live in /admin > Settings (empty sender = emails off). LAN dev server writes emails to `.data/outbox/` instead of sending. 18 unit tests + headless browser flow (6 people = £90, three emails landed) pass.
- **Payments (built 19 Nov, 15:40):** her policy is **full payment at booking, no refunds, bookings get moved instead** (Rob, 19 Nov). PayPal + Square hosted checkouts; slot held 30 min while paying; confirms + Google + emails once paid; no-refund wording editable in admin and shown before paying. Deposit field dropped from admin. Keys go in the Amplify secret `TB_PAYMENTS` (JSON, or `none`); setup steps in the repo README. Only tested against a fake gateway so far: needs one sandbox run per gateway, then her live keys.
- **Not built yet:** her real unmanaged-hire text (placeholder in place), day-before reminder email, pulling edits made directly in Google back into bookings, real events.
- **Needs before emails go live:** SES domain verification (DKIM records on her domain's DNS) + SES production access, in whichever AWS account hosts it.
- **Rob to do:** connect the repo in the Amplify console, set the secret, add the SPA rewrite for /admin (in README).

## Booking types, events, white-label admin (21 Nov 2026, commit 5ef8105 on main)

- **Booking types** now first-class, mirroring her Amelia categories (checked live 21 Nov): **Standard** (up to 4, 1-8h, general 12h notice) and **Group** (4 included, +£10/head once per booking, max 34, 2-8h, no 1-hour, **1h notice**). Same hourly prices. Each type has its own rules + hire options; /book is type, then length; booking label reads "Group booking, 3 hours". Old configs auto-upgrade.
- **Events** managed in /admin > Events (add/edit/duplicate/hide, tickets link). Homepage "What's on" reads them live; empty state points to FetLife. Event button wording changed 23 Nov (`ae46800`) from "Tickets ↗" to "Event Info ↗" (admin field renamed to match); events with no link still say "On FetLife ↗". Preview has 3 sample events (Rope Fundamentals, Twisted Social, Low-Light Masterclass), delete before launch.
- **White-label admin:** product name **"Admin"** (was "Berth" until 23 Nov, Rob wanted generic) (`src/admin/brand.ts`), neutral teal theme in `src/admin/admin.css`, light + dark, sidebar on desktop, top bar on phone. Venue name + booking-ref prefix live in Settings > Business. Rob's idea: resell it to other venues.
- **Homepage pricing** redesigned: one card per booking type with a price list, instead of seven near-identical boxes.
- Preview dev data was reset to the new defaults (old db backed up at /tmp/tb-db-backup.json).
- Still open: the Amelia "8 Hour Booking" is actually 6h long on her current site (both types).

## Settings fixes (23 Nov 2026, commit 02480a3 on main)

- **"Your email" takes several addresses**, comma-separated (Rob wants his + the owner's for testing). All get the new-booking alert; customer Reply-To uses the first. Stored as one normalised string, `ownerEmails()` in `shared/emails.ts`; `Email.to` is now `string[]`.
- **Google push button** was greyed out because no service account key is installed (calendar ID alone isn't enough), and the page didn't say so. Now it explains itself, shows the SA address to share the calendar with once connected, saves an unsaved ID before pushing, and probes freeBusy first so an unshared calendar returns a clear error instead of "sent 0".
- **Still the gate:** someone (Rob) has to create the Google Cloud service account + JSON key, then put it in the `TB_GOOGLE_SERVICE_ACCOUNT` Amplify secret (or `.data/google-service-account.json` on the LAN preview). For resale an OAuth "Connect Google" button would be the cleaner long-term answer.
- Reminder: the LAN preview never sends email (writes to `.data/outbox/`), and SES in sandbox mode only delivers to verified addresses, so both test inboxes need verifying in SES until production access is granted.
- **Admin login (for Jarvis quick reference, hardcoded in `shared/adminCredentials.ts`):** username `admin`, password `rbZ5Io5r3IRKrgcd`. LAN preview only (:3020), not on public internet; replace before the owner relies on it.

### Google Calendar setup (23 Nov 2026)

- Rob created the service account `twisted-email-service@twisted-boudoir.iam.gserviceaccount.com` in the `twisted-boudoir` GCP project (name is a misnomer, it's only used for Calendar, not email, which stays on SES).
- **No IAM roles needed** on the service account itself, that's the trap. Calendar access comes purely from sharing the calendar with it.
- Remaining steps for Rob: enable the Calendar API in that project, create a JSON key for the service account, share her Google Calendar with that address as "Make changes to events", then send the JSON to Jarvis or paste it into the `TB_GOOGLE_SERVICE_ACCOUNT` Amplify secret. Watch for the org policy `iam.disableServiceAccountKeyCreation` blocking key creation.
- **Done 23 Nov night:** Rob sent the JSON key, Calendar API confirmed on, key verified working and installed on the :3020 preview. Still to do before it's live: share her actual calendar with the service-account address and push the calendar ID in admin > Settings.
- **Amplify first deploy:** needs exactly two secrets set before the first build or it fails: `TB_GOOGLE_SERVICE_ACCOUNT` (the whole JSON, unedited) and `TB_PAYMENTS` (`none` until her gateway keys arrive, then the JSON blob per gateway). Plus the SPA rewrite for `/admin` (source `</^[^.]+$/>`, target `/index.html`, type 200 Rewrite). Rob started this deploy 23 Nov 21:36.

## Domain / email DNS (checked 23 Nov 2026)
- twistedboudoir.co.uk DNS is hosted at WHUK (nameservers shn47/48.whukns.com); MX points at the domain itself, so office@ is a mailbox on that host.
- Existing SPF (long ip4 list + include:pinkapplestudios.co.uk) and DMARC `p=none` already present.
- SES sending from office@ only needs the 3 Easy DKIM CNAMEs added at WHUK; no SPF change needed (default MAIL FROM is amazonses.com, DKIM gives DMARC alignment). No domain transfer required.
- Cutover plan (23 Nov): no nameserver change needed (WHUK panel doesn't expose NS anyway). `www` is currently a CNAME to the apex; swap it for Amplify's CloudFront target + add Amplify's ACM validation CNAME. Map only `www` in Amplify. LEAVE the apex A record (213.175.196.66): the MX points at the apex, so changing it kills her mail. Apex already 301s to https://www.../same-path via her WordPress (Let's Encrypt cert, paths preserved), so old links land on Amplify. If the WP hosting is ever cancelled, replace that redirect (WHUK forwarding or .htaccess) and point MX at a mail. host first.
- Rob got WHUK account/DNS access 23 Nov 22:22. Decision: hold off on the `www` CNAME swap until ready to go fully live, not before (emails already sorted separately).
- twistedboudoir.com (checked 23 Nov): registered at **IONOS** (1&1), since 29 Jun 2016, renews 29 Jun 2027. DNS on IONOS too (ns1070.ui-dns.*). MX = mx00/mx01.ionos.co.uk, SPF includes IONOS, apex A 217.160.0.199 (IONOS parking/builder). So the .com mail is IONOS-hosted, entirely separate from WHUK. Managed in a separate IONOS account.
- If DNS ever moves to Route 53: copy EVERY record (MX, SPF, DMARC, DKIM CNAMEs) first or her inbox and SES both break.

## Contact form (23 Nov 2026, ac46377 + f260777 on main)
- Homepage "Get in touch" section (`#contact`, `src/site/Contact.tsx`); "Contact us" buttons + footer link point to it. Engine op `contact` (public, no token).
- Emails go to Settings `contactEmail` (admin > Emails, "Contact form messages go to"), **several comma-separated addresses allowed**, default `office@twistedboudoir.co.uk`, empty = falls back to the owner alert addresses. Reply-To is the sender. Needs `emailFrom` set (same as booking emails).
- Spam guard: hidden honeypot field `website` + must be on the page 3s+ (`CONTACT_MIN_MS`); bots get a fake "sent". No rate limit or message storage: a send failure shows the visitor an error rather than losing the message silently.
- SES sandbox note: once the twistedboudoir.co.uk domain identity is verified, office@ can receive even before production access (recipient on a verified domain). Any other recipient (e.g. Rob's) still needs verifying until production access.
- LAN preview `.data/db.json` now has emailFrom = office@twistedboudoir.co.uk so preview emails land in `.data/outbox/`. Browser check script: `/home/jarvis/tools/browser-check/tb-contact.js`.

### Small-print pages (23 Nov 2026, `6c6801a`)
- `/find-us`, `/rules`, `/terms`, `/privacy`, each editable in **admin > Pages** (title, intro line, body; Find us also a map pin). Text lives in `Config.pages`, defaults in `shared/sitePages.ts` (her own wording from the WordPress site). Public engine op `page`, admin op `admin.savePage`.
- Body format: one line = paragraph, `## ` heading, `- ` bullet; URLs, emails and `///w3w` addresses auto-link. No HTML, no `dangerouslySetInnerHTML`.
- Old WordPress URLs alias to the same pages (`/terms-of-use`, `/privicy-policy` [her typo], `/privacy-policy`, `/house-rules`, `/directions`), covered by the existing Amplify `</^[^.]+$/>` rewrite.
- Her live `/rules/` page is actually a stale copy of the terms (Pink Apple, tickets wording). New House rules = the on-site conduct sections only (age/ID, consent, arriving, alcohol, sharps/flames [only on her rules page], breakages, equipment, CCTV, filming, insurance, behaviour). Terms = her `/terms-of-use/` verbatim, tidied.
- Footer blurb now says "just off the M5 at junction 23, Bridgwater" (was "exact address shared on booking"; her site publishes the address openly). Nav "Find Us" goes to `/find-us`.
- Footer social links (23 Nov): Facebook /Twistedboudoir, Instagram /twistedboudoir, X /TwistedBoudoir (from her WP site), FetLife /TwistedBoudoir (from Rob). Editable in admin > Settings > Social links since 4501e82: `settings.socials`, defaults in `shared/defaults.ts`, public `socials` op feeds `useSocials()` in `src/site/Chrome.tsx`. Empty hides the icon; FetLife is also the events fallback link. `FETLIFE_URL` constant is gone.
- Footer credit (23 Nov, 6cf59f7): colophon reads "Site by Kernow Labs" linking https://kernowlabs.co.uk (Rob's web-design brand), right-aligned opposite the copyright.
- **For her to fix:** privacy policy data-controller email is `info@pinkapplestudios.co.uk`, "Last updated April 2026", and it doesn't mention the new site's contact form, Google Calendar or AWS email. Browser check: `/home/jarvis/tools/browser-check/tb-pages.js` (needs `TB_PW`).

## Priority order (25 Nov 2026)
Needs Rob/her: Amplify build going green (started 23 Nov), her calendar shared with the service account, SES DKIM + production access, her PayPal/Square keys + one sandbox booking each, her real content (events, price fix, privacy policy), replacing the hardcoded admin password, then the `www` CNAME swap. Jarvis can build ahead of that: proper admin login, day-before reminder email, Square webhook for instant paid-booking confirmation, syncing Google edits back into bookings. Picked next: admin login + reminder email, while Rob confirms the Amplify build.
