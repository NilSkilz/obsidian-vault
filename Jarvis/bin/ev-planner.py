#!/usr/bin/env python3
"""EV charge planner for the MG4 (Rob's ask, 13 Oct 2026: "make it automatic").

Cron every 10 min. Three jobs:

1. Habit log: appends a snapshot (time, SoC, home?, plugged?, odometer) to
   ~/.local/state/ev-planner/log.csv. This is what the planner learns from.
2. Bedtime nag: between 22:30 and 00:15, if the car is at home, not plugged in
   and below its charge limit, Telegram Rob and Aimee once per night.
3. Daytime top-up: if the car is plugged in at home outside the cheap window and
   its SoC won't cover what this weekday usually uses for the rest of the day
   (learned from the log, defaults until there's data), boost the Pod Point
   until it will. Otherwise leave it on Smart to fill at 9.5p from 00:30.

The overnight 00:30-05:30 window itself lives on the charger (Smart mode), and
the car's own 80% limit stops it there, so none of that depends on this script.
Kill switch: touch ~/.local/state/ev-planner/off.
"""
import csv, json, os, sys, urllib.request, urllib.parse
from datetime import datetime, timedelta

HOME = os.path.expanduser("~")
STATE = f"{HOME}/.local/state/ev-planner"
LOG = f"{STATE}/log.csv"
os.makedirs(STATE, exist_ok=True)


def env(path):
    out = {}
    for line in open(path):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.strip().split("=", 1)
            out[k.replace("export ", "")] = v.strip().strip('"').strip("'")
    return out


HA = env(f"{HOME}/.config/jarvis/ha.env")
TG = env(f"{HOME}/.config/jarvis/telegram.env")
PEOPLE = json.load(open(f"{HOME}/.config/jarvis/telegram-people.json"))
NOTIFY = [cid for cid, p in PEOPLE.items() if p.get("role") in ("rob", "adult")]

POD_ENTRY = "01M4GZZZNT5M2JVGKX2QM907J4"
CAR = "mg_mg4_electric"
PACK_KWH = 64
MIN_FLOOR = 20      # never let a daytime decision leave it below this
BUFFER = 10         # % on top of the learned need
DEFAULT_NEED = {"weekday": 25, "weekend": 40}  # % for the rest of the day, until learned


def ha(path, data=None):
    req = urllib.request.Request(
        HA["HA_URL"] + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={"Authorization": f"Bearer {HA['HA_TOKEN']}", "Content-Type": "application/json"},
        method="POST" if data is not None else "GET")
    return json.load(urllib.request.urlopen(req, timeout=15))


def state(eid):
    try:
        return ha(f"/api/states/{eid}")["state"]
    except Exception:
        return None


def num(eid):
    try:
        return float(state(eid))
    except (TypeError, ValueError):
        return None


def tg(text):
    for cid in NOTIFY:
        data = urllib.parse.urlencode({"chat_id": cid, "text": text}).encode()
        try:
            urllib.request.urlopen(f"https://api.telegram.org/bot{TG['TELEGRAM_BOT_TOKEN']}/sendMessage", data, timeout=15)
        except Exception as e:
            print("telegram failed", cid, e, file=sys.stderr)


def flag(name, today):
    p = f"{STATE}/{name}"
    return os.path.exists(p) and open(p).read().strip() == today


def set_flag(name, today):
    open(f"{STATE}/{name}", "w").write(today)


def night_of(now):
    """The 'night' a 22:30-00:15 moment belongs to (so 00:10 counts as the evening before)."""
    return (now - timedelta(hours=6)).date().isoformat()


