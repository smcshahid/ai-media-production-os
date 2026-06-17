#!/usr/bin/env bash
# WP-3 local bootstrap verification — Alembic head + STORYBOARD indexes (D-65).
set -uo pipefail

: "${REPO_ROOT:=$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$REPO_ROOT"

FAIL=0

echo "WP-3 bootstrap verify start $(date -Iseconds)"

if [ ! -f .env ]; then
  echo "FAIL: .env missing"
  exit 1
fi

echo "========== B-03-01: ensure-db-migrated =========="
powershell -ExecutionPolicy Bypass -File scripts/dev/ensure-db-migrated.ps1 || FAIL=1

echo "========== B-03-02: alembic version =========="
VER=$(docker compose -f deploy/compose/docker-compose.yml --env-file .env exec -T postgresql \
  sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -A -c "SELECT version_num FROM alembic_version;"' | tr -d '\r\n')
echo "ALEMBIC=$VER"
if [ "$VER" != "0003" ]; then echo "FAIL: expected 0003"; FAIL=1; fi

echo "========== B-03-03: storyboard partial indexes =========="
IDX=$(docker compose -f deploy/compose/docker-compose.yml --env-file .env exec -T postgresql \
  sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -A -c "SELECT indexname FROM pg_indexes WHERE tablename = '\''asset_versions'\'' AND indexname LIKE '\''uq_%'\'' ORDER BY indexname;"')
echo "$IDX"
echo "$IDX" | grep -q uq_asset_versions_storyboard_batch_frame || FAIL=1
echo "$IDX" | grep -q uq_asset_versions_project_stage_version_single || FAIL=1

echo "DONE FAIL=$FAIL"
exit $FAIL
