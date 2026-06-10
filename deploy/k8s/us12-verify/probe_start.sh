#!/usr/bin/env bash
set -uo pipefail
NS=aimpos-mwayolares
# Secret from environment (never hardcode):
#   export TOKEN=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
: "${TOKEN:?set TOKEN to the AIMPOS_API_TOKEN}"
PROJECT="${PROJECT:?set PROJECT to the target project UUID}"
K="sudo k3s kubectl"
API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
echo "new api pod:"
$K get pods -n "$NS" -l app=aimpos-api
echo "start:"
curl -s -m 30 -X POST "$API/pipeline/start" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'"}'
echo
