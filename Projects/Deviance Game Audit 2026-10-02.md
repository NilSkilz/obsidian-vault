# Deviance Game: Deep Audit, 2026-10-02

Read-only audit of `~/projects/deviance-game` (main, 0457ff9). Scope: engine/game logic, consent gates, state/UI logic, validator blind spots. Known-issue context honoured: the 99 ticketed legacy card defects are not re-enumerated. All findings below were verified against the code, and the engine findings were reproduced by running the real card manager against the real decks in a node harness (localStorage shimmed, repo untouched).

Checks run: `node scripts/validate-cards.cjs` (fails with exactly the 99 known legacy errors; all expansion cards pass), `react-scripts test` (28/28 pass), `tsc --noEmit` (clean).

Severity scale: CRITICAL breaks a session or lets a consent-gated card through; HIGH wrong behaviour users will hit; MEDIUM edge case; LOW hygiene.

---

## CRITICAL

### 1. Random Encounter ignores consent gates entirely
`src/data/cardManager.js:66-88` (`getEncounterCardForPlayer`)

The partner filter calls `canDoAction({player: target, ...})` instead of using the loop variable `player`, so it re-checks the *target's* player-gates for every candidate and never checks the candidate at all. Worse, the target's own `target_*` gates are never checked anywhere in this function (compare `getCardForPlayerInDeck`, which checks them at line 142).

**Failure scenario (reproduced):** a couple who ticked *nothing* in setup lands on Random Encounter. In 300 sampled draws, 10 returned consent-gated cards, e.g. "More bad doggie!" with `target_humiliation_receiving: true` dealt to a player who did not consent to receiving humiliation. This defeats the app's core promise.

