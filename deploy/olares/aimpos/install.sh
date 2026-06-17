#!/usr/bin/env bash
# AIMPOS Olares — guided install from release manifest (Phase 3D).
# Run on the Olares host after copying chart + image tars.
set -euo pipefail

NS=aimpos-mwayolares
RELEASE="${AIMPOS_RELEASE:-v0.13.0-phase3d}"
CHART_DIR="${CHART_DIR:-/tmp/aimpos-olares-chart}"
API_TAR="${API_TAR:-/tmp/aimpos-api-${RELEASE}.tar}"
WEB_TAR="${WEB_TAR:-/tmp/aimpos-web-${RELEASE}.tar}"
WORKER_TAR="${WORKER_TAR:-/tmp/aimpos-worker-${RELEASE}.tar}"

echo "AIMPOS install release=$RELEASE"
echo "Prerequisites: backend stack running in $NS (postgres, minio, redis, temporal, api, worker)"
echo "See DEPENDENCIES.md for full inventory"

if [ ! -d "$CHART_DIR" ]; then
  echo "ERROR: chart dir missing: $CHART_DIR"
  echo "Copy deploy/olares/aimpos/ to Olares host"
  exit 1
fi

export AIMPOS_API_IMAGE="docker.io/library/aimpos-api:${RELEASE}"
export AIMPOS_WEB_IMAGE="docker.io/library/aimpos-web:${RELEASE}"
export AIMPOS_WORKER_IMAGE="docker.io/library/aimpos-worker:${RELEASE}"
export API_TAR WEB_TAR WORKER_TAR CHART_DIR

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEPLOY="${SCRIPT_DIR}/../../k8s/phase3d-verify/deploy_release.sh"
if [ ! -f "$DEPLOY" ]; then
  DEPLOY="/tmp/deploy_release.sh"
fi

if [ -f "$DEPLOY" ]; then
  bash "$DEPLOY"
else
  echo "ERROR: deploy_release.sh not found"
  exit 1
fi

if [ -f "$CHART_DIR/templates/application.yaml" ] || [ -f /tmp/aimpos-application.yaml ]; then
  APP="${APP_CR:-/tmp/aimpos-application.yaml}"
  [ -f "$APP" ] && sudo k3s kubectl apply -f "$APP"
fi

echo ""
echo "Install complete. Verify with:"
echo "  make verify-all-olares   (from operator workstation)"
echo "  make check-drift-olares"
