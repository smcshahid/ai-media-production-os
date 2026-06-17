#!/usr/bin/env bash
# Phase 3D — load manifest env and run drift check on Olares.
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"

export PGPW
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)

# Defaults match deploy/release/manifest.yaml — override via env for other releases
export EXPECTED_API_TAG="${EXPECTED_API_TAG:-v0.13.0-phase3d}"
export EXPECTED_WEB_TAG="${EXPECTED_WEB_TAG:-v0.13.0-phase3d}"
export EXPECTED_WORKER_TAG="${EXPECTED_WORKER_TAG:-v0.13.0-phase3d}"
export EXPECTED_ALEMBIC="${EXPECTED_ALEMBIC:-0003}"

exec bash /tmp/check_drift.sh
