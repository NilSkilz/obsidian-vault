#!/usr/bin/env python3
"""MG4 true-cost ledger (Rob's ask, 17 Oct 2026: "an estimate of total cost of
charging ... a rly detailed breakdown so I can see the true costs", plus what
the same miles would cost in petrol and diesel at 46 mpg).

Cron every 15 min on CT 110. Pulls:
  - Home: HA long-term hourly stats of the Shelly ch2 clamp (kWh at the wall,
    so charging losses are included) and sensor.ev_charging_cost (GBP at the
    real Octopus Go rate at the time). Hours before the cost sensor existed
    (9 Oct) are costed at the day rate and flagged as estimates.
  - Away sessions: HA history of the car's charging status / SoC / location.
    Inside zone.work = free. Anywhere else (not home) = public. Sessions are
    persisted in the ledger because the recorder purges after ~10 days.
  - Public payments: Tide finances (Starling + Monzo, synced nightly 05:20),
    matched to public sessions by time. Payments from before the car was in HA
    (9-13 Oct) have no session, so their kWh is estimated from the p/kWh seen
    at matched sessions. Sessions with no payment yet are estimated the same
    way and flagged "awaiting payment".
  - Miles: purchase odometer (listing, 34,839 mi) to the car's live odometer.
  - Fuel: DESNZ weekly UK average pump prices (~/tools/ev/fuel_prices.py).

Pushes sensor.ev_true_cost (+ per-mile and savings sensors) to HA with the
report pre-rendered as markdown attributes for the EV Charging dashboard.
Kill switch: touch ~/.local/state/ev-cost/off.
"""
import asyncio, json, math, os, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import websockets

HOME = os.path.expanduser("~")
STATE = f"{HOME}/.local/state/ev-cost"
LEDGER = f"{STATE}/ledger.json"
os.makedirs(STATE, exist_ok=True)
LON = ZoneInfo("Europe/London")

# --- Facts (see Context/Vehicles.md, Context/Home Assistant.md) ---
PURCHASE = datetime(2026, 10, 9, 15, 0, tzinfo=LON)  # paid Carbase 15:07
PURCHASE_ODO_MI = 34839        # listing odometer, YG73 NUO
PURCHASE_SOC = 59.0            # dash at the 9 Oct battery check (145 mi at 59%)
CAR_DATA_FROM = datetime(2026, 10, 13, 9, 0, tzinfo=LON)  # iSMART bound, in HA
GO_FROM = datetime(2026, 10, 10, 0, 0, tzinfo=LON)  # Octopus Go 12M Fixed start
DC_EFF = 0.93                  # charger meter -> battery on a rapid (cable + cooling losses)
USABLE_KWH = 61.7              # MG4 Long Range 64 kWh gross / 61.7 usable
MPG = 46.0
LITRES_PER_GALLON = 4.54609
HOME_XY = (50.73311, -4.61875)
WORK_XY = (51.9196, -2.0962)
E = "mg_mg4_electric"
SHELLY = "sensor.shellyem_34945470ed50_channel_2_energy"
COST = "sensor.ev_charging_cost"
CHARGE_WORDS = [
    "charge", "gridserve", "instavolt", "ionity", "osprey", "bp pulse", "bppulse",
    "pod point", "podpoint", "shell recharge", "shell ev", "tesla", "fastned",
    "mfg ev", "evyve", "believ", "char.gy", "chargy", "connected kerbside",
    "swarco", "zapmap", "zap-pay", "zappay", "geniepoint", "genie point",
    "ubitricity", "ev power", "electric highway", "ecotricity", "be.ev",
    "joosup", "pogo", "blink", "clenergy", "evolt", "allego", "electroverse",
    "octopus electroverse", "plug-n-go", "plugngo", "ev charging", "evcharg",
]
NOT_CHARGING = ["starling", "monzo", "bank", "overdraft", "interest", "surcharge"]


def env(path):
    out = {}
    for line in open(path):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.strip().split("=", 1)
            out[k.replace("export ", "")] = v.strip().strip('"').strip("'")
    return out


HA = env(f"{HOME}/.config/jarvis/ha.env")
TIDE = env(f"{HOME}/.config/jarvis/health.env")


def dist_m(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(h))


def ts(x):
    return datetime.fromtimestamp(x, LON)


