#!/usr/bin/env bash
# Push a Jarvis ops snapshot (cron jobs, Claude usage, host vitals) to Tide's
# /api/jarvis/status for the parents-only /ops page. Runs from cron every 10 min.
#
#   tide-status.sh          gather + POST to Tide (CT 112)
#   tide-status.sh print    gather + pretty-print, no POST (debugging)
#
# Shared key lives in ~/.config/jarvis/tide-status.env (TIDE_STATUS_KEY=...),
# and the same value sits in /opt/mission-control/.env on CT 112 as
# JARVIS_STATUS_KEY. Endpoint is hit over LAN, not via Cloudflare.
set -euo pipefail
MODE="${1:-post}"
ENV_FILE="$HOME/.config/jarvis/tide-status.env"
[ -f "$ENV_FILE" ] && . "$ENV_FILE"
export TIDE_STATUS_KEY="${TIDE_STATUS_KEY:-}"
export TIDE_STATUS_URL="${TIDE_STATUS_URL:-http://192.168.1.16:3001/api/jarvis/status}"
export USAGE_JSON="$(/data/memory/Jarvis/bin/usage.sh json 2>/dev/null || echo '{}')"
export CRONTAB="$(crontab -l 2>/dev/null || true)"

exec python3 - "$MODE" <<'PY'
import datetime
import json
import os
import re
import shutil
import sys
import urllib.request

MODE = sys.argv[1]
FABLE_SWITCH_AT = 80  # keep in step with usage.sh

# ---- cron ----------------------------------------------------------------

DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']


def field_matches(field, value):
    for part in field.split(','):
        step = 1
        if '/' in part:
            part, s = part.split('/', 1)
            step = int(s)
        if part == '*':
            if value % step == 0:
                return True
        elif '-' in part:
            lo, hi = (int(x) for x in part.split('-', 1))
            if lo <= value <= hi and (value - lo) % step == 0:
                return True
        elif int(part) == value:
            return True
    return False


def cron_matches(fields, dt):
    minute, hour, dom, mon, dow = fields
    if not (field_matches(minute, dt.minute) and field_matches(hour, dt.hour)
            and field_matches(mon, dt.month)):
        return False
    # cron dow: 0 or 7 = Sunday; python weekday(): Mon=0.
    cdow = (dt.weekday() + 1) % 7
    ok_dom = field_matches(dom, dt.day)
    ok_dow = field_matches(dow.replace('7', '0'), cdow)
    # Standard cron: when BOTH dom and dow are restricted, either may match.
    if dom != '*' and dow != '*':
        return ok_dom or ok_dow
    return ok_dom and ok_dow


def next_run(schedule):
    if schedule.startswith('@'):
        return None
    fields = schedule.split()
    dt = datetime.datetime.now().replace(second=0, microsecond=0) + datetime.timedelta(minutes=1)
    for _ in range(8 * 24 * 60):
        if cron_matches(fields, dt):
            return dt.astimezone().isoformat()
        dt += datetime.timedelta(minutes=1)
    return None


def hourpart(hour):
    if hour == '*':
        return ''
    m = re.fullmatch(r'(\d+)-(\d+)(?:/(\d+))?', hour)
    if m:
        a, b, s = m.groups()
        rng = f'{int(a):02d}-{int(b):02d}h'
        return f'every {s}h, {rng}' if s else rng
    if ',' in hour:
        return hour + 'h'
    return None  # single hour: fold into the minute part as HH:MM


def humanize(schedule):
    try:
        return _humanize(schedule)
    except Exception:
        return schedule  # never let a odd schedule kill the whole push


def _humanize(schedule):
    if schedule == '@reboot':
        return 'on boot'
    if schedule.startswith('@'):
        return schedule
    try:
        minute, hour, dom, mon, dow = schedule.split()
    except ValueError:
        return schedule
    bits = []
    m = re.fullmatch(r'(?:\*|\d+-\d+)/(\d+)', minute)
    if m:
        bits.append(f'every {m.group(1)} min')
        hp = hourpart(hour)
        if hp is None:
            hp = f'{int(hour):02d}h'
        if hp:
            bits.append(hp)
    else:
        hp = hourpart(hour)
        if hp is None:  # single hour -> HH:MM
            bits.append(f'{int(hour):02d}:{int(minute):02d}')
        elif hp == '':
            bits.append(f'hourly at :{int(minute):02d}')
        else:
            bits.append(f'{hp} at :{int(minute):02d}')
    if dow != '*':
        m = re.fullmatch(r'(\d+)-(\d+)', dow)
        if m:
            bits.append(f'{DOW[int(m.group(1)) % 7]}-{DOW[int(m.group(2)) % 7]}')
        elif dow.isdigit():
            bits.append(DOW[int(dow) % 7])
        else:
            bits.append(dow)
    if dom != '*':
        bits.append(f'dom {dom}')
    return ', '.join(bits)


