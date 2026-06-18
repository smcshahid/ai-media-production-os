#!/usr/bin/env bash
# Quick API probe for US-V08 character endpoints.
set -uo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
TOKEN=$($K get secret aimpos-api-env -n "$NS" -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
PROJECT=ba0c4636-817c-423b-9771-20100e080b76
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"

echo "GET /characters"
curl -sf -m 10 "$API/characters?project_id=$PROJECT" -H "$AUTH" | head -c 200
echo

echo "POST /characters probe"
curl -sf -m 10 -X POST "$API/characters" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","name":"Probe-Maya","role":"protagonist","description":"probe"}' | head -c 300
echo
