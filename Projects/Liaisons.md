# Liaisons

Party game for consenting adults: "lobby on phones, then phones away". Started 16 Nov 2026 as the no-board successor to the Deviance board game (see `Projects/Deviance Game.md` for the design conversation that led here). **Name:** Liaisons, settled 16 Nov 2026 when Rob created the repo under that name. It started life as "Undertow" (my pick, he said it didn't land and to ignore the sea theme); folder, package, Amplify stack names, boot script and this file were all renamed the same day.

## Where things live

- Local checkout: `/home/jarvis/projects/liaisons`, branch `main`, first commit `9427d3f`.
- Remote: `git@github.com:NilSkilz/liaisons.git` (private, Rob created it 16 Nov; the gh PAT can't create repositories). `main` pushed over the SSH key. Connected in the Amplify console by Rob 16 Nov: **https://main.d2e01z37q2t37t.amplifyapp.com/** (auto-builds on push to `main`; AppSync in eu-west-1, endpoint and API key are in the public bundle as intended).
- **Public: https://liaisons.cracky.co.uk** (NPM proxy host 24 → `192.168.1.11:3010`, wildcard cert, no access list: anyone with the URL can open a room, there are no accounts). LAN: http://192.168.1.11:3010. Served by `Jarvis/bin/liaisons-preview.sh` (`vite preview` plus the LAN game backend on CT 110), in cron `@reboot`; re-run it after every `npm run build`. Rooms persist in `.data/rooms.json`.
- Browser check: `/home/jarvis/tools/browser-check/liaisons-flow.js` drives three phones plus a late joiner through a whole night at 390x844. `liaisons-formats.js` next to it runs five phones with confessions and screenshots every whole-room format. `liaisons-decks.js` runs four phones with mixed deck opt-ins through 300 cards and fails if a Kink or Swinger dare reaches anyone who didn't switch it on.

## Stack

Vite + React 18 + TypeScript, no UI library. Amplify Gen 2 backend, deliberately tiny: AppSync with an API key, one mutation (`play`) and one query (`room`), one Lambda, one DynamoDB table (one item per room, 48h TTL). No Cognito.

The whole game is `shared/engine.ts`, a pure `handle(store, op, args)` used by both the Lambda and the LAN dev server (`dev/server.ts`), so the LAN build runs the same code AWS will. With no `amplify_outputs.json` the app talks to the LAN server; in an Amplify build it uses AppSync.

**Privacy model:** the browser can't read game state. Every move goes through the engine, which returns only that player's view. Nobody's ticks, secrets or missions are ever sent to another phone, the host's included. There's a test that asserts it.

## How it plays (as built)

- **Lobby:** room code, name, then per person: No / Flirty / Hot / Filthy, plus a separate level for solo dares. Everyone starts unanswered and has to choose for each person. Someone joining later shows up as unanswered and knocks you back to "not ready".
- **Start** deals each player a secret mission (aimed only at someone who ticked them back; none of the missions need touch).
- **Host is the dealer:** whole-room cards, solo dares, pair dares.
- **Whole-room cards come in nine formats** (added 16 Nov, Rob asked for all of them): hands up (rule is random: minority forfeits, hands-up forfeit, or hands-down forfeit), swap seats, pick a side, the line (never to all-the-time wall), rank yourselves, most likely to, guess the count, eyes closed, whose confession. The format never repeats twice running, and each has a minimum room size (`FORMATS` in `shared/decks.ts`): movement ones, eyes closed and confessions need 4+, so a three-person night only gets hands up, pick a side, most likely to and guess the count.
  - **Eyes closed:** host counts on a stepper and the screen shows only "3 of 5" to announce. No forfeit. The host keeps their eyes open to count, so it is anonymous to everyone except the host.
  - **Whose confession:** optional box on the answers screen (140 chars). Read out once each with no name attached; the app never reveals the author, owning up is their call. Only dealt once 3+ people have written one. The author id never leaves the engine (test asserts it).
  - **Singling-out formats stay tame on purpose:** most likely to and rank yourselves have no Filthy cards.
- **Hot seat** is a solo card (three questions from the room, dodge one), so it respects each person's solo level. Pairs need a mutual yes and the card never exceeds the lower of the two answers or the room heat. Turns are shared out evenly.
- **Forfeit** is pick-from-two, always two different kinds (so never drink-or-drink), same size whatever was dodged.
- **Partner pass:** free, redraws for the same player with a different partner or a solo card, records nothing.
- **Heat rises by itself** (16 Nov, `4b4d1fc`, replaced the eyes-closed unanimous vote, which Rob found weird): every `max(8, 2 x players)` cards the heat steps up and the host gets a whole-room announcement card ("everyone loses an item of clothing or takes a drink", three variants per level, in `HEAT_UPS`). Host header shows "hotter in N"; "Turn it up now" skips the wait and replaces the card on the table. Room heat only ever caps cards, ticks still decide everything. Resets on New game. Browser-checked across three phones: announcement landed at card 9, "Turn it up now" jumped straight to Filthy, and the button then read "Heat is maxed".
- **Late joiners / changing answers:** host shows the room code; a late joiner gets a mission once they've answered.
- **End:** host reveals each mission, room votes pulled-it-off or busted, then awards (Bravest, Conscientious Objector, Most Wanted, Smooth Operator, Rumbled, Never Flinched).
- **Join QR (16 Nov, `d953843`):** the host gets a "Show QR code" button in the lobby, and the dealer's "Room code / QR" sheet shows it mid-game. It encodes `<origin>/?code=XXXX`, which lands on the join screen with the code filled in. A scanned link for a different room overrides a stale saved session; the same room just carries on. Drawn as inline SVG with `qrcode-generator` (zero dependencies, clean `npm ci` re-checked).
- **Timer on timed dares (16 Nov, `d94b5dd`, Rob asked):** when a solo or pair card names a time limit, the host's card shows a countdown under it: Start, Pause/Resume, +30s, Reset, Finish. It never starts itself. At zero it flashes "Time's up", buzzes (Android only, iOS has no vibrate API) and beeps, and it holds a screen wake lock while running. The limit is parsed from the card wording by `timeLimit` in `shared/timer.ts` (49 cards, 10 seconds to 5 minutes); `shared/timer.test.ts` fails if a new card mentions a time the parser can't read. Local to the host's phone, nothing goes to the engine, so a reload resets it.
- **Leaving (16 Nov, `3fe1239`, Rob asked):** guests get "Leave the game" on the phones-away screen, and the lobby and finale leave links now really take them out (before, they only forgot the room on that phone and left a ghost who still got dealt cards). Op `leave` (`dropPlayer` in `shared/engine.ts`, shared with the host's remove): clears them from everyone's ticks, redeals their card, re-deals any mission aimed at them. The night carries on. The host can't leave (they hold the deck). `resolve` carries the card number, so a host tapping a card that was just redealt does nothing and gets the new one. Browser check: `liaisons-leave.js`.
- **Level legend (16 Nov):** the Flirty / Hot / Filthy explanations sit directly above the per-person choices on the answers screen (they used to be at the bottom, Rob flagged it), pinned so they stay in view down a long guest list.
- **New game, same people (16 Nov, `e293980`):** host gets a "New game, same people" button at the end of the night; it returns everyone to the lobby on the same room code, keeping answers (editable) but wiping missions/confessions/scores and excluding already-played cards so round two isn't a rerun. Lobby also got "Start a new room instead" (host) and "Leave this room" (guest), since before this a phone stuck in a room had no way out short of clearing the browser.

## Decks (added 16 Nov, Rob's call: "vanilla deck, kink deck and swinger deck, host adds 1, 2 or 3 to the pot")

- **Host picks the pot in the lobby** (op `decks`), default Vanilla only, at least one, fixed once the night starts.
- **Kink and Swinger are opt-in per player**, privately, on the answers screen ("Not for me" / "Deal me in", default off). A solo card needs that player's switch, a pair card needs both people's (`decksFor` in `shared/engine.ts`). Nobody else's view carries the opt-ins, host included (test asserts it).
- **Whole-room cards need no opt-in** because they're talk, not touch; they come from every deck in the pot. A pot with no whole-room card at the current heat borrows vanilla's.
- **Heat stays at three levels and one tick per person covers every deck.** Kink runs Flirty to Filthy. Swinger is the board game's levels 4 and 5 (oral, full sex), and every Swinger dare sits at Filthy, so it takes a mutual Filthy tick plus both opt-ins. This replaced the idea of folding levels 4 and 5 into Filthy for everyone, which would have silently changed what a Filthy tick meant.
- The host's card shows a "· Kink" or "· Swinger" tag. Extra decks are weighted 2x in the draw so they show up against the bigger vanilla deck.
- **Deliberately left out:** anal and cards for three or more people (the lobby asks about neither), toys beyond ice/scarf/belt/blindfold-from-whatever. Ties are always "a bow they could pull free". Sex cards say "sort protection first".
- Cards were written fresh in Liaisons format (no anatomy assumed), mined from the Deviance level 4 and 5 cards rather than auto-ported. The 1,056-card port is no longer the plan for reaching that content.

## Content (16 Nov)

405 cards. **Vanilla:** 198 whole-room (60 hands up, 24 swap seats, 22 pick a side, 17 the line, 9 rank yourselves, 20 most likely to, 20 guess the count, 26 eyes closed), 26 solo dares plus 6 hot seats, 48 pair dares (24 at Filthy after Rob asked for more: alone in a room for two minutes, "open your mouth", blindfold, ice, under a blanket). **Kink:** 34 whole-room, 12 solo, 30 pair. **Swinger:** 26 whole-room, 5 solo, 20 pair. Plus 14 forfeits and 18 missions.

## State (16 Nov 2026)

Verified: 35 tests (31 engine, 3 timer parsing, 1 more since) (decks landed in `4af6dad`, six of the tests are deck gating), typecheck on app and backend, production build, and the full flow in headless Chrome at phone size (zero pairings outside mutual ticks across 120 cards, no console errors, no horizontal overflow). The backend definition synthesizes to CloudFormation with `cdk synth` (command in the README).

AWS path verified 16 Nov 19:20: a scripted game against the live AppSync endpoint (create, 2 joins, consent, start, 4 turns, end, finale) round-tripped cleanly at ~100-270ms per call, so the AWSJSON double-encoding is fine. Not yet clicked through in a browser on the Amplify URL. Nobody has played it with actual people.

**Unexplained:** the checkout's `node_modules` on CT 110 was found emptied about 15 minutes before the decks build session (16 Nov), cause untraced. Site stayed up throughout; reinstalled and moved on, but worth a second look if it happens again.

## Next

1. ~~Connect the repo in Amplify~~ done 16 Nov.
2. First real deploy: check a room survives the AppSync path (the AWSJSON round trip is the likeliest snag).
3. Play it, then tune: hands-up to dare ratio, forfeit deck, mission difficulty.
4. Grow the Kink and Swinger decks after a real night; decide whether anal and three-person cards ever come in (each would need its own lobby question).
5. Open questions for Rob: whether the host should be able to sit out as a non-player dealer; whether the public URL should sit behind a password while testing (matters more now Swinger-deck content is reachable by anyone with the link, no accounts).
