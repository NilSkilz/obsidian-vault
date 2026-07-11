# Tethered code review — July 2026

Full-codebase review done 2026-07-11 (Fable 5, four parallel specialist passes: safety path, security/authz, frontend data layer, docs/tests/hygiene). Repo at `/home/jarvis/projects/tethered`, commit `3e8b260` (~8 weeks stale). Findings below were spot-verified against source by the lead, not taken on trust. Severities: **critical** = data loss / safety failure / exploitable now.

## The one that matters most: the safety alert can silently never fire

The whole product promise is "if you don't check in, someone gets alerted." The pipeline (DynamoDB stream → `handleSceneExpiry` arms an EventBridge one-shot → `sceneExpiryTarget` sends SES email + Twilio SMS) is architecturally sound (server-side, survives the phone dying) but **fails quiet at every protective step**:

- **`handleSceneExpiry` swallows schedule-creation errors** and always returns `batchItemFailures: []` — no retry, no DLQ. If arming fails (throttle, clock skew, transient), the scene is never armed and nobody knows. `handler.ts:75-77, 82-84`. VERIFIED.
- **`sceneExpiryTarget` swallows SES/SMS send failures** — logs and returns success, so no retry fires. A transient blip at expiry = contact gets nothing, ever. `handler.ts:64-72`. VERIFIED.
- **The UI then says "Email sent to X, SMS sent to Y"** purely because the client countdown hit zero, with zero backend confirmation → active false reassurance. `TimerPage.tsx:495-506`. VERIFIED.
- Expiry time is computed from the untrusted client clock and formatted without dayjs UTC plugin (works only because Lambda TZ=UTC). `handler.ts:47`, `TimerPage.tsx:138`.
- No DLQ/retry/alarm anywhere in the pipeline. Check-in vs expiry has a race (eventually-consistent read, no atomic status claim) → possible false alarm. Backend never writes scene status after alerting; only a frontend page-load flips it (a page load can suppress a delayed alert).
- Quiet-hours push exemption is dead: code checks `'safetyAlerts'` but callers send `'SAFETY_ALERT'`, so safety pushes ARE suppressed during quiet hours (opposite of intent). `sendPushNotification/handler.ts:259`.

**Fix with most leverage:** make failures loud — rethrow from both catch blocks, return real `batchItemFailures`, add a DLQ + CloudWatch alarm. That single change turns most of these criticals into recoverable retries.

## Security / authorization (exploitable now, ~20 live users' kink+medical data)

- **`adminGiftSubscription` + `adminRefund` have NO server-side admin check** — routes are `COGNITO` only, comment says "admin check handled in frontend." Any logged-in user can gift themselves premium or issue Stripe refunds against other customers. `adminGiftSubscription/handler.ts`, `adminRefund/handler.ts`, `backend.ts:381-393`. VERIFIED.
- **`createPortalSession` is `AuthorizationType.NONE`** and trusts `userId` from the body — anyone pulls up a victim's Stripe billing portal. `backend.ts:342`, `handler.ts:31-62`. VERIFIED.
- **`ShareSnapshotModel` and `Relationship` grant `guest`/`authenticated` `read`** = `list` in Amplify Gen 2. Any account can dump every share snapshot and every relationship: allergies, STIs, safe words, emergency contacts, the full partner graph. `data/resource.ts:188-196, 240-250`. VERIFIED. (Non-password shares encrypt with an empty-string password → zero confidentiality.)
- **Share revoke/expiry never enforced** — `SharedView` decrypts without checking `revoked`/`expiresAt`; the "expires in 30 days" + revoke are decorative. (Same bug found independently by the frontend pass, C4.)
- Any authed user can create notifications / push arbitrary alerts to any other user (harassment/spoofed-alarm vector). `data/resource.ts:280-285`, `sendPushNotification/handler.ts:126`.
- One over-broad IAM policy (`dynamodb`/`scheduler:*`/`ses:*`/`iam:PassRole` on `*`) attached to all 15 lambdas incl. public ones.
- Sensitive PII logged to CloudWatch (partner emails, checklist answers). `sendPartnerInvite` sends unescaped HTML email with no ownership check (spam/phish from the domain).
- **Done well:** Stripe webhook signature IS verified; `acceptPartnerInvite` correctly matches Cognito email + checks expiry + blocks self-accept; `deleteAccount` scoped to caller's own sub; `contactForm` escapes HTML + honeypot + rate limit; secrets use `secret()`.

