#!/usr/bin/env python3
"""MG4 battery health, real-world efficiency and range model (Rob's ask, 25 Oct 2026).

"Estimate battery health, real miles per kWh, how outside temp affects it, a
realistic expected range, does the A30 eat battery, and get to pinpoint journey
estimates." Cron hourly. Steps:

1. Archive: HA's recorder purges after ~10 days, so every run copies the new car
   history (SoC, odometer, outside temp, GPS + elevation, charging) into
   ~/.local/state/ev-health/ev.db (sqlite). Everything below runs off that.
2. Battery capacity: the mg_saic integration integrates battery-side V x I over
   every charge (`last_charge_energy` attrs energy_measured_kWh + soc_added_pct).
   Clean sessions (>=15% added, <5% of the energy gap-filled) give kWh per 1% of
   SoC, so capacity = sum(kWh) / sum(%) x 100. Health = capacity / 61.7 kWh
   (MG4 Long Range usable when new). (The integration's energy_added_kWh is NOT
   a measurement: it's a fixed 0.724 x SoC%, ignore it.)
3. Drives: powered-on windows cut into ~4 mile chunks between 5-min polls:
   miles (odo), kWh (SoC drop x capacity), speed, outside temp, net climb.
   Each poll-to-poll leg is routed through OSRM to tag which road it was on
   (A30 share), cached so each leg is only asked once.
4. Model: kWh = miles x (a + b x mph^2/1000) + hours x (p + q x max(0, 18 - C))
   + climb (fixed physics: 5.6 Wh/m up, 3 Wh/m back on the way down), ridge-
   fitted towards physics priors so a thin dataset can't produce nonsense.
   Saved to model.json; ev-trip.py uses it for journey estimates.
5. Pushes sensor.ev_battery_health, ev_battery_capacity, ev_efficiency_30d,
   ev_expected_range, ev_a30_efficiency and ev_health_report (markdown attrs) to HA.
   On the 1st of the month it also appends a snapshot row to monthly.csv.

Kill switch: touch ~/.local/state/ev-health/off. Errors: errors.log next to it.
"""
import gzip, json, math, os, sqlite3, sys, time, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

HOME = os.path.expanduser("~")
STATE = f"{HOME}/.local/state/ev-health"
os.makedirs(STATE, exist_ok=True)
DB = f"{STATE}/ev.db"
MODEL = f"{STATE}/model.json"
RATED_KWH = 61.7           # MG4 Long Range 64 kWh pack, usable when new
CAR = "mg_mg4_electric"
SCALARS = ["state_of_charge", "mileage", "exterior_temperature", "speed",
           "charging_status", "power_mode"]
UP_KWH_M, DOWN_KWH_M = 0.0056, 0.0030
PRIOR = {"a": (0.08, 0.04), "b": (0.041, 0.02), "p": (0.4, 0.3), "q": (0.08, 0.06)}
UTC = timezone.utc


def env(path):
    out = {}
    for line in open(path):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.strip().split("=", 1)
            out[k.replace("export ", "")] = v.strip().strip('"').strip("'")
    return out


HA = env(f"{HOME}/.config/jarvis/ha.env")


def ha(path, data=None, timeout=60):
    req = urllib.request.Request(
        HA["HA_URL"] + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={"Authorization": f"Bearer {HA['HA_TOKEN']}", "Content-Type": "application/json"},
        method="POST" if data is not None else "GET")
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def ts(s):
    return datetime.fromisoformat(s).timestamp()


# ---------------------------------------------------------------- 1. archive

def db():
    con = sqlite3.connect(DB)
    con.executescript("""
      CREATE TABLE IF NOT EXISTS pts(eid TEXT, t REAL, s TEXT, lat REAL, lon REAL, el REAL,
                                     PRIMARY KEY(eid, t));
      CREATE TABLE IF NOT EXISTS charges(start TEXT PRIMARY KEY, j TEXT);
      CREATE TABLE IF NOT EXISTS osrm(k TEXT PRIMARY KEY, j TEXT);
    """)
    return con


