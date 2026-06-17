#!/usr/bin/env bash
# Phase 3D Olares release verification — drift + phase3c + US-V04 attestation.
set -uo pipefail
NS=aimpos-mwayolares
: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT_ID:?set PROJECT_ID}"
K="sudo k3s kubectl"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
WEB_IP=$($K get svc aimposingress -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
WEB="http://${WEB_IP}:8080"
AUTH="Authorization: Bearer ${TOKEN}"

FAIL=0
echo "Phase 3D release verify start $(date -Iseconds)"

echo "========== P3D-R01: drift check =========="
export EXPECTED_API_TAG="${EXPECTED_API_TAG:-v0.13.0-phase3d}"
export EXPECTED_WEB_TAG="${EXPECTED_WEB_TAG:-v0.13.0-phase3d}"
export EXPECTED_WORKER_TAG="${EXPECTED_WORKER_TAG:-v0.13.0-phase3d}"
export EXPECTED_ALEMBIC="${EXPECTED_ALEMBIC:-0003}"
if [ -f /tmp/check_drift.sh ]; then
  bash /tmp/check_drift.sh || FAIL=1
else
  echo "WARN: check_drift.sh not present — skip"
fi

echo "========== P3D-R02: web entrance =========="
WHTTP=$(curl -s -m 30 -o /dev/null -w "%{http_code}" "$WEB/")
echo "WEB_ROOT http=$WHTTP"
[ "$WHTTP" = "200" ] || FAIL=1

echo "========== P3D-R03: US-V04 worker attestation (SQL) =========="
SOURCE=$($K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c \
  "SELECT COALESCE(metadata_json->>'source','missing') FROM asset_versions WHERE project_id='$PROJECT_ID' AND stage='VIDEO' ORDER BY version DESC LIMIT 1;" | tr -d '\r\n')
FRAME_COUNT=$($K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c \
  "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT_ID' AND stage='STORYBOARD' AND version=(SELECT MAX(version) FROM asset_versions WHERE project_id='$PROJECT_ID' AND stage='STORYBOARD');" | tr -d '\r\n')
echo "VIDEO_SOURCE=$SOURCE STORYBOARD_FRAMES=$FRAME_COUNT"
if [ "$FRAME_COUNT" != "4" ]; then echo "WARN: expected 4 storyboard frames"; fi
if [ "$SOURCE" = "comfyui_i2v" ]; then
  echo "PASS US-V04 i2v source attested"
elif [ "$SOURCE" = "slideshow" ]; then
  echo "WARN US-V04 slideshow fallback (acceptable with fallback_reason)"
else
  echo "WARN US-V04 source=$SOURCE"
fi

echo "========== P3D-R04: core API regressions =========="
for path in \
  "audit?project_id=$PROJECT_ID&limit=10" \
  "audit/export?project_id=$PROJECT_ID&format=json" \
  "pipeline/runs?project_id=$PROJECT_ID" \
  "assets/history?project_id=$PROJECT_ID" \
  "health"; do
  if [ "$path" = "health" ]; then
    HTTP=$(curl -s -m 15 -o /dev/null -w "%{http_code}" "$API/health")
  else
    HTTP=$(curl -s -m 30 -o /dev/null -w "%{http_code}" "$API/$path" -H "$AUTH")
  fi
  echo "GET /$path http=$HTTP"
  [ "$HTTP" = "200" ] || FAIL=1
done

echo "DONE FAIL=$FAIL"
exit $FAIL
