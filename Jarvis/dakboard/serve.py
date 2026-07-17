#!/usr/bin/env python3
"""Tiny static server for the Jarvis DAKboard wall panel.

Serves only index.html and alerts.json from ./www, with no-cache + permissive
CORS headers so the DAKboard iframe always sees the latest alerts. LAN-only;
TLS is terminated upstream by Nginx Proxy Manager (wall.cracky.co.uk).
"""
import http.server
import os

# index.html ships next to this script (git-backed in the vault). alerts.json is
# runtime state, kept OUT of git to avoid churn (WALL_STATE, default ~/dakboard).
SRC = os.path.dirname(os.path.abspath(__file__))
STATE = os.environ.get("WALL_STATE", os.path.expanduser("~/dakboard"))
PORT = int(os.environ.get("WALL_PORT", "3060"))
# Optional shared secret. If set, every request must carry ?k=<token>. Lets the
# panel be public over HTTPS (for a wall display that can't answer a login box)
# while staying unguessable. Empty = no gate (LAN-only use).
TOKEN = os.environ.get("WALL_TOKEN", "").strip()

# path -> (absolute file, content-type)
ROUTES = {
    "/": (os.path.join(SRC, "index.html"), "text/html; charset=utf-8"),
    "/index.html": (os.path.join(SRC, "index.html"), "text/html; charset=utf-8"),
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
