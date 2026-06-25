#!/usr/bin/env bash
# Daily git sync for obsidian vault — run by systemd timer
set -euo pipefail

VAULT="/home/rob/obsidian-vault"
LOG="/home/rob/.claude-code-hermit/state/git-sync.log"

cd "$VAULT"

# Pull first to avoid divergence
git pull --rebase --autostash origin main 2>&1 | tail -2

# Stage all changes
git add -A

# Commit only if there's something to commit
if git diff --cached --quiet; then
  echo "$(date -Iseconds) no changes" >> "$LOG"
else
  git commit -m "auto: daily sync $(date '+%Y-%m-%d')" 2>&1
  git push origin main 2>&1
  echo "$(date -Iseconds) pushed" >> "$LOG"
fi