def archive(con):
    last = con.execute("SELECT max(t) FROM pts").fetchone()[0]
    start = datetime.fromtimestamp(last - 7200, UTC) if last else datetime.now(UTC) - timedelta(days=11)
    q = urllib.parse.quote
    iso = q(start.isoformat()) + "?end_time=" + q(datetime.now(UTC).isoformat())  # default window is only 1 day
    ids = ",".join(f"sensor.{CAR}_{k}" for k in SCALARS)
    for s in ha(f"/api/history/period/{iso}&filter_entity_id={ids}&minimal_response&no_attributes"):
        eid = s[0]["entity_id"].split(f"{CAR}_")[-1]
        con.executemany("INSERT OR IGNORE INTO pts(eid,t,s) VALUES(?,?,?)",
                        [(eid, ts(x["last_changed"]), x["state"]) for x in s])
    ids = f"device_tracker.{CAR}_gps_location,sensor.{CAR}_last_charge_energy"
    for s in ha(f"/api/history/period/{iso}&filter_entity_id={ids}"):
        for x in s:
            a = x.get("attributes", {})
            if x["entity_id"].startswith("device_tracker") and a.get("latitude") is not None:
                con.execute("INSERT OR REPLACE INTO pts VALUES('gps',?,?,?,?,?)",
                            (ts(x["last_changed"]), x["state"], a["latitude"], a["longitude"], a.get("elevation")))
            elif a.get("charge_start_ts") and a.get("energy_measured_kWh") is not None:
                keep = {k: a.get(k) for k in ("charge_start_ts", "charge_end_ts", "soc_start_pct", "soc_end_pct",
                                              "soc_added_pct", "energy_measured_kWh",
                                              "energy_measured_estimated_kWh", "energy_measured_samples",
                                              "average_power_kW", "odometer_km")}
                con.execute("INSERT OR REPLACE INTO charges VALUES(?,?)", (a["charge_start_ts"], json.dumps(keep)))
    con.commit()


# ---------------------------------------------------------------- 2. capacity

def capacity(con, days=120):
    cut = (datetime.now(UTC) - timedelta(days=days)).isoformat()
    rows = [json.loads(j) for (j,) in con.execute("SELECT j FROM charges WHERE start>=? ORDER BY start", (cut,))]
    good = [r for r in rows if (r["soc_added_pct"] or 0) >= 15 and r["energy_measured_kWh"]
            and (r["energy_measured_estimated_kWh"] or 0) <= 0.05 * r["energy_measured_kWh"]]
    if not good:
        return None
    per = [r["energy_measured_kWh"] / r["soc_added_pct"] * 100 for r in good]
    cap = sum(r["energy_measured_kWh"] for r in good) / sum(r["soc_added_pct"] for r in good) * 100
    mean = sum(per) / len(per)
    sd = math.sqrt(sum((x - mean) ** 2 for x in per) / (len(per) - 1)) if len(per) > 1 else None
    return {"kwh": round(cap, 1), "health": round(cap / RATED_KWH * 100), "sessions": len(good),
            "spread_kwh": round(sd, 1) if sd else None,
            "per_session": [(r["charge_start_ts"][:10], round(p, 1)) for r, p in zip(good, per)]}


# ---------------------------------------------------------------- 3. drives

def series(con, eid):
    return con.execute("SELECT t, s, lat, lon, el FROM pts WHERE eid=? ORDER BY t", (eid,)).fetchall()


def at(ser, t):
    """Last value at or before t (bisect)."""
    lo, hi = 0, len(ser)
    while lo < hi:
        mid = (lo + hi) // 2
        if ser[mid][0] <= t:
            lo = mid + 1
        else:
            hi = mid
    return ser[lo - 1] if lo else None


def num(row):
    try:
        return float(row[1])
    except (TypeError, ValueError):
        return None


