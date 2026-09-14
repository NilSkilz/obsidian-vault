#!/bin/sh
# Send a Jarvis voice note to Rob on Telegram (or another chat id).
# Usage: jarvis-voice.sh "text to speak" [voice] [chat_id]
#   voice: OpenAI TTS voice, default "ash" (alloy|ash|ballad|coral|echo|fable|onyx|nova|sage|shimmer|verse)
#   TEMPO env var: playback speed multiplier, default 1.12 (Rob found ash too slow
#   at natural pace, 14 Sep 2026; instructions alone don't reliably change pace)
# TTS via OpenAI gpt-4o-mini-tts (key in openai.env), converted to OGG/Opus with
# ffmpeg (Telegram voice notes require opus), sent via sendVoice.
# Keep the text chat-note length, not an essay: TTS is billed per character.
. "$HOME/.config/jarvis/openai.env"
. "$HOME/.config/jarvis/telegram.env"
TEXT="$1"; VOICE="${2:-ash}"; CHAT="${3:-$TELEGRAM_CHAT_ID}"; TEMPO="${TEMPO:-1.12}"
[ -z "$TEXT" ] && { echo "usage: jarvis-voice.sh \"text\" [voice] [chat_id]" >&2; exit 1; }
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
BODY=$(python3 -c 'import json,sys; print(json.dumps({
  "model": "gpt-4o-mini-tts",
  "voice": sys.argv[2],
  "input": sys.argv[1],
  "instructions": "Warm, dry, British. Conversational and a little wry, like a clever friend, not a customer service agent. Brisk pace, snappy delivery, short pauses.",
  "response_format": "mp3"}))' "$TEXT" "$VOICE")
curl -sS https://api.openai.com/v1/audio/speech \
  -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
  -d "$BODY" -o "$TMP/say.mp3" || exit 1
# A failed API call returns a small JSON error body, not audio
if ! file "$TMP/say.mp3" | grep -qi 'audio\|mpeg'; then
  echo "TTS failed:" >&2; head -c 300 "$TMP/say.mp3" >&2; echo >&2; exit 1
fi
"$HOME/bin/ffmpeg" -y -loglevel error -i "$TMP/say.mp3" -filter:a "atempo=$TEMPO" -c:a libopus -b:a 32k -ar 48000 -ac 1 "$TMP/say.ogg" || exit 1
OK=$(curl -sS -F chat_id="$CHAT" -F voice=@"$TMP/say.ogg" \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendVoice" \
  | python3 -c 'import json,sys; print("1" if json.load(sys.stdin).get("ok") else "0")')
[ "$OK" = "1" ] && echo "voice note sent ($VOICE)" || { echo "sendVoice failed" >&2; exit 1; }
