# Liaisons

Party game for consenting adults: "lobby on phones, then phones away". Started 16 Nov 2026 as the no-board successor to the Deviance board game (see `Projects/Deviance Game.md` for the design conversation that led here). **Name:** Liaisons, settled 16 Nov 2026 when Rob created the repo under that name. It started life as "Undertow" (my pick, he said it didn't land and to ignore the sea theme); folder, package, Amplify stack names, boot script and this file were all renamed the same day.

## Where things live

- Local checkout: `/home/jarvis/projects/liaisons`, branch `main`, first commit `9427d3f`.
- Remote: `git@github.com:NilSkilz/liaisons.git` (private, Rob created it 16 Nov; the gh PAT can't create repositories). `main` pushed over the SSH key. Not yet connected in the Amplify console.
- **Public: https://liaisons.cracky.co.uk** (NPM proxy host 24 → `192.168.1.11:3010`, wildcard cert, no access list: anyone with the URL can open a room, there are no accounts). LAN: http://192.168.1.11:3010. Served by `Jarvis/bin/liaisons-preview.sh` (`vite preview` plus the LAN game backend on CT 110), in cron `@reboot`; re-run it after every `npm run build`. Rooms persist in `.data/rooms.json`.
- Browser check: `/home/jarvis/tools/browser-check/liaisons-flow.js` drives three phones plus a late joiner through a whole night at 390x844.

## Stack

Vite + React 18 + TypeScript, no UI library. Amplify Gen 2 backend, deliberately tiny: AppSync with an API key, one mutation (`play`) and one query (`room`), one Lambda, one DynamoDB table (one item per room, 48h TTL). No Cognito.

The whole game is `shared/engine.ts`, a pure `handle(store, op, args)` used by both the Lambda and the LAN dev server (`dev/server.ts`), so the LAN build runs the same code AWS will. With no `amplify_outputs.json` the app talks to the LAN server; in an Amplify build it uses AppSync.

**Privacy model:** the browser can't read game state. Every move goes through the engine, which returns only that player's view. Nobody's ticks, secrets or missions are ever sent to another phone, the host's included. There's a test that asserts it.

## How it plays (as built)

- **Lobby:** room code, name, then per person: No / Flirty / Hot / Filthy, plus a separate level for solo dares. Everyone starts unanswered and has to choose for each person. Someone joining later shows up as unanswered and knocks you back to "not ready".
- **Start** deals each player a secret mission (aimed only at someone who ticked them back; none of the missions need touch).
- **Host is the dealer:** hands-up questions for the room (rule is random: minority forfeits, hands-up forfeit, or hands-down forfeit), solo dares, pair dares. Pairs need a mutual yes and the card never exceeds the lower of the two answers or the room heat. Turns are shared out evenly.
- **Forfeit** is pick-from-two, always two different kinds (so never drink-or-drink), same size whatever was dodged.
- **Partner pass:** free, redraws for the same player with a different partner or a solo card, records nothing.
- **Heat vote:** eyes closed, host taps in the hand count, only unanimous raises it.
- **Late joiners / changing answers:** host shows the room code; a late joiner gets a mission once they've answered.
- **End:** host reveals each mission, room votes pulled-it-off or busted, then awards (Bravest, Conscientious Objector, Most Wanted, Smooth Operator, Rumbled, Never Flinched).

## Content (starter decks, written 16 Nov)

60 hands-up questions, 20 solo dares, 34 pair dares, 14 forfeits, 18 missions. **Heat stops at 3 (Flirty / Hot / Filthy).** Levels 4 and 5 don't exist yet; they arrive when the legacy 1,056 Deviance cards are ported. That port needs a decision, because those cards use 19 preference gates (pain, restraint, oral and so on) that this lobby doesn't ask about.

## State (16 Nov 2026)

Verified: 16 engine tests, typecheck on app and backend, production build, and the full flow in headless Chrome at phone size (zero pairings outside mutual ticks across 120 cards, no console errors, no horizontal overflow). The backend definition synthesizes to CloudFormation with `cdk synth` (command in the README).

Not verified: nothing has been deployed to AWS (no credentials on this box), so the AppSync and DynamoDB path has never run for real. Nobody has played it with actual people.

## Next

1. Rob connects `NilSkilz/liaisons` in the Amplify console (repo created and pushed 16 Nov). First deploy will be the first time the backend has run on AWS.
2. First real deploy: check a room survives the AppSync path (the AWSJSON round trip is the likeliest snag).
3. Play it, then tune: hands-up to dare ratio, forfeit deck, mission difficulty.
4. Port the legacy deck and decide how levels 4 and 5 get their consent gates.
5. Open questions for Rob: the name; whether the host should be able to sit out as a non-player dealer.
