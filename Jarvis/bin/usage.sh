#!/usr/bin/env bash
# Claude plan usage, straight from the OAuth usage endpoint (same numbers as
# the claude.ai usage page). Uses the CLI's own token from ~/.claude/.credentials.json.
#
#   usage.sh summary   multi-line human summary (for /stats on Telegram)
#   usage.sh brief     one-line data string (embedded in the evening briefing)
#   usage.sh model     prints the chat model the bridge should use right now:
#                      claude-fable-5 normally, claude-opus-5 once the Fable
#                      weekly limit crosses FABLE_SWITCH_AT. NEVER fails: on any
#                      error it prints the default model so the bridge keeps working.
#   usage.sh json      raw endpoint JSON
set -euo pipefail
MODE="${1:-summary}"

exec python3 - "$MODE" <<'PY'
import datetime
import json
import pathlib
import sys
import urllib.request

MODE = sys.argv[1]
CRED = pathlib.Path.home() / ".claude/.credentials.json"
URL = "https://api.anthropic.com/api/oauth/usage"
DEFAULT_MODEL = "claude-fable-5"
FALLBACK_MODEL = "claude-opus-5"
FABLE_SWITCH_AT = 80   # % of the Fable weekly limit at which the bridge downshifts to Opus


def fetch():
    tok = json.loads(CRED.read_text())["claudeAiOauth"]["accessToken"]
    req = urllib.request.Request(URL, headers={
        "Authorization": f"Bearer {tok}",
        "anthropic-beta": "oauth-2025-04-20",
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def parse(data):
    out = {"session": None, "weekly_all": None, "fable": None}
    for lim in data.get("limits") or []:
        entry = {"pct": lim.get("percent"), "resets": lim.get("resets_at")}
        kind = lim.get("kind")
        if kind == "session":
            out["session"] = entry
        elif kind == "weekly_all":
            out["weekly_all"] = entry
        elif kind == "weekly_scoped":
            name = ((lim.get("scope") or {}).get("model") or {}).get("display_name", "")
            if "fable" in str(name).lower():
                out["fable"] = entry
    out["extra"] = data.get("extra_usage") or {}
    return out


def when(iso):
    if not iso:
        return "?"
    dt = datetime.datetime.fromisoformat(iso).astimezone()
    today = datetime.datetime.now().astimezone().date()
    d = dt.date()
    if d == today:
        day = "today"
    elif d == today + datetime.timedelta(days=1):
        day = "tomorrow"
    else:
        day = dt.strftime("%a")
    return f"{dt.strftime('%H:%M')} {day}"


def pct(e):
    return "?" if not e or e.get("pct") is None else f"{e['pct']:.0f}%"


if MODE == "model":
    # Never break the bridge: any failure here means "carry on with the default".
    try:
        u = parse(fetch())
        fable = (u["fable"] or {}).get("pct")
        if fable is not None and fable >= FABLE_SWITCH_AT:
            print(FALLBACK_MODEL)
        else:
            print(DEFAULT_MODEL)
    except Exception:
        print(DEFAULT_MODEL)
    sys.exit(0)

data = fetch()

if MODE == "json":
    print(json.dumps(data, indent=2))
    sys.exit(0)

u = parse(data)
s, w, f = u["session"], u["weekly_all"], u["fable"]
fable_pct = (f or {}).get("pct")
model_note = (f"switched to Opus 5 (Fable at {pct(f)}, back under {FABLE_SWITCH_AT}% after reset)"
              if fable_pct is not None and fable_pct >= FABLE_SWITCH_AT
              else f"Fable 5 (auto-drops to Opus 5 at {FABLE_SWITCH_AT}% Fable weekly)")

if MODE == "brief":
    print(f"session {pct(s)} (resets {when((s or {}).get('resets'))}), "
          f"week all-models {pct(w)}, Fable {pct(f)} (both reset {when((w or {}).get('resets'))}); "
          f"chat model: {model_note}")
    sys.exit(0)

# summary
ex = u["extra"]
lines = [
    "\N{BAR CHART} Claude usage",
    f"Session: {pct(s)} (resets {when((s or {}).get('resets'))})",
    f"Week, all models: {pct(w)} (resets {when((w or {}).get('resets'))})",
    f"Week, Fable: {pct(f)}",
    f"Chat model: {model_note}",
]
if ex.get("is_enabled"):
    dp = ex.get("decimal_places") or 2
    used = (ex.get("used_credits") or 0) / (10 ** dp)
    cap = (ex.get("monthly_limit") or 0) / (10 ** dp)
    cur = "£" if ex.get("currency") == "GBP" else (ex.get("currency") or "")
    lines.append(f"Extra usage: {cur}{used:.2f} of {cur}{cap:.0f} cap")
print("\n".join(lines))
PY
