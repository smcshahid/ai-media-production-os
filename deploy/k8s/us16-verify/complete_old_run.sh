#!/usr/bin/env bash
# Complete a run stuck at STORYBOARD stub gate so a fresh US-16 E2E can start.
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
TOKEN=$($K get secret aimpos-api-env -n "$NS" -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
PROJECT="${PROJECT:-ba0c4636-817c-423b-9771-20100e080b76}"
API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"

echo "=== status before ==="
curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH"
echo

echo "=== approve STORYBOARD (complete stub run) ==="
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORYBOARD","decision":"APPROVED"}'
echo

sleep 5
echo "=== status after ==="
curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH"
echo
