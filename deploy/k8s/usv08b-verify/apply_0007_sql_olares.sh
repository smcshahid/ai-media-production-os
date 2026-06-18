#!/usr/bin/env bash
# Apply Alembic 0007 character snapshot on Olares (Phase 7.5 acceptance migration).
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)

echo "Before:"
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT version_num FROM alembic_version;"

$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark <<'SQL'
BEGIN;

ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS character_snapshot JSON;

UPDATE alembic_version SET version_num = '0007' WHERE version_num = '0006';

COMMIT;
SQL

echo "After:"
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT version_num FROM alembic_version;"
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='pipeline_runs' AND column_name='character_snapshot');"
echo "PASS migration 0007 applied"
