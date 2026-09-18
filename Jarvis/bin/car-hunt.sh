#!/usr/bin/env bash
# Car Hunt: watch for a second-hand EV or plug-in hybrid inside the household
# budget (Projects/Car Hunt.md). Rob's brief, 14 Sep 2026: originally ~£2k cash
# deposit plus a ~4 year loan at ~£300/month (~£14.7k). REVISED same day, 12:25:
# the deposit may go on a heat pump for the house instead, so the ceiling is
# £12,500 (all borrowed, 48mo, ~£295/month at 6.4%). The car has to last the
# 4-year loan at ~20k miles/year, i.e. it gains ~80k miles: starting mileage
# headroom now matters as much as price. Tesla Model 3
# preferred, strong alternatives watched too. PHEVs added later the same day:
# they have to be PLUG-IN (the home charger is the whole point), so ordinary
# self-charging hybrids are deliberately not watched. Confirmed 14 Sep: the
# house already has a 7kW wallbox (from "Timmy", the Model 3 they used to own),
# so charging is solved and a full EV remains the preferred outcome.
# 18 Sep 2026: narrowed to Tesla Model 3 Long Range ONLY (Rob's call); the
# alternative EVs and all PHEV watches are retired, see WATCHES below.
# Range floor (Rob, 14 Sep): home to Torquay and back on one charge, ~150 mi
# round trip, year-round. That rules out small packs and demotes Tesla SR trims.
# Within 100 miles of home (Crackington Haven).
#
# 1. Scrapes public AutoTrader search pages (headless Chrome) for each watch.
# 2. Dedupes against listings seen on previous runs.
# 3. Scores what's new on price / miles / distance / write-off status.
# 4. Pings Rob only for strong new finds; everything else lands in the digest
#    for the evening briefing.
# SEED=1 scrapes and records without pinging (used on first run so he isn't
# spammed with the entire existing market). DRYRUN=1 prints instead of sending.
set -uo pipefail

VAULT="/data/memory"
TOOLS="/home/jarvis/tools/car-hunt"
STATE="$HOME/.local/state"
LOG="$STATE/jarvis-car-hunt.log"
SEEN="$STATE/jarvis-car-hunt-seen.txt"
DIGEST="$STATE/jarvis-car-hunt-digest.log"
BEST="$STATE/jarvis-car-hunt-listings.jsonl"
TCONF="$HOME/.config/jarvis/telegram.env"
DRYRUN="${DRYRUN:-0}"
SEED="${SEED:-0}"

POSTCODE="${POSTCODE:-EX230JG}"   # Crackington Haven
RADIUS="${RADIUS:-100}"
BUDGET="${BUDGET:-15000}"         # raised from £12.5k, Rob 16 Sep 2026: bracket is £15k total again
PING_SCORE="${PING_SCORE:-8}"
# There are far more PHEVs than EVs in this budget, so they need a higher bar
# to earn an interruption. Rob's stated preference is still a full EV.
PHEV_PING_SCORE="${PHEV_PING_SCORE:-9}"

# make | model | max price | max mileage | fuel | pages
# Empty make/model = catch-all for that fuel type.
# AutoTrader's fuel wording is fussy: "Petrol Plug-in Hybrid" works,
# a bare "Plug-in Hybrid" silently returns nothing.
# Named-model caps sit ~£500 over budget: a £13k sticker is a £12.5k car after
# a haggle. Mileage caps tightened 14 Sep: at 20k/yr the car gains 80k miles
# over the loan, so a 90k starter would finish at 170k.
# 18 Sep 2026: Rob narrowed the hunt to Model 3 Long Range ONLY. All the
# alternative-EV and PHEV watches are retired; AutoTrader has no reliable trim
# filter, so the scrape stays "Model 3" and the Long Range cut happens in the
# scoring step below (non-LR cars are dropped entirely, not even digested).
WATCHES=(
  "Tesla|Model 3|15500|80000|Electric|3"
)

mkdir -p "$STATE"; touch "$SEEN"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) car-hunt start (seed=$SEED dryrun=$DRYRUN) -----"

RAW="$(mktemp)"; NEW="$(mktemp)"
trap 'rm -f "$RAW" "$NEW"' EXIT

