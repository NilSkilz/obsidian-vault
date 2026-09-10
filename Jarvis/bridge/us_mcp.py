#!/usr/bin/env python3
"""Scoped MCP server for Tide's /us page (shared relationship agreements).

Attached by bridge.py to Aimee's Telegram sessions only. Her sessions have no
Bash and can't read ~/.config (by the 2026-08-29 privacy design), so this
server holds the key and exposes exactly four tools: list, add, edit, remove.
Acts as the user named in JARVIS_US_USER (the bridge sets it per person).
The /us list is shared Rob+Aimee ground: either parent may add, reword or
remove any entry, and an entry added by one is presumed jointly agreed
(Rob's standing instruction, 9 Sep 2026).

Transport: MCP stdio, newline-delimited JSON-RPC 2.0.
"""
import json
import os
import sys
import urllib.request
import urllib.error

CONF = os.path.expanduser("~/.config/jarvis/health.env")
USER = os.environ.get("JARVIS_US_USER", "").strip().lower()


def load_conf():
    conf = {}
    with open(CONF) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                conf[k.strip()] = v.strip().strip('"').strip("'")
    return conf


def api(method, path, body=None):
    conf = load_conf()
    base = conf.get("TIDE_API_BASE", "http://192.168.1.16:3001") + "/api/family"
    req = urllib.request.Request(base + path, method=method)
    req.add_header("X-Jarvis-Key", conf["JARVIS_API_KEY"])
    req.add_header("X-Jarvis-User", USER)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data, timeout=15) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {"ok": True}


TOOLS = [
    {
        "name": "list_agreements",
        "description": "List every entry on the shared /us page (Rob and Aimee's written relationship agreements and limits), oldest first, with id, text, note, kind ('agreement', 'soft' = soft limit, 'hard' = hard limit, 'messy' = messy-list person neither plays with, 'interested' = interested-list person one of them has mentioned potential interest in, with 'who' = whose interest: 'rob', 'aimee' or 'both' for a couple they might play with together) and who added it.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "add_agreement",
        "description": "Add an agreement to the shared /us page. Either parent may add; an agreement added by one is presumed jointly agreed (they'll have talked first). No approval from the other is needed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The agreement itself, as one clear sentence."},
                "note": {"type": "string", "description": "Optional context or nuance shown under the agreement."},
                "kind": {"type": "string", "enum": ["agreement", "soft", "hard", "messy", "interested"], "description": "Entry type: 'agreement' (default), 'soft' = soft limit (approach with care, talk first), 'hard' = hard limit (absolute no), 'messy' = messy-list entry (text is the person's name; someone neither parent plays with), 'interested' = interested-list entry (text is the person's name; someone one parent has mentioned potential interest in)."},
                "who": {"type": "string", "enum": ["rob", "aimee", "both"], "description": "For kind 'interested' only: whose interest it is. 'both' means a couple Rob and Aimee might play with together. Defaults to the person adding it."},
            },
            "required": ["text"],
            "additionalProperties": False,
        },
    },
    {
        "name": "edit_agreement",
        "description": "Reword an existing /us agreement (text and/or note) by id. Either parent may edit any entry, regardless of who added it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "The agreement id (from list_agreements)."},
                "text": {"type": "string"},
                "note": {"type": ["string", "null"], "description": "New note, or null to clear it."},
                "kind": {"type": "string", "enum": ["agreement", "soft", "hard", "messy", "interested"], "description": "Reclassify the entry: 'agreement', 'soft' (soft limit), 'hard' (hard limit), 'messy' (messy list) or 'interested' (interested list)."},
                "who": {"type": "string", "enum": ["rob", "aimee", "both"], "description": "For kind 'interested' only: whose interest it is ('both' = a couple they might play with together)."},
            },
            "required": ["id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "remove_agreement",
        "description": "Remove an agreement from the shared /us page by id. Either parent may remove any entry; the removal reflects a conversation they'll have had.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string", "description": "The agreement id (from list_agreements)."}},
            "required": ["id"],
            "additionalProperties": False,
        },
    },
]


def call_tool(name, args):
    if name == "list_agreements":
        return api("GET", "/enm")
    if name == "add_agreement":
        body = {"text": args["text"]}
        if args.get("note"):
            body["note"] = args["note"]
        if args.get("kind"):
            body["kind"] = args["kind"]
        if args.get("who"):
            body["who"] = args["who"]
        return api("POST", "/enm", body)
    if name == "edit_agreement":
        body = {}
        if "text" in args:
            body["text"] = args["text"]
        if "note" in args:
            body["note"] = args["note"]
        if "kind" in args:
            body["kind"] = args["kind"]
        if "who" in args:
            body["who"] = args["who"]
        return api("PATCH", "/enm/" + str(args["id"]), body)
    if name == "remove_agreement":
        return api("DELETE", "/enm/" + str(args["id"]))
    raise ValueError("unknown tool: " + name)


def reply(msg_id, result=None, error=None):
    out = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        out["error"] = error
    else:
        out["result"] = result
    sys.stdout.write(json.dumps(out) + "\n")
    sys.stdout.flush()


def main():
    if not USER:
        sys.stderr.write("us_mcp: JARVIS_US_USER not set\n")
        sys.exit(1)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        method = msg.get("method", "")
        msg_id = msg.get("id")
        if msg_id is None:  # notification (e.g. notifications/initialized)
            continue
        if method == "initialize":
            reply(msg_id, {
                "protocolVersion": msg.get("params", {}).get("protocolVersion", "2024-11-05"),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "us", "version": "1.0.0"},
            })
        elif method == "tools/list":
            reply(msg_id, {"tools": TOOLS})
        elif method == "tools/call":
            params = msg.get("params", {})
            try:
                result = call_tool(params.get("name"), params.get("arguments") or {})
                reply(msg_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]})
            except urllib.error.HTTPError as e:
                detail = e.read().decode(errors="replace")
                reply(msg_id, {"content": [{"type": "text", "text": f"API error {e.code}: {detail}"}], "isError": True})
            except Exception as e:
                reply(msg_id, {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True})
        elif method == "ping":
            reply(msg_id, {})
        else:
            reply(msg_id, error={"code": -32601, "message": "method not found: " + method})


if __name__ == "__main__":
    main()
