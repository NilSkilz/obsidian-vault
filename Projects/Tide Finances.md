# Tide Finances

Home finances section in Tide (mission-control, cracky.co.uk). Income/expenditure, savings, P&L, mortgage, house value, spending plans. Kicked off 24 Sep 2026.

**Scope:** parents-only (same wall as mood/health/journal). Default is a shared Rob+Aimee view unless Rob says otherwise. Kids see nothing.

## Data sources

| Source | What | How | Status |
|---|---|---|---|
| Starling | **Joint account** (opened Oct 2022), balance + transactions | Personal Access Token from developer.starlingbank.com (read scopes), nightly sync | **LIVE 24 Sep.** Token in `~/.config/jarvis/starling.env` (chmod 600). Scopes: account, balance, transaction, receipts. Full history reachable via `settled-transactions-between` in ≤1yr chunks. Missing `savings-goal:read` so Spaces are invisible (balance shows ~£111 sitting in Spaces); Rob to add scope or reissue token |
| Monzo | current account, balance + transactions | OAuth client at developers.monzo.com; SCA approval in app. Full history only for 5 min post-auth (then rolling 90 days), so full backfill runs immediately on first auth. Tokens ~6h, refresh token needs a confidential client | waiting on client creds from Rob |
| NS&I | savings | no API. Manual value entry (or Rob forwards statement email) | manual |
| Wealthify | savings/investments | no API. Manual value entry, monthly-ish | manual |
| PensionBee | Rob's pension pot | no public API. Manual value entry | manual |
| Private pensions | Rob's + Aimee's workplace/private pensions | manual, true-up from annual statements | manual, need current values |
| HSBC mortgage | balance, rate, term, payment | one-time terms from Rob; Jarvis computes amortisation, equity, payoff date; true-up yearly from statement | need terms |
| House value | estimate | purchase price + UK House Price Index (free gov data, monthly) | need purchase price + date |

Decision 24 Sep: **no GoCardless/aggregator needed.** Starling + Monzo first-party APIs cover all transactional accounts; everything else is slow-moving manual entry.

## Build plan (once tokens land)

1. Secrets in `~/.config/jarvis/finance.env` (never in the vault or repo).
2. Finance schema in Tide DB: accounts, balances (daily snapshots), transactions, manual_assets (NS&I, Wealthify, pensions, house), mortgage terms, spending plans.
3. Nightly sync cron (Starling pull, Monzo pull with token refresh, HPI monthly).
4. Monzo first-auth full-history backfill script, run within the 5-minute window.
5. `/finances` page: net worth over time, P&L monthly, categorised spend, account balances, mortgage curve + equity, plans.

## Needed from Rob

- ~~Starling personal access token~~ done 24 Sep
- Starling: add `savings-goal:read` scope (or reissue token with it) so Spaces show up
- Monzo OAuth client ID + secret (confidential client)
- Mortgage terms: balance, rate + fix end date, remaining term, monthly payment
- House purchase price + year
- Current values: NS&I, Wealthify, PensionBee, both private pensions
