#!/usr/bin/env python3
"""Minimal Home Assistant websocket client, stdlib only (no pip on this box).

Usage: ha_ws.py '<json command>' [...]
  Auths against HA_URL/HA_TOKEN from ~/.config/jarvis/ha.env, sends each JSON
  command (id auto-assigned), prints each result as JSON on one line.
  Example: ha_ws.py '{"type":"supervisor/api","endpoint":"/supervisor/info","method":"get"}'
"""
import base64, json, os, socket, struct, sys, urllib.parse

def read_env():
    env = {}
    with open(os.path.expanduser("~/.config/jarvis/ha.env")) as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                env[k] = v
    return env

class WS:
    def __init__(self, url):
        u = urllib.parse.urlparse(url)
        self.sock = socket.create_connection((u.hostname, u.port or 80), timeout=float(os.environ.get("HA_WS_TIMEOUT", "30")))
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((
            f"GET {u.path} HTTP/1.1\r\nHost: {u.hostname}:{u.port}\r\n"
            f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        resp = b""
        while b"\r\n\r\n" not in resp:
            resp += self.sock.recv(4096)
        if b" 101 " not in resp.split(b"\r\n", 1)[0]:
            raise RuntimeError(f"handshake failed: {resp[:200]!r}")

    def send(self, obj):
        data = json.dumps(obj).encode()
        mask = os.urandom(4)
        head = b"\x81"  # FIN + text
        n = len(data)
        if n < 126: head += bytes([0x80 | n])
        elif n < 65536: head += bytes([0x80 | 126]) + struct.pack(">H", n)
        else: head += bytes([0x80 | 127]) + struct.pack(">Q", n)
        self.sock.sendall(head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def _read_exact(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk: raise RuntimeError("connection closed")
            buf += chunk
        return buf

    def recv(self):
        while True:
            b1, b2 = self._read_exact(2)
            op, ln = b1 & 0x0F, b2 & 0x7F
            if ln == 126: ln = struct.unpack(">H", self._read_exact(2))[0]
            elif ln == 127: ln = struct.unpack(">Q", self._read_exact(8))[0]
            payload = self._read_exact(ln)
            if op == 0x9:  # ping -> pong
                self.sock.sendall(b"\x8a" + bytes([0x80]) + b"\x00\x00\x00\x00")
                continue
            if op == 0x8: raise RuntimeError("closed by server")
            return json.loads(payload)

def main():
    env = read_env()
    url = env["HA_URL"].replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"
    ws = WS(url)
    assert ws.recv()["type"] == "auth_required"
    ws.send({"type": "auth", "access_token": env["HA_TOKEN"]})
    r = ws.recv()
    if r["type"] != "auth_ok":
        sys.exit(f"auth failed: {r}")
    mid = 1
    for arg in sys.argv[1:]:
        cmd = json.loads(arg)
        cmd["id"] = mid
        ws.send(cmd)
        while True:
            r = ws.recv()
            if r.get("id") == mid and r.get("type") == "result":
                print(json.dumps(r))
                break
        mid += 1

if __name__ == "__main__":
    main()
