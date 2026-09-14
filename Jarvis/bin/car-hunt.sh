#!/usr/bin/env bash
# Car Hunt: watch for a second-hand EV inside the household budget
# (Projects/Car Hunt.md). Rob's brief, 14 Sep 2026: ~£2k cash deposit plus a
# ~4 year loan at ~£300/month, so about £14.5k all in. Tesla Model 3 preferred,
# strong alternatives watched too. Within 100 miles of home (Crackington Haven).
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
BUDGET="${BUDGET:-14700}"         # £2k deposit + ~£12.7k borrowed (Tesco 6.4% APR, 48mo)
PING_SCORE="${PING_SCORE:-8}"

# make | model | max price | max mileage   (empty make/model = any EV)
WATCHES=(
  "Tesla|Model 3|15500|110000"
  "Hyundai|Kona Electric|15000|90000"
  "Kia|e-Niro|15000|90000"
  "Polestar|2|15000|90000"
  "Volkswagen|ID.3|14500|90000"
  "MG|MG4|14500|70000"
  "||14500|60000"
)

mkdir -p "$STATE"; touch "$SEEN"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) car-hunt start (seed=$SEED dryrun=$DRYRUN) -----"

RAW="$(mktemp)"; NEW="$(mktemp)"
trap 'rm -f "$RAW" "$NEW"' EXIT

for w in "${WATCHES[@]}"; do
  IFS='|' read -r mk md pmax mmax <<<"$w"
  args=(--postcode "$POSTCODE" --radius "$RADIUS" --price-to "$pmax" --pages 2 --fuel Electric)
  [ -n "$mk" ] && args+=(--make "$mk")
  [ -n "$md" ] && args+=(--model "$md")
  [ -n "$mmax" ] && args+=(--max-mileage "$mmax")
  [ -z "$mk" ] && args+=(--label "any EV")
  timeout 300 node "$TOOLS/scrape-autotrader.js" "${args[@]}" >>"$RAW" 2>>"$LOG.scrape" \
    || echo "scrape failed for '${mk:-any} ${md:-EV}' (continuing)"
done
echo "scraped $(grep -c . "$RAW" || echo 0) listing rows"

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
    if miles and miles < 60000: s += 1; why.append(f"{miles//1000}k miles")
    elif miles and miles > 90000: s -= 2; why.append(f"{miles//1000}k miles")
    if dist is not None and dist <= 60: s += 1; why.append(f"{dist} miles away")
    if (j.get('make') or '') == 'Tesla': s += 2
    if 'Long Range' in (j.get('spec') or ''): s += 1; why.append('long range')
    # Battery size matters more than usual out here: Crackington to Cheltenham
    # is 120 miles each way, so anything under ~45kWh is a second car at best.
    import re as _re
    kwh = _re.search(r'([\d.]+)\s*kWh', j.get('spec') or '')
    if kwh:
        k = float(kwh.group(1))
        if k < 45: s -= 3; why.append(f'only {k:g}kWh')
        elif k >= 60: s += 1; why.append(f'{k:g}kWh')

    j['score'] = max(0, min(10, s))
    j['why'] = ', '.join(why)
    out.append(j)
for j in sorted(out, key=lambda x: -x['score']): print(json.dumps(j))
with open(seenf, 'a') as f:
    for jid in batch: f.write(jid + '\n')
PY

COUNT="$(grep -c . "$NEW" || echo 0)"
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
MSG="$(python3 - "$NEW" "$PING_SCORE" <<'PY'
import json, sys
hits = [json.loads(l) for l in open(sys.argv[1])]
hits = [h for h in hits if h['score'] >= int(sys.argv[2]) and not h.get('writeoff')][:5]
for h in hits:
    loc = h.get('location') or '?'
    if h.get('distance') is not None: loc += f" ({h['distance']} mi)"
    print(f"• {h.get('year','?')} {h.get('title','')} {h.get('spec') or ''}".rstrip())
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
