#!/usr/bin/env python3
"""Tiny static server for the Jarvis DAKboard wall panel.

Serves index.html + alerts.json (alerts panel) and car.html + car.json
(one-line car strip, live from HA), with no-cache + permissive
CORS headers so the DAKboard iframe always sees the latest alerts. LAN-only;
TLS is terminated upstream by Nginx Proxy Manager (wall.cracky.co.uk).
"""
import http.server
import json
import os
import threading
import time
import urllib.request

# index.html ships next to this script (git-backed in the vault). alerts.json is
# runtime state, kept OUT of git to avoid churn (WALL_STATE, default ~/dakboard).
SRC = os.path.dirname(os.path.abspath(__file__))
STATE = os.environ.get("WALL_STATE", os.path.expanduser("~/dakboard"))
PORT = int(os.environ.get("WALL_PORT", "3060"))
# Optional shared secret. If set, every request must carry ?k=<token>. Lets the
# panel be public over HTTPS (for a wall display that can't answer a login box)
# while staying unguessable. Empty = no gate (LAN-only use).
TOKEN = os.environ.get("WALL_TOKEN", "").strip()

# HA creds for the car strip, read server-side so the token never reaches the wall.
HA_ENV = os.environ.get("WALL_HA_ENV", os.path.expanduser("~/.config/jarvis/ha.env"))
CAR = "sensor.mg_mg4_electric_"
CHARGER_W = "sensor.shellyem_34945470ed50_channel_2_power"  # Shelly ch2 = Pod Point circuit
CAR_TTL = 20  # seconds; the page polls every 30
_car_cache = {"at": 0, "body": None}
_car_lock = threading.Lock()


def _ha_env():
    env = {}
    try:
        with open(HA_ENV) as f:
            for line in f:
                if "=" in line and not line.lstrip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env[k] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return env.get("HA_URL", "http://192.168.1.4:8123").rstrip("/"), env.get("HA_TOKEN", "")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def car_status():
    """Small JSON for the car strip. Charging = car says so OR the charger is
    drawing >500 W (the car polls every 5-30 min, the Shelly is live)."""
    with _car_lock:
        if _car_cache["body"] and time.time() - _car_cache["at"] < CAR_TTL:
            return _car_cache["body"]
        url, token = _ha_env()
        req = urllib.request.Request(url + "/api/states",
                                     headers={"Authorization": "Bearer " + token})
        try:
            with urllib.request.urlopen(req, timeout=8) as r:
                states = {s["entity_id"]: s for s in json.load(r)}
        except Exception:
            # keep showing the last good reading rather than blanking the wall
            if _car_cache["body"]:
                return _car_cache["body"]
            return json.dumps({"ok": False}).encode()
        st = lambda e: (states.get(e) or {}).get("state")
        status = st(CAR + "charging_status") or ""
        watts = _num(st(CHARGER_W)) or 0
        charging = watts > 500 or status.lower().startswith("charging")
        plugged = charging or status.lower() not in ("unplugged", "", "unavailable", "unknown")
        soc_state = states.get(CAR + "state_of_charge") or {}
        body = json.dumps({
            "ok": True,
            "soc": _num(soc_state.get("state")),
            "soc_at": soc_state.get("last_updated"),
            "range_mi": _num(st(CAR + "electric_range")),
            "charging": charging,
            "plugged": plugged,
            "kw": round(watts / 1000, 1) if watts > 500 else None,
            "mins_left": _num(st(CAR + "remaining_charging_time")) if charging else None,
            "status": status,
        }).encode()
        _car_cache.update(at=time.time(), body=body)
        return body


# path -> (absolute file, content-type)
ROUTES = {
    "/": (os.path.join(SRC, "index.html"), "text/html; charset=utf-8"),
    "/index.html": (os.path.join(SRC, "index.html"), "text/html; charset=utf-8"),
    "/car": (os.path.join(SRC, "car.html"), "text/html; charset=utf-8"),
    "/alerts.json": (os.path.join(STATE, "alerts.json"), "application/json; charset=utf-8"),
}


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "JarvisWall/1.0"

    def _send(self, code, body=b"", ctype="text/plain; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _query(self):
        from urllib.parse import parse_qs, urlparse
        return parse_qs(urlparse(self.path).query)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if TOKEN and self._query().get("k", [""])[0] != TOKEN:
            self._send(403, b"forbidden")
            return
        if path == "/car.json":
            self._send(200, car_status(), "application/json; charset=utf-8")
            return
        route = ROUTES.get(path)
        if not route:
            self._send(404, b"not found")
            return
        fpath, ctype = route
        try:
            with open(fpath, "rb") as f:
                self._send(200, f.read(), ctype)
        except FileNotFoundError:
            # alerts.json may not exist yet -> serve an empty feed, not a 404
            if fpath.endswith("alerts.json"):
                self._send(200, b'{"updated":"","alerts":[]}', ctype)
            else:
                self._send(404, b"not found")

    def log_message(self, *args):
        pass  # quiet


if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
