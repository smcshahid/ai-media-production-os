#!/usr/bin/env bash
# Phase 8 — load manifest env and run drift check on Olares.
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"

export PGPW
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)

MANIFEST="${MANIFEST_PATH:-/tmp/aimpos-manifest.yaml}"
LOADER="${MANIFEST_LOADER:-/tmp/load-manifest-env.sh}"

if [ ! -f "$MANIFEST" ]; then
  echo "FAIL missing manifest at $MANIFEST — run deploy/k8s/lib/sync_manifest_to_olares.sh first" >&2
  exit 1
fi

if [ -f "$LOADER" ]; then
  # shellcheck source=/dev/null
  source "$LOADER" "$MANIFEST"
else
  echo "FAIL missing $LOADER — sync scripts/release/load-manifest-env.sh to Olares" >&2
  exit 1
fi

if [ -n "${ACCEPTANCE_IMAGE_TAG:-}" ]; then
  export EXPECTED_API_TAG="$ACCEPTANCE_IMAGE_TAG"
  export EXPECTED_WEB_TAG="$ACCEPTANCE_IMAGE_TAG"
  export EXPECTED_WORKER_TAG="$ACCEPTANCE_IMAGE_TAG"
fi

: "${EXPECTED_API_TAG:?}"
: "${EXPECTED_WEB_TAG:?}"
: "${EXPECTED_WORKER_TAG:?}"
: "${EXPECTED_ALEMBIC:?}"

exec bash /tmp/check_drift.sh
