#!/usr/bin/env bash
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
TOKEN=$($K get secret aimpos-api-env -n $NS -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
API=$($K get svc aimpos-api -n $NS -o jsonpath='{.spec.clusterIP}')
curl -sf "http://${API}:8000/health"
echo
curl -sf -X POST "http://${API}:8000/episodes" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{"project_id":"ba0c4636-817c-423b-9771-20100e080b76","title":"US-V07 probe"}'
echo
