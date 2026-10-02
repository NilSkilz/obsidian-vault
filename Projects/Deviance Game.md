# Deviance Game

Adult board game ("sexy Monopoly"): buy properties going round the board; if you can't pay rent, you pay in sexual favours instead. Rob's build, picked up again 2 Oct 2026.

## Where things live

- Repo: `github.com/the-deviance/deviance-game` (cloned via HTTPS with gh auth, SSH key refused)
- Local checkout: `/home/jarvis/projects/deviance-game`, branch `main`
- Dev server: `yarn start` on CT 110, http://192.168.1.11:3000
- **Trello board: https://trello.com/b/26K0iCIB** (created 2 Oct 2026, lists: Backlog / To Do / Doing / Done)

## Stack

React 18 + partial TypeScript, Create React App, Bootstrap/Bootswatch, two dice libraries. Card decks in `src/data/` (action/chamber/fate/stage, ~6k lines of card data), game state split across GameContext, `useGameData.js` and raw localStorage reads (a known bug source, ticketed).

## State (2 Oct 2026)

Rob says it all basically works but was buggy, main culprit being magic-number "enums" (dress level, gender, target_sex are bare numbers). Top tickets on the board: unit tests, mobile support (currently unusable on phones), better/more varied cards. Backlog has the enum refactor, TS migration, new-game/resume flow, lint cleanup, HTTPS hosting.

**State single-source refactor done** (eve of 2 Oct, branch `refactor/single-state-source`, commit 645b5b1, local only): all game state now lives in one reducer in `GameContext.tsx`, lazy-loaded from and persisted to localStorage by the provider. `useGameData` kept its public API as a thin typed wrapper, so components barely changed; `movePlayer` resolves with the post-move player so `Board/center.js` no longer re-reads localStorage mid-handler. Deleted the dead parallel state system (`useGameOperations.ts`, `PlayerDataContext.js`). Fixed en route: MainScreen's Increase Spice Level button was passing its click event in as game data and writing NaN spice to storage; dress level could increment past "Naked". 16 reducer unit tests added (all green), smoke-tested in headless Chrome.

**Blocked on push**: Jarvis's GitHub auth is a fine-grained PAT that doesn't include this repo (NilSkilz has write as a collaborator, but the token's repo list doesn't cover `the-deviance/deviance-game`), and the box's SSH key isn't on GitHub. Rob needs to either add the repo to the PAT (github.com/settings/personal-access-tokens) or add Jarvis's SSH key as a write deploy key. Key: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIjbqaKpAX/B1ggQtUp9lBaCjGBp+lcB2C+2kMe5i1X9 jarvis@192.168.1.11`

### Gotchas found in the code

- Two opposite dress scales coexist: game state uses 0=Fully Clothed → 3=Naked (`center.js` labels), while `PlayerForm`'s slider UI uses the inverse and converts with `3-value`. Default new player is dress 3 (naked) but PlayerForm's mount effect resets it to 0. One for the enums ticket.
- `propertyData` is still its own context + localStorage store (`usePropertyData.js`), with owners kept in memory after New Game until a reload. Belongs to the new-game/resume ticket.
- `cardManager.js` reads the used-card pile from localStorage at module load; the spice auto-increase in `center.js` keys off that pile's length.
