#!/usr/bin/env bash
# Weekly movie recommendations (Rob, 27 Sep 2026: "recommends cool movies once
# per week, based on what's in Plex for genre etc").
# Every Friday ~17:00: read the Plex movie library + watch history, build a
# taste profile, and Telegram Rob a short drop: a few unwatched gems already
# sitting in Plex, plus one or two "not in the library but right up your
# street" picks he can reply to and have me add to Radarr.
# RECOMMENDATIONS ONLY. Never adds anything to Radarr itself.
#
# Mirrors inspiration.sh: cron -> agentic `claude -p` in the vault -> one
# Telegram summary. DRYRUN=1 prints the summary instead of sending it.
set -uo pipefail

VAULT="/data/memory"
LOG="$HOME/.local/state/jarvis-movie-recs.log"
CONF="$HOME/.config/jarvis/telegram.env"
CLAUDE_BIN="$(command -v claude || echo "$HOME/.local/bin/claude")"
DRYRUN="${DRYRUN:-0}"

PLEX="http://192.168.1.3:32400"
PLEX_TOKEN="jLzjydWMj6xzykLFPyKp"

mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) movie-recs start -----"

send_tg() {
  set -a; source "$CONF"; set +a
  curl -s --max-time 15 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=${1:0:4000}" >/dev/null || echo "telegram send failed"
}

read -r -d '' PROMPT <<PROMPT_EOF || true
You are Jarvis, running the WEEKLY MOVIE RECOMMENDER (unattended, on a cron, Friday teatime). Rob asked for this standing job on 27 Sep 2026: once a week, recommend cool movies based on what is in Plex (genres, what gets watched). The drop lands just before the weekend so he can actually use it.

Data sources (Plex is on the LAN, token is fine to use in curl):

1. Movie library (786-ish titles). Pull it with:
   curl -s "$PLEX/library/sections/1/all?X-Plex-Token=$PLEX_TOKEN"
   Each Video element has title, year, Genre tags, rating/audienceRating, viewCount (present = watched), addedAt, lastViewedAt. It is big; pipe through grep/sed or python3 to extract what you need rather than reading raw XML into context.

2. Watch history (taste signal, newest first):
   curl -s "$PLEX/status/sessions/history/all?X-Plex-Token=$PLEX_TOKEN&sort=viewedAt:desc&X-Plex-Container-Size=200"
   Movies are librarySectionID="1" entries. TV (librarySectionID="2") still hints at taste.

3. Read "$VAULT/Jarvis/Movie Recs Log.md" first (may not exist yet) so you never repeat a previous week's picks.

Your job:

1. Build a quick taste profile: which genres/eras/directors actually get WATCHED (viewCount + history), not just hoarded. Note anything recently watched (e.g. a binge) worth riffing on.

2. Pick recommendations:
   - 2-3 "already in Plex, unwatched" gems (viewCount absent/0) that fit the taste profile. Ready to press play tonight.
   - 1-2 "not in the library" picks matched to taste (use your film knowledge; a quick web search to sanity-check is fine). Mark these clearly as not in Plex and tell him to reply if he wants them added to Radarr. Do NOT add anything to Radarr yourself.
   - Mix it up week to week: sometimes a deep cut, sometimes a crowd-pleaser for a family-sofa night. Rob lives with Aimee and two teenage boys (15 and 12), so where a pick is a good family-sofa shout, say so; assume the rest are for Rob (and maybe Aimee) after hours.

3. Append a dated "## $(date +%F)" section to "$VAULT/Jarvis/Movie Recs Log.md" listing this week's picks one line each (create the file with a one-line intro if missing), then commit AND push the vault per the CLAUDE.md workflow.

Hard rules:
- RECOMMENDATIONS ONLY. Nothing gets added, downloaded, deleted or changed in Plex/Radarr.
- Never recommend something already recommended in the log, and never recommend something as "in Plex" without checking it is actually there and unwatched.
- No em dashes anywhere.
- If the library genuinely has no fresh angle this week, fewer good picks beats padding.

Your FINAL message must be ONLY the Telegram drop for Rob: 3-5 picks, one or two lines each saying what it is and WHY it fits what he actually watches, clearly split between "in Plex now" and "want me to grab it?", warm and direct with real personality, mobile-friendly, no markdown headers or tables. That final message is the only thing sent to him.
PROMPT_EOF

cd "$VAULT"
SUMMARY="$(timeout 840 "$CLAUDE_BIN" -p "$PROMPT" --model claude-opus-5 --dangerously-skip-permissions 2>/tmp/jarvis-movie-recs-err.$$)" || {
  echo "$(date -Iseconds) ERROR: claude invocation failed"
  cat /tmp/jarvis-movie-recs-err.$$ || true
  rm -f /tmp/jarvis-movie-recs-err.$$
  send_tg "🎬 Weekly movie recs failed to run (claude error). Log: ~/.local/state/jarvis-movie-recs.log"
  exit 0
}
rm -f /tmp/jarvis-movie-recs-err.$$

echo "--- summary ---"
echo "$SUMMARY"
echo "---------------"

if [ "$DRYRUN" = "1" ]; then
  echo "DRYRUN: not sending"
else
  send_tg "🎬 Friday film drop

$SUMMARY"
fi
echo "----- $(date -Iseconds) movie-recs end -----"
