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

Rob says it all basically works but was buggy, main culprit being magic-number "enums" (dress level, gender, target_sex are bare numbers). Top tickets on the board: unit tests, mobile support (currently unusable on phones), better/more varied cards. Backlog has the enum refactor, state single-source-of-truth, TS migration, new-game/resume flow, lint cleanup, HTTPS hosting.
