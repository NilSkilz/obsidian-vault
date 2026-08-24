# Domain migration: tethered.me.uk → tetheredapp.co.uk

Drafted 2026-08-24. Status: **parked until Rob calls go-live**. Currently the redirect runs the OTHER way (.co.uk 301s to .me.uk via NPM on CT 108, set up 23 Aug).

## Correction to the assumption

It's **Amplify Hosting**, not AppSync, where the custom domain lives. AppSync is the GraphQL API; clients hit its own URL from `amplify_outputs.json` regardless of the site domain, so nothing changes there.

## The two real gotchas (users, not DNS)

1. **Anonymous users lose everything.** `LocalStorageAdapter` keeps the entire free-tier/anonymous dataset (scenes, checklists, answers, tasks) in localStorage, which is origin-bound. A 301 to the new domain silently wipes it. Need a handoff: a one-time export/import step (old origin serializes to a URL fragment or postMessage iframe on the new origin) shipped BEFORE the flip, or accept the loss and say so.
2. **Everyone gets logged out and installed PWAs break.** Cognito tokens are localStorage too, and home-screen PWA installs are pinned to the old origin. All users re-log-in on the new domain; PWA users must reinstall from the new origin (InstallPrompt will re-fire, at least).

## Cutover checklist

### Before (code, on develop, ship WITH the flip not before)
- `amplify/functions/*`: hardcoded `https://tethered.me.uk` fallbacks in createCheckoutSession, createPortalSession, createDonationSession, sendPartnerInvite (`APP_URL`)
- `src/utils/sentry.ts` + `src/utils/analytics.ts`: add tetheredapp.co.uk to the prod-hostname checks (keep old ones during transition)
- Cosmetic: PDF footer (`generatePdf.ts:399`), PrivacyPage + timer SettingsPage support email, invite email copy
- Anonymous-data handoff (gotcha 1) if we're doing it

### Flip day
1. Jarvis: remove the NPM 301 for tetheredapp.co.uk and delete the proxied CNAMEs in Cloudflare (zone is in our CF account, token has DNS edit)
2. Rob: Amplify Hosting console → add custom domain tetheredapp.co.uk + www. Amplify emits verification + CloudFront CNAMEs
3. Jarvis: add those records in Cloudflare, **DNS-only (grey cloud)**, no CF proxy in front of CloudFront
4. Rob: merge develop → main, release (the code changes above go live)
5. Reverse redirect: point tethered.me.uk (Route 53, Rob's side) at cracky.co.uk / home IP; Jarvis sets up the 301 + Let's Encrypt cert on NPM, mirror image of what exists today. (Alternative: S3 redirect bucket + CloudFront in AWS, more faff.) Keep the .me.uk registration forever, ~£10/yr, so old invite links and bookmarks never die.

### After
- Google Search Console: add new property, submit change of address
- Stripe: nothing server-side (webhooks hit function URLs), but sanity-check a live checkout round-trip lands back on .co.uk
- test.tethered.me.uk and the Cypress/scheduled-test scripts can stay on .me.uk indefinitely, migrate whenever convenient

### Phase 2 (optional, later)
- Email domain: noreply@/alert@/support@ are SES on tethered.me.uk. Moving them means verifying tetheredapp.co.uk in SES + DKIM/SPF records in Cloudflare (Jarvis can do DNS). Works fine mixed-domain in the meantime.
