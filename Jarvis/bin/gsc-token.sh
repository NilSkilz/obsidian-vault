#!/bin/bash
# Mint a Google OAuth2 access token from the GSC service-account key.
# Usage: TOKEN=$(gsc-token.sh)
set -euo pipefail

KEY_FILE="${GSC_KEY_FILE:-$HOME/.config/jarvis/gsc-service-account.json}"
SCOPE="https://www.googleapis.com/auth/webmasters.readonly"

CLIENT_EMAIL=$(python3 -c "import json;print(json.load(open('$KEY_FILE'))['client_email'])")
TOKEN_URI=$(python3 -c "import json;print(json.load(open('$KEY_FILE'))['token_uri'])")

PK_FILE=$(mktemp)
trap 'rm -f "$PK_FILE"' EXIT
python3 -c "import json;print(json.load(open('$KEY_FILE'))['private_key'])" > "$PK_FILE"

b64url() { openssl base64 -A | tr '+/' '-_' | tr -d '='; }

NOW=$(date +%s)
EXP=$((NOW + 3600))
HEADER=$(printf '{"alg":"RS256","typ":"JWT"}' | b64url)
CLAIMS=$(printf '{"iss":"%s","scope":"%s","aud":"%s","iat":%d,"exp":%d}' \
  "$CLIENT_EMAIL" "$SCOPE" "$TOKEN_URI" "$NOW" "$EXP" | b64url)
SIG=$(printf '%s.%s' "$HEADER" "$CLAIMS" | openssl dgst -sha256 -sign "$PK_FILE" -binary | b64url)
JWT="$HEADER.$CLAIMS.$SIG"

curl -s -X POST "$TOKEN_URI" \
  -d "grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=$JWT" \
  | python3 -c "import json,sys;print(json.load(sys.stdin)['access_token'])"