def osrm_drive(con, key, pts):
    """Per poll-to-poll leg: metres on the A30, routed metres and OSRM seconds (one request
    per drive, cached by drive start + point count)."""
    hit = con.execute("SELECT j FROM osrm WHERE k=?", (key,)).fetchone()
    if hit:
        return json.loads(hit[0])
    legs = []
    for k in range(0, len(pts) - 1, 99):
        sub = pts[k:k + 100]
        url = ("https://router.project-osrm.org/route/v1/driving/"
               + ";".join(f"{p['lon']:.5f},{p['lat']:.5f}" for p in sub) + "?steps=true&overview=false")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "jarvis-home-ev/1.0"})
            r = json.load(urllib.request.urlopen(req, timeout=30))
        except Exception:
            return None
        for leg in r["routes"][0]["legs"]:
            st = leg["steps"]
            legs.append({"a30": sum(x["distance"] for x in st
                                    if "A30" in (x.get("ref") or "").replace(" ", "").split(";")),
                         "total": leg["distance"], "dur": leg["duration"]})
        time.sleep(1)  # public demo server: be polite
    con.execute("INSERT OR REPLACE INTO osrm VALUES(?,?)", (key, json.dumps(legs)))
    con.commit()
    return legs


def chunks(con):
    soc, odo, tmp = series(con, "state_of_charge"), series(con, "mileage"), series(con, "exterior_temperature")
    gps, pm, cs = series(con, "gps"), series(con, "power_mode"), series(con, "charging_status")
    charging = []  # (start, end) intervals the car was charging
    for i, r in enumerate(cs):
        if (r[1] or "").startswith("Charging") and r[1] != "Charging Stopped":
            end = cs[i + 1][0] if i + 1 < len(cs) else time.time()
            charging.append((r[0], end))
    out = []
    for i, r in enumerate(pm):
        if r[1] != "On":
            continue
        off = next((x[0] for x in pm[i + 1:] if x[1] == "Off"), None)
        if not off:
            continue
        # One sample per poll: gps rows inside the window (deduped to >=60 s apart) + the Off poll
        polls = []
        for g in gps:
            if r[0] - 30 <= g[0] <= off + 90 and (not polls or g[0] - polls[-1] >= 60):
                polls.append(g[0])
        pts = []
        for t in polls:
            s, o, g, tt = at(soc, t + 5), at(odo, t + 5), at(gps, t + 5), at(tmp, t + 5)
            if None in (s, o, g) or num(s) is None or num(o) is None:
                continue
            pts.append({"t": t, "soc": num(s), "mi": num(o), "lat": g[2], "lon": g[3], "el": g[4],
                        "T": num(tt) if tt else None})
        cur = None
        legs = osrm_drive(con, f"{r[0]:.0f}:{len(pts)}", pts) if len(pts) > 1 else None
        for li, (p0, p1) in enumerate(zip(pts, pts[1:])):
            if any(c0 < p1["t"] and c1 > p0["t"] for c0, c1 in charging):
                cur = None
                continue
            dmi = p1["mi"] - p0["mi"]
            leg_a30, o = 0.0, legs[li] if legs and li < len(legs) else None
            if o and o["total"] > 0 and dmi > 0:
                leg_a30 = dmi * min(1.0, o["a30"] / o["total"])
            if cur is None:
                cur = {"t0": p0["t"], "soc0": p0["soc"], "mi0": p0["mi"], "el0": p0["el"], "Ts": [], "a30": 0.0,
                       "osrm_s": 0.0}
            cur.update(t1=p1["t"], soc1=p1["soc"], mi1=p1["mi"], el1=p1["el"])
            cur["a30"] += leg_a30
            cur["osrm_s"] += o["dur"] if o else 0.0
            if p0["T"] is not None:
                cur["Ts"].append(p0["T"])
            if cur["mi1"] - cur["mi0"] >= 4:
                out.append(cur)
                cur = None
        if cur and cur["mi1"] - cur["mi0"] >= 2:
            out.append(cur)
    res = []
    for c in out:
        mi, hrs = c["mi1"] - c["mi0"], (c["t1"] - c["t0"]) / 3600
        dsoc = c["soc0"] - c["soc1"]
        if hrs <= 0 or dsoc < -0.5 or mi / hrs > 95:
            continue
        dh = (c["el1"] or 0) - (c["el0"] or 0) if c["el0"] is not None and c["el1"] is not None else 0
        res.append({"t": c["t0"], "mi": mi, "hrs": hrs, "mph": mi / hrs, "dsoc": dsoc, "dh": dh,
                    "T": sum(c["Ts"]) / len(c["Ts"]) if c["Ts"] else 12.0, "a30": c["a30"] / mi if mi else 0,
                    "osrm_s": c["osrm_s"]})
    return res