## Frontend data layer (integrity + silent data loss)

- **An entire correct business-logic layer in DataService is dead code** — `completeTask`, `awardPoints`, `claimReward`, `denyRewardClaim`, `fulfillRewardClaim` have zero callers; every page hand-rolls a divergent version. VERIFIED (grep).
  - Task approval pipeline dead: subs get points instantly on tap, `requiresApproval`/`requiresPhotoProof` ignored, dom "Needs attention" queue can never populate, approval awards nothing.
  - Recurring (daily/weekly) tasks complete once forever — no reset logic exists.
  - "Adjust Points" is a stub: success toast + local state only, vanishes on refresh.
  - Points balance is client-authored → any user can mint points / claim any reward.
  - Three different definitions of "points" across three tabs; deny/fulfill sign flips by code path.
- **`updateRelationship` drops `checklistProfileId`** — it's in the schema (`data/resource.ts:223`) but missing from the adapter's `validFields` whitelist, so the update silently no-ops → deleted profiles get auto-reselected. One-line fix. `AmplifyAdapter.ts:911-917`. VERIFIED.
- **`SyncService` loses data at sign-up** — uploads only tried/rating/desire; drops `notes`, `shareNotes`, `context`, and never uploads custom activities. Demo user converts → data quietly shredded. `SyncService.ts:160-200`.
- **SharedView can hide a hard limit** — collapses giving/receiving with `||`, so a `desireGiving:1` (hard limit) hidden behind `desireReceiving:4`. In a limits-communication product that's a safety bug. `SharedView.tsx:379-382`.
- `useSceneTimer` counts setInterval ticks not wall-clock (background-tab throttling lags a safety timer); `scheduleNotification` no-ops if SW controller absent on first load; `deleteCustomActivity` cascade delete is unpaginated (orphans answers). Streaks hardcoded to 0 while marketing promises streaks.
- **Done well:** pagination discipline (do/while nextToken) nearly everywhere; DataServiceCache is small and correct (TTL + in-flight dedup, failures not cached); share encryption is proper client-side PBKDF2-200k → AES-GCM, ciphertext-only stored.

## Docs / hygiene (fixed in PR — branch `docs/review-cleanup-2026-07` off develop)

- README was the stock AWS Amplify starter template → rewritten.
- CONTRIBUTING sent security reports to Amazon → now private to Rob.
- CLAUDE.md drift fixed: 2024→2025 dates, offline-first "Shipped", env vars (VAPID, not VITE_ENVIRONMENT), Sorry-Cypress not Cypress Cloud, cypress.env.test.json committed-on-purpose note. (Still ~12 models and several routes/PWA undocumented — noted, not all filled yet.)
- Deleted git-verified dead artifacts (PWA phase reports, SHARE_FIX_ANALYSIS, version.txt x2, screenshots/, stray amplify.yml, old-NUC scripts).
- Tests: e2e healthy (39 features, 0 orphan steps). Unit tests thin (11 files / 108 src); the data adapters + Stripe webhook have ~zero coverage — highest-value gap. Scene-expiry lambdas DO have tests (but they enshrine the error-swallowing).

## Open question for Rob
`scheduling/me.tethered.cypress.plist` is a macOS launchd job hardwired to `/Users/rob.stokes/...` on the old iMac. If that Mac is off, the every-6-hours scheduled test run has been silently dead since the rebuild. Not deleted (may still run on the iMac). Decide: port to a systemd timer on this box, or retire.

## Meta: newer-model read on older-model work
The architecture instincts are consistently right (server-side deadman switch, adapter abstraction, client-side share crypto, pagination discipline, real e2e coverage). The failures cluster in two habits: (1) **failing quiet** — swallowing errors and returning success/empty in a product whose whole job is to fail loud; (2) **trusting the client** — "admin check in frontend," client-authored points/balances, table-wide read rules. Both are fixable without a rewrite. Priority order: safety-path loudness → auth holes (admin/portal/list rules) → points integrity + sync data loss.
