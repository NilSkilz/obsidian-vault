#!/usr/bin/env python3
"""Nightly household finance sync: Starling + Monzo -> Tide /api/finance/ingest.

Pulls balances, spaces and recent transactions from the bank APIs and pushes
them to the live Tide server (CT 112) with the shared Jarvis key. Transactions
upsert on (account, providerTxnId), so overlapping windows are harmless.

Usage:
  finance-sync.py            # nightly: last 8 days of txns + today's balances
  finance-sync.py --backfill # one-off: load the full-history dumps from ~/finance

Secrets: ~/.config/jarvis/starling.env, monzo.env (refresh token rotated here),
health.env (JARVIS_API_KEY + TIDE_API_BASE). Money is signed pence, out = negative.

Internal moves are ingested with category='internal' so the cash-flow chart can
exclude them. A move only counts as internal when BOTH sides are visible:
space/pot transfers always, and own-name transfers only when the opposite leg
(same amount, opposite sign, another account, within 4 days) is in the batch.
An unpaired own-name credit is money entering from an account we can't see
(Aimee's wages into joint, Aperture drawings) and counts as income; an unpaired
own-name debit leaves the tracked system and counts as spend ('transfer').
That pairing is why the Starling window matches Monzo's 89 days: re-ingesting a
transaction without its twin in the batch would flip its category.

Also posts a monthly house valuation from the Land Registry UK HPI (Cornwall),
scaled from the £199,950 Feb 2015 purchase.
"""
import json
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

CONF = Path.home() / '.config/jarvis'
FINANCE = Path.home() / 'finance'
STARLING_ACCOUNTS = [
    # (env token key, account name, kind)
    ('STARLING_TOKEN_PERSONAL', 'Starling Personal', 'current'),
    ('STARLING_TOKEN_JOINT', 'Starling Joint', 'joint'),
]
MONZO_NAMES = {  # account type -> display name
    'uk_retail': 'Monzo Personal',
    'uk_retail_joint': 'Monzo Joint (old)',
    'uk_prepaid': 'Monzo Prepaid (old)',
    'uk_business': 'Monzo Business (old)',
    'uk_rewards': 'Monzo Rewards',
}


# Exact-match set of the household's own names as banks render them (seen in the
# 2016-2026 dumps). Exact, not substring: 'Anne Stokes' and 'Ashley Jeffs' are
# real other people. A transfer to/from any of these is our own money moving.
OWN_NAMES = {
    'robert stokes', 'rob stokes', 'r stokes', 'mr robert stokes', 'robert mark stokes',
    'amy stokes', 'a stokes', 'mrs amy stokes',
    'amy stokes & robert stokes', 'robert stokes & amy stokes',
}


def is_own(name):
    return bool(name) and ' '.join(name.lower().split()) in OWN_NAMES


def parse_ts(ts):
    try:
        return datetime.fromisoformat((ts or '').replace('Z', '+00:00'))
    except ValueError:
        return None


def pair_own_transfers(txns):
    """Categorise own-name transfers: paired (both legs in the batch) ->
    'internal'; unpaired credit -> 'income'; unpaired debit -> 'transfer'.
    Greedy nearest-in-time matching on (abs amount), opposite signs, different
    accounts, <=4 days apart. Mutates txns in place and drops the _own flag."""
    own = [t for t in txns if t.pop('_own', False)]
    by_amount = {}
    for t in own:
        by_amount.setdefault(abs(t['amountMinor']), []).append(t)
    for group in by_amount.values():
        group.sort(key=lambda t: t['ts'] or '')
        for t in group:
            if t.get('_paired') or t['amountMinor'] >= 0:
                continue
            tt = parse_ts(t['ts'])
            best, best_gap = None, timedelta(days=4)
            for c in group:
                if c.get('_paired') or c['amountMinor'] <= 0:
                    continue
                if c['providerAccountId'] == t['providerAccountId'] and c['provider'] == t['provider']:
                    continue
                ct = parse_ts(c['ts'])
                gap = abs(ct - tt) if ct and tt else timedelta(days=99)
                if gap <= best_gap:
                    best, best_gap = c, gap
            if best is not None:
                t['_paired'] = best['_paired'] = True
    for t in own:
        if t.pop('_paired', False):
            t['category'] = 'internal'
        else:
            t['category'] = 'income' if t['amountMinor'] > 0 else 'transfer'


