#!/usr/bin/env bash
# Phase 3D — detect image drift between cluster and release manifest.
set -uo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
MANIFEST="${MANIFEST:-/tmp/aimpos-manifest.yaml}"

: "${EXPECTED_API_TAG:?set EXPECTED_API_TAG e.g. v0.13.0-phase3d}"
: "${EXPECTED_WEB_TAG:?set EXPECTED_WEB_TAG}"
: "${EXPECTED_WORKER_TAG:?set EXPECTED_WORKER_TAG}"

FAIL=0
echo "Drift check start $(date -Iseconds)"
echo "Expected API=$EXPECTED_API_TAG WEB=$EXPECTED_WEB_TAG WORKER=$EXPECTED_WORKER_TAG"

get_image() {
  local dep="$1"
  $K get deploy "$dep" -n "$NS" -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo missing
}

API_IMG=$(get_image aimpos-api)
WEB_IMG=$(get_image aimpos-web)
WORKER_IMG=$(get_image aimpos-worker)

echo "Cluster API=$API_IMG"
echo "Cluster WEB=$WEB_IMG"
echo "Cluster WORKER=$WORKER_IMG"

check_tag() {
  local img="$1" expected="$2" name="$3"
  if [[ "$img" == *":$expected" ]] || [[ "$img" == *"/aimpos-$name:$expected" ]]; then
    echo "PASS $name tag"
  else
    echo "DRIFT $name expected :$expected got $img"
    FAIL=1
  fi
}

check_tag "$API_IMG" "$EXPECTED_API_TAG" api
check_tag "$WEB_IMG" "$EXPECTED_WEB_TAG" web
check_tag "$WORKER_IMG" "$EXPECTED_WORKER_TAG" worker

echo "========== Alembic version =========="
: "${PGPW:?set PGPW}"
ALEMBIC=$($K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT version_num FROM alembic_version;" 2>/dev/null | tr -d '\r\n')
echo "CLUSTER_ALEMBIC=$ALEMBIC"
: "${EXPECTED_ALEMBIC:?set EXPECTED_ALEMBIC from deploy/release/manifest.yaml via load-manifest-env.sh}"
if [ "$ALEMBIC" != "$EXPECTED_ALEMBIC" ]; then
  echo "DRIFT alembic expected $EXPECTED_ALEMBIC got $ALEMBIC"
  FAIL=1
else
  echo "PASS alembic"
fi

echo "DONE DRIFT=$FAIL"
exit $FAIL
