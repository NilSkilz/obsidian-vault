# Tide Finances: Spending Analysis

> **Correction, 24 Sep 23:30:** the groceries figures below include Morrisons Bude petrol-station fuel (~£300/mo since March 2026), which the bank tagged GROCERIES via the 'MORR BUDE' kiosk terminal. Recategorised to fuel that night (round 5 in `Tide Finances.md`). True groceries typical is ~£950/mo, not £1,254; the grocery "creep" is roughly half real, half fuel misfiled. Household fuel total is ~£670/mo, which is its own conversation. Total spend and the £466/mo overspend are unchanged (money moved between categories, not in or out).

Analysed: 2026-09-24. Window: 2025-09-01 to 2026-08-31 (12 full months). Accounts: Starling Joint, Starling Personal, Monzo Personal, Monzo Rewards (open, non-space). Internal transfers excluded. All figures from `db/family.sqlite` on CT 112, read-only.

## Headline numbers

| Figure | Value |
|---|---|
| Total debits, 12 months | £79,693 |
| Less savings (NS&I £3,750, Wealthify £1,000) | £74,943 true consumption |
| Average true spend per month | £6,245 |
| Recent run rate (Mar to Aug 2026) | ~£6,670/mo and rising |
| Income (credits incl. Aimee's wages) | ~£6,418/mo average |
| Committed minimum monthly outgoings | **~£2,030** (see below) |
| Survival floor (bills + lean groceries + fuel) | ~£3,200/mo |

The uncomfortable trend: spending in the first half of the window averaged £6,210/mo, the last six months averaged £7,073/mo, up 14%. The Black Horse car finance (£682.79/mo) ended in February 2026, which should have freed ~£680/mo, but total spend went UP afterwards. The headroom got absorbed, mostly by groceries, shopping and transport.

## 1. Committed monthly outgoings (the "minimum")

Regular payments verified by cadence in the data, at current (mid-2026) amounts:

| Payment | £/mo | Notes |
|---|---|---|
| HSBC mortgage (house) | 837.88 | Fix ends May 2027, 4.44% |
| HSBC mortgage (field) | 181.54 | Fix ends Jan 2027, 1.89% |
| Council tax (Cornwall Council) | 191.00 | 10-month schedule, £181 to £191 over the year. Bank miscategorises it as "transport" |
| Octopus Energy | 150.00 | DD has floated £100 to £246; summer 2026 is £100 to £150, Sep DD back to £200. Budget £150 to £200 |
| South West Water | 74.46 | £893.50/yr, some months doubled |
| BoilerJuice oil plan | 40.00 | £40/mo plan since spring; £434 total over the year |
| EE mobiles | 95.00 | 4 to 5 charges/mo, crept from ~£66-88 to ~£97 (see savings) |
| Aviva (policy MHO074964349) | 45.05 | Was £40.87 until June 2026, +10% creep |
| Aviva (policy 2789498EF) | 13.51 | Second policy, flat all year |
| Sheilas' Wheels car insurance | 16.68 | Was ~£54 early in window, now £16.68 (car change?) |
| Halifax DD (ref 128716577) | 45.48 | **Unidentified**, see oddities |
| Parentpay (school) | 96.00 | £1,060 over 11 months, term-time weighted |
| Anne Stokes | 50.00 | £50 on the nose, every month |
| Tamar Bridge | 10.50 | 42 crossings at £3 |
| Subscriptions (full list below) | 179.00 | |
| **Total committed** | **~£2,026** | Range £1,950 (summer, non-council-tax month) to ~£2,200 (winter energy + council tax) |

**Minimum monthly outgoings: call it £2,030.** Everything the household is contractually or practically on the hook for before anyone eats. Note this excludes NS&I (£312/mo avg) and Wealthify (£100/mo), which are savings, not costs, and excludes the finished Black Horse finance.

### Subscription inventory (~£179/mo)

| Sub | £/mo | Verdict |
|---|---|---|
| Spotify | 21.99 | Family plan, fine if all using it |
| Netflix | 18.99 | Standard |
| DigitalOcean | 19.20 | **Candidate**: Rob self-hosts a Proxmox cluster. What is still on DO that could not live on CT hardware? £230/yr |
| Xbox Game Pass / Microsoft | ~17.00 | Being bought month-to-month ("Ultimate 1 M" £14.99 to £16.99). Month-by-month is the most expensive way to buy it |
| OpenAI | 17.87 | 9 months running, ~£20/mo. API or ChatGPT Plus? |
| IONOS + 1&1 Web Hosting | 14.35 | **Two hosting payments to the same company** (1&1 is IONOS). £172/yr combined. Consolidate |
| Newshosting | 12.68 | Usenet. £139/yr, still used? |
| Adobe | 11.99 | 8 months. Photography plan? Cancel if idle |
| Google Workspace (cracky) | 10.54 | Two billing lines, £126.50/yr |
| Amazon Prime | 7.92 | £95/yr annual, good value if used |
| Nabu Casa | 6.50 | HA Cloud, keep |
| JetBrains | 5.96 | Keep |
| Ring | 4.99 | Doorbell, keep |
| Dakboard | 4.59 | The DAKboard died with the NUC rebuild. **Is this paying for a dead dashboard?** |
| AWS | 4.40 | Small, check what it hosts |

Forgotten/duplicated flags: **Dakboard** (possibly paying for retired kit), **IONOS + 1&1 double hosting**, **Adobe** if unused, **Xbox month-to-month pricing**, **DigitalOcean vs the Proxmox cluster**.

## 2. Variable spend: averages and trends

| Category | £/mo avg | First 6 mo | Last 6 mo | Trend |
|---|---|---|---|---|
| Groceries | 1,073 | 892 | 1,254 | **Up 41%, the big creep** |
| Shopping | 833 | 799 | 866 | High and lumpy (Dec £1,698, Aug £1,329) |
| Eating out | 474 | 437 | 511 | Creeping up |
| Transport + fuel | 456* | 414 | 498 | Up (May £1,001 spike: tyres/MOT season) |
| Entertainment | 322 | 360 | 283 | Oct 2025 skewed by Merlin £965 |
| Cash withdrawals | 127 | 133 | 122 | £1,520/yr untracked |
| Lifestyle | 114 | 86 | 141 | Small but doubling |
| Holidays | 90 | | | £1,082/yr, mostly one £567 payment |

*Transport excludes the £1,859 of council tax the bank miscoded as transport.

### Where the money actually goes (12-month merchant totals)

- **Grocery mix**: Morrisons £4,484 (326 visits), Tesco £2,195, Lidl £1,857 (233 visits), B&M £1,574, Iceland £1,432, Crackington village shop £284. Note the Lidl average basket is £7.97 vs Morrisons £13.75: lots of small top-up shops rather than one planned weekly shop, which is the classic overspend pattern.
- **Amazon**: £2,962 across 164 orders (avg £18) plus Amazon Marketplace £374 and AliExpress £405. Combined **£312/mo** of largely impulse-sized orders.
- **Eating out**: McDonald's £1,201 across **80 visits** (6 to 7 a month), Noteworthy Cafe £383, Harvester £337, Highway 39 £275, Subway £253 (42 visits), Rosies Kitchen £250.
- **Fuel**: Tesco Petrol £1,394, BP £922, Shell £230, plus Tesla public charging £752 (stopped April 2026). ~£275/mo for the cars while the EV was around.

## 3. Top savings opportunities (realistic, from the data)

1. **Groceries back to the spring baseline: ~£180/mo.** The last six months ran £1,254/mo against £892/mo a year ago; food inflation does not explain a 41% jump. Concretely: the household made 640+ separate grocery visits this year (Morrisons 326, Lidl 233, B&M small buys). Shift the weekly shop weight from Morrisons/Tesco/Iceland (£8,111/yr combined) toward Lidl, and kill the daily top-up habit. Target £1,050 to £1,070/mo, which is just the year's own average.

2. **Amazon/AliExpress impulse orders: ~£100/mo.** £3,741/yr over ~198 orders averaging £18. A one-week cooling-off basket rule (nothing under £25 ordered same-day) typically kills a third of these. Target £210/mo from £312.

3. **Eating out, McDonald's specifically: ~£110/mo.** 80 McDonald's visits at £15 average is £100/mo on its own; halve it and trim one takeaway (Domino's runs £30 a hit) and eating out drops from £474 to ~£365/mo without becoming joyless.

4. **Subscription and hosting cull: ~£50/mo.** Dakboard £4.59 (likely paying for a dead dashboard), IONOS/1&1 duplication ~£8 net, DigitalOcean £19.20 (migrate to Proxmox), Adobe £11.99 if idle, Newshosting £12.68 if idle, switch Xbox Game Pass from month-to-month buying to annual/discounted (~£4/mo). Even the conservative half of that list is £40 to £60/mo.

5. **EE bill audit: ~£30/mo.** £95 to £97/mo and rising across 4 to 5 lines/charges. Any handset now paid off should drop to SIM-only (£8 to £12/line). Worth a 20-minute account review; £60 to £70/mo is achievable for four SIMs plus one contract.

**Total identified: roughly £470/mo (~£5,600/yr)** without touching holidays, entertainment, or anyone's hobbies.

Also worth booking ahead: the **field mortgage fix ends Jan 2027** (1.89%) and the **house fix May 2027** (4.44%). The field payment will jump materially at current rates; start the remortgage shop around November 2026.

## 4. Oddities for a human look

- **Brian Solomon, £2,000, 9 Mar 2026** (Starling Joint, ref "Rob Stokes"). Largest single payment of the year. Presumably known, but it is unlabelled in the data.
- **Halifax DD, £45.48/mo, ref 128716577, £551/yr.** ~~Unidentified~~ Resolved 24 Sep: car insurance (Rob: the Dacia). Policy runs back to Aug 2018; the double-months are just a wobbly payment date. Remaining question: why it jumped £26 -> £46.50 mid-term in June 2025 (see Tide Finances round 7).
- **Black Horse finance ended Feb 2026** (£682.79 x 6 in window, plus a £90.68 "Blackhorse Ltd" settlement). Tesla public charging (£752, 101 sessions) stopped in April 2026. Reads like the financed EV left the household around then. The £683/mo freed up has been fully absorbed by higher variable spend.
- **Merlin Entertainments £964.96, Oct 2025.** Annual passes, presumably. Renewal will be coming round about now: decide deliberately, not by auto-renew.
- **Sheilas' Wheels dropped from ~£54 to £16.68/mo** mid-window. Resolved 24 Sep: it was the Tesla's policy (started Dec 2025, dropped Mar 2026 when the car went back); the £16.68 residual is presumably the Fiesta. Aviva is home + life (two policies), not motor.
- **Aimee's wages show £0 in June 2026 then £2,800 in July** (catch-up payment). Also her wages are miscategorised as "internal" in the DB (known bug, being fixed).
- **Category noise in the bank data**: council tax coded "transport", a KFC coded "groceries", B&M split across groceries/shopping. The per-merchant numbers above are the trustworthy ones.
- **First Sports International (leisure/gym) charges stopped Nov 2025** after double-charging £30 + £35 in Sep to Nov. Stopped, so no action, just noting the £190.
- **Counselling payments** (Natsai Telfer, £50 x 2) and Tresmeer Dog Boarding (£501, 5 stays) appear as "payments": real spend, not transfers.
- **August 2026 was the most expensive month of the year at £9,181**: back-to-school (shopping £1,329, Sports Direct heavy), groceries £1,447, transport £908, IKEA £334, plus two house-mortgage DDs landing in the same calendar month (31 Aug timing quirk, not a double charge).

## Method notes

- Spend = debits on open, non-space accounts, category not 'internal', 2025-09-01 to 2026-08-31.
- NS&I and Wealthify treated as savings and excluded from consumption.
- No real debits leave the Starling spaces, so excluding them loses nothing.
- Income figure includes refunds (Amazon returns etc.) so is slightly flattering; the true margin is thinner than income minus spend suggests.
