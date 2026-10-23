#!/usr/bin/env python3
"""EV charge planner for the MG4 (Rob's ask, 13 Oct 2026: "make it automatic").

Cron every 10 min. Three jobs:

1. Habit log: appends a snapshot (time, SoC, home?, plugged?, odometer) to
   ~/.local/state/ev-planner/log.csv.
2. Bedtime nag: between 22:30 and 00:15, if the car is at home, not plugged in
   and below its charge limit, Telegram Rob and Aimee once per night.
5. Cut-out rescue: if the Pod Point ends a session itself (out-of-service, LED
   dark) mid-charge, restart it from the car (max 4 a day).

16 Oct 2026 (Rob: "kill any automations that stop the car charging, including
waiting till 00:30"): the daytime top-up (3) and night backstop (4) are gone,
along with the HA hold / 00:30 start / 05:30 stop automations. Plug in and it
charges straight away; the car's own 80% limit is the only thing that ends it.
This script never stops a charge.
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

VIN = "LSJWH4099PN166408"
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


def km(eid):
    """Distance sensor in km, whatever display unit HA has it set to."""
    try:
        e = ha(f"/api/states/{eid}")
        v = float(e["state"])
    except Exception:
        return None
    return v * 1.609344 if e["attributes"].get("unit_of_measurement") == "mi" else v


def car(cmd):
    # SAIC's cloud often takes >15s to ack; HA carries on with the call regardless, so a
    # timeout here isn't a failure and mustn't skip the rescue count + Telegram (23 Oct 2026).
    try:
        ha(f"/api/services/mg_saic/{cmd}", {"vin": VIN})
    except TimeoutError:
        pass


def tg(text, who=None):
    for cid in (who or NOTIFY):
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


def flag_day(name, day):
    p = f"{STATE}/{name}"
    return os.path.exists(p) and open(p).read().split()[:1] == [day]


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
    odo = km(f"sensor.{CAR}_mileage")

    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "soc", "home", "plugged", "charger_w", "odo"])
        w.writerow([now.isoformat(timespec="minutes"), soc if soc is not None else "", int(home), int(plugged), round(charger_w), round(odo, 1) if odo else ""])

    if soc is None:
        return
    today = now.date().isoformat()

    # 2. Bedtime nag, once per night.
    night = night_of(now)
    if (hm >= 22 * 60 + 30 or hm <= 15) and home and not plugged and soc < limit - 5 and not flag("nagged", night):
        miles = round((km(f"sensor.{CAR}_electric_range") or 0) / 1.609344)
        tg(f"🔌 The MG4 isn't plugged in. It's on {soc:.0f}% (~{miles} miles). "
           f"Plug it in before bed and it'll charge to {limit:.0f}%.")
        set_flag("nagged", night)

    charging = charger_w > 500

    # 5. Cut-out rescue (16 Oct 2026). The Pod Point sometimes ends a session itself (LED dark,
    # status out-of-service, RCBO fine) and doesn't always retry. A car-side start revives it.
    # Only when it was drawing in the last 40 min, so holds and full stops are left alone.
    if charging:
        open(f"{STATE}/last_drawing", "w").write(str(now.timestamp()))
    else:
        try:
            drew = float(open(f"{STATE}/last_drawing").read())
        except Exception:
            drew = 0
        # A cut-out inside 10 min falls between runs and never sets last_drawing (23 Oct 13:45:
        # drew 13:45-13:47, out-of-service by 13:50, rescue never armed). Ask HA's history too.
        try:
            since = (now - timedelta(minutes=40)).astimezone().isoformat()
            hist = ha("/api/history/period/" + urllib.parse.quote(since) +
                      "?filter_entity_id=sensor.shellyem_34945470ed50_channel_2_power&minimal_response")
            for p in (hist[0] if hist else []):
                try:
                    if float(p["state"]) > 500:
                        drew = max(drew, datetime.fromisoformat(p["last_changed"]).timestamp())
                except (TypeError, ValueError):
                    pass
        except Exception:
            pass
        try:
            st = ha("/api/states/sensor.psl_557234_status")
            dark_for = now.timestamp() - datetime.fromisoformat(st["last_changed"]).timestamp()
        except Exception:
            st, dark_for = {"state": None}, 0
        tries = open(f"{STATE}/rescues").read().split() if flag_day("rescues", today) else [today, "0"]
        # A deliberate stop (dashboard Stop / script.ev_charge_stop) is never a cut-out (19 Oct 2026).
        # Only a stop since the last time it was drawing counts: a 21:26 pause must not block
        # rescuing a 01:22 cut-out after the 00:30 restart (missed exactly that, 21 Oct 2026).
        try:
            stopped = ha("/api/states/script.ev_charge_stop")["attributes"].get("last_triggered")
            stopped_ts = datetime.fromisoformat(stopped).timestamp() if stopped else 0
        except Exception:
            stopped_ts = 0
        deliberate = stopped_ts > drew - 15 * 60
        # The Pod Point cloud can sit on "charging" through a cut-out (21 Oct 01:22: car went
        # "Charging Stopped" then "Connecting", gun in, no pilot, for 6h), so the car is a second tell.
        car_st = state(f"sensor.{CAR}_charging_status") or ""
        car_dark = car_st in ("Connecting", "Charging Stopped")
        try:
            car_dark_for = now.timestamp() - datetime.fromisoformat(
                ha(f"/api/states/sensor.{CAR}_charging_status")["last_changed"]).timestamp()
        except Exception:
            car_dark_for = 0
        cut = ((st["state"] == "out-of-service" and dark_for > 8 * 60)
               or (car_dark and now.timestamp() - drew > 8 * 60 and car_dark_for > 5 * 60))
        if (home and plugged and soc < limit - 2 and cut and not deliberate
                and now.timestamp() - drew < 40 * 60 and int(tries[1]) < 4):
            car("start_charging")
            open(f"{STATE}/rescues", "w").write(f"{today} {int(tries[1]) + 1}")
            rob = [c for c, p in PEOPLE.items() if p.get("role") == "rob"]
            tg(f"🔁 Pod Point cut out on its own (not a trip) with the MG4 on {soc:.0f}%. "
               f"Restarted it from the car. Rescue {int(tries[1]) + 1} of 4 today.", rob)
            return

if __name__ == "__main__":
    main()
