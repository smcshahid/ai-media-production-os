#!/usr/bin/env bash
set -euo pipefail
NS=aimpos-mwayolares
: "${TOKEN:?}"
: "${PROJECT:?}"
K="sudo k3s kubectl"
API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"

approve_stage() {
  local stage="$1"
  curl -s -m 30 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","stage":"'"$stage"'","decision":"GRANT"}'
  echo
  sleep 2
}

S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
ST=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
echo "CURRENT=$S stage=$ST"

if [ "$ST" = "SCRIPT" ]; then approve_stage SCRIPT; fi
S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
ST=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
if [ "$ST" = "STORYBOARD" ]; then approve_stage STORYBOARD; fi

echo "FINAL=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")"
