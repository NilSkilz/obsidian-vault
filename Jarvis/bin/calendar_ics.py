#!/usr/bin/env python3
"""Minimal ICS parser for a published iCloud calendar (read-only, stdlib only).
Handles single events and the recurrence patterns actually present in Rob's
family calendar (YEARLY birthdays, WEEKLY with UNTIL, basic MONTHLY/DAILY).
Not a full RFC5545 implementation, just enough for a daily briefing.

Usage: calendar_ics.py <ics_url> <YYYY-MM-DD> [YYYY-MM-DD ...]
Prints one line per event found, per date, to stdout as:
  <date>\t<HH:MM or "all day">\t<summary>
"""
import sys
import urllib.request
from datetime import date, datetime, timedelta

WEEKDAY_CODES = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


def unfold(raw):
    lines = raw.replace("\r\n", "\n").split("\n")
    out = []
    for line in lines:
        if line.startswith((" ", "\t")) and out:
            out[-1] += line[1:]
        else:
            out.append(line)
    return out


def parse_dt(value, params):
    value = value.strip()
    is_date_only = params.get("VALUE") == "DATE" or (len(value) == 8 and "T" not in value)
    if is_date_only:
        d = datetime.strptime(value, "%Y%m%d").date()
        return d, True
    value = value.rstrip("Z")
    dt = datetime.strptime(value[:15], "%Y%m%dT%H%M%S")
    return dt, False


def parse_prop_line(line):
    if ":" not in line:
        return None, {}, None
    head, value = line.split(":", 1)
    parts = head.split(";")
    name = parts[0]
    params = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k] = v
    return name, params, value


def parse_rrule(value):
    rule = {}
    for part in value.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            rule[k] = v
    return rule


def parse_events(text):
    events = []
    cur = None
    in_event = False
    for line in unfold(text):
        if line == "BEGIN:VEVENT":
            in_event = True
            cur = {"EXDATE": []}
            continue
        if line == "END:VEVENT":
            if cur:
                events.append(cur)
            in_event = False
            cur = None
            continue
        if not in_event:
            continue
        name, params, value = parse_prop_line(line)
        if name is None:
            continue
        if name == "DTSTART":
            cur["dtstart"], cur["all_day"] = parse_dt(value, params)
        elif name == "DTEND":
            cur["dtend"], _ = parse_dt(value, params)
        elif name == "SUMMARY":
            cur["summary"] = value.replace("\\,", ",").replace("\\;", ";")
        elif name == "RRULE":
            cur["rrule"] = parse_rrule(value)
        elif name == "EXDATE":
            try:
                exd, _ = parse_dt(value, params)
                cur["EXDATE"].append(exd.date() if isinstance(exd, datetime) else exd)
            except ValueError:
                pass
        elif name == "UID":
            cur["uid"] = value
    return events


def as_date(d):
    return d.date() if isinstance(d, datetime) else d


def occurs_on(ev, target):
    dtstart = ev.get("dtstart")
    if dtstart is None:
        return False
    start_date = as_date(dtstart)
    dtend = ev.get("dtend")
    end_date = as_date(dtend) if dtend is not None else start_date

    exdates = ev.get("EXDATE", [])
    if target in exdates:
        return False

    rrule = ev.get("rrule")
    if not rrule:
        span = max((end_date - start_date).days, 1) if ev.get("all_day") else 1
        return start_date <= target < start_date + timedelta(days=span) if ev.get("all_day") else start_date == target

    freq = rrule.get("FREQ")
    interval = int(rrule.get("INTERVAL", "1"))
    until = None
    if "UNTIL" in rrule:
        try:
            until, _ = parse_dt(rrule["UNTIL"], {})
            until = as_date(until)
        except ValueError:
            until = None
    count = rrule.get("COUNT")

    if target < start_date:
        return False
    if until and target > until:
        return False
    if count:
        # Without full expansion we can't cheaply bound COUNT-based series;
        # treat as unbounded but this is rare in practice for this calendar.
        pass

    if freq == "YEARLY":
        if (target.month, target.day) != (start_date.month, start_date.day):
            return False
        return (target.year - start_date.year) % interval == 0
    if freq == "WEEKLY":
        byday = rrule.get("BYDAY")
        if byday:
            codes = byday.split(",")
            if WEEKDAY_CODES[target.weekday()] not in codes:
                return False
        else:
            if target.weekday() != start_date.weekday():
                return False
        weeks_diff = (target - start_date).days // 7
        return weeks_diff % interval == 0
    if freq == "MONTHLY":
        if target.day != start_date.day:
            return False
        months_diff = (target.year - start_date.year) * 12 + (target.month - start_date.month)
        return months_diff >= 0 and months_diff % interval == 0
    if freq == "DAILY":
        days_diff = (target - start_date).days
        return days_diff >= 0 and days_diff % interval == 0
    return False


def main():
    if len(sys.argv) < 3:
        print("usage: calendar_ics.py <ics_url> <YYYY-MM-DD> [more dates...]", file=sys.stderr)
        sys.exit(1)
    url = sys.argv[1]
    targets = [datetime.strptime(a, "%Y-%m-%d").date() for a in sys.argv[2:]]

    req = urllib.request.Request(url, headers={"User-Agent": "jarvis-calendar/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        text = resp.read().decode("utf-8", errors="replace")

    events = parse_events(text)

    for target in targets:
        matches = []
        for ev in events:
            summary = ev.get("summary")
            if not summary:
                continue
            try:
                if occurs_on(ev, target):
                    matches.append(ev)
            except Exception:
                continue
        matches.sort(key=lambda e: (e.get("all_day", True), as_date(e["dtstart"])))
        for ev in matches:
            dtstart = ev["dtstart"]
            if ev.get("all_day"):
                when = "all day"
            else:
                when = dtstart.strftime("%H:%M")
            print(f"{target.isoformat()}\t{when}\t{ev['summary']}")


if __name__ == "__main__":
    main()