def fnum(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- HA access
async def _ws(msgs):
    url = HA["HA_URL"].replace("http", "ws") + "/api/websocket"
    async with websockets.connect(url, max_size=None) as w:
        await w.recv()
        await w.send(json.dumps({"type": "auth", "access_token": HA["HA_TOKEN"]}))
        await w.recv()
        out = []
        for i, m in enumerate(msgs, 1):
            await w.send(json.dumps({**m, "id": i}))
            while True:
                r = json.loads(await w.recv())
                if r.get("id") == i and r.get("type") == "result":
                    if not r.get("success"):
                        raise RuntimeError(f"HA ws {m['type']}: {r.get('error')}")
                    out.append(r["result"])
                    break
        return out


def ha_ws(*msgs):
    return asyncio.run(_ws(list(msgs)))


def ha_rest(path, data=None):
    req = urllib.request.Request(
        HA["HA_URL"] + path, data=json.dumps(data).encode() if data is not None else None,
        headers={"Authorization": f"Bearer {HA['HA_TOKEN']}", "Content-Type": "application/json"},
        method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"null")


# ---------------------------------------------------------------- ledger
def load_ledger():
    try:
        return json.load(open(LEDGER))
    except (OSError, ValueError):
        return {"sessions": {}, "payments": {}, "fuel": None, "efficiency": None}


def save_ledger(led):
    tmp = LEDGER + ".tmp"
    json.dump(led, open(tmp, "w"), indent=1, sort_keys=True)
    os.replace(tmp, LEDGER)


# ---------------------------------------------------------------- home
def home_hours(stats, night_p, day_p):
    """Per-hour home charging: kWh at the wall, GBP, night kWh."""
    cost = {r["start"]: r.get("change") for r in stats.get(COST, [])}
    first_cost = min(cost) if cost else None
    out = []
    for r in stats.get(SHELLY, []):
        k = r.get("change") or 0.0
        if k <= 0.0005:
            continue
        start = ts(r["start"] / 1000)
        if start < PURCHASE.replace(minute=0):
            continue
        c = cost.get(r["start"])
        est = False
        if c is None:
            if first_cost is not None and r["start"] >= first_cost:
                c = 0.0
            else:
                est = True
                c = k * day_p / 100  # before the cost sensor existed (9 Oct)
        elif not (night_p * 0.9 <= c * 100 / k <= day_p * 1.1):
            # backfill seam (11 Oct 14:38): split by the clock instead
            frac = 1.0 if 1 <= start.hour <= 4 else 0.5 if start.hour in (0, 5) else 0.0
            c = (k * frac * night_p + k * (1 - frac) * day_p) / 100
        # night share from the blended rate actually charged that hour
        if est:
            night = 0.0
        else:
            night = (day_p / 100 * k - c) / ((day_p - night_p) / 100)
            night = max(0.0, min(k, night))
        out.append({"t": start, "kwh": k, "gbp": max(c, 0.0), "night": night, "est": est})
    return out


def is_night(t, night_from=(0, 30), night_to=(5, 30)):
    hm = (t.hour, t.minute)
    return night_from <= hm < night_to


def home_charges(s5, night_p, day_p):
    """Each home plug-in from the clamp's 5-minute stats: buckets drawing
    >~1 kW, merged across gaps of up to 20 min (the Pod Point's 7-11 min
    cut-outs stay one charge). Cost from the cost sensor's 5-min stats where
    it existed, else kWh x the Go rate for that time of day."""
    cost = {r["start"]: r.get("change") for r in s5.get(COST, [])}
    charges, cur = [], None
    for r in s5.get(SHELLY, []):
        k = r.get("change") or 0.0
        if k < 0.08:
            continue
        t = ts(r["start"] / 1000)
        if t < PURCHASE:
            continue
        c = cost.get(r["start"])
        est = False
        # no cost stat yet, or the 11 Oct backfill seam (+£27 in one bucket): price it by the clock
        if c is None or not (night_p * 0.9 <= c * 100 / k <= day_p * 1.1):
            est = t < GO_FROM
            c = k * (day_p if est or not is_night(t) else night_p) / 100
        night = k if (not est and is_night(t)) else 0.0
        if cur and t - cur["end"] <= timedelta(minutes=20):
            cur["end"] = t + timedelta(minutes=5)
            cur["kwh"] += k
            cur["gbp"] += c
            cur["night"] += night
            cur["est"] = cur["est"] or est
        else:
            cur = {"start": t, "end": t + timedelta(minutes=5), "kwh": k, "gbp": c, "night": night, "est": est}
            charges.append(cur)
    return [c for c in charges if c["kwh"] >= 0.5]


# ---------------------------------------------------------------- away sessions
def detect_sessions(hist):
    st = hist.get(f"sensor.{E}_charging_status", [])
    soc = [(x["lu"], fnum(x["s"])) for x in hist.get(f"sensor.{E}_state_of_charge", []) if fnum(x["s"]) is not None]
    trk = [(x["lu"], x.get("a", {})) for x in hist.get(f"device_tracker.{E}_gps_location", [])]
    pw = [(x["lu"], fnum(x["s"])) for x in hist.get(f"sensor.{E}_charging_power", []) if fnum(x["s"]) is not None]
    runs, cur = [], None
    for s in st:
        on = s["s"] in ("Charging", "Charging (AC)", "Charging (DC)")
        if on and cur is None:
            cur = {"a": s["lu"], "b": None, "dc": False}
        if on:
            cur["dc"] = cur["dc"] or "DC" in s["s"]
        if not on and cur is not None and s["s"] not in ("unavailable", "unknown"):
            cur["b"] = s["lu"]
            runs.append(cur)
            cur = None
    if cur:
        cur["b"] = st[-1]["lu"] if st else cur["a"]
        cur["open"] = True
        runs.append(cur)

    def where(t0, t1):
        pts = [a for (t, a) in trk if t0 <= t <= t1 and "latitude" in a]
        if not pts:
            pts = [a for (t, a) in trk if t <= t0 and "latitude" in a][-1:]
        if not pts:
            return None
        a = pts[len(pts) // 2]
        return (a["latitude"], a["longitude"])

    sessions = []
    for r in runs:
        xy = where(r["a"], r["b"])
        if xy is None:
            continue
        kind = "home" if dist_m(xy, HOME_XY) < 200 else "work" if dist_m(xy, WORK_XY) < 400 else "public"
        # merge with the previous run if same place and the gap is short (poll blips)
        if sessions and sessions[-1]["kind"] == kind and r["a"] - sessions[-1]["b"] < 45 * 60 \
                and dist_m(xy, tuple(sessions[-1]["xy"])) < 300:
            sessions[-1]["b"] = r["b"]
            sessions[-1]["dc"] = sessions[-1]["dc"] or r["dc"]
            sessions[-1]["open"] = r.get("open", False)
            continue
        sessions.append({"a": r["a"], "b": r["b"], "dc": r["dc"], "kind": kind, "xy": list(xy),
                         "open": r.get("open", False)})
    for s in sessions:
        # the poll that first reports "Charging" writes SoC in the same second,
        # so the true start is the reading from the poll before it
        before = [v for (t, v) in soc if s["a"] - 30 * 60 <= t < s["a"] - 5]
        during = [v for (t, v) in soc if s["a"] <= t <= s["b"] + 15 * 60]
        start = min(before[-1:] + during[:1]) if (before or during) else None
        end = max(during) if during else None
        s["soc0"], s["soc1"] = start, end
        s["pmax"] = max([v for (t, v) in pw if s["a"] <= t <= s["b"]] or [0.0])
        s["kwh"] = max(0.0, (end - start)) / 100 * USABLE_KWH if start is not None and end is not None else 0.0
    return sessions


# ---------------------------------------------------------------- payments
def fetch_payments():
    hdr = {"X-Jarvis-Key": TIDE["JARVIS_API_KEY"]}
    seen = {}
    for w in CHARGE_WORDS:
        url = f"{TIDE['TIDE_API_BASE']}/api/finance/transactions?limit=200&q={urllib.parse.quote(w)}"
        with urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=30) as r:
            for t in json.load(r)["transactions"]:
                if t["ts"] < PURCHASE.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M"):
                    continue
                who = f"{t.get('counterparty') or ''} {t.get('description') or ''}".lower()
                if any(n in who for n in NOT_CHARGING):
                    continue
                if t.get("category") == "internal":
                    continue
                seen[str(t["id"])] = {"ts": t["ts"], "pence": -int(t["amountMinor"]),
                                      "who": t.get("counterparty") or t.get("description"),
                                      "account": t.get("account")}
    return seen


def match_payments(sessions, payments):
    """Greedy nearest-in-time match of payments to public sessions."""
    pub = [s for s in sessions if s["kind"] == "public"]
    for s in pub:
        s["pay"] = []
    pairs = []
    for pid, p in payments.items():
        pt = datetime.fromisoformat(p["ts"].replace("Z", "+00:00")).timestamp()
        for i, s in enumerate(pub):
            if s["a"] - 90 * 60 <= pt <= s["b"] + 6 * 3600:
                pairs.append((abs(pt - s["a"]), pid, i))
    used = set()
    for _, pid, i in sorted(pairs):
        if pid in used:
            continue
        pub[i]["pay"].append(pid)
        used.add(pid)
    return used


# ---------------------------------------------------------------- fuel
def fuel_series(led):
    """Weekly UK average pump prices (DESNZ), kept in the ledger and in HA's
    long-term stats as external statistics jarvis:uk_petrol_price /
    jarvis:uk_diesel_price (Rob, 17 Oct 2026: track fuel prices from now on).
    Refetched every 12h; DESNZ publishes one row per week (Mondays)."""
    sys.path.insert(0, f"{HOME}/tools/ev")
    checked = led.get("fuel_checked")
    if not led.get("fuel_series") or not checked or \
            datetime.now(LON) - datetime.fromisoformat(checked) > timedelta(hours=12):
        try:
            from fuel_prices import all_uk_fuel_prices
            series = all_uk_fuel_prices()
            new = not led.get("fuel_series") or series[-1][0] != led["fuel_series"][-1][0] \
                or not led.get("fuel_in_ha")
            led["fuel_series"] = series
            led["fuel_checked"] = datetime.now(LON).isoformat()
            if new:
                push_fuel_stats(series)
                led["fuel_in_ha"] = series[-1][0]
        except Exception as e:  # keep the last good series
            print(f"fuel price fetch failed: {e}", file=sys.stderr)
    return led.get("fuel_series") or [("2026-10-12", 175.28, 200.04)]


def push_fuel_stats(series):
    msgs = []
    for sid, name, col in (("jarvis:uk_petrol_price", "UK average petrol price", 1),
                           ("jarvis:uk_diesel_price", "UK average diesel price", 2)):
        stats = []
        for row in series:
            t = datetime.fromisoformat(row[0]).replace(tzinfo=LON).astimezone(timezone.utc)
            stats.append({"start": t.isoformat(), "mean": row[col], "min": row[col], "max": row[col]})
        msgs.append({"type": "recorder/import_statistics",
                     "metadata": {"statistic_id": sid, "source": "jarvis", "name": name,
                                  "unit_of_measurement": "p/L", "has_mean": True, "has_sum": False,
                                  "mean_type": 1, "unit_class": None},
                     "stats": stats})
    ha_ws(*msgs)


def price_on(series, when):
    """(petrol, diesel, week) in force on a date: the latest weekly row on or before it."""
    d = when.strftime("%Y-%m-%d")
    row = series[0]
    for r in series:
        if r[0] <= d:
            row = r
        else:
            break
    return row[1], row[2], row[0]


def fuel_cost(miles, ppl):
    return miles / MPG * LITRES_PER_GALLON * ppl / 100


# ---------------------------------------------------------------- formatting
def gbp(x):
    return f"£{x:,.2f}" if abs(x) < 1000 else f"£{x:,.0f}"


def pp(x):
    return f"{x:.1f}p"


def day(t):
    return t.strftime("%a %-d %b")


def maplink(xy, label):
    return f"[{label}](https://www.google.com/maps?q={xy[0]:.5f},{xy[1]:.5f})"


# ---------------------------------------------------------------- main
def main():
    if os.path.exists(f"{STATE}/off"):
        return
    led = load_ledger()
    led.setdefault("home", {})
    now = datetime.now(LON)

    states = {s["entity_id"]: s for s in ha_rest("/api/states")}
    night_p = fnum(states.get("input_number.ev_night_rate", {}).get("state")) or 9.5
    day_p = fnum(states.get("input_number.ev_day_rate", {}).get("state")) or 36.17
    odo = fnum(states.get(f"sensor.{E}_mileage", {}).get("state"))
    if odo is not None and states[f"sensor.{E}_mileage"]["attributes"].get("unit_of_measurement") == "km":
        odo /= 1.609344
    odo = odo or led.get("last_odo") or PURCHASE_ODO_MI
    led["last_odo"] = odo
    soc_now = fnum(states.get(f"sensor.{E}_state_of_charge", {}).get("state")) or led.get("last_soc", PURCHASE_SOC)
    led["last_soc"] = soc_now

    start_utc = (PURCHASE - timedelta(days=1)).astimezone(timezone.utc).isoformat()
    s5_from = (now - timedelta(days=9)).astimezone(timezone.utc).isoformat()
    hist_from = max(CAR_DATA_FROM, now - timedelta(days=9)).astimezone(timezone.utc).isoformat()
    stats, s5, hist = ha_ws(
        {"type": "recorder/statistics_during_period", "start_time": start_utc, "period": "hour",
         "statistic_ids": [SHELLY, COST, f"sensor.{E}_mileage"], "types": ["change", "state"],
         "units": {"distance": "mi"}},
        {"type": "recorder/statistics_during_period", "start_time": s5_from, "period": "5minute",
         "statistic_ids": [SHELLY, COST], "types": ["change"]},
        {"type": "history/history_during_period", "start_time": hist_from,
         "entity_ids": [f"sensor.{E}_charging_status", f"sensor.{E}_state_of_charge",
                        f"device_tracker.{E}_gps_location", f"sensor.{E}_charging_power"],
         "minimal_response": False, "no_attributes": False, "significant_changes_only": False},
    )

    # --- away sessions, persisted (the recorder forgets after ~10 days)
    for s in detect_sessions(hist):
        led["sessions"][str(int(s["a"]))] = s
    sessions = sorted(led["sessions"].values(), key=lambda s: s["a"])

    # --- home plug-ins from the 5-min clamp stats, persisted the same way.
    # Recompute everything the 5-min window still covers; keep older ones.
    s5_start = min((r["start"] / 1000 for r in s5.get(SHELLY, [])), default=now.timestamp())
    led["home"] = {k: v for k, v in led["home"].items() if v["a"] < s5_start + 1800}
    for c in home_charges(s5, night_p, day_p):
        if c["start"].timestamp() < s5_start + 1800 and str(int(c["start"].timestamp())) not in led["home"]:
            continue  # might be clipped by the window edge; the stored copy wins
        led["home"][str(int(c["start"].timestamp()))] = {
            "a": c["start"].timestamp(), "b": c["end"].timestamp(), "kwh": c["kwh"], "gbp": c["gbp"],
            "night": c["night"], "est": c["est"]}
    home_list = sorted(led["home"].values(), key=lambda h: h["a"])

    # --- payments
    try:
        led["payments"].update(fetch_payments())
    except Exception as e:
        print(f"finance fetch failed: {e}", file=sys.stderr)
    payments = led["payments"]
    used = match_payments(sessions, payments)

    # --- home totals: hourly long-term stats (kept forever), cost at the rate in force
    hours = home_hours(stats, night_p, day_p)
    home_kwh = sum(h["kwh"] for h in hours)
    home_gbp = sum(h["gbp"] for h in hours)
    home_night = sum(h["night"] for h in hours)
    home_day = home_kwh - home_night
    night_gbp = home_night * night_p / 100
    day_gbp = home_gbp - night_gbp
    est_home = sum(h["gbp"] for h in hours if h["est"])
    standby = max(0.0, home_kwh - sum(h["kwh"] for h in home_list))

    # --- AC wall->battery efficiency: car-seen home charges (SoC) vs the clamp
    eff = led.get("efficiency") or 0.88
    hs = [s for s in sessions if s["kind"] == "home" and not s.get("open")]
    if hs:
        t0, t1 = hs[0]["a"] - 1800, hs[-1]["b"] + 1800
        wall = sum(h["kwh"] for h in home_list if t0 <= h["a"] <= t1)
        batt = sum(s["kwh"] for s in hs)
        if wall > 30:
            eff = max(0.75, min(0.95, batt / wall))
    led["efficiency"] = round(eff, 3)

    def plug(s):  # battery kWh -> kWh through the charger's meter
        return s["kwh"] / (DC_EFF if s["dc"] else eff)

    # --- public: matched sessions give a real p/kWh, used for the rest
    pub = [s for s in sessions if s["kind"] == "public"]
    samples = [(sum(payments[p]["pence"] for p in s["pay"]), plug(s)) for s in pub if s.get("pay") and s["kwh"] > 3]
    pub_rate = sum(p for p, _ in samples) / sum(k for _, k in samples) if samples else 80.0
    pub_rows = []
    for s in pub:
        paid = sum(payments[p]["pence"] for p in s.get("pay", []))
        who = ", ".join(sorted({payments[p]["who"] for p in s.get("pay", [])})) or "Public charger"
        stale = now.timestamp() - s["b"] > 10 * 86400
        # nothing in the bank 10 days on = a free charger (or paid some way we can't see)
        pence, status = (paid, "paid") if paid else (0.0, "no payment found") if stale else (plug(s) * pub_rate, "awaiting payment")
        pub_rows.append({"t": ts(s["a"]), "end": ts(s["b"]), "kwh": plug(s), "batt": s["kwh"], "gbp": pence / 100,
                         "who": who, "status": status, "xy": s["xy"], "dc": s["dc"],
                         "soc": (s["soc0"], s["soc1"]), "pmax": s["pmax"]})
    for pid in payments:
        if pid in used:
            continue
        p = payments[pid]
        pt = datetime.fromisoformat(p["ts"].replace("Z", "+00:00")).astimezone(LON)
        k = max(0.0, p["pence"] / pub_rate)
        pub_rows.append({"t": pt, "end": None, "kwh": k, "batt": k * DC_EFF, "gbp": p["pence"] / 100, "who": p["who"],
                         "status": "before car data" if pt < CAR_DATA_FROM else "no session seen",
                         "xy": None, "dc": True, "soc": (None, None), "pmax": None})
    pub_rows.sort(key=lambda r: r["t"])
    pub_kwh = sum(r["kwh"] for r in pub_rows)
    pub_gbp = sum(r["gbp"] for r in pub_rows)
    pub_pending = sum(r["gbp"] for r in pub_rows if r["status"] == "awaiting payment")

    # --- work (free)
    work = [s for s in sessions if s["kind"] == "work"]
    work_kwh_seen = sum(plug(s) for s in work)

    # --- miles, and an energy balance for the 9-13 Oct gap (no car data):
    # whatever the miles needed beyond home + public must have come from work.
    miles = max(0.0, odo - PURCHASE_ODO_MI)
    mi_stats = [r for r in stats.get(f"sensor.{E}_mileage", []) if r.get("state") is not None]
    for r in mi_stats:
        if r["state"] > 50000:
            r["state"] /= 1.609344  # came back in km
    odo_at_data = mi_stats[0]["state"] if mi_stats else odo
    miles_seen = max(0.0, odo - odo_at_data)
    socs = [(x["lu"], fnum(x["s"])) for x in hist.get(f"sensor.{E}_state_of_charge", []) if fnum(x["s"]) is not None]
    if led.get("soc_at_data") is None and socs and ts(socs[0][0]) < CAR_DATA_FROM + timedelta(hours=1):
        led["soc_at_data"] = socs[0][1]
    soc_at_data = led.get("soc_at_data", 33.9)
    batt_in_seen = sum(h["kwh"] for h in home_list if h["a"] >= CAR_DATA_FROM.timestamp()) * eff \
        + sum(r["batt"] for r in pub_rows if r["t"] >= CAR_DATA_FROM) + sum(s["kwh"] for s in work)
    used_seen = batt_in_seen - (soc_now - soc_at_data) / 100 * USABLE_KWH
    mi_per_kwh = max(2.0, min(5.5, miles_seen / used_seen)) if used_seen > 20 else 3.5
    led["mi_per_kwh"] = round(mi_per_kwh, 2)
    miles_gap = max(0.0, (odo_at_data or odo) - PURCHASE_ODO_MI)
    gap_known = sum(h["kwh"] for h in home_list if h["a"] < CAR_DATA_FROM.timestamp()) * eff \
        + sum(r["batt"] for r in pub_rows if r["t"] < CAR_DATA_FROM)
    gap_need = miles_gap / mi_per_kwh + (soc_at_data - PURCHASE_SOC) / 100 * USABLE_KWH
    work_gap = max(0.0, gap_need - gap_known) / eff
    work_kwh = work_kwh_seen + work_gap

    total_gbp = home_gbp + pub_gbp
    total_kwh = home_kwh + pub_kwh + work_kwh
    ppm = total_gbp * 100 / miles if miles else 0.0

    # --- fuel, week by week
    series = fuel_series(led)
    p_now, d_now, wk_now = price_on(series, now)
    petrol_ppm = p_now / MPG * LITRES_PER_GALLON
    diesel_ppm = d_now / MPG * LITRES_PER_GALLON
    days = max(1.0, (now - PURCHASE).total_seconds() / 86400)

    def odo_at(t):
        if t <= PURCHASE:
            return PURCHASE_ODO_MI
        best = odo_at_data
        for r in mi_stats:
            if ts(r["start"] / 1000) + timedelta(hours=1) <= t:
                best = r["state"]
        return best

    edges = [PURCHASE, CAR_DATA_FROM]
    wk = (CAR_DATA_FROM - timedelta(days=CAR_DATA_FROM.weekday())).replace(hour=0) + timedelta(days=7)
    while wk < now:
        edges.append(wk)
        wk += timedelta(days=7)
    edges.append(now)
    periods = []
    for a, b in zip(edges, edges[1:]):
        oa = PURCHASE_ODO_MI if a == PURCHASE else odo_at(a)
        ob = odo if b == now else odo_at(b)
        mi = max(0.0, ob - oa)
        fp, fd, _ = price_on(series, a + (b - a) / 2)
        periods.append({
            "label": f"{a:%-d}–{(b - timedelta(minutes=1)):%-d %b}" + ("*" if a == PURCHASE else ""),
            "mi": mi, "ev": sum(h["gbp"] for h in hours if a <= h["t"] < b) + sum(r["gbp"] for r in pub_rows if a <= r["t"] < b),
            "petrol": fuel_cost(mi, fp), "diesel": fuel_cost(mi, fd)})
    petrol = sum(p["petrol"] for p in periods)
    diesel = sum(p["diesel"] for p in periods)
    saved_p, saved_d = petrol - total_gbp, diesel - total_gbp

    # ---------------- render
    def per_kwh(g, k):
        return pp(g * 100 / k) if k > 0.5 else "–"

    def share(k):
        return f"{k / total_kwh * 100:.0f}%" if total_kwh else "–"

    est_bits = []
    if pub_pending:
        est_bits.append(f"{gbp(pub_pending)} of public charging not in the bank yet (estimated)")
    if est_home:
        est_bits.append(f"{gbp(est_home)} of home charging on 9 Oct (old tariff, costed at the Go day rate)")
    summary = [
        f"# ⛽ {gbp(saved_p)} saved vs petrol",
        f"Over **{miles:,.0f} miles** since you bought it on 9 Oct ({days:.0f} days): petrol would have cost {gbp(petrol)}, "
        f"charging has cost **{gbp(total_gbp)}** ({pp(ppm)} a mile). Against diesel you're {gbp(saved_d)} up.",
        "",
        "| Same miles, 46 mpg car | Fuel | Per mile | You saved |",
        "|:--|--:|--:|--:|",
        f"| ⛽ Petrol ({p_now:.1f}p/L) | {gbp(petrol)} | {pp(petrol_ppm)} | **{gbp(saved_p)}** |",
        f"| 🛢️ Diesel ({d_now:.1f}p/L) | {gbp(diesel)} | {pp(diesel_ppm)} | **{gbp(saved_d)}** |",
        f"| ⚡ MG4, actual | {gbp(total_gbp)} | {pp(ppm)} | |",
        "",
        f"**Per 1,000 miles:** EV {gbp(ppm * 10)}, petrol {gbp(petrol_ppm * 10)}, diesel {gbp(diesel_ppm * 10)}. "
        f"At your pace so far ({miles / days * 7:,.0f} mi a week) that's about **{gbp((petrol_ppm - ppm) * miles / days * 365 / 100)} a year** saved against petrol"
        + (" (early days, so a rough guess)." if days < 28 else "."),
    ]
    if est_bits:
        summary += ["", "<small>Includes " + "; ".join(est_bits) + ".</small>"]

    sources = [
        "### Where the energy came from",
        "| Source | kWh | Share | Cost | p/kWh |",
        "|:--|--:|--:|--:|--:|",
        f"| 🌙 Home, night | {home_night:.0f} | {share(home_night)} | {gbp(night_gbp)} | {per_kwh(night_gbp, home_night)} |",
        f"| ☀️ Home, day | {home_day:.0f} | {share(home_day)} | {gbp(day_gbp)} | {per_kwh(day_gbp, home_day)} |",
        f"| 🛣️ Public | {pub_kwh:.0f} | {share(pub_kwh)} | {gbp(pub_gbp)} | {per_kwh(pub_gbp, pub_kwh)} |",
        f"| 🏢 Work | {work_kwh:.0f} | {share(work_kwh)} | free | 0p |",
        f"| **Total** | **{total_kwh:.0f}** | | **{gbp(total_gbp)}** | **{per_kwh(total_gbp, total_kwh)}** |",
        "",
        f"- **Charging in the day at home cost you {gbp(home_day * (day_p - night_p) / 100)} extra.** {home_day:.0f} kWh went in at {day_p:g}p rather than {night_p:g}p.",
        f"- **Free work charging was worth {gbp(work_kwh * night_p / 100)}** at your night rate, or {gbp(work_kwh * day_p / 100)} at the day rate."
        + (f" About {work_gap:.0f} kWh of that is from 9–13 Oct, before the car was in HA, worked out from the miles." if work_gap > 1 else ""),
        f"- **Public charging averaged {per_kwh(pub_gbp, pub_kwh)}/kWh**, about {pp(pub_gbp * 100 / pub_kwh / mi_per_kwh / eff * DC_EFF) if pub_kwh else '–'} a mile, which is more than petrol ({pp(petrol_ppm)}). Fine on a long run, worth avoiding otherwise.",
        f"- **Home night charging is {pp(night_p / mi_per_kwh / eff)} a mile, day rate {pp(day_p / mi_per_kwh / eff)}.**",
        f"- **The car's doing {mi_per_kwh:.1f} mi/kWh**, and going by its battery %, about {eff * 100:.0f}% of what goes in at home reaches the battery."
        + (f" The charger's own standby use is in the home figures ({standby:.1f} kWh)." if standby >= 0.5 else ""),
    ]

    weeks = ["### By week", "| Week | Miles | EV | p/mi | Petrol | Diesel |", "|:--|--:|--:|--:|--:|--:|"]
    for p in periods[-10:]:
        weeks.append(f"| {p['label']} | {p['mi']:,.0f} | {gbp(p['ev'])} | {pp(p['ev'] * 100 / p['mi']) if p['mi'] > 1 else '–'} | "
                     f"{gbp(p['petrol'])} | {gbp(p['diesel'])} |")
    weeks.append(f"| **Total** | **{miles:,.0f}** | **{gbp(total_gbp)}** | **{pp(ppm)}** | **{gbp(petrol)}** | **{gbp(diesel)}** |")
    weeks += ["", "<small>* 9–13 Oct, before the car's data reached HA. EV = home + public. Weeks run Mon–Sun. "
              "Petrol and diesel use each week's UK average price.</small>"]

    rows = []
    for h in home_list:
        a = ts(h["a"])
        ns = h["night"] / h["kwh"] if h["kwh"] else 0
        tag = "🌙" if ns > 0.8 else "☀️" if ns < 0.2 else "🌗"
        dur = (h["b"] - h["a"]) / 3600
        rows.append((h["a"], f"| {day(a)} {a:%H:%M} | {tag} Home · {dur:.1f}h | {h['kwh']:.1f} | "
                             f"{gbp(h['gbp'])}{'*' if h['est'] else ''} | {per_kwh(h['gbp'], h['kwh'])} |"))
    for s in work:
        a = ts(s["a"])
        rows.append((s["a"], f"| {day(a)} {a:%H:%M} | 🏢 Work · {(s['b'] - s['a']) / 3600:.1f}h | {plug(s):.1f} | free | 0p |"))
    for r in pub_rows:
        lab = r["who"] + (" · DC" if r["dc"] else " · AC")
        lab = maplink(r["xy"], lab) if r["xy"] else lab
        flag = {"paid": "", "awaiting payment": " ⏳", "no payment found": " ❓", "before car data": " †", "no session seen": " †"}[r["status"]]
        est = r["status"] == "awaiting payment"
        rows.append((r["t"].timestamp(), f"| {day(r['t'])} {r['t']:%H:%M} | 🛣️ {lab}{flag} | {r['kwh']:.1f} | "
                                         f"{gbp(r['gbp'])}{'*' if est else ''} | {per_kwh(r['gbp'], r['kwh'])} |"))
    rows.sort(key=lambda x: x[0], reverse=True)
    sess_md = [f"**{len(rows)} charges since 9 Oct**, newest first.", "", "| When | Where | kWh | Cost | p/kWh |", "|:--|:--|--:|--:|--:|"]
    sess_md += [r for _, r in rows[:60]]
    if len(rows) > 60:
        sess_md.append(f"| … | {len(rows) - 60} older charges | | | |")
    sess_md += ["", "<small>kWh through the charger's meter. 🌙 night rate, ☀️ day rate, 🌗 both. "
                "⏳ not in the bank yet, so estimated at your public average. ❓ no payment turned up within 10 days, counted as free. "
                "† no car data for that charge, kWh estimated from the price. * estimated cost. "
                "Tap a public charger to see it on a map.</small>"]

    notes = [
        "### How this is worked out",
        f"- **Home:** the Shelly clamp on the charger circuit (what you actually pay for, losses included), priced at the Octopus Go rate at the time: {night_p:g}p 00:30–05:30, {day_p:g}p otherwise. Standing charge left out, because you'd pay it anyway.",
        "- **Public:** the real payments from Starling and Monzo, matched to the charge the car reported. The bank feed syncs at 05:20 each night.",
        "- **Work:** any charge inside the Cheltenham work zone. Free.",
        f"- **Miles:** odometer now ({odo:,.0f} mi) minus {PURCHASE_ODO_MI:,} at purchase (the listing figure).",
        f"- **Petrol and diesel:** UK average pump prices from the government's weekly survey (DESNZ), latest week {datetime.fromisoformat(wk_now):%-d %b}, at {MPG:g} mpg for both. Fuel only, no servicing or road tax.",
        f"- Updated {now:%a %-d %b %H:%M}, every 15 minutes.",
    ]

    md = {"summary": "\n".join(summary), "sources": "\n".join(sources), "weeks": "\n".join(weeks),
          "sessions": "\n".join(sess_md), "notes": "\n".join(notes)}

    def push(entity, state, attrs):
        ha_rest(f"/api/states/{entity}", {"state": state, "attributes": attrs})

    # md_* attributes are rendered by the dashboard's markdown cards
    push("sensor.ev_true_cost", round(total_gbp, 2), {
        "friendly_name": "EV total charging cost", "unit_of_measurement": "GBP", "device_class": "monetary",
        "icon": "mdi:cash-multiple", "miles": round(miles), "home_gbp": round(home_gbp, 2),
        "public_gbp": round(pub_gbp, 2), "work_kwh": round(work_kwh, 1), "pence_per_mile": round(ppm, 2),
        **{f"md_{k}": v for k, v in md.items()}})
    push("sensor.ev_cost_per_mile", round(ppm, 1), {"friendly_name": "EV cost per mile", "unit_of_measurement": "p/mi",
                                                    "state_class": "measurement", "icon": "mdi:road-variant"})
    push("sensor.ev_saving_vs_petrol", round(saved_p, 2), {"friendly_name": "Saved vs petrol", "unit_of_measurement": "GBP",
                                                          "device_class": "monetary", "icon": "mdi:gas-station-off"})
    push("sensor.ev_saving_vs_diesel", round(saved_d, 2), {"friendly_name": "Saved vs diesel", "unit_of_measurement": "GBP",
                                                          "device_class": "monetary", "icon": "mdi:barrel"})
    push("sensor.ev_miles_since_purchase", round(miles), {"friendly_name": "Miles since purchase", "unit_of_measurement": "mi",
                                                         "icon": "mdi:counter"})
    push("sensor.uk_petrol_price", p_now, {"friendly_name": "UK petrol (avg)", "unit_of_measurement": "p/L",
                                           "icon": "mdi:gas-station", "week": wk_now})
    push("sensor.uk_diesel_price", d_now, {"friendly_name": "UK diesel (avg)", "unit_of_measurement": "p/L",
                                           "icon": "mdi:gas-station-outline", "week": wk_now})
    save_ledger(led)
    if "-v" in sys.argv:
        for v in md.values():
            print(v, "\n")


if __name__ == "__main__":
    main()
