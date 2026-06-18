#!/usr/bin/env bash
# Phase 3D — load manifest env and run drift check on Olares.
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"

export PGPW
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)

# Defaults loaded from deploy/release/manifest.yaml when synced to Olares.
# Override via env for acceptance image tags (e.g. usv08-phase7).
if [ -f /tmp/load-manifest-env.sh ]; then
  # shellcheck source=/dev/null
  source /tmp/load-manifest-env.sh /tmp/aimpos-manifest.yaml /tmp
elif [ -f /tmp/aimpos-manifest.yaml ]; then
  export EXPECTED_API_TAG="${EXPECTED_API_TAG:-v0.16.0-phase6-episode}"
  export EXPECTED_WEB_TAG="${EXPECTED_WEB_TAG:-v0.16.0-phase6-episode}"
  export EXPECTED_WORKER_TAG="${EXPECTED_WORKER_TAG:-v0.16.0-phase6-episode}"
  export EXPECTED_ALEMBIC="${EXPECTED_ALEMBIC:-0006}"
else
  export EXPECTED_API_TAG="${EXPECTED_API_TAG:-v0.16.0-phase6-episode}"
  export EXPECTED_WEB_TAG="${EXPECTED_WEB_TAG:-v0.16.0-phase6-episode}"
  export EXPECTED_WORKER_TAG="${EXPECTED_WORKER_TAG:-v0.16.0-phase6-episode}"
  export EXPECTED_ALEMBIC="${EXPECTED_ALEMBIC:-0006}"
fi

exec bash /tmp/check_drift.sh
