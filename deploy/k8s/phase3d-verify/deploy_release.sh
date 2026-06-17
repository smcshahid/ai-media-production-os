#!/usr/bin/env bash
# Phase 3D — deploy pinned API + web + worker images to Olares k3s.
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
CTR="sudo ctr -a /run/containerd/containerd.sock -n k8s.io"

API_IMAGE="${AIMPOS_API_IMAGE:-docker.io/library/aimpos-api:v0.13.0-phase3d}"
WEB_IMAGE="${AIMPOS_WEB_IMAGE:-docker.io/library/aimpos-web:v0.13.0-phase3d}"
WORKER_IMAGE="${AIMPOS_WORKER_IMAGE:-docker.io/library/aimpos-worker:v0.13.0-phase3d}"
CHART_DIR="${CHART_DIR:-/tmp/aimpos-olares-chart}"

import_tar() {
  local tar="$1" image="$2"
  if [ -f "$tar" ]; then
    echo "Importing $tar as $image"
    $CTR images import "$tar"
  else
    echo "WARN: tar missing $tar — assuming image already on host"
  fi
}

[ -n "${API_TAR:-}" ] && import_tar "$API_TAR" "$API_IMAGE"
[ -n "${WEB_TAR:-}" ] && import_tar "$WEB_TAR" "$WEB_IMAGE"
[ -n "${WORKER_TAR:-}" ] && import_tar "$WORKER_TAR" "$WORKER_IMAGE"

echo "Rolling API -> $API_IMAGE"
$K set image deployment/aimpos-api api="$API_IMAGE" -n "$NS"
$K rollout status deployment/aimpos-api -n "$NS" --timeout=300s

echo "Rolling worker -> $WORKER_IMAGE"
$K set image deployment/aimpos-worker worker="$WORKER_IMAGE" -n "$NS" 2>/dev/null || \
  $K set image deployment/aimpos-worker aimpos-worker="$WORKER_IMAGE" -n "$NS" 2>/dev/null || \
  echo "WARN: worker deployment name may differ — set image manually"
$K rollout status deployment/aimpos-worker -n "$NS" --timeout=300s 2>/dev/null || true

if [ -d "$CHART_DIR" ]; then
  echo "Installing web chart from $CHART_DIR"
  helm upgrade --install aimpos-web "$CHART_DIR" \
    -n "$NS" \
    --set webImage="$WEB_IMAGE" \
    --wait --timeout 5m
  $K rollout status deployment/aimpos-web -n "$NS" --timeout=300s
  $K rollout status deployment/aimposingress -n "$NS" --timeout=300s
else
  echo "Rolling web -> $WEB_IMAGE (no chart dir)"
  $K set image deployment/aimpos-web web="$WEB_IMAGE" -n "$NS" 2>/dev/null || \
    $K set image deployment/aimpos-web aimpos-web="$WEB_IMAGE" -n "$NS"
  $K rollout status deployment/aimpos-web -n "$NS" --timeout=300s
fi

if [ -f /tmp/aimpos-application.yaml ]; then
  echo "Applying Olares Application CR"
  $K apply -f /tmp/aimpos-application.yaml
fi

echo "Deployed API=$API_IMAGE WEB=$WEB_IMAGE WORKER=$WORKER_IMAGE"
