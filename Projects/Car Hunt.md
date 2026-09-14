# Car Hunt (used EV)

Started 14 Sep 2026, after the flat tyre on the M5 made the case for itself. Replace/supplement the household fleet with a second-hand electric car.

## The brief (Rob, 14 Sep 2026)

- **Preference:** Tesla Model 3. Open to alternatives if the numbers are better.
- **Cash:** about £2,000 deposit.
- **Rest on finance:** a personal loan (Tesco or similar), around 4 years.
- **Monthly ceiling:** about £300.
- **Search area:** within 100 miles of home (Crackington Haven, anchored on EX23 0JG).

## What that actually buys

Tesco Bank's representative APR is **6.4%** on £7,500-£25,000 over 1-5 years (checked 14 Sep 2026; representative means at least 51% of accepted customers get it, so treat it as the best case).

| Term | APR | Borrow for £300/mo | + £2k deposit = car budget | Total paid |
|---|---|---|---|---|
| 48 mo | 6.4% | ~£12,700 | **~£14,700** | £16,400 |
| 48 mo | 9.9% | ~£11,900 | ~£13,900 | £16,400 |
| 60 mo | 6.4% | ~£15,300 | ~£17,300 | £20,000 |

**Working ceiling: £14,700**, with £15,500 as the stretch on a car worth haggling over. Going to 5 years buys ~£2,600 more car for ~£3,600 more interest and payments.

A personal loan (not PCP/HP) is the right shape here: he owns the car outright from day one, no mileage limits, no balloon, and a used EV's residual risk stays his problem either way. Budget separately for the insurance change, an EV on a Cornwall postcode is not a like-for-like swap for the Fiesta.

## Rules the hunt applies

- Hard exclude: **Cat N/S/C/D** write-offs (scored down to nothing, never pinged).
- **Battery size matters more than usual here.** Crackington to the Cheltenham office is ~120 miles each way. Anything under ~45kWh (Mazda MX-30, e-Golf, Mini SE, 40kWh Leaf) is a second car at best, and gets penalised.
- Under 60k miles is a plus, over 90k a minus.
- Within 60 miles is a plus (viewable without a day out).
- Tesla gets a thumb on the scale, per Rob's preference.
- "Delivery only" listings are included, they're usually the bigger dealer groups.

## Market snapshot, 14 Sep 2026 (first sweep, 104 listings)

**Tesla Model 3, within 100 miles, under £15.5k** (only nine exist at this price, so the market is thin):

| Price | Year | Spec | Miles | Where |
|---|---|---|---|---|
| £13,000 | 2020 | SR+ RWD | 54,054 | Swansea (68 mi), private |
| £14,200 | 2019 | SR+ RWD | 54,000 | **Saltash (30 mi)**, private |
| £14,500 | 2020 | SR+ RWD | 60,000 | delivery |
| £14,700 | 2020 | SR+ RWD | 55,000 | delivery, listed with 87.8% battery health |
| £14,999 | 2019 | Long Range AWD | 67,798 | **Plymouth (36 mi)** |
| £12,280 | 2020 | Long Range AWD | 101,176 | Barry (77 mi), very high miles |
| £11,199 | 2019 | SR+ RWD | 85,000 | Cardiff, **Cat N, excluded** |

Read: a Model 3 is reachable, but it's 2019-2020 SR+ with 55-70k miles at the very top of budget. The Saltash car (2019 SR+, 54k, £14,200, private) and the Plymouth Long Range (£14,999, 67k) are the two worth seeing in person.

**Better value if he'll flex on the badge** (all 50-58kWh, all real-range usable):

- **MG4 SE 51kWh** 2022-2024, 24k-42k miles, **£11,695-£12,400**, several in Plymouth. Newest cars in the budget by years, and MG's 7-year warranty may still be live.
- **VW ID.3 Pro 58kWh** 2020-2023, **£12,000-£12,500**, Plymouth and Cardiff. Biggest usable battery at the price.
- **Peugeot e-2008 50kWh GT** 2020-2021, **£10,299-£11,850**, Plymouth.

The pattern: £3,000 of the Tesla price is the badge and the Supercharger network. Worth naming out loud before he commits, not to talk him out of it.

## Things to check before buying any Model 3

- **Battery health** (ask for a screenshot of a full-charge range estimate, or a third-party report). 85%+ at this age is normal, under 80% is a haggle.
- **Battery/drive warranty is 8 years / 100,000 miles.** A 2019 car runs out in 2027, and a 101k-mile car is already out.
- **Autopilot hardware** (HW2.5 vs HW3) and whether any paid FSD/EAP transfers. Usually it doesn't.
- MOT history, and whether it's had the **12V battery** and **upper control arms** done, both are known age items.
- Home charging: a 7kW wallbox is £800-£1,200 installed, and it's the difference between an EV being cheap and being annoying.

## The automation

`Jarvis/bin/car-hunt.sh`, cron **40 8,12,16,20 daily**.

- Scrapes public AutoTrader search pages with headless Chrome (`/home/jarvis/tools/car-hunt/scrape-autotrader.js`), two pages per watch.
- Watches: Tesla Model 3, Hyundai Kona Electric, Kia e-Niro, Polestar 2, VW ID.3, MG4, plus a catch-all "any EV under £14.5k with under 60k miles".
- Dedupes against `~/.local/state/jarvis-car-hunt-seen.txt`, so a listing is only ever considered once.
- Scores each new listing and **pings Telegram only for 8+**. Everything else goes to the digest and surfaces as a line in the evening briefing.
- State: `jarvis-car-hunt-listings.jsonl` (everything seen, with scores), `jarvis-car-hunt-digest.log` (for the brief), `jarvis-car-hunt.log`.
- `SEED=1` scrapes without pinging, `DRYRUN=1` prints instead of sending.

Seeded 14 Sep 2026 with the 104 listings already on the market, so from here he only hears about genuinely new ones.

## Open threads

- Rob and Aimee to agree whether this **replaces the Fiesta** (MOT 22 Sep, coolant and handbrake both open) or the Dacia, or is a third car. That changes the deposit: selling the Fiesta adds to the £2k.
- Is there off-street parking for a wallbox? Assumed yes, unconfirmed.
- Loan: get an actual rate quote (soft search) before committing to a price ceiling. 6.4% is the advertised best case, not a promise.
