#!/usr/bin/env bash
# Olares cluster probe for US-V07 acceptance (read-only).
set -uo pipefail
NS="${AIMPOS_NAMESPACE:-aimpos-mwayolares}"
K="sudo k3s kubectl"

echo "=== Deployments ==="
$K get deploy -n "$NS" -o custom-columns=NAME:.metadata.name,IMAGE:.spec.template.spec.containers[0].image

echo "=== Alembic ==="
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A <<'SQL'
SELECT version_num FROM alembic_version;
SQL

echo "=== Phase 6 schema ==="
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A <<'SQL'
SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='episodes');
SELECT column_name FROM information_schema.columns
WHERE table_name='pipeline_runs' AND column_name='episode_id';
SQL

echo "=== Project ==="
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A <<'SQL'
SELECT id::text, name FROM projects ORDER BY created_at LIMIT 1;
SQL

echo "=== Episodes count ==="
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A <<'SQL' 2>/dev/null || echo "0"
SELECT COUNT(*) FROM episodes;
SQL

echo "=== API cluster IP ==="
$K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}{"\n"}'
