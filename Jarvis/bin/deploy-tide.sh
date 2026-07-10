#!/usr/bin/env bash
# One-command deploy of the live Tide site (family app "Tide", repo mission-control).
#
# Live at https://cracky.co.uk (also mc./tide.cracky.co.uk), served by CT 112
# (192.168.1.16) from /opt/mission-control via systemd `mission-control.service`,
# behind Nginx Proxy Manager. This box (jarvis LXC) only holds a DEV checkout at
# ~/projects/mission-control, so editing here does NOT change the live site.
#
# Workflow: commit + push to the deployed branch, then run this. It reaches CT 112
# through the Proxmox host (root, via pct exec) and runs /root/deploy-tide.sh there:
# pull -> build -> restart. ~10s. No SSH creds needed for the container itself.
#
# Usage: deploy-tide.sh [branch]   (default: feature/tide-build)
set -euo pipefail
BRANCH="${1:-feature/tide-build}"
echo "Deploying $BRANCH to CT 112 (cracky.co.uk)..."
ssh -i "$HOME/.ssh/proxmox-root" -o BatchMode=yes root@192.168.1.2 \
  "pct exec 112 -- /root/deploy-tide.sh $BRANCH"
echo "OK: $BRANCH is live at https://cracky.co.uk (hard-refresh to bust browser cache)"
