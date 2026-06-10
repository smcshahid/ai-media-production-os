#!/usr/bin/env bash
# Drive the prior run (SCRIPT/STORYBOARD stub gates) to COMPLETED so a fresh run can start.
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
TOKEN=$($K get secret aimpos-api-env -n "$NS" -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
PROJECT=ba0c4636-817c-423b-9771-20100e080b76
API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"

for STAGE in SCRIPT STORYBOARD; do
  echo "=== approve $STAGE ==="
  curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","stage":"'"$STAGE"'","decision":"APPROVED"}'
  echo
  sleep 12
  curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH"
  echo
done
