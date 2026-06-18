#!/usr/bin/env bash
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "
SELECT 'chars', id::text, name FROM characters WHERE project_id='ba0c4636-817c-423b-9771-20100e080b76' ORDER BY created_at DESC LIMIT 5;
SELECT 'run', id::text, character_snapshot::json->0->>'name' FROM pipeline_runs WHERE id IN ('5d99fc7b-2a59-4b59-be86-f048b4cdd9d4','a6a92786-6e55-499d-9d15-39153af62f81');
"