def learned_need(now):
    """90th percentile of SoC used from this time of day to 00:30, on the same kind of day.

    Built from log.csv: for each past day of the same weekday (falls back to
    weekday/weekend), take SoC at the nearest snapshot to this time minus the
    lowest SoC seen before 00:30, ignoring any charging in between by summing
    only drops. Needs 3+ days, else the default.
    """
    if not os.path.exists(LOG):
        return None, 0
    rows = list(csv.DictReader(open(LOG)))
    kind = "weekend" if now.weekday() >= 5 else "weekday"
    by_day = {}
    for r in rows:
        t = datetime.fromisoformat(r["time"])
        day = (t - timedelta(minutes=30)).date()  # day runs to 00:30
        if day == now.date():
            continue
        try:
            by_day.setdefault(day, []).append((t, float(r["soc"])))
        except ValueError:
            pass
    used = []
    for day, pts in by_day.items():
        same = day.weekday() == now.weekday()
        if not same and ("weekend" if day.weekday() >= 5 else "weekday") != kind:
            continue
        cut = datetime.combine(day, now.time())
        pts = sorted(p for p in pts if p[0] >= cut)
        if len(pts) < 3 or (pts[0][0] - cut) > timedelta(minutes=30):
            continue
        drop = sum(max(0, a[1] - b[1]) for a, b in zip(pts, pts[1:]))
        used.append((same, drop))
    same_day = [d for s, d in used if s]
    pool = same_day if len(same_day) >= 3 else [d for _, d in used]
    if len(pool) < 3:
        return None, len(pool)
    pool.sort()
    return pool[int(0.9 * (len(pool) - 1))], len(pool)


def main():
    if os.path.exists(f"{STATE}/off"):
        return
    now = datetime.now()
    hm = now.hour * 60 + now.minute

    soc = num(f"sensor.{CAR}_state_of_charge")
    limit = num(f"number.{CAR}_target_soc") or 80
    where = state(f"device_tracker.{CAR}_gps_location")
    home = where == "home"
    plugged = state(f"binary_sensor.{CAR}_charging_gun_state") == "on" or state("binary_sensor.psl_557234_cable_status") == "on"
    charger_w = num("sensor.shellyem_34945470ed50_channel_2_power") or 0
    odo = num(f"sensor.{CAR}_mileage")

    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "soc", "home", "plugged", "charger_w", "odo"])
        w.writerow([now.isoformat(timespec="minutes"), soc if soc is not None else "", int(home), int(plugged), round(charger_w), odo or ""])

    if soc is None:
        return
    today = now.date().isoformat()

    # 2. Bedtime nag, once per night.
    night = night_of(now)
    if (hm >= 22 * 60 + 30 or hm <= 15) and home and not plugged and soc < limit - 5 and not flag("nagged", night):
        miles = round((num(f"sensor.{CAR}_electric_range") or 0) / 1.609)
        tg(f"🔌 The MG4 isn't plugged in. It's on {soc:.0f}% (~{miles} miles). "
           f"Plug it in before bed and it'll fill to {limit:.0f}% at 9.5p from 00:30.")
        set_flag("nagged", night)

    # 3. Daytime top-up. Cheap window (00:30-05:30) is the charger's job.
    boosting = os.path.exists(f"{STATE}/boosting")
    in_cheap = 30 <= hm < 5 * 60 + 30
    if in_cheap or not (home and plugged):
        if boosting:
            os.remove(f"{STATE}/boosting")
        return

    learned, n = learned_need(now)
    kind = "weekend" if now.weekday() >= 5 else "weekday"
    base = learned if learned is not None else DEFAULT_NEED[kind]
    # Late evening needs less: scale the default down towards midnight.
    if learned is None and hm >= 18 * 60:
        base *= max(0.3, (24 * 60 - hm) / (6 * 60))
    need = min(limit, max(MIN_FLOOR, base + BUFFER))

    if soc < need:
        # Re-up a 1h boost each hour while short; Pod Point override ends itself.
        last = float(open(f"{STATE}/boosting").read()) if boosting else 0
        if now.timestamp() - last > 50 * 60:
            ha("/api/services/pod_point/charge_now", {"config_entry_id": POD_ENTRY, "hours": 1})
            open(f"{STATE}/boosting", "w").write(str(now.timestamp()))
            if not flag("boost_told", today):
                kwh = (need - soc) / 100 * PACK_KWH / 0.9
                why = f"{'on a usual ' + now.strftime('%A') if learned is not None else 'on a ' + kind} you use about {base:.0f}% more before bed"
                tg(f"⚡ MG4 plugged in on {soc:.0f}%. Topping it up to {need:.0f}% now at the day rate "
                   f"(~£{kwh * 0.3617:.2f}) because {why}. The rest goes in at 9.5p tonight.")
                set_flag("boost_told", today)
    elif boosting:
        ha("/api/services/pod_point/stop_charge_now", {"config_entry_id": POD_ENTRY})
        os.remove(f"{STATE}/boosting")


if __name__ == "__main__":
    main()
