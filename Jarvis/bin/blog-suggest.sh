#!/usr/bin/env bash
# Weekly Tethered content + SEO/AI-search review (Rob, 14 Sep 2026).
# Every Monday ~10:00: look at what shipped in the last week, run a light
# SEO / AI-search health check on the live site (tethered.me.uk), then
# 1) suggest ONE new blog post for the coming week, and
# 2) suggest concrete site updates that follow from last week's work.
# SUGGESTIONS ONLY. This never writes to the tethered repo or publishes
# anything; Rob decides what actually gets built.
#
# Mirrors self-learn.sh: cron -> agentic `claude -p` in the vault -> one
# Telegram summary. Full analysis is appended to
# Projects/Tethered/Blog & SEO Log.md so there's a durable record.
# DRYRUN=1 prints the summary instead of sending it.
set -uo pipefail

VAULT="/data/memory"
REPO="/home/jarvis/projects/tethered"
SITE="https://tethered.me.uk"
LOG="$HOME/.local/state/jarvis-blog-suggest.log"
CONF="$HOME/.config/jarvis/telegram.env"
CLAUDE_BIN="$(command -v claude || echo "$HOME/.local/bin/claude")"
DRYRUN="${DRYRUN:-0}"

mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) blog-suggest start -----"

send_tg() {
  set -a; source "$CONF"; set +a
  curl -s --max-time 15 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=${1:0:4000}" >/dev/null || echo "telegram send failed"
}

# Fresh view of the week's work. Fetch is nice-to-have; the local checkout is
# usually current because Jarvis commits to develop here.
git -C "$REPO" fetch origin develop --quiet 2>/dev/null || true
WEEKLOG="$(mktemp /tmp/jarvis-blog-suggest.XXXXXX)"
trap 'rm -f "$WEEKLOG" /tmp/jarvis-blog-suggest-err.$$' EXIT
git -C "$REPO" log --since="8 days ago" --date=short \
  --pretty='%ad %h %s' origin/develop 2>/dev/null > "$WEEKLOG" \
  || git -C "$REPO" log --since="8 days ago" --date=short \
       --pretty='%ad %h %s' develop > "$WEEKLOG" 2>/dev/null || true
echo "week's commits: $(grep -c . "$WEEKLOG" || echo 0)"

read -r -d '' PROMPT <<PROMPT_EOF || true
You are Jarvis, running the WEEKLY TETHERED CONTENT + SEO REVIEW (unattended, on a cron, Monday morning). Nobody is waiting while you work; do it properly, then produce one short Telegram summary at the end.

Tethered is Rob's BDSM safety check-in SaaS at $SITE (repo: $REPO, vault file: $VAULT/Projects/Tethered/overview.md). The strategy context: the paywall pivot (gate on partner-linking, retention over traffic) and the recent SEO push (blog + prerender pipeline, llms.txt for AI assistants).

Your job, in order:

1. CATCH UP on the last week's work:
   - The week's commits on develop are in the file $WEEKLOG (read it).
   - Existing blog posts live in $REPO/scripts/blog-posts/ (read the slugs/titles, skim front matter; do NOT reread every post in full).
   - Skim the last week of $VAULT/Daily/ logs for Tethered context the commits don't show.

2. SEO / AI-SEARCH HEALTH CHECK on the live site (read-only):
   - Fetch $SITE/sitemap.xml and $SITE/llms.txt. Cross-check: is every published blog post in both? Anything shipped last week missing from either?
   - Spot-check 2-3 key pages (home, one blog post, one feature/landing page) for title/meta description/H1 and internal links to the blog and signup.
   - Do 2-3 web searches for the questions Tethered's audience actually asks (BDSM safety check-in, safe call app, risk-aware kink tools etc). Note who ranks, and whether Tethered shows up. Think about AI-assistant answers as well as Google: would an LLM citing sources find and cite Tethered?

3. SUGGEST ONE new blog post for this week. Pick the highest-leverage topic given what searches show and what last week shipped. Give: proposed title, slug, the search queries / AI-assistant questions it targets, a 4-6 bullet outline, and one line on why this one now.

4. SUGGEST site updates that follow from last week's work: gaps found in step 2 (sitemap/llms.txt misses, weak metas, missing internal links), plus at most 2-3 broader improvements. Concrete and small; each one should be a single sitting of work.

Hard rules:
- READ-ONLY on the tethered repo and the live site. Do not commit, push, edit code, or publish anything. Suggestions only.
- Append your full analysis (dated ## $(date +%F) section: findings, the post pitch, the update list) to "$VAULT/Projects/Tethered/Blog & SEO Log.md" (create it with a one-line intro if missing), then commit AND push the vault per the CLAUDE.md workflow.
- No em dashes anywhere.
- Keep web fetches/searches modest (this runs weekly, it is a check-in, not an audit).

Your FINAL message must be ONLY the Telegram summary for Rob: the blog post pitch in 2-3 lines, then the top site updates as short bullets (lead with anything genuinely broken), warm and direct, mobile-friendly, no markdown headers or tables. That final message is the only thing sent to him.
PROMPT_EOF

cd "$VAULT"
SUMMARY="$(timeout 840 "$CLAUDE_BIN" -p "$PROMPT" --model claude-opus-5 --dangerously-skip-permissions 2>/tmp/jarvis-blog-suggest-err.$$)" || {
  echo "$(date -Iseconds) ERROR: claude invocation failed"
  cat /tmp/jarvis-blog-suggest-err.$$ || true
  send_tg "📝 Weekly blog/SEO review failed to run (claude error). Log: ~/.local/state/jarvis-blog-suggest.log"
  exit 0
}

echo "--- summary ---"
echo "$SUMMARY"
echo "---------------"

if [ "$DRYRUN" = "1" ]; then
  echo "DRYRUN: not sending"
else
  send_tg "📝 Weekly Tethered blog + SEO review

$SUMMARY"
fi
echo "----- $(date -Iseconds) blog-suggest end -----"