# ---------------------------------------------------------------- 4. model

def elev_kwh(dh):
    return dh * UP_KWH_M if dh > 0 else dh * DOWN_KWH_M


def feats(mi, hrs, mph, T):
    return [mi, mi * mph * mph / 1000, hrs, hrs * max(0.0, 18 - T)]


def fit(rows, cap):
    import numpy as np
    keys = ["a", "b", "p", "q"]
    X = np.array([feats(r["mi"], r["hrs"], r["mph"], r["T"]) for r in rows])
    y = np.array([r["dsoc"] * cap / 100 - elev_kwh(r["dh"]) for r in rows])
    w = np.array([r["mi"] for r in rows])
    th0 = np.array([PRIOR[k][0] for k in keys])
    L = np.diag([1 / PRIOR[k][1] ** 2 for k in keys]) * 0.5  # prior weight ~ a couple of short drives
    A = X.T @ (X * w[:, None]) / w.mean() + L
    rhs = X.T @ (y * w) / w.mean() + L @ th0
    th = np.linalg.solve(A, rhs)
    th = np.maximum(th, [0.03, 0.01, 0.1, 0.0])  # physics floors
    pred = X @ th
    rmse = float(np.sqrt(np.average((y - pred) ** 2, weights=w)))  # kWh per chunk
    return dict(zip(keys, map(float, th))), rmse


def kwh(m, mi, mph, T, dh=0.0):
    return sum(c * f for c, f in zip((m["a"], m["b"], m["p"], m["q"]), feats(mi, mi / mph, mph, T))) + elev_kwh(dh)


def mix_eff(m, rows, T):
    """Rob's real driving mix (speeds/distances as driven), re-run at temperature T, flat."""
    mi = sum(r["mi"] for r in rows)
    return mi / sum(kwh(m, r["mi"], r["mph"], T) for r in rows)


# ---------------------------------------------------------------- 5. publish

def push(eid, state, attrs):
    ha(f"/api/states/{eid}", {"state": state, "attributes": attrs}, timeout=15)


def outside_temp():
    for e in (f"sensor.{CAR}_exterior_temperature",):
        try:
            v = float(ha(f"/api/states/{e}", timeout=15)["state"])
            if -30 < v < 45:
                return v
        except Exception:
            pass
    return float(ha("/api/states/weather.forecast_home", timeout=15)["attributes"]["temperature"])


