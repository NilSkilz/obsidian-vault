#!/usr/bin/env python3
"""Scoped MCP server for shared household tools: family calendar + household Todoist.

Attached by bridge.py to Aimee's Telegram sessions (Rob's standing instruction,
9 Sep 2026: the household keys are shared, she can do what he does). Her
sessions have no Bash and can't read ~/.config, so this server holds the keys
and exposes a fixed toolset. What it deliberately does NOT expose:

  - Todoist project "Wishlist" (private, never shared): invisible to every
    tool here. Listing skips it, its tasks are filtered out, adding to it or
    completing/rescheduling its tasks is refused.
  - Calendars other than "Shared Home Calendar", "Logan", "Dexter"
    (LimeNinja and the broken new-format ones stay Rob's).
  - Rob's email, Slack, code, servers: not here at all.

Transport: MCP stdio, newline-delimited JSON-RPC 2.0 (same shape as us_mcp.py).
"""
import json
import os
import re
import sys
import uuid
import base64
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, "/data/memory/Jarvis/bin")
import calendar_ics  # reuse the ICS parser (parse_events / occurs_on)

LONDON = ZoneInfo("Europe/London")
CALDAV = "https://caldav.icloud.com"
ALLOWED_CALENDARS = ["Shared Home Calendar", "Logan", "Dexter"]
DEFAULT_CALENDAR = "Shared Home Calendar"
BLOCKED_PROJECTS = {"wishlist"}
TODOIST_API = "https://api.todoist.com/api/v1"
USER = os.environ.get("JARVIS_FAMILY_USER", "family").strip().lower()


def load_env(name):
    conf = {}
    with open(os.path.expanduser(f"~/.config/jarvis/{name}")) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                conf[k.strip()] = v.strip().strip('"').strip("'")
    return conf


# ---------- calendar (iCloud CalDAV) ----------

def caldav_request(method, path, body=None, headers=None):
    conf = load_env("icloud.env")
    auth = base64.b64encode(f"{conf['ICLOUD_USER']}:{conf['ICLOUD_APP_PASSWORD']}".encode()).decode()
    req = urllib.request.Request(CALDAV + path, method=method)
    req.add_header("Authorization", "Basic " + auth)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    data = body.encode() if isinstance(body, str) else body
    with urllib.request.urlopen(req, data, timeout=30) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


_calendars = None  # {display name: href}, discovered once per process


def calendars():
    global _calendars
    if _calendars is not None:
        return _calendars
    _, body = caldav_request(
        "PROPFIND", "/", headers={"Depth": "0", "Content-Type": "text/xml"},
        body='<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:current-user-principal/></d:prop></d:propfind>')
    principal = re.search(r"<href[^>]*>(/\d+/principal/)</href>", body).group(1)
    home = principal.rsplit("principal/", 1)[0] + "calendars/"
    _, body = caldav_request(
        "PROPFIND", home, headers={"Depth": "1", "Content-Type": "text/xml"},
        body='<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:displayname/></d:prop></d:propfind>')
    found = {}
    root = ET.fromstring(body)
    for resp in root.iter("{DAV:}response"):
        href = resp.findtext("{DAV:}href", "")
        name = (resp.findtext(".//{DAV:}displayname") or "").strip()
        if name in ALLOWED_CALENDARS and href != home:
            found[name] = href
    _calendars = found
    return found


def resolve_calendar(name):
    cals = calendars()
    if not name:
        name = DEFAULT_CALENDAR
    for cal_name, href in cals.items():
        if cal_name.lower() == name.strip().lower():
            return cal_name, href
    raise ValueError(f"unknown calendar '{name}'; available: {', '.join(cals)}")


