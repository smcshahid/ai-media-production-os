#!/usr/bin/env bash
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
export TOKEN
TOKEN=$($K get secret aimpos-api-env -n "$NS" -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
export PGPW
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)
export PROJECT_ID
PROJECT_ID=$($K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT id FROM projects ORDER BY created_at LIMIT 1;")
export RUN_ID
RUN_ID=$($K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT id FROM pipeline_runs WHERE project_id='$PROJECT_ID' ORDER BY created_at DESC LIMIT 1;")
echo "PROJECT_ID=$PROJECT_ID RUN_ID=$RUN_ID"
exec bash /tmp/verify_phase3c.sh
