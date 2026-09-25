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

## Categorisation rules the sync applies

- Own-name transfers between visible accounts pair off as `internal`.
- NS&I moves are `internal` BOTH ways (added 25 Sep 2026): deposits go to counterparty 'NS&I', withdrawals return as codes ending 'nspb'. Before this, premium bond withdrawals inflated "Other income".
- Wealthify stays visible as the "Savings & investments" line (one-way, committed).
