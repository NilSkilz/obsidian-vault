# Tide Finances

Home finances section in Tide (mission-control, cracky.co.uk). Income/expenditure, savings, P&L, mortgage, house value, spending plans. Kicked off 24 Sep 2026.

**Scope:** parents-only (same wall as mood/health/journal). Default is a shared Rob+Aimee view unless Rob says otherwise. Kids see nothing.

## Data sources

| Source | What | How | Status |
|---|---|---|---|
| Starling | **Joint account** (opened Oct 2022) + **Personal account** (opened Oct 2022): balances, transactions, Spaces | Personal Access Tokens from developer.starlingbank.com (read scopes incl. savings-goal), nightly sync | **BOTH LIVE 24 Sep.** Tokens in `~/.config/jarvis/starling.env` (chmod 600) as `STARLING_TOKEN_JOINT` / `STARLING_TOKEN_PERSONAL`. Spaces visible on both (joint has 6: Food, Bills, Short Term Savings, Holidays, Fuel, Swear Jar). Full history reachable via `settled-transactions-between` in ≤1yr chunks |
| Monzo | current account, balance + transactions | OAuth client at developers.monzo.com; SCA approval in app. Full history only for 5 min post-auth (then rolling 90 days). Access + refresh tokens (confidential client, so refresh works) in `~/.config/jarvis/monzo.env` | **LIVE + FULL BACKFILL DONE 24 Sep 22:05.** Rob authed via the old LAN-IP link (worked despite the browser error page: the listener caught the code and exchanged it). Backfill poller choked on `invalid_time_range`, so history was grabbed by `~/finance/monzo-grab.py` (60-day windows, `since`=txn-id pagination) inside the 5-min window: **14,335 txns across 5 accounts** to `~/finance/monzo/txns-<acc>.json`. Personal retail (open, 3,951 txns 2017→now), rewards acct (open, Sep 2025, 0 txns), old joint (closed 2022, 9,865), old prepaid (closed, 80), old business (closed, 439). Personal balance 24 Sep: **-£713.09 (overdrawn)**; pots all deleted/empty. Ongoing sync now only needs the rolling 90 days + refresh-token rotation |
| NS&I | savings (Premium Bonds) | no API, but **ledger-tracked**: seed £4,000 (24 Sep 2026), then derive from Starling joint transactions. Only flows: £250/month in from the Bills Space, occasional transfers out to joint. Wins are invisible unless paid out, so true-up the real NS&I number occasionally | semi-auto, seeded 24 Sep |
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

- ~~Starling tokens (joint + personal, with savings-goal scope)~~ done 24 Sep, both verified
- ~~Monzo OAuth client ID + secret (confidential client)~~ done 24 Sep, authed + approved, full history backfilled
- ~~NS&I current value~~ £4,000 as of 24 Sep, ledger-tracked from here
- Mortgage terms: balance, rate + fix end date, remaining term, monthly payment
- House purchase price + year
- Current values: Wealthify, PensionBee, both private pensions