def env(name):
    out = {}
    for line in (CONF / name).read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            out[k] = v
    return out


def http(url, headers=None, data=None, form=None):
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or '{}')


def iso(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')


# ---------- Starling ----------

def starling_txn(item):
    sign = 1 if item.get('direction') == 'IN' else -1
    pot = item.get('counterPartyType') in ('CATEGORY', 'SAVINGS_GOAL')
    amount = sign * item['amount']['minorUnits']
    cp = item.get('counterPartyName')
    ref = (item.get('reference') or '').strip()
    cat = 'internal' if pot else (item.get('spendingCategory') or '').lower() or None
    # Fuel normalisation. The Morrisons Bude petrol station terminal comes
    # through as ref 'MORR BUDE' under the plain 'Morrisons' counterparty and
    # Starling tags it GROCERIES; >=£10 there is a tank, not a meal deal
    # (the store itself is 'MORRISONS BUDE - 325' / 'WM MORRISONS STORE').
    if not pot and 'petrol' in (cp or '').lower():
        cat = 'fuel'
    elif not pot and ref == 'MORR BUDE' and amount <= -1000:
        cat = 'fuel'
        cp = 'Morrisons Petrol'
    elif not pot and ref.startswith('TESCO PAY AT PUMP'):
        cat = 'fuel'
        cp = 'Tesco Petrol'
    return {
        'providerTxnId': item['feedItemUid'],
        'ts': item.get('transactionTime') or item.get('settlementTime'),
        'amountMinor': amount,
        'description': item.get('reference') or item.get('counterPartyName'),
        'counterparty': cp,
        'source': item.get('source'),
        'category': cat,
        '_own': not pot and is_own(item.get('counterPartyName')),
    }


def pull_starling(days=89):
    accounts, txns, balances = [], [], []
    tokens = env('starling.env')
    for key, name, kind in STARLING_ACCOUNTS:
        hdr = {'Authorization': f'Bearer {tokens[key]}'}
        acct = http('https://api.starlingbank.com/api/v2/accounts', hdr)['accounts'][0]
        uid = acct['accountUid']
        accounts.append({'provider': 'starling', 'providerId': uid, 'name': name, 'kind': kind,
                         'closed': False, 'sortOrder': 0 if kind == 'current' else 1})
        bal = http(f'https://api.starlingbank.com/api/v2/accounts/{uid}/balance', hdr)
        balances.append({'provider': 'starling', 'providerAccountId': uid,
                         'balanceMinor': bal['effectiveBalance']['minorUnits']})
        lo = iso(datetime.now(timezone.utc) - timedelta(days=days))
        hi = iso(datetime.now(timezone.utc) + timedelta(days=1))
        feed = http(f'https://api.starlingbank.com/api/v2/feed/account/{uid}/settled-transactions-between'
                    f'?minTransactionTimestamp={lo}&maxTransactionTimestamp={hi}', hdr)
        for item in feed.get('feedItems', []):
            txns.append({'provider': 'starling', 'providerAccountId': uid, **starling_txn(item)})
        # Spaces: one pseudo-account per savings goal, balance only.
        goals = http(f'https://api.starlingbank.com/api/v2/account/{uid}/savings-goals', hdr)
        for g in goals.get('savingsGoalList', []):
            accounts.append({'provider': 'starling', 'providerId': g['savingsGoalUid'],
                             'name': f"{g['name']} (space)", 'kind': 'space', 'closed': False, 'sortOrder': 10})
            balances.append({'provider': 'starling', 'providerAccountId': g['savingsGoalUid'],
                             'balanceMinor': g['totalSaved']['minorUnits']})
    return accounts, txns, balances


# ---------- Monzo ----------

def monzo_refresh():
    m = env('monzo.env')
    tok = http('https://api.monzo.com/oauth2/token', form={
        'grant_type': 'refresh_token', 'client_id': m['MONZO_CLIENT_ID'],
        'client_secret': m['MONZO_CLIENT_SECRET'], 'refresh_token': m['MONZO_REFRESH_TOKEN'],
    })
    m['MONZO_ACCESS_TOKEN'] = tok['access_token']
    m['MONZO_REFRESH_TOKEN'] = tok['refresh_token']
    m['MONZO_TOKEN_OBTAINED'] = datetime.now(timezone.utc).isoformat()
    path = CONF / 'monzo.env'
    path.write_text(''.join(f'{k}={v}\n' for k, v in m.items()))
    path.chmod(0o600)
    return m


def monzo_txn(t):
    merchant = t.get('merchant')
    if isinstance(merchant, dict):
        merchant = merchant.get('name')
    counterparty = merchant or (t.get('counterparty') or {}).get('name') or None
    pot = (t.get('scheme') or '').endswith('_pot')
    return {
        'providerTxnId': t['id'],
        'ts': t['created'],
        'amountMinor': t['amount'],
        'description': t.get('description'),
        'counterparty': counterparty,
        'source': t.get('scheme'),
        'category': 'internal' if pot else t.get('category'),
        '_own': not pot and is_own(counterparty),
    }


def pull_monzo(days=89):
    m = monzo_refresh()
    hdr = {'Authorization': f"Bearer {m['MONZO_ACCESS_TOKEN']}"}
    accounts, txns, balances = [], [], []
    for a in http('https://api.monzo.com/accounts', hdr)['accounts']:
        name = MONZO_NAMES.get(a['type'], f"Monzo {a['type']}")
        accounts.append({'provider': 'monzo', 'providerId': a['id'], 'name': name,
                         'kind': 'joint' if a['type'] == 'uk_retail_joint' else 'current',
                         'closed': bool(a.get('closed')), 'sortOrder': 2})
        if a.get('closed'):
            continue
        bal = http(f"https://api.monzo.com/balance?account_id={a['id']}", hdr)
        balances.append({'provider': 'monzo', 'providerAccountId': a['id'], 'balanceMinor': bal['balance']})
        since = iso(datetime.now(timezone.utc) - timedelta(days=days))
        page = http(f"https://api.monzo.com/transactions?account_id={a['id']}&since={since}&limit=200", hdr)
        for t in page.get('transactions', []):
            if t.get('decline_reason'):
                continue
            txns.append({'provider': 'monzo', 'providerAccountId': a['id'], **monzo_txn(t)})
    return accounts, txns, balances


# ---------- backfill from the on-disk full-history dumps ----------

def backfill():
    accounts, txns = [], []
    star_uids = {'personal': '136ff947-5ce6-49c8-9727-511b96904c1e',
                 'joint': '27089ba8-0ed8-448b-8920-52f9db6bd470'}
    for label, uid in star_uids.items():
        dump = FINANCE / 'starling' / f'{label}-full.json'
        if dump.exists():
            for item in json.loads(dump.read_text()):
                txns.append({'provider': 'starling', 'providerAccountId': uid, **starling_txn(item)})
    # Monzo dumps are one file per account; account metadata comes from the API.
    m = monzo_refresh()
    hdr = {'Authorization': f"Bearer {m['MONZO_ACCESS_TOKEN']}"}
    for a in http('https://api.monzo.com/accounts', hdr)['accounts']:
        name = MONZO_NAMES.get(a['type'], f"Monzo {a['type']}")
        accounts.append({'provider': 'monzo', 'providerId': a['id'], 'name': name,
                         'kind': 'joint' if a['type'] == 'uk_retail_joint' else 'current',
                         'closed': bool(a.get('closed')), 'sortOrder': 2})
        dump = FINANCE / 'monzo' / f"txns-{a['id']}.json"
        if dump.exists():
            for t in json.loads(dump.read_text()):
                if t.get('decline_reason'):
                    continue
                txns.append({'provider': 'monzo', 'providerAccountId': a['id'], **monzo_txn(t)})
    return accounts, txns, []


# ---------- house value from the Land Registry UK HPI ----------

HOUSE_PURCHASE_MINOR = 19995000   # £199,950 on 2 Feb 2015
HPI_BASE_MONTH = '2015-02'
HPI_REGION = 'cornwall'


def hpi_index(month):
    d = http(f'https://landregistry.data.gov.uk/data/ukhpi/region/{HPI_REGION}/month/{month}.json')
    return d['result']['primaryTopic'].get('housePriceIndex')


def update_house_value():
    """Scale the purchase price by Cornwall's HPI. The baseline is fetched live
    too (the index gets revised); publication lags ~2 months, so walk back from
    last month to the newest month that exists. Idempotent: the value row is
    keyed on the HPI month."""
    base = hpi_index(HPI_BASE_MONTH)
    if not base:
        return None
    now_dt = datetime.now(timezone.utc)
    for back in range(1, 8):
        y, m = now_dt.year, now_dt.month - back
        while m < 1:
            m += 12
            y -= 1
        month = f'{y:04d}-{m:02d}'
        try:
            idx = hpi_index(month)
        except Exception:
            idx = None
        if not idx:
            continue
        value = round(HOUSE_PURCHASE_MINOR * idx / base)
        conf = env('health.env')
        base_url = conf.get('TIDE_API_BASE', 'http://192.168.1.16:3001')
        hdr = {'X-Jarvis-Key': conf['JARVIS_API_KEY'], 'Content-Type': 'application/json'}
        http(f'{base_url}/api/finance/asset-value', hdr, data=json.dumps({
            'key': 'house', 'valueMinor': value, 'date': f'{month}-01', 'source': 'hpi',
            'note': f'UKHPI Cornwall {month}: index {idx} vs {base} at the Feb 2015 purchase',
        }).encode())
        return {'month': month, 'index': idx, 'valueMinor': value}
    return None


# ---------- push ----------

def push(accounts, txns, balances):
    conf = env('health.env')
    base = conf.get('TIDE_API_BASE', 'http://192.168.1.16:3001')
    hdr = {'X-Jarvis-Key': conf['JARVIS_API_KEY'], 'Content-Type': 'application/json'}
    totals = {'accounts': 0, 'transactions': 0, 'balances': 0, 'skipped': 0}
    # accounts + balances first, then transactions in chunks
    res = http(f'{base}/api/finance/ingest', hdr,
               data=json.dumps({'accounts': accounts, 'balances': balances}).encode())
    for k in totals:
        totals[k] += res.get(k, 0)
    for i in range(0, len(txns), 2000):
        res = http(f'{base}/api/finance/ingest', hdr,
                   data=json.dumps({'transactions': txns[i:i + 2000]}).encode())
        for k in totals:
            totals[k] += res.get(k, 0)
    return totals


def main():
    if '--backfill' in sys.argv:
        accounts, txns, balances = backfill()
        # the nightly pull adds live balances/spaces; run it too for a full seed
        a2, t2, b2 = pull_starling()
        a3, t3, b3 = pull_monzo()
        accounts += a2 + a3
        txns += t2 + t3
        balances += b2 + b3
    else:
        a2, t2, b2 = pull_starling()
        a3, t3, b3 = pull_monzo()
        accounts, txns, balances = a2 + a3, t2 + t3, b2 + b3
    # Dedupe (backfill dumps overlap the live pull; keep the live copy) so the
    # transfer pairing sees each leg exactly once.
    seen = {}
    for t in txns:
        seen[(t['provider'], t['providerAccountId'], t['providerTxnId'])] = t
    txns = list(seen.values())
    pair_own_transfers(txns)
    totals = push(accounts, txns, balances)
    try:
        hpi = update_house_value()
    except Exception as e:
        hpi = f'failed: {e}'
    print(f"{datetime.now().isoformat(timespec='seconds')} finance-sync: {totals} house-hpi: {hpi}")


if __name__ == '__main__':
    main()
