#!/usr/bin/env bash
# Minimal Trello CLI for the "Jarvis" board — read-only creds, curl+jq, no node needed.
# Usage:
#   trello.sh lists
#   trello.sh cards <list-name-substring>   # e.g. "To Do"
#   trello.sh move <card-id> <list-name-substring>
#   trello.sh comment <card-id> <text>
set -euo pipefail

ENV_FILE="/home/jarvis/.config/jarvis/trello.env"
BOARD_ID="6981c75edb5758a1a2d689e7"   # board "Jarvis" (trailing space in name), https://trello.com/b/IMUJxUvx/jarvis
API="https://api.trello.com/1"

source "$ENV_FILE"
AUTH="key=${TRELLO_KEY}&token=${TRELLO_TOKEN}"

find_list_id() {
  local needle="$1"
  curl -s "$API/boards/$BOARD_ID/lists?${AUTH}&fields=name,id" \
    | jq -r --arg n "$needle" '.[] | select(.name | ascii_downcase | contains($n | ascii_downcase)) | .id' \
    | head -n1
}

cmd="${1:-}"; shift || true

case "$cmd" in
  lists)
    curl -s "$API/boards/$BOARD_ID/lists?${AUTH}&fields=name,id"
    ;;
  cards)
    list_name="${1:?usage: trello.sh cards <list-name>}"
    list_id="$(find_list_id "$list_name")"
    [ -n "$list_id" ] || { echo "no list matching '$list_name'" >&2; exit 1; }
    curl -s "$API/lists/$list_id/cards?${AUTH}&fields=name,desc,id,shortUrl"
    ;;
  move)
    card_id="${1:?usage: trello.sh move <card-id> <list-name>}"
    list_name="${2:?usage: trello.sh move <card-id> <list-name>}"
    list_id="$(find_list_id "$list_name")"
    [ -n "$list_id" ] || { echo "no list matching '$list_name'" >&2; exit 1; }
    curl -s -X PUT "$API/cards/$card_id?${AUTH}&idList=$list_id"
    ;;
  comment)
    card_id="${1:?usage: trello.sh comment <card-id> <text>}"
    shift
    text="$*"
    curl -s -X POST "$API/cards/$card_id/actions/comments?${AUTH}" --data-urlencode "text=$text"
    ;;
  *)
    echo "usage: trello.sh {lists|cards <list>|move <card-id> <list>|comment <card-id> <text>}" >&2
    exit 1
    ;;
esac
