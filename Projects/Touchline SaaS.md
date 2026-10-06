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

### 6. Repo split (decided 06 Oct)
Two repos:
- **touchline** (public, AGPL): the whole app including the home page and the client-side entitlement checks. The homepage is just part of the app shell; splitting it out buys nothing and doubles the deploy story.
- **touchline-cloud** (private): the Stripe webhook worker, magic-link auth, entitlement-token issuing, any future settings-sync. Legally clean: AGPL's network clause binds the AGPL *program*, and a separate backend service talking to it over HTTP is its own work, not a derivative (standard open-core split, same as GitLab/Plausible). Practically right too: Stripe webhook secrets, price IDs and the token-signing key never belong anywhere near a public repo, and the issuing logic staying private means the only public half of the paywall is the client check we already accepted as a nudge.
Fuss level: one extra repo with one Worker and a wrangler deploy. Create it when step 4 below starts, not before.

### 7. Capture app + open hardware (Rob, 06 Oct)
Rob is building an iOS capture app (left/right phones, blacked screen, master phone over peer networking, possible App Store release) and publishing the mount STL. Details in `Projects/DIY Veo.md`. SaaS relevance:
- **The free capture app is the acquisition funnel.** A "Process your match" button in the app pointing at Touchline web is distribution Veo cannot match on price.
- If the app embeds sync/start-time metadata, app-captured footage can skip the Sync step in the web app entirely: smoother onboarding for exactly the paying audience.
- The app is Rob's own code (no Reco derivation), so its licence is free choice regardless of the AGPL story; open-sourcing it fits the DIY-kit positioning.

## Next actions (when Rob says go)
1. Rob eyeballs the home page, tweaks copy/pricing names.
2. Decide the AGPL stance (recommend: publish repo + embrace open-core). Optionally email reco-project re dual licence.
3. Domain + trademark sanity check.
4. Stripe account + magic-link auth + entitlement worker (a weekend, not a month).
5. ToS/privacy pages, then flip "Coming soon" to live.

## Naming (06 Oct 2026): "Touchline" is too crowded, shortlist found

Checked because Rob asked. The space is genuinely busy, at least five live sports products trade as Touchline, several in UK grassroots football, and one (Touchline Tracker, touchlinetracker.co.uk) is a grassroots football VIDEO highlights platform, direct collision. Also touchlineapp.com (assistant-coach app), gettouchline.app (tournament manager), touchlineapp.uk, touchlinefc.co.uk (club websites), a Touchline coaching app on the App Store. Renaming before buying domains/branding is the right call.

Shortlist (domains RDAP-verified 06 Oct):

1. **Huer** (front-runner). The Cornish cliff-top lookout who watched for pilchard shoals and directed the boats below; a person stood up high watching the field, guiding the team. Fits the Crackington/sea naming pattern (Tide, Haven). Zero software/app clashes found. **huer.app, huer.football, gethuer.com, huerapp.com all unregistered.** huer.co.uk is taken (small site behind a bot-blocker). Bonus flavour: the huer's shout was "Hevva!", nice for release names/free tier copy.
2. **Matchmast**: literal (phones up a mast at a match), self-explaining, no clashes. matchmast.com and matchmast.co.uk unregistered.
3. **Crowsnest**: same lookout idea, but crowsnest.app/.com taken and the mainsail-crew "crowsnest" webcam tool owns the name in camera software. Only crowsnest.football free. Third place.

Rejected: TopBins (topbins.app taken), MatchReel (.com/.app taken, SportReel/MatchCut adjacent), Gantry (gantry.football + gantrycam.com taken, Gantry web framework), mast.football alone too thin.

### Rugby round (06 Oct, Rob found Huer too obscure and asked for rugby names)

New front-runner: **TouchJudge**. The touch judge is the official who stands ON the touchline watching the whole game, so it keeps the original Touchline concept but names the watcher instead of the line. Self-explaining to anyone in rugby, readable even outside it. No software/app clash found (searched; only the rugby role itself and unrelated video-analysis tools). Domains RDAP-verified 06 Oct: **touchjudge.app, touchjudge.co.uk, touchjudge.io, gettouchjudge.com all unregistered**; touchjudge.com is registered but only a registrar parking lander, nobody trades under it.

Backups from the same round:
- **Garryowen** (the up-and-under high kick; the camera literally hangs in the air over the pitch). garryowen.app free, .com taken. No software clash, but the famous Limerick club owns the word culturally; product would always be "like the club".
- **DropGoal**: dropgoal.app + dropgoal.co.uk free, .com taken. Fine, but less on-concept for a camera.
- **Uprights**: uprights.app free, .co.uk taken. Generic-ish.

Checked and rejected: TMO (perfect concept, the video official, but tmo.app taken and the acronym is owned by T-Mobile/Thermo Fisher associations), Gainline (gainline.app taken, Gain Line Analytics is an existing rugby analytics firm), Fifty22 (both domains taken), Lineout/Grubber/Highball (.app all taken).
