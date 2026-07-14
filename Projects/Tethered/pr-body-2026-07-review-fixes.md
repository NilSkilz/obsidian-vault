# July 2026 code-review fixes (P0-P3)

Addresses the issues from the July 2026 security/correctness review ([[code-review-2026-07]]), tracked in `Projects/Tethered/fix-list-2026-07.md`. Covers items **#1-#22, #25-#33** (#23 and #24 already landed via PR #24).

Base: `develop`. 28 commits, one per fix (or coherent group), each with tests.

## P0: Safety path (the expiry pipeline now fails loud, not quiet)
- **#1** `handleSceneExpiry` retries failed schedule creation via `batchItemFailures`; added a stream DLQ + CloudWatch alarm.
- **#2, #4, #5** `sceneExpiryTarget` rethrows send failures (async retry + DLQ), atomically claims the scene (`ConsistentRead` + conditional update) before alerting, and the backend owns the `running → alerting → alerted` transition.
- **#3, #4** The "contact notified" screen is driven by real backend scene status, not the client countdown hitting zero. A page load no longer flips status on its own.
- **#6** Untrusted client `startedAt` is clamped/validated; schedule times are formatted in explicit UTC.
- **#7** Quiet-hours exemption now matches the notification-type strings callers actually send, so safety pushes are never suppressed.
- **#8** `useSceneTimer` computes remaining time from the wall clock (`startTime + duration - now`) instead of counting `setInterval` ticks; fixed the stale-closure service-worker listener.

## P1: Security / authorization
- **#9, #10** `adminGiftSubscription` and `adminRefund` enforce a server-side admin check (shared `adminAuth.ts`).
- **#11** `createPortalSession` requires Cognito auth and derives `userId` from the token, ignoring the body.
- **#12** Removed table-wide guest/authenticated read on `ShareSnapshotModel` and `Relationship`; share-by-id and invite-by-code now go through single-record Lambdas (`getSharedSnapshot`, `getRelationshipByInviteCode`).
- **#13** Share revoke + expiry enforced server-side; reads counted; revoke UI added.
- **#14** Notification create / push verifies the caller's relationship with the target (`createPartnerNotification` Lambda).
- **#15** Replaced the one shared `*`-resource IAM policy across all Lambdas with per-function least-privilege policies.
- **#16** No-password shares stop pretending to encrypt with an empty passphrase; the unguessable id is the secret and the copy is honest.
- **#17** Stopped logging PII (emails, checklist answers, full event bodies) to CloudWatch across five handlers.
- **#18** `sendPartnerInvite` verifies invite-code ownership and HTML-escapes user-controlled strings in the email (shared `escapeHtml.ts`); safety-alert email HTML escaped too.

## P2: Data integrity
- **#19, #20, #27, #28** One server-backed path for task completions, reward claims and points via the new `pointsOperation` Lambda: honours `requiresApproval`, writes `PointsTransaction` audit rows, models recurring completions per-occurrence, and enforces reward affordability/cooldown/max-claims atomically against the specific relationship's balance.
- **#21** Points mutations are server-authoritative; clients can no longer mint balance.
- **#22** "Adjust Points" persists a `PointsTransaction` + balance update instead of a toast.
- **#25** `deleteCustomActivity` cascade delete paginates on `nextToken` so no orphaned answers remain.
- **#26** SharedView shows giving and receiving directions separately, so a high receiving score can't mask a giving-direction hard limit.

## P3: Correctness & UX
- **#29** Real day streaks (`taskStreak.ts`) replace the hardcoded `0` on TasksPage and SubDashboardPage.
- **#30** One shared local-timezone date module (`taskDates.ts`); grouping and labels no longer disagree across the UTC boundary.
- **#31** ManagePage renders a proper empty/not-found state instead of an infinite spinner when there are no relationships, and a monotonic load-sequence guard stops a superseded load bleeding the previous partner's data (including points).
- **#32** Fetch failures no longer masquerade as "no data" in the sync modal: `getCloudSummary` throws on failure, Upload Local is disabled until the cloud check succeeds, and checklist answer caches invalidate on write.

## Found along the way
- **#33** `sendPushNotification` queried a `byUserIdAndActive` GSI that the schema never defines, and queried the preferences base table by `userId` when the PK is the Amplify `id`. Both errors were swallowed, so every push (safety alerts included) silently reached zero devices and preferences/quiet hours were ignored. Now queries the real `byUserId` GSI (with `isActive` as a filter), and a genuine lookup failure returns 500 instead of a fake `sent: 0` success.

## Testing
- Full suite green: **429/429**, `tsc --noEmit` clean.
- New/expanded unit tests for the points Lambda, scene expiry/claim, share crypto + lifecycle, invite/notification auth, push-notification query shapes, date/streak/occurrence utils, and the sync error paths.

## Not in this PR (deferred)
- Verification pass against each fix-list **Test:** line in a real environment.
- Test-dashboard scheduling revival (dead macOS launchd Cypress job): needs a decision, systemd timer on Proxmox vs retire.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