def calendar_events(start, end=None):
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end) if end else start_d
    if end_d < start_d:
        start_d, end_d = end_d, start_d
    if (end_d - start_d).days > 31:
        raise ValueError("range too large, max 31 days")
    # iCloud's time-range filter can miss old recurring masters, so query a
    # wide window and let occurs_on() decide per day, like the ICS feed path.
    t0 = datetime(start_d.year, start_d.month, start_d.day, tzinfo=LONDON).astimezone(timezone.utc)
    t1 = (datetime(end_d.year, end_d.month, end_d.day, tzinfo=LONDON) + timedelta(days=1)).astimezone(timezone.utc)
    query = f'''<?xml version="1.0"?>
<c:calendar-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
  <d:prop><c:calendar-data/></d:prop>
  <c:filter><c:comp-filter name="VCALENDAR"><c:comp-filter name="VEVENT">
    <c:time-range start="{t0.strftime('%Y%m%dT%H%M%SZ')}" end="{t1.strftime('%Y%m%dT%H%M%SZ')}"/>
  </c:comp-filter></c:comp-filter></c:filter>
</c:calendar-query>'''
    out = []
    for cal_name, href in calendars().items():
        _, body = caldav_request("REPORT", href, body=query,
                                 headers={"Depth": "1", "Content-Type": "text/xml"})
        root = ET.fromstring(body)
        events = []
        for node in root.iter("{urn:ietf:params:xml:ns:caldav}calendar-data"):
            if node.text:
                events += calendar_ics.parse_events(node.text)
        d = start_d
        while d <= end_d:
            for ev in events:
                try:
                    if ev.get("summary") and calendar_ics.occurs_on(ev, d):
                        dtstart = ev["dtstart"]
                        out.append({
                            "date": d.isoformat(),
                            "time": "all day" if ev.get("all_day") else dtstart.strftime("%H:%M"),
                            "title": ev["summary"],
                            "calendar": cal_name,
                            "uid": ev.get("uid", ""),
                        })
                except Exception:
                    continue
            d += timedelta(days=1)
    out.sort(key=lambda e: (e["date"], e["time"] == "all day" and "00:00" or e["time"]))
    return {"events": out} if out else {"events": [], "note": "nothing on the shared calendars in that range"}


def ics_escape(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


VTIMEZONE = "\r\n".join([
    "BEGIN:VTIMEZONE", "TZID:Europe/London",
    "BEGIN:DAYLIGHT", "TZOFFSETFROM:+0000", "TZOFFSETTO:+0100", "TZNAME:BST",
    "DTSTART:19700329T010000", "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU", "END:DAYLIGHT",
    "BEGIN:STANDARD", "TZOFFSETFROM:+0100", "TZOFFSETTO:+0000", "TZNAME:GMT",
    "DTSTART:19701025T020000", "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU", "END:STANDARD",
    "END:VTIMEZONE"])


def calendar_add(args):
    cal_name, href = resolve_calendar(args.get("calendar"))
    d = date.fromisoformat(args["date"])
    uid = str(uuid.uuid4()).upper()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # Timed events go in as local wall-clock with a TZID (like the phone writes
    # them); the ICS parser reads times naively, so UTC-Z times would display
    # an hour off in summer.
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Jarvis//household//EN",
             VTIMEZONE,
             "BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp}",
             f"SUMMARY:{ics_escape(args['title'])}"]
    if args.get("start_time"):
        h, m = map(int, args["start_time"].split(":"))
        start_dt = datetime(d.year, d.month, d.day, h, m)
        if args.get("end_time"):
            eh, em = map(int, args["end_time"].split(":"))
            end_dt = datetime(d.year, d.month, d.day, eh, em)
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
        else:
            end_dt = start_dt + timedelta(hours=1)
        lines.append("DTSTART;TZID=Europe/London:" + start_dt.strftime("%Y%m%dT%H%M%S"))
        lines.append("DTEND;TZID=Europe/London:" + end_dt.strftime("%Y%m%dT%H%M%S"))
    else:
        lines.append("DTSTART;VALUE=DATE:" + d.strftime("%Y%m%d"))
        lines.append("DTEND;VALUE=DATE:" + (d + timedelta(days=1)).strftime("%Y%m%d"))
    if args.get("location"):
        lines.append(f"LOCATION:{ics_escape(args['location'])}")
    if args.get("notes"):
        lines.append(f"DESCRIPTION:{ics_escape(args['notes'])}")
    lines += ["END:VEVENT", "END:VCALENDAR"]
    status, _ = caldav_request("PUT", f"{href}{uid}.ics", body="\r\n".join(lines) + "\r\n",
                               headers={"Content-Type": "text/calendar; charset=utf-8",
                                        "If-None-Match": "*"})
    return {"ok": status in (200, 201, 204), "uid": uid, "calendar": cal_name,
            "summary": f"added '{args['title']}' on {args['date']}"
                       + (f" at {args['start_time']}" if args.get("start_time") else " (all day)")}


def calendar_remove(args):
    uid = args["uid"].strip()
    if not re.fullmatch(r"[A-Za-z0-9@._-]+", uid):
        raise ValueError("that doesn't look like an event uid")
    for cal_name, href in calendars().items():
        try:
            status, _ = caldav_request("DELETE", f"{href}{uid}.ics")
            if status in (200, 204):
                return {"ok": True, "removed_from": cal_name}
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
    return {"ok": False, "error": "no event with that uid on the shared calendars"}


