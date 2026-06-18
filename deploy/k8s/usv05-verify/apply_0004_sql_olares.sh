#!/usr/bin/env bash
# Apply Alembic 0004 SQL directly on Olares (acceptance migration evidence).
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)

echo "Before:"
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT version_num FROM alembic_version;"

$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark <<'SQL'
BEGIN;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS scene_count INTEGER;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS current_scene_index INTEGER;
ALTER TABLE approvals ADD COLUMN IF NOT EXISTS scene_index INTEGER;
DROP INDEX IF EXISTS uq_asset_versions_storyboard_batch_frame;
CREATE UNIQUE INDEX IF NOT EXISTS uq_asset_versions_storyboard_batch_scene_frame
ON asset_versions (
    project_id,
    stage,
    version,
    COALESCE(metadata_json->>'scene_index', '1'),
    (metadata_json->>'frame_index')
)
WHERE stage = 'STORYBOARD';
UPDATE alembic_version SET version_num = '0004' WHERE version_num = '0003';
COMMIT;
SQL

echo "After:"
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT version_num FROM alembic_version;"
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT column_name FROM information_schema.columns WHERE table_name='pipeline_runs' AND column_name IN ('scene_count','current_scene_index');"
echo "PASS migration 0004 applied"
