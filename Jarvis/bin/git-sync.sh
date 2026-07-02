#!/usr/bin/env bash
# Nightly git sync for Rob's memory vault.
# Pulls (rebase) to reconcile edits from other machines, then commits and pushes any changes.
# Invoked by root cron. Also runnable by hand: bash /data/memory/Jarvis/bin/git-sync.sh
set -euo pipefail

VAULT="/data/memory"
LOG="/var/log/memory-git-sync.log"

# Non-interactive SSH so cron never hangs waiting on a prompt; fail fast instead.
export GIT_SSH_COMMAND="ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new"

# Send all output to the log.
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) sync start -----"

cd "$VAULT"

# Reconcile with the remote first. If the rebase can't proceed cleanly, back out
# and skip this run rather than committing conflict markers.
if ! git pull --rebase --autostash origin main; then
  echo "$(date -Iseconds) ERROR: pull/rebase failed, aborting rebase and skipping this run"
  git rebase --abort 2>/dev/null || true
  echo "----- $(date -Iseconds) sync aborted -----"
  exit 0
fi

git add -A

if git diff --cached --quiet; then
  echo "$(date -Iseconds) no changes, nothing to commit"
else
  git commit -m "auto: nightly memory sync $(date '+%Y-%m-%d')"
  if git push origin main; then
    echo "$(date -Iseconds) pushed"
  else
    echo "$(date -Iseconds) ERROR: push failed (committed locally, will retry next run)"
  fi
fi

echo "----- $(date -Iseconds) sync end -----"
