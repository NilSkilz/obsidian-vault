#!/usr/bin/env bash
# Jarvis Docker stack updates. `updates.sh` covers apt on the host, every LXC
# and HA, but five services run as Docker Compose stacks inside their LXCs and
# their images never get pulled by that routine (Proposals.md entry, 2026-07-09).
# This closes the gap: weekly `docker compose pull && up -d` per stack, health
# check after, Telegram only if something breaks or needs Rob.
#
# Safety model: every stack is either pinned to an exact tag (Plausible) or to a
# major (GlitchTip :6, Kuma :1), so a pull is patch/minor only and can't jump a
# major unattended. Vaultwarden and Paperless track :latest deliberately (both
# handle their own migrations, and a stale Vaultwarden breaks the mobile app,
# see Infrastructure.md). Plausible majors surface as a NEEDS-ROB line when the
# upstream latest release differs from the pinned tag.
#
# Usage: docker-updates.sh [check|apply]   (default apply). DRYRUN=1 = check.
set -uo pipefail

MODE="${1:-apply}"; [ "${DRYRUN:-0}" = "1" ] && MODE=check
PVE_SSH="ssh -n -o ConnectTimeout=10 -o BatchMode=yes proxmox"
LOG="$HOME/.local/state/jarvis-docker-updates.log"
TCONF="$HOME/.config/jarvis/telegram.env"
VAULT="/data/memory"
mkdir -p "$(dirname "$LOG")"
exec > >(tee -a "$LOG") 2>&1
echo "----- $(date -Iseconds) docker updates ($MODE) -----"

# CTID:dir:name:pinned-image-to-watch (or -)
STACKS=(
  "111:/opt/plausible-ce:Plausible:ghcr.io/plausible/community-edition"
  "106:/opt/glitchtip:GlitchTip:-"
  "113:/opt/vaultwarden:Vaultwarden:-"
  "114:/opt/paperless:Paperless:-"
  "115:/opt/uptime-kuma:Uptime Kuma:-"
)

PROBLEMS=()
SUMMARY=()

for entry in "${STACKS[@]}"; do
  IFS=: read -r ct dir name watch <<<"$entry"
  # image ids before, so we can tell whether anything actually changed
  before=$($PVE_SSH "pct exec $ct -- sh -c 'cd $dir && docker compose images -q 2>/dev/null | sort'" 2>/dev/null) || {
    PROBLEMS+=("$name (CT $ct): cannot reach stack"); continue; }

  if [ "$MODE" = "apply" ]; then
    if ! $PVE_SSH "pct exec $ct -- sh -c 'cd $dir && docker compose pull -q && docker compose up -d --remove-orphans'" >/dev/null 2>&1; then
      PROBLEMS+=("$name (CT $ct): compose pull/up FAILED"); continue
    fi
    sleep 20
  fi

  after=$($PVE_SSH "pct exec $ct -- sh -c 'cd $dir && docker compose images -q 2>/dev/null | sort'" 2>/dev/null)
  # health: every service must be running (and healthy if it has a healthcheck).
  # Containers report "starting" for up to a couple of minutes after a fresh
  # image (Paperless runs migrations first), so poll rather than snapshot.
  for _try in $(seq 1 12); do
    bad=$($PVE_SSH "pct exec $ct -- sh -c 'cd $dir && docker compose ps -a --format \"{{.Name}} {{.State}} {{.Health}}\"'" 2>/dev/null \
          | awk '$2!="running" || ($3!="" && $3!="healthy") {print}')
    [ -z "$bad" ] && break
    echo "$bad" | grep -q starting || break   # a real failure, stop waiting
    [ "$MODE" = "check" ] && break
    sleep 15
  done
  if [ -n "$bad" ]; then
    PROBLEMS+=("$name (CT $ct) unhealthy after update: $(echo "$bad" | tr '\n' ';')")
  fi
  if [ "$MODE" = "apply" ] && [ "$before" != "$after" ]; then
    SUMMARY+=("$name: images updated")
  else
    SUMMARY+=("$name: no change")
  fi
  # reclaim old image layers, quietly
  [ "$MODE" = "apply" ] && $PVE_SSH "pct exec $ct -- docker image prune -f" >/dev/null 2>&1

  # upstream major/minor watch for exact-pinned images
  if [ "$watch" != "-" ]; then
    pinned=$($PVE_SSH "pct exec $ct -- grep -ho \"$watch:[^ ]*\" $dir/compose.yml" 2>/dev/null | head -1 | sed 's/.*://')
    case "$watch" in
      ghcr.io/plausible/community-edition)
        latest=$(curl -sS --max-time 15 "https://api.github.com/repos/plausible/analytics/releases/latest" \
                 | python3 -c 'import sys,json; print(json.load(sys.stdin).get("tag_name",""))' 2>/dev/null) ;;
      *) latest="" ;;
    esac
    if [ -n "$latest" ] && [ -n "$pinned" ] && [ "$latest" != "$pinned" ]; then
      PROBLEMS+=("NEEDS-ROB: $name pinned at $pinned, upstream latest is $latest. Bump = edit the tag in $dir/compose.yml on CT $ct (git pull there first), then compose pull && up -d. Check the release notes for migrations.")
    fi
  fi
done

printf '%s\n' "${SUMMARY[@]}"
[ ${#PROBLEMS[@]} -gt 0 ] && printf 'PROBLEM: %s\n' "${PROBLEMS[@]}"

# daily log line (heartbeat style: short, only when something happened or broke)
if [ "$MODE" = "apply" ]; then
  today="$VAULT/Daily/$(date +%F).md"
  changed=$(printf '%s\n' "${SUMMARY[@]}" | grep -c "images updated")
  line="- $(date +%H:%M) docker-updates.sh: pulled all 5 Compose stacks (Plausible, GlitchTip, Vaultwarden, Paperless, Kuma); $changed updated, all healthy."
  [ ${#PROBLEMS[@]} -gt 0 ] && line="- $(date +%H:%M) docker-updates.sh: $(printf '%s; ' "${PROBLEMS[@]}")"
  if [ -f "$today" ]; then printf '%s\n' "$line" >>"$today"
  else printf '# %s (%s)\n\n## Work & Projects\n%s\n' "$(date +%F)" "$(date +%A)" "$line" >"$today"; fi
fi

if [ ${#PROBLEMS[@]} -gt 0 ] && [ "$MODE" = "apply" ] && [ -f "$TCONF" ]; then
  set -a; source "$TCONF"; set +a
  msg="🐳 Docker updates need a look:"$'\n'"$(printf '%s\n' "${PROBLEMS[@]}")"
  curl -sS --max-time 10 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" --data-urlencode "text=${msg}" >/dev/null || echo "telegram send failed"
fi
echo "----- $(date -Iseconds) done -----"
