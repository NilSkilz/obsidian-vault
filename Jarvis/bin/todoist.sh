#!/usr/bin/env bash
# Minimal Todoist CLI — curl+jq, read-focused, no node needed.
# Usage:
#   todoist.sh today          # tasks due today (includes overdue), across all projects
#   todoist.sh projects       # list projects
#   todoist.sh add <content> [project-name]   # quick-add a task, optionally into a project
set -euo pipefail

ENV_FILE="/home/jarvis/.config/jarvis/todoist.env"
API="https://api.todoist.com/api/v1"

source "$ENV_FILE"
AUTH_HEADER="Authorization: Bearer ${TODOIST_TOKEN}"

find_project_id() {
  local needle="$1"
  curl -s -H "$AUTH_HEADER" "$API/projects" \
    | jq -r --arg n "$needle" '.results[] | select(.name | ascii_downcase | contains($n | ascii_downcase)) | .id' \
    | head -n1
}

cmd="${1:-}"; shift || true

case "$cmd" in
  today)
    curl -s -H "$AUTH_HEADER" -G "$API/tasks/filter" --data-urlencode "query=today" \
      | jq -r '.results[] | "- \(.content)" + (if .description != "" then " (\(.description))" else "" end)'
    ;;
  projects)
    curl -s -H "$AUTH_HEADER" "$API/projects" | jq -r '.results[] | "\(.id)\t\(.name)"'
    ;;
  add)
    content="${1:?usage: todoist.sh add <content> [project-name]}"
    shift || true
    project_name="${1:-}"
    if [ -n "$project_name" ]; then
      project_id="$(find_project_id "$project_name")"
      [ -n "$project_id" ] || { echo "no project matching '$project_name'" >&2; exit 1; }
      curl -s -X POST -H "$AUTH_HEADER" -H "Content-Type: application/json" "$API/tasks" \
        -d "$(jq -n --arg c "$content" --arg p "$project_id" '{content:$c, project_id:$p}')"
    else
      curl -s -X POST -H "$AUTH_HEADER" -H "Content-Type: application/json" "$API/tasks" \
        -d "$(jq -n --arg c "$content" '{content:$c}')"
    fi
    ;;
  *)
    echo "usage: todoist.sh {today|projects|add <content> [project-name]}" >&2
    exit 1
    ;;
esac