for w in "${WATCHES[@]}"; do
  IFS='|' read -r mk md pmax mmax fuel npages <<<"$w"
  args=(--postcode "$POSTCODE" --radius "$RADIUS" --price-to "$pmax" \
        --pages "${npages:-2}" --fuel "$fuel")
  [ -n "$mk" ] && args+=(--make "$mk")
  [ -n "$md" ] && args+=(--model "$md")
  [ -n "$mmax" ] && args+=(--max-mileage "$mmax")
  case "$fuel" in
    Electric) [ -z "$mk" ] && args+=(--label "any EV") ;;
    *Plug-in*) args+=(--label "${mk:-any} ${md:-$fuel}") ;;
  esac
  timeout 400 node "$TOOLS/scrape-autotrader.js" "${args[@]}" >>"$RAW" 2>>"$LOG.scrape" \
    || echo "scrape failed for '${mk:-any} ${md:-$fuel}' (continuing)"
done
echo "scraped $(grep -c . "$RAW" || true) listing rows"

# Dedupe + score. Score drives whether Rob gets interrupted.
python3 - "$RAW" "$SEEN" "$BUDGET" >"$NEW" <<'PY'
import json, sys
raw, seenf, budget = sys.argv[1], sys.argv[2], int(sys.argv[3])
seen = set(open(seenf).read().split())
batch, out = set(), []
for line in open(raw):
    line = line.strip()
    if not line: continue
    try: j = json.loads(line)
    except ValueError: continue
    jid = j.get('id')
    if not jid or jid in seen or jid in batch: continue
    batch.add(jid)

    # Long Range only (Rob, 18 Sep 2026). Tesla listings carry the trim in the
    # spec or title text; anything that doesn't say Long Range is dropped here,
    # after being marked seen, so it never resurfaces. This also bins the
    # SR+/LFP wildcard: Rob has decided.
    if 'long range' not in f"{j.get('spec') or ''} {j.get('title') or ''}".lower():
        continue

    price = j.get('price') or 0
    miles = j.get('mileage') or 0
    dist  = j.get('distance')
    s, why = 5, []
    if j.get('writeoff'):
        s -= 5; why.append(j['writeoff'])
    if price <= budget: s += 1
    if price <= budget - 1500: s += 1; why.append('room in budget')
    if j.get('rating') in ('Great price', 'Good price', 'Lower price'):
        s += 2; why.append(j['rating'].lower())
    elif j.get('rating') == 'Higher price':
        s -= 1
    # Rob does ~20k miles/year and the car has to last the 4-year loan, so it
    # finishes ~80k up on where it starts. Starting mileage is headroom, not
    # just condition: a 40k car ends at 120k, a 90k car ends at 170k.
    if miles and miles < 40000: s += 2; why.append(f"{miles//1000}k miles, ends ~{(miles+80000)//1000}k")
    elif miles and miles < 60000: s += 1; why.append(f"{miles//1000}k miles")
    elif miles and miles > 70000: s -= 2; why.append(f"{miles//1000}k now = ~{(miles+80000)//1000}k by loan end")
    if dist is not None and dist <= 60: s += 1; why.append(f"{dist} miles away")
    if (j.get('make') or '') == 'Tesla': s += 2
    if 'Long Range' in (j.get('spec') or ''): s += 1; why.append('long range')
    import re as _re
    kwh = _re.search(r'([\d.]+)\s*kWh', j.get('spec') or '')
    k = float(kwh.group(1)) if kwh else None
    phev = 'Plug-in' in (j.get('fuel') or '')
    j['phev'] = phev
    if phev:
        # A PHEV's battery is small by design, so the EV yardstick below would
        # bin every one of them. What matters instead is whether the electric
        # range is big enough that the home charger actually does the local
        # driving: ~12kWh and up is 30+ real miles, under 8kWh is barely worth
        # plugging in.
        if k is not None:
            if k >= 12: s += 1; why.append(f'{k:g}kWh usable EV range')
            elif k < 8: s -= 2; why.append(f'only {k:g}kWh, ~20 EV miles')
        # Most PHEVs in this budget score well (they're cheap and dealers rate
        # them a "good price"), so score alone would ping constantly. To earn
        # an interruption a PHEV also has to be worth the home charger:
        # 12kWh+ of battery and 2020 or newer. Everything else still lands in
        # the digest for the evening brief.
        j['ping_ok'] = k is not None and k >= 12 and (j.get('year') or 0) >= 2020
    else:
        j['ping_ok'] = True
    if not phev:
        # Range floor (Rob, 14 Sep): home to Torquay and back on one charge,
        # ~150 miles round trip, in winter, on a degraded pack. Under ~45kWh
        # is a second car; 45-55kWh (MG4 SE, e-2008) is tight in January;
        # 58kWh+ does it without thinking.
        if k is not None:
            if k < 45: s -= 3; why.append(f'only {k:g}kWh')
            elif k < 55: s -= 1; why.append(f'{k:g}kWh, tight for the Torquay run in winter')
            elif k >= 58: s += 1; why.append(f'{k:g}kWh')
        # Tesla listings rarely quote kWh; the trim string carries the same
        # information. Timmy was a Standard Range and Rob found it short.
        # 16 Sep: Rob says Timmy was barely doing 100 real miles by the end,
        # so plan on ~80% pack capacity at this age. An SR+ at 80% is ~140
        # real summer miles and fails the Torquay run outright; penalty raised.
        if 'Standard Range' in (j.get('spec') or ''):
            s -= 2; why.append('SR at ~80% pack fails the Torquay test')

    j['score'] = max(0, min(10, s))
    j['why'] = ', '.join(why)
    out.append(j)
