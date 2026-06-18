#!/usr/bin/env bash
# Apply Alembic 0006 character bible on Olares (acceptance migration evidence).
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)

echo "Before:"
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT version_num FROM alembic_version;"

$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark <<'SQL'
BEGIN;

CREATE TABLE IF NOT EXISTS characters (
    id UUID NOT NULL PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id),
    name VARCHAR(128) NOT NULL,
    description TEXT,
    role VARCHAR(128),
    visual_traits TEXT,
    personality_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_characters_project_name UNIQUE (project_id, name)
);
CREATE INDEX IF NOT EXISTS ix_characters_project_id ON characters (project_id);

ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS character_ids JSON;

UPDATE alembic_version SET version_num = '0006' WHERE version_num = '0005';

COMMIT;
SQL

echo "After:"
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT version_num FROM alembic_version;"
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='characters');"
echo "PASS migration 0006 applied"