# ---------- Todoist (household projects, Wishlist walled off) ----------

def todoist(method, path, body=None, query=None):
    conf = load_env("todoist.env")
    url = TODOIST_API + path
    if query:
        from urllib.parse import urlencode
        url += "?" + urlencode(query)
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", "Bearer " + conf["TODOIST_TOKEN"])
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    elif method != "GET":
        data = b""  # bodyless POST without Content-Length gets 503'd by their gateway
    with urllib.request.urlopen(req, data, timeout=20) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw.strip() else {"ok": True}


def todoist_projects():
    """Household projects only: the blocked ones (and their subtrees) never leave this function."""
    results = todoist("GET", "/projects").get("results", [])
    blocked_ids = set()
    for p in results:  # parents come before children in practice, but loop twice to be safe
        if p["name"].strip().lower() in BLOCKED_PROJECTS:
            blocked_ids.add(p["id"])
    for _ in range(3):
        for p in results:
            if p.get("parent_id") in blocked_ids:
                blocked_ids.add(p["id"])
    visible = [p for p in results if p["id"] not in blocked_ids]
    return visible, blocked_ids


def task_row(t):
    row = {"id": t["id"], "content": t["content"], "project_id": t.get("project_id")}
    if t.get("description"):
        row["description"] = t["description"]
    if t.get("due"):
        row["due"] = t["due"].get("date")
        if t["due"].get("is_recurring"):
            row["recurring"] = t["due"].get("string")
    return row


def todoist_list_tasks(args):
    visible, blocked_ids = todoist_projects()
    names = {p["id"]: p["name"] for p in visible}
    if args.get("project"):
        needle = args["project"].strip().lower()
        if needle in BLOCKED_PROJECTS:
            return {"error": "that list isn't shared"}
        matches = [p for p in visible if needle in p["name"].lower()]
        if not matches:
            return {"error": f"no project matching '{args['project']}'",
                    "projects": [p["name"] for p in visible]}
        query = f"##{matches[0]['name']}"
    else:
        query = args.get("query") or "overdue | today"
    res = todoist("GET", "/tasks/filter", query={"query": query})
    tasks = [t for t in res.get("results", []) if t.get("project_id") not in blocked_ids]
    out = []
    for t in tasks:
        row = task_row(t)
        row["project"] = names.get(t.get("project_id"), "Inbox")
        out.append(row)
    return {"query": query, "tasks": out}


def todoist_add_task(args):
    visible, _ = todoist_projects()
    body = {"content": args["content"]}
    if args.get("project"):
        needle = args["project"].strip().lower()
        if needle in BLOCKED_PROJECTS:
            return {"error": "that list isn't shared; pick a household project"}
        matches = [p for p in visible if needle in p["name"].lower()]
        if not matches:
            return {"error": f"no project matching '{args['project']}'",
                    "projects": [p["name"] for p in visible]}
        body["project_id"] = matches[0]["id"]
    if args.get("due"):
        body["due_string"] = args["due"]
    if args.get("description"):
        body["description"] = args["description"]
    t = todoist("POST", "/tasks", body=body)
    return {"ok": True, "task": task_row(t)}


def guard_task(task_id):
    _, blocked_ids = todoist_projects()
    t = todoist("GET", f"/tasks/{task_id}")
    if t.get("project_id") in blocked_ids:
        raise ValueError("that task isn't on a shared list")
    return t


def todoist_complete_task(args):
    t = guard_task(args["id"])
    todoist("POST", f"/tasks/{args['id']}/close")
    return {"ok": True, "completed": t["content"]}


def todoist_reschedule_task(args):
    t = guard_task(args["id"])
    todoist("POST", f"/tasks/{args['id']}", body={"due_string": args["due"]})
    return {"ok": True, "task": t["content"], "due": args["due"]}


# ---------- MCP plumbing ----------