def main():
    if os.path.exists(f"{STATE}/off"):
        return
    con = db()
    archive(con)
    cap = capacity(con)
    capk = cap["kwh"] if cap else RATED_KWH
    rows = chunks(con)
    if len(rows) < 8:
        print("not enough driving yet", file=sys.stderr)
        return
    m, rmse = fit(rows, capk)
    now = time.time()
    r30 = [r for r in rows if r["t"] > now - 30 * 86400]
    mi30 = sum(r["mi"] for r in r30)
    kwh30 = sum(r["dsoc"] for r in r30) * capk / 100
    eff30 = mi30 / kwh30 if kwh30 > 0 else None
    T = outside_temp()
    temps = [0, 5, 10, 15, 20]

    def obs(rs):
        mi = sum(r["mi"] for r in rs)
        k = sum(r["dsoc"] for r in rs) * capk / 100
        Tm = sum(r["T"] * r["mi"] for r in rs) / mi if mi else 12
        return (mi / k if k > 0 else None), mi, Tm, k

    # Measured efficiency, scaled to other temperatures by the model's temperature curve
    # (anchoring to what the car actually did keeps Cornish hills, Rob's speeds etc. in).
    all_eff, all_mi, all_T, _ = obs(rows)
    a30_rows = [r for r in rows if r["a30"] >= 0.7]
    oth_rows = [r for r in rows if r["a30"] <= 0.1]
    a30_eff, a30_mi, a30_T, a30_k = obs(a30_rows)
    oth_eff, oth_mi, oth_T, _ = obs(oth_rows)
    a30_mph = sum(r["mi"] for r in a30_rows) / sum(r["hrs"] for r in a30_rows) if a30_rows else 62
    cruise_m = lambda t: 10 / kwh(m, 10, a30_mph, t)
    mixed = lambda t: all_eff * mix_eff(m, rows, t) / mix_eff(m, rows, all_T)
    cruise = (lambda t: a30_eff * cruise_m(t) / cruise_m(a30_T)) if a30_mi >= 30 else cruise_m
    band = {t: mixed(t) for t in temps}
    cruise_t = {t: cruise(t) for t in temps}
    eff_now, cruise_now = mixed(T), cruise(T)
    oth_at_a30_T = oth_eff * mix_eff(m, oth_rows, a30_T) / mix_eff(m, oth_rows, oth_T) if oth_rows else None
    a30_pen = round((1 - a30_eff / oth_at_a30_T) * 100) if a30_eff and oth_at_a30_T else None
    # chunk-level calibration of the raw model (used by ev-trip.py, which also has real hills)
    pred = lambda rs: sum(kwh(m, r["mi"], r["mph"], r["T"], r["dh"]) for r in rs)
    calib = sum(r["dsoc"] for r in rows) * capk / 100 / pred(rows)
    a30_calib = (a30_k / pred(a30_rows) / calib) if a30_mi >= 30 else 1.0
    rng_full = capk * eff_now
    # how Rob's real moving time compares with OSRM's estimate (for ev-trip.py)
    tr = [r for r in rows if r["osrm_s"] > 0]
    osrm_ratio = (sum(r["osrm_s"] for r in tr) / sum(r["hrs"] * 3600 for r in tr)) if tr else 1.0
    model = {"updated": datetime.now(UTC).isoformat(), "coef": m, "rmse_kwh_per_chunk": rmse,
             "capacity_kwh": capk, "chunks": len(rows), "miles": round(sum(r["mi"] for r in rows)),
             "a30_mph": a30_mph, "calib": calib, "a30_calib": a30_calib, "osrm_speed_ratio": osrm_ratio, "up_kwh_m": UP_KWH_M, "down_kwh_m": DOWN_KWH_M}
    json.dump(model, open(MODEL, "w"), indent=1)

    r1 = lambda x: round(x, 1) if x is not None else None
    if cap:
        push("sensor.ev_battery_health", cap["health"], {
            "unit_of_measurement": "%", "state_class": "measurement", "icon": "mdi:battery-heart-variant",
            "friendly_name": "MG4 battery health", "capacity_kwh": cap["kwh"], "rated_kwh": RATED_KWH,
            "clean_charges": cap["sessions"], "spread_kwh": cap["spread_kwh"],
            "per_charge": [f"{d}: {k} kWh" for d, k in cap["per_session"][-12:]]})
        push("sensor.ev_battery_capacity", cap["kwh"], {
            "unit_of_measurement": "kWh", "device_class": "energy_storage", "state_class": "measurement",
            "icon": "mdi:car-battery", "friendly_name": "MG4 usable capacity"})
    push("sensor.ev_efficiency_30d", r1(eff30), {
        "unit_of_measurement": "mi/kWh", "state_class": "measurement", "icon": "mdi:leaf",
        "friendly_name": "MG4 efficiency (30 days)", "miles": round(mi30), "kwh": r1(kwh30),
        **{f"at_{t}c": r1(v) for t, v in band.items()}})
    push("sensor.ev_expected_range", round(rng_full), {
        "unit_of_measurement": "mi", "state_class": "measurement", "icon": "mdi:map-marker-distance",
        "friendly_name": "MG4 realistic range (100%)", "outside_c": T, "mi_per_kwh": r1(eff_now),
        "range_80_to_10": round(capk * 0.7 * eff_now), "a30_range_100": round(capk * cruise_now),
        **{f"range_at_{t}c": round(capk * v) for t, v in band.items()}})
    push("sensor.ev_a30_efficiency", r1(a30_eff), {
        "unit_of_measurement": "mi/kWh", "icon": "mdi:highway", "friendly_name": "MG4 on the A30",
        "a30_miles": round(a30_mi), "other_roads_mi_per_kwh": r1(oth_eff), "other_miles": round(oth_mi),
        "a30_avg_mph": round(a30_mph),
        "a30_avg_c": r1(a30_T), "penalty_pct_same_temp": a30_pen,
        **{f"a30_range_at_{t}c": round(capk * v) for t, v in cruise_t.items()}})

    md = [f"**Battery health: {cap['health']}%** ({cap['kwh']} kWh usable vs {RATED_KWH} new, "
          f"{cap['sessions']} clean charges, spread ±{cap['spread_kwh']} kWh)" if cap else "**Battery health:** not enough clean charges yet",
          "",
          f"**Last 30 days:** {r1(eff30)} mi/kWh over {round(mi30)} mi",
          f"**Right now ({T:.0f}°C):** {eff_now:.1f} mi/kWh, so **{round(rng_full)} mi** from 100%, "
          f"**{round(capk * 0.7 * eff_now)} mi** for 80%→10%",
          f"**A30 at {round(a30_mph)} mph:** {r1(a30_eff)} mi/kWh vs {r1(oth_eff)} on other roads "
          f"({round(a30_mi)} vs {round(oth_mi)} mi measured), **{a30_pen}% worse** at the same temperature"
          if a30_eff and oth_eff else "",
          "", "| Outside | Mixed | Range 100% | A30 cruise | A30 range |", "|---|---|---|---|---|"]
    md += [f"| {t}°C | {band[t]:.1f} | {round(capk * band[t])} mi | {cruise_t[t]:.1f} | {round(capk * cruise_t[t])} mi |"
           for t in temps]
    md += ["", f"<sub>Model from {len(rows)} drive chunks, {model['miles']} mi. "
           f"Updated {datetime.now().strftime('%d %b %H:%M')}.</sub>"]
    push("sensor.ev_health_report", "ok", {"friendly_name": "MG4 health report", "md": "\n".join(md),
                                           "icon": "mdi:file-chart"})

    if datetime.now().day == 1:
        path, month = f"{STATE}/monthly.csv", datetime.now().strftime("%Y-%m")
        if not os.path.exists(path) or month not in open(path).read():
            new = not os.path.exists(path)
            with open(path, "a") as f:
                if new:
                    f.write("month,health_pct,capacity_kwh,eff_30d,range_now_mi,a30_mi_per_kwh,other_mi_per_kwh\n")
                f.write(f"{month},{cap['health'] if cap else ''},{capk},{r1(eff30)},{round(rng_full)},"
                        f"{r1(a30_eff)},{r1(oth_eff)}\n")
    if "-v" in sys.argv:
        print(json.dumps({"cap": cap, "model": model, "eff30": eff30, "T": T, "band": band, "cruise": cruise_t, "a30_pen": a30_pen,
                          "a30": (a30_eff, a30_mi), "other": (oth_eff, oth_mi)}, indent=1, default=str))
        print("\n".join(md))


if __name__ == "__main__":
    main()
