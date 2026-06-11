#!/usr/bin/env bash
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
TOKEN=$($K get secret aimpos-api-env -n "$NS" -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
PROJECT="${PROJECT:-ba0c4636-817c-423b-9771-20100e080b76}"
API="http://$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}'):8000"
for i in $(seq 1 12); do
  curl -s -m 10 "$API/pipeline/status?project_id=$PROJECT" -H "Authorization: Bearer $TOKEN"
  echo
  sleep 5
done
