#!/usr/bin/env bash
# Complete active pipeline run on Olares before US-17 E2E.
set -euo pipefail
NS=aimpos-mwayolares
: "${PROJECT:?set PROJECT}"
: "${TOKEN:?set TOKEN}"
K="sudo k3s kubectl"
API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"

S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
echo "status=$ST stage=$STG"

if [ "$ST" = "COMPLETED" ] || [ "$ST" = "FAILED" ] || [ -z "$ST" ]; then
  echo "No active run to complete"
  exit 0
fi

if [ "$ST" = "AWAITING_APPROVAL" ] && [ -n "$STG" ]; then
  echo "Approving stage $STG to unblock..."
  curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","stage":"'"$STG"'","decision":"APPROVED"}'
  echo
  sleep 5
fi

echo "Done"
