# Tethered fix list — July 2026 review

Working tracker for the issues found in [[code-review-2026-07]]. Ordered by priority. Tick items as fixes land; each has a **Test** line so you can verify independently of "the PR says it's fixed."

**Status key:** `[ ]` open · `[~]` fix in progress / PR open · `[x]` fixed + verified by Rob

Repo: `/home/jarvis/projects/tethered`. All line refs are as of commit `3e8b260`.

---

## P0 — Safety path (do first; this is the product's whole promise)

The theme: the expiry pipeline fails *quiet*. Fixes below make it fail *loud* so a missed alert becomes a retry + an alarm, never a silent nothing.

- [ ] **1. `handleSceneExpiry` swallows schedule-creation failures**
  `amplify/functions/handleSceneExpiry/handler.ts:75-84`
  Fix: on `CreateSchedule` failure, add the record to `batchItemFailures` (return real failures, not `[]`) so the stream retries; add an SQS DLQ on the event source mapping (`backend.ts:237-245`) + a CloudWatch alarm.
  **Test:** temporarily point the scheduler at a bad role ARN (or throttle), start a scene, confirm the invocation now reports a batch failure and retries, and that the scene does NOT silently end up unarmed. Restore config, confirm normal arming still works.

- [ ] **2. `sceneExpiryTarget` swallows SES/SMS send failures**
  `amplify/functions/sceneExpiryTarget/handler.ts:64-72`
  Fix: rethrow after a failed send so Lambda async retry + scheduler retry fire; add a DLQ on the target; only mark the scene alerted after a confirmed send.
  **Test:** put SES in sandbox / use an unverified recipient so the send fails, trigger expiry, confirm the function errors (visible in CloudWatch + DLQ) rather than logging "Alert sent" and returning success.

