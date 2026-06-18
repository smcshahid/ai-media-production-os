#!/usr/bin/env bash
# Export drift-check env vars from deploy/release/manifest.yaml (Phase 8).
set -euo pipefail
MANIFEST="${1:-deploy/release/manifest.yaml}"
ROOT="${2:-.}"

M="$MANIFEST"
if [[ "$MANIFEST" != /* ]]; then
  M="$ROOT/$MANIFEST"
fi

if [ ! -f "$M" ]; then
  echo "missing manifest: $M" >&2
  exit 1
fi

export EXPECTED_API_TAG="${EXPECTED_API_TAG:-$(grep -A1 'api:' "$M" | grep tag | sed -n 's/.*"\([^"]*\)".*/\1/p' | head -1)}"
export EXPECTED_WEB_TAG="${EXPECTED_WEB_TAG:-$(grep -A1 'web:' "$M" | grep tag | sed -n 's/.*"\([^"]*\)".*/\1/p' | head -1)}"
export EXPECTED_WORKER_TAG="${EXPECTED_WORKER_TAG:-$(grep -A1 'worker:' "$M" | grep tag | sed -n 's/.*"\([^"]*\)".*/\1/p' | head -1)}"
export EXPECTED_ALEMBIC="${EXPECTED_ALEMBIC:-$(grep alembic_head "$M" | sed -n 's/.*"\([^"]*\)".*/\1/p' | head -1)}"

echo "manifest env: API=$EXPECTED_API_TAG WEB=$EXPECTED_WEB_TAG WORKER=$EXPECTED_WORKER_TAG ALEMBIC=$EXPECTED_ALEMBIC"
