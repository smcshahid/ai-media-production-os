#!/usr/bin/env bash
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
TOKEN=$($K get secret aimpos-api-env -n "$NS" -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
RUN=a6894d3e-df8e-412b-9e13-73add88060c2
curl -s -m 120 -w "\nHTTP:%{http_code}\n" "$API/export/$RUN" -H "Authorization: Bearer ${TOKEN}" -o /tmp/test-export.zip | tail -1
ls -la /tmp/test-export.zip
