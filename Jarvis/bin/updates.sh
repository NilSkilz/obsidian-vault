#!/usr/bin/env bash
# Jarvis fleet updates — Home Assistant (add-ons/core/OS), all Debian LXCs, Proxmox host.
#
#   updates.sh check      report available updates, change nothing
#   updates.sh apply      apply everything. Never reboots anything itself, with one
#                         designed exception: `ha os update` reboots the HAOS VM.
#   updates.sh heartbeat  daily-throttled apply for the heartbeat cron (stamp file)
#
# Output is plain text for the heartbeat model to summarise. Lines starting with
# "NEEDS-ROB:" are things a human must look at (failures, pending reboots).
set -u

HA_SSH="ssh -n -o ConnectTimeout=10 -o BatchMode=yes -i $HOME/.ssh/ha-root root@192.168.1.4"
PVE_SSH="ssh -n -o ConnectTimeout=10 -o BatchMode=yes proxmox"
STAMP="$HOME/.local/state/jarvis-updates.stamp"
APT_OPTS='-y -qq -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold'

mode="${1:-check}"

ha_json() { $HA_SSH "ha $1 --raw-json" 2>/dev/null; }

check_ha() {
  local core os addons
  core=$(ha_json "core info") || { echo "NEEDS-ROB: cannot reach HAOS over SSH"; return 1; }
  os=$(ha_json "os info")
  addons=$(ha_json "addons")
  echo "$core"   | jq -r '.data | "ha-core: \(.version) -> \(.version_latest) (update: \(.update_available))"'
  echo "$os"     | jq -r '.data | "ha-os: \(.version) -> \(.version_latest) (update: \(.update_available))"'
  echo "$addons" | jq -r '.data.addons[] | select(.update_available) | "ha-addon: \(.slug) \(.version) -> \(.version_latest)"'
}

apply_ha() {
  local addons slug
  addons=$(ha_json "addons" | jq -r '.data.addons[] | select(.update_available) | .slug')
  for slug in $addons; do
    echo "updating ha-addon $slug..."
    $HA_SSH "ha addons update --backup $slug" >/dev/null 2>&1 \
      && echo "ha-addon $slug: updated" || echo "NEEDS-ROB: ha-addon $slug update failed"
  done
  if ha_json "core info" | jq -e '.data.update_available' >/dev/null; then
    echo "updating ha-core (partial backup first, core restarts itself)..."
    $HA_SSH "ha core update --backup" >/dev/null 2>&1 \
      && echo "ha-core: updated to $(ha_json "core info" | jq -r .data.version)" \
      || echo "NEEDS-ROB: ha-core update failed"
  fi
  if ha_json "os info" | jq -e '.data.update_available' >/dev/null; then
    echo "updating ha-os (HAOS VM will reboot itself, ~2 min)..."
    if $HA_SSH "ha os update" >/dev/null 2>&1; then
      echo "ha-os: update applied, waiting for the VM to come back..."
      local i
      for i in $(seq 1 30); do
        sleep 10
        if ha_json "core info" >/dev/null 2>&1; then
          echo "ha-os: VM back up"
          return 0
        fi
      done
      echo "NEEDS-ROB: HAOS VM not reachable 5 min after the OS update"
    else
      echo "NEEDS-ROB: ha-os update failed"
    fi
  fi
}

lxc_ids() { $PVE_SSH "pct list" | awk 'NR>1 && $2=="running" {print $1" "$NF}'; }

check_lxc() {
  local id name n
  while read -r id name; do
    n=$($PVE_SSH "pct exec $id -- bash -c 'apt-get update -qq >/dev/null 2>&1; apt-get -s upgrade 2>/dev/null | grep -c ^Inst; true'") || n="?"
    echo "lxc $id ($name): $n packages upgradable"
  done < <(lxc_ids)
}

apply_lxc() {
  local id name
  while read -r id name; do
    if $PVE_SSH "pct exec $id -- bash -c 'apt-get update -qq >/dev/null 2>&1; DEBIAN_FRONTEND=noninteractive apt-get $APT_OPTS upgrade >/dev/null 2>&1'"; then
      echo "lxc $id ($name): upgraded"
    else
      echo "NEEDS-ROB: lxc $id ($name) apt upgrade failed"
    fi
  done < <(lxc_ids)
}

check_host() {
  local n
  n=$($PVE_SSH "apt-get update -qq >/dev/null 2>&1; apt-get -s dist-upgrade 2>/dev/null | grep -c ^Inst; true") || n="?"
  echo "proxmox host: $n packages upgradable"
  $PVE_SSH "test -f /var/run/reboot-required" 2>/dev/null \
    && echo "NEEDS-ROB: proxmox host has a pending reboot (kernel update); not rebooting it myself"
  return 0
}

apply_host() {
  if $PVE_SSH "apt-get update -qq >/dev/null 2>&1; DEBIAN_FRONTEND=noninteractive apt-get $APT_OPTS dist-upgrade >/dev/null 2>&1"; then
    echo "proxmox host: upgraded"
  else
    echo "NEEDS-ROB: proxmox host dist-upgrade failed"
  fi
  $PVE_SSH "test -f /var/run/reboot-required" 2>/dev/null \
    && echo "NEEDS-ROB: proxmox host wants a reboot after updates; not rebooting it myself"
  return 0
}

run_check() { check_host; check_lxc; check_ha; }

run_apply() {
  echo "== apply $(date -Iseconds) =="
  apply_host
  apply_lxc
  apply_ha
  echo "== post-apply state =="
  run_check
  echo "note: Plausible runs as a Docker compose stack (CT 111); apt does not update its images."
}

case "$mode" in
  check) run_check ;;
  apply) run_apply ;;
  heartbeat)
    mkdir -p "$(dirname "$STAMP")"
    if [ -f "$STAMP" ] && [ "$(( $(date +%s) - $(stat -c %Y "$STAMP") ))" -lt 72000 ]; then
      echo "updates: already ran in the last 20h, skipping"
      exit 0
    fi
    touch "$STAMP"
    run_apply
    ;;
  *) echo "usage: updates.sh check|apply|heartbeat"; exit 1 ;;
esac