def job_name(command):
    if '/bridge/run.sh' in command:
        return 'telegram bridge'
    m = re.search(r'/([\w.-]+\.(?:sh|py|mjs))\b\s*([\w-]*)', command)
    if not m:
        return command.split()[0].rsplit('/', 1)[-1]
    name = m.group(1).rsplit('.', 1)[0]
    return f'{name} {m.group(2)}'.strip()


SCHED_RE = re.compile(r'^(@\w+|(?:[\d*,/-]+\s+){4}[\d*,/-]+)\s+(.+)$')


def parse_crontab(text):
    jobs, note = [], None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            note = None
            continue
        enabled = True
        if line.startswith('#'):
            body = line.lstrip('#').strip()
            if body.startswith('NOTIF-OFF'):
                body = body[len('NOTIF-OFF'):].strip()
                enabled = False
                line = body
            else:
                note = body
                continue
        m = SCHED_RE.match(line)
        if not m:
            continue
        schedule, command = m.groups()
        jobs.append({
            'name': job_name(command),
            'note': note,
            'schedule': schedule,
            'human': humanize(schedule),
            'next': next_run(schedule) if enabled else None,
            'enabled': enabled,
        })
        note = None
    return jobs

# ---- claude usage ---------------------------------------------------------


def parse_usage(data):
    out = {'session': None, 'weeklyAll': None, 'fable': None, 'extra': None, 'model': None}
    for lim in data.get('limits') or []:
        entry = {'pct': lim.get('percent'), 'resets': lim.get('resets_at')}
        kind = lim.get('kind')
        if kind == 'session':
            out['session'] = entry
        elif kind == 'weekly_all':
            out['weeklyAll'] = entry
        elif kind == 'weekly_scoped':
            name = ((lim.get('scope') or {}).get('model') or {}).get('display_name', '')
            if 'fable' in str(name).lower():
                out['fable'] = entry
    ex = data.get('extra_usage') or {}
    if ex.get('is_enabled'):
        dp = ex.get('decimal_places') or 2
        out['extra'] = {
            'enabled': True,
            'used': (ex.get('used_credits') or 0) / (10 ** dp),
            'cap': (ex.get('monthly_limit') or 0) / (10 ** dp),
            'currency': '£' if ex.get('currency') == 'GBP' else (ex.get('currency') or ''),
        }
    fable_pct = (out['fable'] or {}).get('pct')
    out['model'] = ('claude-opus-5' if fable_pct is not None and fable_pct >= FABLE_SWITCH_AT
                    else 'claude-fable-5')
    return out

# ---- vitals ---------------------------------------------------------------


def human_bytes(n):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024:
            return f'{n:.0f} {unit}'
        n /= 1024
    return f'{n:.1f} PB'


def vitals():
    load1, load5, load15 = os.getloadavg()
    mem = {}
    for line in open('/proc/meminfo'):
        k, v = line.split(':', 1)
        mem[k] = int(v.strip().split()[0])  # kB
    total, avail = mem['MemTotal'], mem.get('MemAvailable', 0)
    disk = shutil.disk_usage('/')
    up = float(open('/proc/uptime').read().split()[0])
    d, rem = divmod(int(up), 86400)
    h = rem // 3600
    return {
        'load1': round(load1, 2), 'load5': round(load5, 2), 'load15': round(load15, 2),
        'memUsedPct': round(100 * (total - avail) / total),
        'memTotalMb': round(total / 1024),
        'diskUsedPct': round(100 * disk.used / disk.total),
        'diskFree': human_bytes(disk.free),
        'uptime': f'{d}d {h}h' if d else f'{h}h',
    }


def bridge():
    log = os.path.expanduser('~/.local/state/jarvis-bridge/conversation.log')
    try:
        mtime = os.path.getmtime(log)
        return {'lastActivity': datetime.datetime.fromtimestamp(mtime).astimezone().isoformat()}
    except OSError:
        return {'lastActivity': None}

# ---- assemble + ship ------------------------------------------------------

try:
    usage = parse_usage(json.loads(os.environ.get('USAGE_JSON') or '{}'))
except Exception:
    usage = {}

status = {
    'generatedAt': datetime.datetime.now().astimezone().isoformat(),
    'host': 'jarvis LXC (192.168.1.11)',
    'cron': parse_crontab(os.environ.get('CRONTAB', '')),
    'usage': usage,
    'vitals': vitals(),
    'bridge': bridge(),
}

if MODE == 'print':
    print(json.dumps(status, indent=2))
    sys.exit(0)

key = os.environ.get('TIDE_STATUS_KEY')
if not key:
    sys.exit('TIDE_STATUS_KEY missing (expected in ~/.config/jarvis/tide-status.env)')
req = urllib.request.Request(
    os.environ['TIDE_STATUS_URL'],
    data=json.dumps(status).encode(),
    headers={'Content-Type': 'application/json', 'x-jarvis-key': key},
    method='POST',
)
with urllib.request.urlopen(req, timeout=15) as r:
    print(f'pushed ok ({r.status})')
PY
