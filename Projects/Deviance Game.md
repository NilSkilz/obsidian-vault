# Deviance Game

Adult board game ("sexy Monopoly"): buy properties going round the board; if you can't pay rent, you pay in sexual favours instead. Rob's build, picked up again 2 Oct 2026.

## Where things live

- Repo: `github.com/the-deviance/deviance-game`. Push/pull via SSH deploy key (added 2 Oct eve, remote set to SSH). The gh PAT does NOT cover this repo, so `gh pr create` 403s.
- **Workflow: commit straight to `main` and push, no branches, no PRs** (Rob, 2 Oct 2026, "this is just for me atm"). Typecheck + tests before pushing still apply.
- Local checkout: `/home/jarvis/projects/deviance-game`, branch `main`
- Dev server: `yarn start` on CT 110, http://192.168.1.11:3000
- **Trello board: https://trello.com/b/26K0iCIB** (created 2 Oct 2026, lists: Backlog / To Do / Doing / Done)

## Stack

React 18 + partial TypeScript, Create React App, Bootstrap/Bootswatch, two dice libraries. Card decks in `src/data/` (action/chamber/fate/stage, ~6k lines of card data), game state split across GameContext, `useGameData.js` and raw localStorage reads (a known bug source, ticketed).

## State (2 Oct 2026)

Rob says it all basically works but was buggy, main culprit being magic-number "enums" (dress level, gender, target_sex are bare numbers). Top tickets on the board: unit tests, mobile support (currently unusable on phones), better/more varied cards. Backlog has the enum refactor, TS migration, new-game/resume flow, lint cleanup, HTTPS hosting.

**State single-source refactor done** (eve of 2 Oct, branch `refactor/single-state-source`, commit 645b5b1, pushed): all game state now lives in one reducer in `GameContext.tsx`, lazy-loaded from and persisted to localStorage by the provider. `useGameData` kept its public API as a thin typed wrapper, so components barely changed; `movePlayer` resolves with the post-move player so `Board/center.js` no longer re-reads localStorage mid-handler. Deleted the dead parallel state system (`useGameOperations.ts`, `PlayerDataContext.js`). Fixed en route: MainScreen's Increase Spice Level button was passing its click event in as game data and writing NaN spice to storage; dress level could increment past "Naked". 16 reducer unit tests added (all green), smoke-tested in headless Chrome.

**Enum refactor done** (later that evening, branch `refactor/typed-enums`, stacked on the state branch, pushed): `DressLevel` / `Gender` / `Sexuality` / `TargetSex` as const-object enums in `src/types/game.ts`, `DRESS_LABELS` as the single label source (center.js's duplicate array deleted), `genderToTargetSex` for the off-by-one card scale, `canPlayersInteract` rewritten with named values and covered by new tests (22 tests green total). Bugs fixed en route: selecting "Gay" in player setup silently did nothing (the input parser only handled values 0-2), and `createDefaultPlayer` defaulted new players to dress 3 (Naked on the game scale, masked by PlayerForm's reset). Both merged to `main` and pushed 2 Oct eve (fast-forward, 22 tests + typecheck green on the merge); the refactor branches are deleted local and remote.

### Gotchas found in the code

- Two opposite dress scales: game state uses 0=Fully Clothed to 3=Naked (`DressLevel`), the setup slider runs the other way. Handled on the enums branch: the inversion now lives only in `sliderToDress` inside PlayerForm.
- `propertyData` is still its own context + localStorage store (`usePropertyData.js`), with owners kept in memory after New Game until a reload. Belongs to the new-game/resume ticket.
- `cardManager.js` reads the used-card pile from localStorage at module load; the spice auto-increase in `center.js` keys off that pile's length.
