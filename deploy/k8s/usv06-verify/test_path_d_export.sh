#!/usr/bin/env bash
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
TOKEN=$($K get secret aimpos-api-env -n "$NS" -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
API="http://$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}'):8000"
LEGACY="${1:-e5da4992-226c-4969-b95d-e7a2c6415b30}"
curl -sf -m 60 "$API/export/$LEGACY" -H "Authorization: Bearer $TOKEN" -o /tmp/path-d-test.zip
unzip -p /tmp/path-d-test.zip manifest.json | grep -E 'manifest_version|narration'
