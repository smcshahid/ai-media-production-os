#!/usr/bin/env bash
# Copy release manifest + loader to Olares /tmp for drift checks (Phase 8).
set -euo pipefail
HOST="${1:?olares host e.g. olares@10.0.0.34}"
ROOT="${2:-.}"

scp -q "$ROOT/deploy/release/manifest.yaml" "${HOST}:/tmp/aimpos-manifest.yaml"
scp -q "$ROOT/scripts/release/load-manifest-env.sh" "${HOST}:/tmp/load-manifest-env.sh"
echo "synced manifest + loader to $HOST:/tmp/"