**Fix:** mirror `getCardForPlayerInDeck`: inside the filter check `canDoAction({player, card, isTarget: false})` on the loop variable, and before returning check `canDoAction({player: target, card, isTarget: true})` (plus the target's player-gates if the card has them).

### 2. Opt-out underflow crashes the game and the save is bricked
`src/components/ActionModal/index.js:50`, `src/components/SpecialModal/index.js:92-95` and `119-124`, render crash at `src/components/Board/center.js:179`

Nothing stops `optOuts` going negative: the Opt Out button stays enabled at 0 (both modals dispatch `delta: -1` unguarded), and 7 fate cards carry `delta_optOut: -1` which SpecialModal applies with no floor. Center panel then renders `Array(player.optOuts || 1)` — `-1` is truthy, and `Array(-1)` throws `RangeError: Invalid array length`.

**Failure scenario:** a player with 0 tokens taps Opt Out (or has 0 and draws "Tribute to Lady Luck"). The board render throws, ErrorBoundary swallows the whole app, and because the negative value is already persisted in `gameData`, every reload crashes again. Only "Reset Game Data" (full wipe) recovers — the session is lost.

**Fix:** clamp in the reducer (`ADJUST_OPT_OUTS`: `Math.max(0, ...)`), disable Opt Out when `optOuts <= 0`, and render `Array(Math.max(player.optOuts, 0))`.

### 3. Random Encounter stack-overflow when no compatible partner exists
`src/data/cardManager.js:81-83`

When `availablePlayers` is empty the function recurses with `skip + 1` and no base case. Once `getCardForTargetInDeck` starts returning `null` (skip past deck length), `canDoAction(card=null)` returns null, the filter stays empty forever, and the recursion never terminates.

**Failure scenario (reproduced):** two players whose orientation combination blocks interaction (e.g. two straight players of the same gender — setup allows it) land on Random Encounter: `RangeError: Maximum call stack size exceeded`, deterministically, every time they hit that tile. Also reachable by a compatible couple if no remaining card passes the gates. Bonus damage: every recursion level marks a card used, so the pile floods before the crash.

**Fix:** add `if (!card) return null;` right after the draw (as `getActionCardforTarget` does), and have the modal show its "no tasks" fallback.

---

## HIGH

### 4. Players get paired with themselves on Stage / Dungeon / Chance / Encounter draws
`src/data/cardManager.js:127-132` (also 75-79)

`availablePlayers` is built from `gameData.players` without excluding the drawing player. `canPlayersInteract(owner, player)` with the same person twice is "same gender pair", which passes whenever that player is not straight. So for any bi / bi-curious / gay player, the target is in their own partner pool.

**Failure scenario (reproduced):** bi couple, Theatre tile: 156 of 300 draws (52%) produced self-pairings like "Alice, ... Demonstrate your oral technique on Alice ...". It also corrupts the participant count check (line 136: target counted twice), letting 3-person cards through for 2 real people.

**Fix:** `gameData.players.filter(p => p.id !== player.id && ...)` in both functions.

### 5. Three-person expansion action cards render literal "%player2%" and skip the third person's gates
`src/data/cardManager.js:63` and `86-87`; cards in `actionExpansionLow/High`

The expansion added 16 action-deck cards with `number_of_participants: 3` ("The Understudy", "Mystery Smooch", "Crowded House", "Twenty Fingers", ...; spice 0-2). Both action-deck draw paths supply exactly one player to `replacePlaceholders` (`players: [player]`) and never check `number_of_participants`. The validator passes these cards because message and count are self-consistent; the engine just can't fulfil them.

**Failure scenario:** rent work-off or Random Encounter draws "Crowded House": the card shows raw "%player2%" (and "%2h%" pronouns) on screen, and whoever plays the third role was never consent-checked for the card's `player_*` gates.

**Fix:** either filter the action paths to `number_of_participants <= 2`, or select and gate-check `n - 1` partners in `getActionCardforTarget` / `getEncounterCardForPlayer`. Add a validator rule capping action-deck cards at 2 participants until the engine supports more.

### 6. Every rejected candidate card is burned into the used pile
`src/data/cardManager.js:379` (markCardUsed) with the retry loops at 55-62 and 136-145

`getCardForTargetInDeck` marks a card used at draw time, before the gate / participant checks in the callers. Every rejection burns a card the players never saw.

**Failure scenario (measured):** a cautious couple (few prefs ticked) needed 16 pile entries for 10 actually-played cards. Consequences: the no-repeats pool depletes up to ~2x faster; the auto-spice trigger in `center.js:28` (keyed on `usedCards.length`) fires faster *precisely for the most cautious players*; and the `skip >= deckCopy.length` bail-out (line 367) returns "No Tasks Found" while valid cards remain, since rejections shrink the pool while skip grows.

**Fix:** mark a card used only when it is actually returned to the UI (move `markCardUsed` to the successful exit of each public getter), and base the spice heuristic on `totalMoves` instead of pile length.

---

## MEDIUM

### 7. `can_opt_out: false` is documented, validated, and completely unenforced
`docs/card-spec.md:32`, validator knows the field; neither modal reads it (`ActionModal/index.js:45-55`, `SpecialModal/index.js:86-101`)

35 fate cards (e.g. "Rats!", "The Tip Jar", all the money-penalty cards) set `can_opt_out: false`, but the Opt Out button renders unconditionally. Players can dodge every penalty card for a token, which the deck design explicitly forbids. **Fix:** hide/disable Opt Out when `task.can_opt_out === false`.

### 8. Old-save migration: resumed games silently lose all newly-gated cards
`src/contexts/GameContext.tsx:120-128` (loadGameData), `src/data/cardManager.js:160-166`

`loadGameData` spreads the save over `initialGameData` at the top level only; player objects are taken as-is. A pre-v2 save has 8 pref keys (or none at all for pre-reducer saves), so the 11 new keys (`oral_giving/receiving`, `pain_giving/receiving`, `restraining`, `restrained`, `forceful`, `will_orgasm`, `exhibitionism`, `feet`, `roleplay`) read as `undefined` and `canDoAction` fails them closed. Direction is safe (nothing non-consensual appears), but every card gated on those keys — the bulk of the expansion's spicier material — silently never draws, and there is no UI to edit prefs mid-game, so a resumed game can never fix it. **Fix:** on load, run players through a migration (`prefs: {...defaultPrefs(), ...p.prefs}` keeps it fail-safe but explicit) and surface a "review your preferences" prompt when legacy keys were missing; or version the save and route old saves through setup.

### 9. Select All in the toys modal only visually updates half the checkboxes
`src/components/AddToys/index.js:68` vs `:87`

Column one binds `defaultChecked` (uncontrolled — ignores state updates), column two binds `checked` (controlled). Select All updates state for all 16 toys but only the even-index column re-renders ticked. **Failure scenario:** user taps Select All, sees 8 toys apparently still off, assumes they are off — but toy-gated cards for them will draw. Inverse confusion when deselecting. **Fix:** use `checked={!!toyList[...]}` in both columns.

### 10. ~62 expansion cards render timer text with no unit: "kiss for 1"
`src/data/cardManager.js:212-222`; 8 cards in actionExpansionLow, 2 in actionExpansionHigh, 31 in stageExpansion, 21 in fateExpansion

Timer tokens replace with the bare number (`%m1%` → "1", `%d30%` → "30"). Legacy cards embed the unit in surrounding text; 62 expansion-card tokens don't (e.g. "The Quiet Game": "...%m1% you..." renders "...1 you..."). Countdown still works; the card text is broken English. **Fix:** render "%m1%" as "1 minute" / "%d30%" as "30 seconds" (and strip unit words that would double up), or fix the card texts; add a validator warning for a timer token not followed by a unit word.

### 11. Timer countdown and card effects run as render-phase side effects
`src/components/ActionModal/index.js:25-38`, `src/components/SpecialModal/index.js:52-77`

The `if (run) {...}` block sits in the render body: it schedules `setTimeout`s during render (never cleaned up) and, on the final tick, dispatches reducer actions and calls the parent's `next()` mid-render. React logs "cannot update a component while rendering" warnings; any extra re-render while `run > 1` schedules a duplicate timeout (countdown skips seconds), and a re-render at `run === 1` can double-fire `removeItemOfClothingForPlayer` / money / opt-out deltas. **Fix:** move the countdown into `useEffect` with cleanup, and fire the end-of-timer effects from the effect, once.

### 12. Auto spice-increase heuristic is erratic
`src/components/Board/center.js:22-32`

Triggers on `usedCards.length % (players * 3) === 0`, but the pile grows in unpredictable bursts (finding 6) so the exact multiple is often skipped over or hit early; it is also evaluated before the current turn's draw. Combined effect: some games never auto-increase, cautious groups increase fastest. **Fix:** key on `gameData.totalMoves` (already in the reducer, incremented exactly once per turn).

---

## LOW

### 13. "The Casting Director" (stage, 5 participants) is undrawable
Max players is 4 (`AddPlayers/index.js:64`), so `number_of_participants: 5` never passes the count check — except via the self-inclusion bug (finding 4), which is the only way it can appear, with a duplicated participant. Dead card; validator allows n up to 5. Reduce to 4 or raise the player cap.

### 14. PlayerForm writes junk and mutates state without dispatch
`src/components/PlayerForm/index.tsx:65-69`: after recording a pref checkbox it falls through to `player[e.target.name] = value`; checkboxes have no `name`, so every player gets a persisted `"": "on"` key. Also all form edits mutate the context state object directly; nothing is saved until "Next Step" dispatches, so a mid-setup refresh loses the players. Add an early `return` for checkboxes and dispatch per-field updates.

### 15. Money has no floor anywhere
Rent (`ShowRentModal/index.js:31-37`) and negative fate `delta_money` apply unconditionally; a player can go arbitrarily negative with no game response (NoFunds handling exists only for purchases). Decide behaviour (floor at 0, or a forced work-it-off) and enforce in `ADJUST_MONEY`.

### 16. Opt-out display shows one token for a player who has zero
`src/components/Board/center.js:179`: `Array(player.optOuts || 1)` renders 1 chick at 0 opt-outs. Fold into the finding-2 fix (`Math.max(optOuts, 0)` and accept an empty cell).

---

## Legacy-deck note (new defect class only, per brief)

Within the 99 ticketed validator errors, 11 legacy action/chamber cards use `others_will_orgasm` and 4 use `massage_oil` (vs toy key "Massage Oil"). Flagging because the ticket classes were "duplicate names" and "phantom player 2": these two are a different class — gate keys the engine silently ignores at runtime. The 11 `others_will_orgasm` cards describe other participants orgasming with nobody's `will_orgasm` consent ever checked (consent-grade, suggest prioritising), and the 4 `massage_oil` cards bypass the toy filter. The validator does flag them (as "unknown field"), so no validator change needed — just triage priority.

## Validator blind spots (summary)

- No rule that action-deck cards stay within what the engine can supply (2 people) — finding 5.
- `can_opt_out` accepted but unenforceable — finding 7.
- `number_of_participants` allowed up to 5 with a 4-player cap — finding 13.
- Timer tokens with no unit wording — finding 10.
- Nothing cross-checks that the engine's draw paths enforce all validated fields; a tiny engine-side test drawing each deck with a no-consent player would have caught findings 1 and 5.

## What's healthy

Typecheck clean; 28/28 unit tests pass (canDoAction covers all 19 keys both roles; reducer well covered); the 19 setup-form keys, `PREF_KEYS`, and the gate keys used across all 981 cards match exactly (no orphaned or unreachable gates in the expansion); toy casing fix works for both casings against lowercased saves; spice/dress pool coverage has no empty combination per deck; used-pile reset and new-game flow correctly wipe all three stores.
