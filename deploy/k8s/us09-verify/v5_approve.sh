#!/usr/bin/env bash
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
export PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)
export TOKEN=$($K get secret aimpos-api-env -n "$NS" -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
PROJECT=ba0c4636-817c-423b-9771-20100e080b76
RUN_ID=8c35926c-0a4e-44ed-ac5a-ea3c178902cd
API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
AUTH="Authorization: Bearer ${TOKEN}"
API="http://${API_IP}:8000"

echo "=== V5 APPROVE ==="
curl -s -m 60 -w "\nHTTP:%{http_code}\n" -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORY","decision":"APPROVED"}'
sleep 10
echo "=== STATUS ==="
curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH"
echo
echo "=== APPROVALS ==="
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A \
  -c "SELECT id||'|'||stage||'|'||decision||'|'||COALESCE(rationale,'') FROM approvals WHERE pipeline_run_id='$RUN_ID' ORDER BY created_at;"
echo "=== RUN ==="
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A \
  -c "SELECT status||'|'||current_stage FROM pipeline_runs WHERE id='$RUN_ID';"
