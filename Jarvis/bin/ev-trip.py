#!/usr/bin/env python3
"""MG4 journey estimate from the learned model (ev-health.py writes model.json).

Usage: ev-trip.py "<destination>" [--from "<place>"] [--soc 80] [--return] [--temp 6]
                  [--depart 2026-10-26T07:30] [--stay-hours 8]
Places are free text (Nominatim, GB) or "lat,lon". Default origin is home, default
start SoC is the car's live SoC, default temp is the Open-Meteo forecast for the
departure hour. Route + road speeds from OSRM, climb from Open-Meteo elevation,
then the fitted kWh model chunk by chunk (~0.5 km). Prints kWh, % used, arrival %.
"""
import argparse, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime

HOME = os.path.expanduser("~")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
H = __import__("ev-health")  # same model + HA helpers
UA = {"User-Agent": "jarvis-home-ev/1.0 (rob, personal use)"}
HOME_LL = (50.733119, -4.618527)


def get(url, timeout=30):
    for attempt in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout))
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 3:
                raise
            time.sleep(5 * (attempt + 1))


def place(text):
    if text.lower() == "home":
        return HOME_LL, "Home"
    try:
        lat, lon = map(float, text.split(","))
        return (lat, lon), text
    except ValueError:
        pass
    r = get("https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=gb&q="
            + urllib.parse.quote(text))
    if not r:
        sys.exit(f"Can't find '{text}'")
    return (float(r[0]["lat"]), float(r[0]["lon"])), r[0]["display_name"].split(",")[0]


def route(a, b):
    r = get(f"https://router.project-osrm.org/route/v1/driving/{a[1]},{a[0]};{b[1]},{b[0]}"
            "?overview=full&geometries=geojson&annotations=distance,duration&steps=true")["routes"][0]
    coords = [(c[1], c[0]) for c in r["geometry"]["coordinates"]]
    ann = r["legs"][0]["annotation"]
    is30 = lambda st: "A30" in (st.get("ref") or "").replace(" ", "").split(";")
    a30 = sum(st["distance"] for st in r["legs"][0]["steps"] if is30(st))
    spans, cum = [], 0.0  # (start m, end m) of A30 steps along the route
    for st in r["legs"][0]["steps"]:
        if is30(st):
            spans.append((cum, cum + st["distance"]))
        cum += st["distance"]
    # ~500 m chunks (longer on long routes, max ~300 elevation lookups)
    step = max(500.0, r["distance"] / 300)
    chunks, d, t, start = [], 0.0, 0.0, 0
    for i, (dd, tt) in enumerate(zip(ann["distance"], ann["duration"])):
        d, t = d + dd, t + tt
        if d >= step or i == len(ann["distance"]) - 1:
            chunks.append({"i0": start, "i1": i + 1, "m": d, "s": max(t, 1)})
            d, t, start = 0.0, 0.0, i + 1
    pts = [coords[c["i0"]] for c in chunks] + [coords[-1]]
    el = []
    for k in range(0, len(pts), 100):
        sub = pts[k:k + 100]
        el += get("https://api.open-meteo.com/v1/elevation?latitude=" + ",".join(f"{p[0]:.5f}" for p in sub)
                  + "&longitude=" + ",".join(f"{p[1]:.5f}" for p in sub))["elevation"]
        time.sleep(1)
    cum = 0.0
    for c, e0, e1 in zip(chunks, el, el[1:]):
        c["dh"] = e1 - e0
        mid, cum = cum + c["m"] / 2, cum + c["m"]
        c["a30"] = any(a <= mid <= b for a, b in spans)
    return {"m": r["distance"], "s": r["duration"], "a30_m": a30, "chunks": chunks,
            "climb": sum(max(0, c["dh"]) for c in chunks)}


def forecast_temp(ll, when):
    r = get(f"https://api.open-meteo.com/v1/forecast?latitude={ll[0]}&longitude={ll[1]}"
            "&hourly=temperature_2m&forecast_days=7&timezone=Europe%2FLondon")
    key = when.strftime("%Y-%m-%dT%H:00")
    h = r["hourly"]
    return h["temperature_2m"][h["time"].index(key)] if key in h["time"] else h["temperature_2m"][0]


def leg_kwh(model, rt, T):
    """Fitted model per ~500 m chunk at Rob's real speeds (OSRM x his measured ratio),
    calibrated to what the car actually used, with the measured A30 correction on A30 bits."""
    m, slow = model["coef"], model.get("osrm_speed_ratio", 1.0)
    tot = 0.0
    for c in rt["chunks"]:
        mi = c["m"] / 1609.34
        mph = max(8.0, min(70.0, mi / (c["s"] / 3600) * slow))
        k = H.kwh(m, mi, mph, T, c["dh"]) * model.get("calib", 1.0)
        tot += k * (model.get("a30_calib", 1.0) if c["a30"] else 1.0)
    return tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dest")
    ap.add_argument("--from", dest="origin", default="home")
    ap.add_argument("--soc", type=float)
    ap.add_argument("--return", dest="ret", action="store_true")
    ap.add_argument("--temp", type=float)
    ap.add_argument("--depart")
    ap.add_argument("--stay-hours", type=float, default=4)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    model = json.load(open(H.MODEL))
    cap, slow = model["capacity_kwh"], model.get("osrm_speed_ratio", 1.0)
    o, oname = place(a.origin)
    d, dname = place(a.dest)
    when = datetime.fromisoformat(a.depart) if a.depart else datetime.now()
    soc = a.soc if a.soc is not None else float(H.ha(f"/api/states/sensor.{H.CAR}_state_of_charge")["state"])
    out = route(o, d)
    T1 = a.temp if a.temp is not None else forecast_temp(o, when)
    k1 = leg_kwh(model, out, T1)
    res = {"from": oname, "to": dname, "miles": out["m"] / 1609.34, "mins": out["s"] / 60 / slow,
           "a30_miles": out["a30_m"] / 1609.34, "climb_m": out["climb"], "temp": T1, "kwh": k1,
           "pct": k1 / cap * 100, "start_soc": soc, "arrive_soc": soc - k1 / cap * 100}
    if a.ret:
        back = route(d, o)
        from datetime import timedelta
        T2 = a.temp if a.temp is not None else forecast_temp(d, when + timedelta(hours=out["s"] / 3600 + a.stay_hours))
        k2 = leg_kwh(model, back, T2)
        res.update(back_kwh=k2, back_pct=k2 / cap * 100, back_temp=T2, home_soc=res["arrive_soc"] - k2 / cap * 100)
    err = 0.1  # +-10% until the model has a few months behind it
    if a.json:
        print(json.dumps(res, indent=1))
        return
    print(f"{res['from']} → {res['to']}: {res['miles']:.0f} mi, ~{res['mins']:.0f} min, "
          f"{res['a30_miles']:.0f} mi on the A30, {res['climb_m']:.0f} m of climbing, {T1:.0f}°C")
    print(f"  {k1:.1f} kWh = {res['pct']:.0f}% (±{res['pct'] * err:.0f}), "
          f"{soc:.0f}% → arrive ~{res['arrive_soc']:.0f}%  ({res['miles'] / k1:.1f} mi/kWh)")
    if a.ret:
        print(f"  Back: {res['back_kwh']:.1f} kWh = {res['back_pct']:.0f}% at {res['back_temp']:.0f}°C, "
              f"home on ~{res['home_soc']:.0f}%")


if __name__ == "__main__":
    main()
