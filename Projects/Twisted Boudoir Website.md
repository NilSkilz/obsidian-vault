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

- Repo: `/home/jarvis/projects/twisted-boudoir` (local git, no remote yet). Vite + React + TS, single-page marketing mock. Target stack per Rob: React/Vite on Amplify.
- Design: near-black plum background, violet/fuchsia/pink gradients (Tide-adjacent but its own look), Fraunces display serif + Outfit body. Real photos pulled from their current site into `public/photos/`.
- Sections: hero (playroom wide shot), The Space feature grid, private-hire pricing tiers (sample prices), events/workshops list (sample), Boudoir Bar split, gallery, booking CTA, footer with an "Owners: edit site content" teaser for the custom-admin pitch.
- Served on LAN at http://192.168.1.11:4620 (python http.server on the dist build). Screenshots sent to Rob 30 Sep.

## Follow-ups

- Rob to continue the conversation; next step is the open questions above.
- If the owner bites: real prices/events from their current site, decide Amelia vs replacement booking flow, then scope the admin backend (the actual build).