- [ ] **3. UI claims "contact notified" with no backend confirmation**
  `src/pages/dashboard/timer/TimerPage.tsx:495-506`
  Fix: drive the "we notified X" screen from a real backend status (e.g. scene status `alerted` written only after a confirmed send), not from the client countdown hitting zero. If delivery is unknown/failed, say so.
  **Test:** force a send failure (as in #2); the expired screen must NOT claim the contact was notified.

- [ ] **4. Backend never records scene status after alerting; only a page-load flips it**
  `sceneExpiryTarget/handler.ts` (no status write) + `TimerPage.tsx:103-105`
  Fix: backend owns the post-alert transition with an atomic conditional update (`running -> alerting -> alerted`); distinguish "checked in safe" from "expired + alerted".
  **Test:** let a scene expire without loading the app; confirm the backend marks it alerted on its own and the alert fired.

- [ ] **5. Check-in vs expiry race (stale read, no atomic claim)**
  `sceneExpiryTarget/handler.ts:59-62, 126-133`
  Fix: `ConsistentRead: true` on the scene fetch + a conditional `UpdateItem` (`ConditionExpression: status = running`) to atomically claim the scene before alerting.
  **Test:** check in within ~1s of expiry repeatedly; confirm no false "please check on X" alert is sent after a successful check-in.

- [ ] **6. Expiry time uses the untrusted client clock + no dayjs UTC plugin**
  `handleSceneExpiry/handler.ts:47`, `TimerPage.tsx:138`
  Fix: derive `startedAt` server-side (or clamp/validate the client value); add `dayjs.extend(utc)` and format in UTC explicitly so it doesn't rely on Lambda TZ.
  **Test:** set a device clock skewed backwards by > scene duration, start a scene; confirm it still arms (a past `at()` no longer throws into the swallowed path) and fires on time.

- [ ] **7. Quiet-hours push exemption is dead (string mismatch)**
  `sendPushNotification/handler.ts:259` checks `'safetyAlerts'`; callers send `'SAFETY_ALERT'`
  Fix: match the real notification type so safety pushes are NOT suppressed during quiet hours.
  **Test:** set quiet hours to now, send a SAFETY_ALERT push, confirm it still delivers.

- [ ] **8. `useSceneTimer` counts setInterval ticks, not wall-clock**
  `src/hooks/useSceneTimer.tsx:38-49` (use the existing `timerUtils.calculateRemainingTime`)
  Fix: compute remaining from `startTime + duration - now`; also fix the stale-closure SW listener (`[]` deps) that reschedules using the initial `remaining`.
  **Test:** start a timer, background the tab / lock the phone for a few minutes, return; the countdown should reflect real elapsed time, not lag.

---

## P1 — Security / authorization (exploitable now, sensitive data)

- [ ] **9. `adminGiftSubscription` has no server-side admin check**
  `amplify/functions/adminGiftSubscription/handler.ts` + route `backend.ts:388-393`
  Fix: verify the caller is an admin server-side (Cognito group or verified claim), not "in frontend."
  **Test:** as a normal (non-admin) user, call the endpoint to self-gift `gifted`; must be rejected 403.

- [ ] **10. `adminRefund` has no server-side admin check**
  `amplify/functions/adminRefund/handler.ts` + route `backend.ts:381-386`
  Fix: same admin gate.
  **Test:** as a normal user, call admin-refund with any `cus_...`; must be rejected, no Stripe refund issued.

- [ ] **11. `createPortalSession` is unauthenticated + trusts body `userId`**
  `backend.ts:342` (`AuthorizationType.NONE`), `createPortalSession/handler.ts:31-62`
  Fix: require Cognito auth; derive `userId` from the token claim, ignore the body.
  **Test:** call it unauthenticated / with someone else's userId; must not return a portal URL for another user.

- [ ] **12. `ShareSnapshotModel` + `Relationship` grant guest/authenticated `read` (= `list`)**
  `amplify/data/resource.ts:188-196, 240-250`
  Fix: remove the table-wide read grants; do share-by-id and invite-by-code lookups through a Lambda that fetches a single record. Keep owner rules.
  **Test:** as any account, run `ShareSnapshotModel.list()` / `Relationship.list()`; must return only your own records (ideally deny list entirely).

- [ ] **13. Share revoke + expiry never enforced (also frontend C4)**
  `src/pages/public/SharedView.tsx:190-218`; ideally enforce server-side too
  Fix: check `revoked` and `expiresAt` before decrypting; increment `reads`; add a revoke button. Consider server-side TTL.
  **Test:** create a share, revoke it, open the link → must refuse. Set `expiresAt` in the past → must refuse.

- [ ] **14. Any authed user can create notifications / push to any user**
  `amplify/data/resource.ts:280-285`; `sendPushNotification/handler.ts:126`
  Fix: on create, force `userId` to the caller (or restrict to a trusted Lambda); in the push handler, verify the target against the caller's claim.
  **Test:** as user A, try to create a PartnerNotification / push for user B; must be rejected.

- [ ] **15. Over-broad IAM: one `*`-resource policy on all 15 lambdas**
  `amplify/backend.ts:156-217`
  Fix: scope each function's policy to the specific tables/actions it uses; drop `iam:PassRole`/`ses:*`/`scheduler:*` from functions that don't need them.
  **Test:** deploy, run the full e2e suite; confirm each function still works with least-privilege.

- [ ] **16. Non-password shares encrypt with an empty-string password**
  `src/components/shared/ShareModal.tsx:346-348`, `SharedView.tsx:211`
  Fix: for no-password shares, rely on the unguessable id as the secret (don't pretend it's encrypted), or require a password. Decide the model and make the copy honest.
  **Test:** create a no-password share; confirm the stored ciphertext isn't trivially decryptable with `""` by anyone who lists the table (depends on #12 too).

- [ ] **17. Sensitive PII logged to CloudWatch**
  `getPartnerProfile/handler.ts:193-195`, `acceptPartnerInvite/handler.ts:133`, `adminGetAllUsers/handler.ts:58`, `sendPartnerInvite/handler.ts:14`
  Fix: remove or redact emails / checklist answers / full event bodies from logs.
  **Test:** run the flows, grep the log group; no emails or answer content present.

- [ ] **18. `sendPartnerInvite`: no ownership check + unescaped HTML in email**
  `sendPartnerInvite/handler.ts:32-48, 74-75, 168`
  Fix: verify the caller owns a relationship with that invite code; HTML-escape `inviteCode`/`inviterLabel` before interpolation.
  **Test:** try to send an invite for a code you don't own → rejected; inject `"><script>` into a label → rendered inert.

---

## P2 — Data integrity & silent data loss

- [ ] **19. Task/points/rewards: pages hand-roll a divergent copy; DataService's correct layer is dead code**
  callers in `SubDashboardPage.tsx`, `TasksPage.tsx`, `ManagePage.tsx`; unused helpers in `services/data/DataService.ts`
  Fix: route all completions/claims through `DataService.completeTask/claimReward/...`; honor `requiresApproval`/`requiresPhotoProof`; write `PointsTransaction` audit rows; delete the page-local copies.
  **Test:** complete a task that `requiresApproval`; it should appear in the dom's "Needs attention" queue and award points only on approval.

- [ ] **20. Recurring (daily/weekly) tasks complete once, forever**
  `SubDashboardPage.tsx:554-557`, `TasksPage.tsx:325-328`; no reset logic exists
  Fix: model completions per-occurrence (TaskCompletion rows) rather than flipping `Task.status`; add reset/rollover.
  **Test:** complete a daily task; next day it's available again and the streak counts.

- [ ] **21. Points balance is client-authored (mintable)**
  `SubDashboardPage.tsx:565-580`, `TasksPage.tsx:336-351`, `ManagePage.tsx:577-584`
  Fix: move points math server-side (Lambda) or at least behind the DataService helpers; tighten auth so a sub can't write their own balance directly.
  **Test:** from dev tools, try to write your RelationshipPoints balance; must be rejected.

- [ ] **22. "Adjust Points" is a stub (toast + local state only)**
  `ManagePage.tsx:669-692`
  Fix: persist the adjustment as a PointsTransaction + balance update.
  **Test:** adjust points, refresh; the change persists.

- [x] **23. `SyncService` drops data at sign-up** — merged to `develop` (PR #24 merge commit `c6f02fb`, 2026-07-13).
  `src/services/data/SyncService.ts:160-200`
  Fix: upload `notes`, `shareNotes`, `context`, and custom activities (+ their answers) during the local→cloud sync.
  **Test:** in demo mode add notes + a custom activity, sign up, confirm both survive in the cloud account.

- [x] **24. `updateRelationship` silently drops `checklistProfileId` (one-line)** — merged to `develop` (same PR as #23).
  `src/services/data/AmplifyAdapter.ts:911-917` (missing from `validFields`; schema has it at `resource.ts:223`)
  Fix: add `'checklistProfileId'` to the whitelist.
  **Test:** set/clear a partner's checklist profile; the change persists (and deleting a profile actually clears the reference).

- [~] **25. `deleteCustomActivity` cascade delete is unpaginated** — fixed on `release/2026-07-review-fixes` (2026-07-13).
  `AmplifyAdapter.ts:606-617`
  Fix: loop on `nextToken` like the other list calls before deleting matched answers.
  **Test:** with many answers, delete a custom activity used across a big table; confirm no orphaned answers remain.

- [ ] **26. SharedView can hide a hard limit (giving/receiving collapsed)**
  `src/pages/public/SharedView.tsx:379-382`
  Fix: show giving and receiving directions separately; never let a high receiving score mask a `desireGiving:1` hard limit.
  **Test:** rate an activity receiving=4, giving=1; the shared view must show the giving-direction hard limit.

---

## P3 — Correctness & UX

- [ ] **27. Three different "points" totals across tabs**
  `TasksPage.tsx:283-289` vs `SubDashboardPage.tsx:480-497` vs `ManagePage.tsx:497-508`
  Fix: one source of truth (RelationshipPoints balance) everywhere.
  **Test:** same user, same relationship shows the same number on every tab.

- [ ] **28. Reward cooldown + affordability not enforced; "All" filter sums across relationships**
  `ClaimRewardModal.tsx:24-55`, `SubDashboardPage.tsx:488-497`
  Fix: check affordability against the specific relationship's balance; enforce `cooldownDays` and `maxClaims` server-side/atomically.
  **Test:** with 50pts in A and 100 in B, you cannot claim a 120pt reward in A; a reward on cooldown is blocked.

- [~] **29. Streaks hardcoded to 0 while marketing promises streaks** — fixed on `release/2026-07-review-fixes` (2026-07-13, `src/utils/taskStreak.ts` + 13 unit tests).
  `TasksPage.tsx:526-530`, `SubDashboardPage.tsx:797-801`
  Fix: compute a real streak, or remove the claim until it exists.
  **Test:** complete tasks on consecutive days; streak increments.

- [~] **30. Task date grouping uses UTC while labels use local time** — fixed on `release/2026-07-review-fixes` (2026-07-13, shared `src/utils/taskDates.ts`).
  `TasksPage.tsx:85-99` vs `:49-63` (helpers copy-pasted into 3 pages, already drifting)
  Fix: one shared date helper, consistent timezone handling.
  **Test:** as a non-UTC user, a task due tonight groups under "Today" and is labelled "Today" consistently.

- [~] **31. ManagePage infinite spinner when no active relationships + cross-partner points bleed** — fixed on `release/2026-07-review-fixes` (2026-07-13, empty state + stale-load sequence guard).
  `ManagePage.tsx:517-522, 497-508`
  Fix: handle the zero-relationship case (show "not found" not a spinner); cancel/sequence in-flight `loadData`; reset `subPoints` between partners.
  **Test:** open Manage with no relationships → get a clear empty state; switch partners quickly → no stale points shown.

- [~] **32. Swallowed errors → empty UI can mislead sync conflict choice** — fixed on `release/2026-07-review-fixes` (2026-07-13, sync modal blocks upload until the cloud check succeeds; answer caches invalidate on write).
  `DataService.getCloudDataSummary`, `SyncService.getCloudSummary`, `ChecklistContextProvider` caches
  Fix: distinguish "no data" from "fetch failed"; invalidate answer caches on write.
  **Test:** simulate a transient network failure during the sync modal; it must not report "no cloud data."

---

## Found along the way

- [~] **33. `sendPushNotification` queried nonexistent indexes; every push silently sent to zero devices** — found during the batch-2 auth work, fixed on `release/2026-07-review-fixes` (2026-07-13).
  `amplify/functions/sendPushNotification/handler.ts` (subscriptions used a `byUserIdAndActive` GSI the schema never defined; preferences queried the base table by `userId` when the PK is `id`; both errors were swallowed).
  **Test:** with an active push subscription, trigger any notification (e.g. task assigned); it must actually arrive. Set quiet hours to now; a non-safety push must be suppressed.

## Done (this review)

- [x] **Docs pass** — PR `docs/review-cleanup-2026-07` off `develop` (README rewrite, security-contact fix, CLAUDE.md drift, dead-artifact deletions). Open: https://github.com/NilSkilz/tethered/pull/new/docs/review-cleanup-2026-07

## Needs a decision (not a code fix)

- [ ] **Scheduled test runs** — `scheduling/me.tethered.cypress.plist` is a macOS launchd job on the old iMac path. If that Mac is off, the every-6-hours Cypress safety net has been dead since the rebuild. Decide: port to a systemd timer on the Proxmox box, or retire. Same for `tools/test-dashboard/scheduling/`.

## Suggested batching for PRs (so you can test in coherent chunks)
1. **Safety-loud** (1-6) — one PR; test by forcing failures and confirming retries/alarms fire.
2. **Auth holes** (9-12, 14) — one PR; test with a normal (non-admin) account.
3. **Share lifecycle** (13, 16, 26) — one PR; test link revoke/expiry + limit display.
4. **Points integrity** (19-22, 27, 28) — one PR; test the approval + claim flows end to end.
5. **Sync + small data bugs** (23, 24, 25) — one PR.
6. Correctness/UX (29-32) — as capacity allows.
