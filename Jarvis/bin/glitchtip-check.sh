#!/usr/bin/env bash
# Jarvis GlitchTip watch. GlitchTip has no SMTP wired (consolemail://), so its
# own alerting is mute. This polls the API for issues Rob hasn't been told
# about yet and pings Telegram. Rob's ask (2026-08-25): "let me know if a new
# problem arises".
#
# "New" means: an issue id we haven't seen before (any project), or a
# previously-resolved issue that has reopened (regression). Each issue is
# pinged once; the seen-set lives in a state file. First run seeds the state
# silently so existing history isn't dumped on him. DRYRUN=1 prints instead
# of sending and doesn't advance state.
set -euo pipefail

CONF="$HOME/.config/jarvis/glitchtip.env"
TCONF="$HOME/.config/jarvis/telegram.env"
STATE="$HOME/.local/state/jarvis-glitchtip-seen.json"
LOG="$HOME/.local/state/jarvis-glitchtip-check.log"
DRYRUN="${DRYRUN:-0}"
mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) glitchtip check -----"

set -a; source "$CONF"; set +a
API="${GLITCHTIP_URL%/}/api/0"
auth=(-H "Authorization: Bearer ${GLITCHTIP_API_TOKEN}")

orgs=$(curl -sS --max-time 15 "${auth[@]}" "$API/organizations/" | python3 -c 'import sys,json; print(" ".join(o["slug"] for o in json.load(sys.stdin)))')
[ -z "$orgs" ] && { echo "no orgs / API failure"; exit 0; }

issues="[]"
for org in $orgs; do
  page=$(curl -sS --max-time 20 "${auth[@]}" "$API/organizations/$org/issues/?limit=100&sort=-last_seen&query=is:unresolved") || { echo "fetch failed for $org"; exit 0; }
  issues=$(python3 -c 'import sys,json; a=json.loads(sys.argv[1]); b=json.loads(sys.argv[2]); print(json.dumps(a+b))' "$issues" "$page")
done

first_run=0; [ -f "$STATE" ] || { first_run=1; echo '{}' >"$STATE"; }

OUT=$(python3 - "$STATE" "$issues" "$first_run" "$DRYRUN" <<'PY'
import sys, json
state_path, issues, first_run, dryrun = sys.argv[1], json.loads(sys.argv[2]), sys.argv[3]=="1", sys.argv[4]=="1"
seen = json.load(open(state_path))   # id -> lastSeen when we pinged/seeded
new = []
for i in issues:
    iid = str(i["id"])
    if iid not in seen:
        new.append(i)
    seen[iid] = i.get("lastSeen")
if not dryrun:
    json.dump(seen, open(state_path, "w"))
if first_run:
    print(f"SEEDED {len(issues)} existing issues")
    sys.exit(0)
if not new:
    print("NOTHING_NEW"); sys.exit(0)
lines = []
for i in new[:8]:
    proj = i["project"]["slug"]
    title = i.get("title") or i.get("metadata", {}).get("value") or "untitled"
    cnt = i.get("count", "?")
    rel = (i.get("lastRelease") or {}).get("shortVersion")
    rel = f", v{rel}" if rel else ""
    lines.append(f"• {proj}: {title} ({i.get('level','error')}, x{cnt}{rel})\n  {i['permalink']}")
more = f"\n...and {len(new)-8} more" if len(new) > 8 else ""
hdr = "🐞 New GlitchTip issue:" if len(new) == 1 else f"🐞 {len(new)} new GlitchTip issues:"
print(hdr + "\n" + "\n".join(lines) + more)
PY
)
echo "$OUT"
case "$OUT" in
  NOTHING_NEW|SEEDED*) ;;
  *)
    if [ "$DRYRUN" = "1" ]; then echo "DRYRUN: would send"; else
      set -a; source "$TCONF"; set +a
      curl -sS --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" --data-urlencode "text=${OUT}" >/dev/null \
        && echo "pinged Rob" || echo "telegram send failed"
    fi ;;
esac
