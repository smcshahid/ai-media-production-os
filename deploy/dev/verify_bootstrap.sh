#!/usr/bin/env bash
# Phase 8 local bootstrap verification — Alembic head from manifest + STORYBOARD indexes.
set -uo pipefail

: "${REPO_ROOT:=$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$REPO_ROOT"

FAIL=0
MANIFEST="$REPO_ROOT/deploy/release/manifest.yaml"
EXPECTED_ALEMBIC=$(grep alembic_head "$MANIFEST" | sed -n 's/.*"\([^"]*\)".*/\1/p' | head -1)

echo "WP-3 bootstrap verify start $(date -Iseconds)"
echo "Expected Alembic from manifest: $EXPECTED_ALEMBIC"

if [ ! -f .env ]; then
  echo "WARN: .env missing — skip live DB bootstrap checks"
  exit 0
fi

echo "========== B-03-01: ensure-db-migrated =========="
if command -v powershell.exe >/dev/null 2>&1; then
  powershell.exe -ExecutionPolicy Bypass -File scripts/dev/ensure-db-migrated.ps1 || FAIL=1
elif command -v pwsh >/dev/null 2>&1; then
  pwsh -ExecutionPolicy Bypass -File scripts/dev/ensure-db-migrated.ps1 || FAIL=1
else
  echo "WARN: powershell not found — skip ensure-db-migrated"
fi

echo "========== B-03-02: alembic version =========="
VER=$(docker compose -f deploy/compose/docker-compose.yml --env-file .env exec -T postgresql \
  sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -A -c "SELECT version_num FROM alembic_version;"' 2>/dev/null | tr -d '\r\n' || echo "")
echo "ALEMBIC=$VER"
if [ -z "$VER" ]; then
  echo "WARN: could not read alembic_version (stack down?)"
elif [ "$VER" != "$EXPECTED_ALEMBIC" ]; then
  echo "FAIL: expected $EXPECTED_ALEMBIC got $VER"
  FAIL=1
fi

echo "========== B-03-03: storyboard partial indexes =========="
IDX=$(docker compose -f deploy/compose/docker-compose.yml --env-file .env exec -T postgresql \
  sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -A -c "SELECT indexname FROM pg_indexes WHERE tablename = '\''asset_versions'\'' AND indexname LIKE '\''uq_%'\'' ORDER BY indexname;"' 2>/dev/null || echo "")
if [ -z "$IDX" ]; then
  echo "WARN: could not read indexes (stack down?)"
else
  echo "$IDX"
  echo "$IDX" | grep -q uq_asset_versions_storyboard_batch_frame || FAIL=1
  echo "$IDX" | grep -q uq_asset_versions_project_stage_version_single || FAIL=1
fi

echo "DONE FAIL=$FAIL"
exit $FAIL
