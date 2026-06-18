#!/usr/bin/env bash
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)
PROJECT=ba0c4636-817c-423b-9771-20100e080b76
LEGACY=e5da4992-226c-4969-b95d-e7a2c6415b30
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark <<SQL
SELECT id::text, pipeline_run_id::text, metadata_json->>'has_narration' AS narr
FROM asset_versions
WHERE stage='VIDEO' AND project_id='$PROJECT'
ORDER BY created_at DESC LIMIT 10;
SELECT id::text, pipeline_run_id::text FROM asset_versions
WHERE stage='VIDEO' AND pipeline_run_id='$LEGACY';
SQL
