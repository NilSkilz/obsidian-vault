# Tide Finances

Home finances section in Tide (mission-control, cracky.co.uk). Income/expenditure, savings, P&L, mortgage, house value, spending plans. Kicked off 24 Sep 2026.

**Scope:** parents-only (same wall as mood/health/journal). Default is a shared Rob+Aimee view unless Rob says otherwise. Kids see nothing.

## Data sources

| Source | What | How | Status |
|---|---|---|---|
| Starling | **Joint account** (opened Oct 2022) + **Personal account** (opened Oct 2022): balances, transactions, Spaces | Personal Access Tokens from developer.starlingbank.com (read scopes incl. savings-goal), nightly sync | **BOTH LIVE 24 Sep.** Tokens in `~/.config/jarvis/starling.env` (chmod 600) as `STARLING_TOKEN_JOINT` / `STARLING_TOKEN_PERSONAL`. Spaces visible on both (joint has 6: Food, Bills, Short Term Savings, Holidays, Fuel, Swear Jar). Full history reachable via `settled-transactions-between` in ≤1yr chunks |
| Monzo | current account, balance + transactions | OAuth client at developers.monzo.com; SCA approval in app. Full history only for 5 min post-auth (then rolling 90 days). Access + refresh tokens (confidential client, so refresh works) in `~/.config/jarvis/monzo.env` | **LIVE + FULL BACKFILL DONE 24 Sep 22:05.** Rob authed via the old LAN-IP link (worked despite the browser error page: the listener caught the code and exchanged it). Backfill poller choked on `invalid_time_range`, so history was grabbed by `~/finance/monzo-grab.py` (60-day windows, `since`=txn-id pagination) inside the 5-min window: **14,335 txns across 5 accounts** to `~/finance/monzo/txns-<acc>.json`. Personal retail (open, 3,951 txns 2017→now), rewards acct (open, Sep 2025, 0 txns), old joint (closed 2022, 9,865), old prepaid (closed, 80), old business (closed, 439). Personal balance 24 Sep: **-£713.09 (overdrawn)**; pots all deleted/empty. Ongoing sync now only needs the rolling 90 days + refresh-token rotation |
| NS&I | savings (Premium Bonds) | no API, but **ledger-tracked**: seed £4,000 (24 Sep 2026), then derive from Starling joint transactions. Only flows: £250/month in from the Bills Space, occasional transfers out to joint. Wins are invisible unless paid out, so true-up the real NS&I number occasionally | semi-auto, seeded 24 Sep |
| Wealthify | savings/investments | no API, and the Starling "marketplace integration" only surfaces Wealthify inside the Starling app, not via the public API (checked 24 Sep: no marketplace endpoints, token scopes can't cover it). BUT the full contribution ledger is in the Starling personal feed: 34 x £100 direct debits + a £10 opener = **£3,410 in**, withdrawals back out £500 + £33.76 + £91.80 + £480.11 = **£1,105.67 out**, so **net contributions £2,304.33** since Dec 2022. Plan: ledger-track contributions automatically like NS&I, true-up the market value from Rob monthly-ish | semi-auto (flows), value manual |
| PensionBee | Rob's pension pot | no public API. Manual value entry | manual |
| Private pensions | Rob's + Aimee's workplace/private pensions | manual, true-up from annual statements | manual, need current values |
| House mortgage (HSBC) | balance, rate, term, payment | one-time terms from Rob; Jarvis computes amortisation, equity, payoff date; true-up yearly from statement | **terms in 24 Sep:** balance **£126,311**, rate **4.44%** fixed to **31 May 2027**, 10% p.a. overpayment allowed, original loan £179,955, **221 payments remaining** (ends ~Feb 2045). Rob thinks it was a 25yr loan but isn't sure; 221 from Sep 2026 maths out to a 30yr term from the Feb 2015 purchase (or a remortgage that reset the term). Estimated payment from amortisation ~£838/mo, verify against the actual DD in the Starling feed |
| Field mortgage | balance, rate, term | same treatment as the house | **terms in 24 Sep:** balance **£35,126.83**, rate **1.89%** expiring **Jan 2027** (nearest rate cliff in the household!), original loan £42k, **231 payments remaining** (ends ~Dec 2045). Estimated payment ~£182/mo, verify against Starling feed |
| House value | estimate | purchase price + UK House Price Index (free gov data, monthly) | **have it: £199,950 on 2 Feb 2015** (from Rob, 24 Sep). HPI scaling from Feb 2015 baseline |
| Field value | estimate | bought from woodlands.co.uk: a couple of acres of meadow + woodland, held as an investment for the kids. Purchase price/date TBC (original mortgage was £42k, so likely bought around 2026 given 231 payments left) | manual; need purchase price + date from Rob, then hold at cost or true-up occasionally (no HPI equivalent for amenity woodland) |

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
- ~~House purchase price + year~~ £199,950, 2 Feb 2015
- ~~Mortgage terms~~ house + field both in, 24 Sep (see table). Monthly payments to be confirmed from the Starling DD feed
- Field purchase price + date (for the asset side; mortgage side is fully specced)
- Current values: Wealthify (net contributions £2,304.33 known, need market value), PensionBee, both private pensions
