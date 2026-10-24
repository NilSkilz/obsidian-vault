# Household Money (structure)

How the Stokes household money actually flows, per Rob 25 Sep 2026. The live numbers are on cracky.co.uk/finances; this file is the shape, not the balances.

## Accounts and pots, what each is FOR

| Pot | Purpose |
|---|---|
| Starling Joint | The household hub: both salaries land (via personal accts), all bills/mortgages/family spend |
| Starling Personal (Rob) | Rob's salary lands, then moves to joint minus pocket money |
| Monzo Personal (Rob) | Rob's day-to-day personal spending card (overdraft cleared to 1p on 25 Sep 2026) |
| NS&I Premium Bonds | HOUSEHOLD savings (the de facto emergency fund), ~£500/mo in, withdrawals when the month runs short |
| Wealthify | Rob's PERSONAL pot, earmarked for holidays and Christmas (a sinking fund, not investing) |

## Pocket money system

- Rob and Aimee each take **£200/mo pocket money**; the rest of both salaries goes to the joint account.
- Rob saves £100 of his (the £100/mo Wealthify DD) and spends the remainder, historically overspending into the Monzo overdraft.
- Rob's hobby spend (crafting materials, electronics, project parts) comes out of personal money; lots of small amounts. From Sep 2026 rope sales (2 orders in hand) start offsetting it.

## Car repayment to Rob's mum (from Nov 2026)

- Rob's mum (Anne Stokes) fronted the money for the MG4 (YG73 NUO, £14,218, bought 9 Oct 2026). Rob repays her **£300/mo by standing order**, roughly 47 payments (about 4 years) if it's interest-free. The plan is the 1st of the month from the Starling Joint, starting Nov 2026 (per Rob, 24 Oct 2026; the SO itself still needs setting up).
- This is separate from the long-running **£50/mo to Anne** (listed in the committed outgoings). Whether that £50 continues is still open.
- For context, it replaces nothing: the Black Horse finance (£682.79/mo) ended Feb 2026. The car's real cost is set against the drop in petrol spend.

## Categorisation rules the sync applies

- Own-name transfers between visible accounts pair off as `internal`.
- NS&I moves are `internal` BOTH ways (added 25 Sep 2026): deposits go to counterparty 'NS&I', withdrawals return as codes ending 'nspb'. Before this, premium bond withdrawals inflated "Other income".
- Wealthify stays visible as the "Savings & investments" line (one-way, committed).

## The old spreadsheet P&L (design reference, 25 Sep 2026)

Rob shared his pre-Jarvis finance spreadsheet (2023-era numbers, so the figures are dead: Tesla PCP, old salaries). What it shows about the P&L he WANTS, beyond what /finances already does:

- **A budget, not just actuals**: named line items with a fixed expected monthly amount (Mortgage £x, Netflix £y), grouped as House Bills / Insurance / Entertainment / Debts / Subscriptions -> Total Fixed, then Allowances / Expenses / Savings -> Surplus.
- **A "confirmed" tick per line**: is this DD verified as still live at this amount.
- **Explicit allowances as lines**: Rob £200, Aimee £200, Dexter £25, Logan £25.
- **Sinking funds inside savings**: Oil £50, Boiler £100, MOT £75, Appliances £75 (monthly set-asides for lumpy costs).

Possible future feature: budget-vs-actual (expected line amounts vs what the ledger says). The wishlist tab became the /finances wishlist section (shipped 25 Sep 2026, `financeWishlist` table, seeded with his house items).