TOOLS = [
    {"name": "calendar_list_events",
     "description": "List events on the shared family calendars (Shared Home Calendar, Logan, Dexter) for a date or date range. Dates are YYYY-MM-DD, times shown are UK local.",
     "inputSchema": {"type": "object", "properties": {
         "start": {"type": "string", "description": "First date, YYYY-MM-DD."},
         "end": {"type": "string", "description": "Last date inclusive, YYYY-MM-DD (max 31 days; omit for a single day)."},
     }, "required": ["start"], "additionalProperties": False}},
    {"name": "calendar_add_event",
     "description": "Add an event to a shared family calendar (default: Shared Home Calendar; also Logan or Dexter). All-day if no start_time. Times are UK local, HH:MM.",
     "inputSchema": {"type": "object", "properties": {
         "title": {"type": "string"},
         "date": {"type": "string", "description": "YYYY-MM-DD"},
         "start_time": {"type": "string", "description": "HH:MM, omit for all-day"},
         "end_time": {"type": "string", "description": "HH:MM, default one hour after start"},
         "calendar": {"type": "string", "description": "Shared Home Calendar (default), Logan, or Dexter"},
         "location": {"type": "string"},
         "notes": {"type": "string"},
     }, "required": ["title", "date"], "additionalProperties": False}},
    {"name": "calendar_remove_event",
     "description": "Remove an event from the shared family calendars by uid (from calendar_list_events or calendar_add_event).",
     "inputSchema": {"type": "object", "properties": {
         "uid": {"type": "string"},
     }, "required": ["uid"], "additionalProperties": False}},
    {"name": "todoist_list_projects",
     "description": "List the household Todoist projects (the shared task lists, e.g. Shopping List, Shared Todo).",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "todoist_list_tasks",
     "description": "List open household Todoist tasks. Give a project name, or a Todoist filter query (e.g. 'today', '7 days | overdue'); default is overdue + today across household lists.",
     "inputSchema": {"type": "object", "properties": {
         "project": {"type": "string", "description": "Project name (partial match ok)."},
         "query": {"type": "string", "description": "Todoist filter query, used when no project is given."},
     }, "additionalProperties": False}},
    {"name": "todoist_add_task",
     "description": "Add a task to a household Todoist list (e.g. put something on the Shopping List). Defaults to the Inbox if no project given.",
     "inputSchema": {"type": "object", "properties": {
         "content": {"type": "string", "description": "The task itself."},
         "project": {"type": "string", "description": "Project name (partial match ok), e.g. 'Shopping List'."},
         "due": {"type": "string", "description": "Natural-language due date, e.g. 'tomorrow', 'friday 5pm'."},
         "description": {"type": "string"},
     }, "required": ["content"], "additionalProperties": False}},
    {"name": "todoist_complete_task",
     "description": "Mark a household Todoist task done, by id (from todoist_list_tasks).",
     "inputSchema": {"type": "object", "properties": {
         "id": {"type": "string"},
     }, "required": ["id"], "additionalProperties": False}},
    {"name": "todoist_reschedule_task",
     "description": "Change a household Todoist task's due date, by id. Keeps recurrence intact when given a recurring due string.",
     "inputSchema": {"type": "object", "properties": {
         "id": {"type": "string"},
         "due": {"type": "string", "description": "Natural-language due date, e.g. 'tomorrow', 'next monday'."},
     }, "required": ["id", "due"], "additionalProperties": False}},
]


def call_tool(name, args):
    if name == "calendar_list_events":
        return calendar_events(args["start"], args.get("end"))
    if name == "calendar_add_event":
        return calendar_add(args)
    if name == "calendar_remove_event":
        return calendar_remove(args)
    if name == "todoist_list_projects":
        visible, _ = todoist_projects()
        return {"projects": [{"id": p["id"], "name": p["name"]} for p in visible]}
    if name == "todoist_list_tasks":
        return todoist_list_tasks(args)
    if name == "todoist_add_task":
        return todoist_add_task(args)
    if name == "todoist_complete_task":
        return todoist_complete_task(args)
    if name == "todoist_reschedule_task":
        return todoist_reschedule_task(args)
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
        if msg_id is None:
            continue
        if method == "initialize":
            reply(msg_id, {
                "protocolVersion": msg.get("params", {}).get("protocolVersion", "2024-11-05"),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "household", "version": "1.0.0"},
            })
        elif method == "tools/list":
            reply(msg_id, {"tools": TOOLS})
        elif method == "tools/call":
            params = msg.get("params", {})
            try:
                result = call_tool(params.get("name"), params.get("arguments") or {})
                reply(msg_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]})
            except urllib.error.HTTPError as e:
                detail = e.read().decode(errors="replace")[:500]
                reply(msg_id, {"content": [{"type": "text", "text": f"API error {e.code}: {detail}"}], "isError": True})
            except Exception as e:
                reply(msg_id, {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True})
        elif method == "ping":
            reply(msg_id, {})
        else:
            reply(msg_id, error={"code": -32601, "message": "method not found: " + method})


if __name__ == "__main__":
    main()