for j in sorted(out, key=lambda x: -x['score']): print(json.dumps(j))
with open(seenf, 'a') as f:
    for jid in batch: f.write(jid + '\n')
PY

COUNT="$(grep -c . "$NEW" || true)"
echo "$COUNT new listings"
[ "$COUNT" -eq 0 ] && { echo "nothing new"; exit 0; }

cat "$NEW" >> "$BEST"
TODAY="$(date +%F)"
python3 - "$NEW" "$TODAY" >>"$DIGEST" <<'PY'
import json, sys
for line in open(sys.argv[1]):
    j = json.loads(line)
    print(f"{sys.argv[2]} {j['id']} {j['score']} {j.get('year','?')} {j.get('title','?')} "
          f"{j.get('spec') or ''} | {(j.get('mileage') or 0):,} mi | £{(j.get('price') or 0):,} | "
          f"{j.get('location') or '?'} | {j.get('why','')} | {j['url']}")
PY

# Strong new finds only. Good used EVs sell in days, so this one is worth a ping.
MSG="$(python3 - "$NEW" "$PING_SCORE" "$PHEV_PING_SCORE" <<'PY'
import json, sys
ev_bar, phev_bar = int(sys.argv[2]), int(sys.argv[3])
hits = [json.loads(l) for l in open(sys.argv[1])]
hits = [h for h in hits
        if h['score'] >= (phev_bar if h.get('phev') else ev_bar)
        and h.get('ping_ok') and not h.get('writeoff')][:5]
for h in hits:
    loc = h.get('location') or '?'
    if h.get('distance') is not None: loc += f" ({h['distance']} mi)"
    tag = ' [PHEV]' if h.get('phev') else ''
    print(f"• {h.get('year','?')} {h.get('title','')} {h.get('spec') or ''}".rstrip() + tag)
    print(f"  £{(h.get('price') or 0):,} | {(h.get('mileage') or 0):,} miles | {loc}"
          + (f" | {h['rating']}" if h.get('rating') else ""))
    print(f"  {h['url']}")
PY
)"

if [ -n "$MSG" ] && [ "$SEED" != "1" ]; then
  if [ "$DRYRUN" = "1" ]; then
    echo "DRYRUN would ping:"; echo "$MSG"
  else
    set -a; source "$TCONF"; set +a
    curl -sS --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
      --data-urlencode "text=🚗 New in the car hunt:
${MSG}" >/dev/null || echo "telegram send failed"
    echo "pinged Rob"
  fi
else
  echo "no ping (seed mode or nothing strong)"
fi
echo "----- done -----"
