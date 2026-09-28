#!/bin/bash
# Bing Webmaster API helper for tethered.me.uk.
# Usage: bing.sh <method> [key=value ...]        (GET, params appended)
#        bing.sh submit <url> [url ...]          (SubmitUrlBatch POST)
# Examples:
#   bing.sh GetFeeds
#   bing.sh GetQueryStats
#   bing.sh GetUrlSubmissionQuota
#   bing.sh submit https://tethered.me.uk/blog
set -euo pipefail

. "$HOME/.config/jarvis/bing.env"
BASE="https://ssl.bing.com/webmaster/api.svc/json"
SITE="https://tethered.me.uk/"

METHOD="${1:?usage: bing.sh <ApiMethod|submit> [args]}"
shift || true

if [ "$METHOD" = "submit" ]; then
  [ $# -ge 1 ] || { echo "usage: bing.sh submit <url> [url ...]" >&2; exit 1; }
  URLS=$(printf '"%s",' "$@"); URLS=${URLS%,}
  curl -s -X POST "$BASE/SubmitUrlBatch?apikey=$BING_API_KEY" \
    -H 'Content-Type: application/json; charset=utf-8' \
    -d "{\"siteUrl\":\"$SITE\",\"urlList\":[$URLS]}"
  echo
  exit 0
fi

QS="apikey=$BING_API_KEY&siteUrl=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=''))" "$SITE")"
for kv in "$@"; do QS="$QS&$kv"; done
curl -s "$BASE/$METHOD?$QS"
echo
