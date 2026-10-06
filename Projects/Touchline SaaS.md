# Touchline SaaS pivot (opened 06 Oct 2026)

Rob's brief (06 Oct): turn Touchline into a SaaS. Free tier capped at 5 minutes, subscription around £4.99/month for more. Home page shipped same day (touchline 6a7ec0c, live at https://touchline.cracky.co.uk): hero, how-it-works, pricing cards (Kickabout £0 / Season Ticket £4.99 "coming soon"), "why so cheap" privacy pitch, browser check, FAQ. No billing wired up; the Go Unlimited button says so honestly.

## The implications, ranked

### 1. AGPL. The big one, decide this first.
Reco video-stitcher is **AGPL-3.0** (confirmed in the cloned repo's LICENSE) and Touchline is a direct port of its crates (shaders near-verbatim, test suites ported). That makes Touchline a **derivative work**, so it is AGPL-bound too. What that means:

- Charging money is **fine**. AGPL does not forbid commercial use.
- But every user must be offered the **complete corresponding source**, and anyone may self-host it for free. We cannot close the source without replacing the Reco-derived code.
- Realistic options:
  a) **Embrace it (recommended).** Open-source the app, sell the hosted convenience: accounts, settings sync, support, club features, future cloud extras. Rugby parents do not self-host. Plausible SaaS businesses run this way (GitLab, Plausible).
  b) Ask the reco-project maintainers about a **commercial/dual licence**. Worth one polite email before launch.
  c) Clean-room rewrite: not realistic, it IS a port.
- Consequence for enforcement: the 5-minute gate will be visible in published source. See point 2.

### 2. The paywall is client-side, so it is a nudge, not a lock.
There is no server render step; everything runs in the user's browser. Any cap we enforce lives in JS the user controls. Design accordingly:

- Entitlement = signed token (JWT) issued by a tiny account service after Stripe confirms the sub; the app checks it before long exports.
- A motivated dev bypasses that in devtools, and with AGPL the bypass is one fork away. **Accept it.** The target customer is a rugby parent on a Sunday with 80 minutes of footage; £4.99 is below the faff threshold. Honesty + low price IS the enforcement.
- Corollary: do not spend effort on obfuscation; spend it on making paying frictionless.

### 3. Minimum viable stack (small, cheap)
- **Stripe Checkout + Customer Portal + Stripe Tax**: cards, SCA, VAT, invoices, cancel-any-time, all outsourced.
- **Auth**: magic-link email (Supabase Auth or Clerk free tiers, or a ~200-line worker). No passwords.
- **One small backend** (Cloudflare Worker + KV/D1): Stripe webhook → entitlement token; also gives us settings-sync later. The video path stays 100% client-side, that is the moat and the margin.
- Running cost at small scale: roughly £0-10/month + Stripe's ~1.5% + 20p per transaction. At £4.99/mo Stripe takes ~6%, fine.
- Needs a real domain (cracky.co.uk subdomain is dev). "Touchline" is a crowded sports mark (Touchline Embroidery, Touchtight, etc.); check UK trademark before buying merch-level branding. Candidate: touchline.app / usetouchline.com.

### 4. Boring-but-required admin
- Rob becomes a merchant: terms of service, privacy policy, refund policy. Sole trader is fine to start; revisit Ltd if it grows.
- **GDPR**: accounts hold an email address and a Stripe customer id, nothing else. Footage never uploads, children's data never touches us. Lead with that in the privacy policy, it is a genuine differentiator, and the architecture makes the DPIA trivial.
- **VAT**: UK registration threshold £90k so nothing to do domestically at first; selling digital services to EU consumers has NO threshold (OSS registration needed). Simplest launch: UK-only, let Stripe Tax flag the moment EU sales matter.
- Rob contracts at Superdry: a side SaaS is normally fine for a contractor, but worth one read of his contract's conflict/IP clauses before taking money.

### 5. Product and market realities
- **Chrome/Edge desktop only** today (WebGPU + WebCodecs). Safari/iPad-only households are out of the funnel; say so on the page (we do) rather than letting them bounce confused.
- **Seasonality**: rugby/football parents churn in May and return in September. "Season Ticket" naming leans into it; later add an annual "Full Season" price (~£39) to smooth it.
- **Free-tier definition** currently "exports up to 5 minutes long" per export. Alternative levers if abuse shows up: per-month cap, or watermark on free exports. Decide after real usage, not before.
- **Pricing sanity**: £4.99 vs Veo's ~£75/mo + £900 hardware is almost suspiciously cheap. It is defensible because our marginal cost is ~£0, and it prices like a no-brainer. Could test £6.99 later; do not go lower.
- **Safeguarding trust page**: users film kids. A short "filming junior sport properly" guide (club permission, both-teams consent, private sharing) costs an afternoon and buys real trust. We have the playbook in the DIY Veo file already.

## Next actions (when Rob says go)
1. Rob eyeballs the home page, tweaks copy/pricing names.
2. Decide the AGPL stance (recommend: publish repo + embrace open-core). Optionally email reco-project re dual licence.
3. Domain + trademark sanity check.
4. Stripe account + magic-link auth + entitlement worker (a weekend, not a month).
5. ToS/privacy pages, then flip "Coming soon" to live.
