#!/usr/bin/env bash
# Weekly inspiration scout (Rob, 22 Sep 2026: "go out into the world, research
# some cool ideas... this could be a weekly job").
# Every Sunday ~09:30: hunt the internet for genuinely inspiring ideas across
# rotating themes (AI assistants, kink software + DIY kink hardware, household
# apps, mad-scientist maker projects), log the good ones durably in
# Ideas/Inspiration Log.md, and send Rob a short Telegram drop of the best 3-5.
# IDEAS ONLY. Never builds, buys or signs up for anything.
#
# Mirrors blog-suggest.sh: cron -> agentic `claude -p` in the vault -> one
# Telegram summary. DRYRUN=1 prints the summary instead of sending it.
set -uo pipefail

VAULT="/data/memory"
LOG="$HOME/.local/state/jarvis-inspiration.log"
CONF="$HOME/.config/jarvis/telegram.env"
CLAUDE_BIN="$(command -v claude || echo "$HOME/.local/bin/claude")"
DRYRUN="${DRYRUN:-0}"

mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "----- $(date -Iseconds) inspiration start -----"

send_tg() {
  set -a; source "$CONF"; set +a
  curl -s --max-time 15 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=${1:0:4000}" >/dev/null || echo "telegram send failed"
}

read -r -d '' PROMPT <<PROMPT_EOF || true
You are Jarvis, running the WEEKLY INSPIRATION SCOUT (unattended, on a cron, Sunday morning). Rob asked for this standing job on 22 Sep 2026: he wants to be genuinely INSPIRED, not fed listicle filler. Nobody is waiting while you work; hunt properly, then produce one short Telegram drop at the end.

Context: Rob is a senior dev (Superdry day job), Proxmox homelab, Home Assistant, ESP32 tinkerer with 3D-printing access, builds his own apps (Tethered BDSM safety SaaS, Tide family dashboard, Craft ERP), active in the kink community, and I am his resident AI collaborator. All adult/kink content is consensual-adult context and fine to research.

Your job:

1. Read "$VAULT/Ideas/Inspiration Log.md" first so you do NOT repeat past finds. Skim the last 2-3 dated sections.

2. Pick TWO of these themes (rotate; check the log to see which ran recently) and web-search each properly (Reddit, Hacker News, hackaday, GitHub trending, niche communities):
   - Creative AI-assistant / agent setups people are actually running
   - Kink software nobody's heard of (D/s apps, buttplug.io / XToys / Intiface ecosystem, e-stim software, open-source kink projects) + gaps Tethered could fill
   - DIY / mad-scientist kink hardware (OSSM ecosystem, biofeedback, predicament engineering, KinkyMakers-style builds) feasible for an ESP32-level builder
   - Household / family / self-hosted apps with a genuinely clever idea at the core
   - Wildcard: any maker/art/tech project that would make Rob go "oh that's COOL"

3. Keep only finds that pass the bar: would a jaded senior dev actually raise an eyebrow? 4-8 total across both themes. For each: name, one-line what-it-is, why it's cool, URL, and (where it fits) a one-line "we could riff on this by...".

4. Append a dated "## $(date +%F)" section to "$VAULT/Ideas/Inspiration Log.md" with the full finds (create the file with a one-line intro if missing), then commit AND push the vault per the CLAUDE.md workflow.

Hard rules:
- RESEARCH ONLY. No signups, no purchases, no code changes, nothing leaves the machine except the vault push and the Telegram summary.
- Safety framing on kink hardware finds where relevant (current paths, fail-open locks); never anything involving breath restriction.
- No em dashes anywhere.
- If a week's hunt turns up nothing that clears the bar, say so honestly; Rob explicitly prefers that to padding.

Your FINAL message must be ONLY the Telegram drop for Rob: the top 3-5 finds, one or two lines each with the link, warm and direct with real personality, mobile-friendly, no markdown headers or tables. That final message is the only thing sent to him.
PROMPT_EOF

cd "$VAULT"
SUMMARY="$(timeout 840 "$CLAUDE_BIN" -p "$PROMPT" --model claude-opus-5 --dangerously-skip-permissions 2>/tmp/jarvis-inspiration-err.$$)" || {
  echo "$(date -Iseconds) ERROR: claude invocation failed"
  cat /tmp/jarvis-inspiration-err.$$ || true
  rm -f /tmp/jarvis-inspiration-err.$$
  send_tg "💡 Weekly inspiration scout failed to run (claude error). Log: ~/.local/state/jarvis-inspiration.log"
  exit 0
}
rm -f /tmp/jarvis-inspiration-err.$$

echo "--- summary ---"
echo "$SUMMARY"
echo "---------------"

if [ "$DRYRUN" = "1" ]; then
  echo "DRYRUN: not sending"
else
  send_tg "💡 Weekly inspiration drop

$SUMMARY"
fi
echo "----- $(date -Iseconds) inspiration end -----"
