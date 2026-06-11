#!/usr/bin/env bash
# Apply Alembic 0003 STORYBOARD multi-frame indexes on Olares (idempotent checks).
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)

psql() {
  $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -v ON_ERROR_STOP=1 "$@"
}

echo "=== alembic_version before ==="
psql -t -A -c "SELECT version_num FROM alembic_version;"

echo "=== apply 0003 if needed ==="
psql <<'SQL'
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_asset_versions_project_id_stage_version'
  ) THEN
    ALTER TABLE asset_versions DROP CONSTRAINT uq_asset_versions_project_id_stage_version;
  END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_asset_versions_project_stage_version_single
  ON asset_versions (project_id, stage, version)
  WHERE stage != 'STORYBOARD';

CREATE UNIQUE INDEX IF NOT EXISTS uq_asset_versions_storyboard_batch_frame
  ON asset_versions (project_id, stage, version, (metadata_json->>'frame_index'))
  WHERE stage = 'STORYBOARD';

UPDATE alembic_version SET version_num = '0003' WHERE version_num = '0002';
SQL

echo "=== alembic_version after ==="
psql -t -A -c "SELECT version_num FROM alembic_version;"

echo "=== indexes ==="
psql -c "\d asset_versions"
