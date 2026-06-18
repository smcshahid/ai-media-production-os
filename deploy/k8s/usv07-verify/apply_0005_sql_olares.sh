#!/usr/bin/env bash
# Apply Alembic 0005 episode model on Olares (acceptance migration evidence).
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)

echo "Before:"
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT version_num FROM alembic_version;"

$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark <<'SQL'
BEGIN;

CREATE TABLE IF NOT EXISTS episodes (
    id UUID NOT NULL PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id),
    episode_number INTEGER NOT NULL,
    title VARCHAR(255),
    status VARCHAR(16) NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_episodes_project_number UNIQUE (project_id, episode_number)
);
CREATE INDEX IF NOT EXISTS ix_episodes_project_id ON episodes (project_id);

ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS episode_id UUID;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_pipeline_runs_episode_id'
    ) THEN
        ALTER TABLE pipeline_runs
            ADD CONSTRAINT fk_pipeline_runs_episode_id
            FOREIGN KEY (episode_id) REFERENCES episodes(id);
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS ix_pipeline_runs_episode_id ON pipeline_runs (episode_id);

UPDATE alembic_version SET version_num = '0005' WHERE version_num = '0004';

COMMIT;
SQL

echo "After:"
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT version_num FROM alembic_version;"
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='episodes');"
echo "PASS migration 0005 applied"
