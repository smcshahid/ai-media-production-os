#!/usr/bin/env bash
# Import AIMPOS web image and roll out web + ingress (Phase 3C).
set -euo pipefail
NS=aimpos-mwayolares
WEB_IMAGE="${AIMPOS_WEB_IMAGE:-docker.io/library/aimpos-web:v0.13.0-phase3d}"
WEB_TAR="${WEB_TAR:?set WEB_TAR path to docker save tarball on Olares host}"
K="sudo k3s kubectl"
CTR="sudo ctr -a /run/containerd/containerd.sock -n k8s.io"
CHART_DIR="${CHART_DIR:-/tmp/aimpos-olares-chart}"

echo "Importing web $WEB_TAR as $WEB_IMAGE"
$CTR images import "$WEB_TAR"

echo "Installing Helm chart from $CHART_DIR"
helm upgrade --install aimpos-web "$CHART_DIR" \
  -n "$NS" \
  --set webImage="$WEB_IMAGE" \
  --wait --timeout 5m

$K rollout status deployment/aimpos-web -n "$NS" --timeout=300s
$K rollout status deployment/aimposingress -n "$NS" --timeout=300s

if [ -f /tmp/aimpos-application.yaml ]; then
  echo "Applying Olares Application CR"
  $K apply -f /tmp/aimpos-application.yaml
fi

echo "Deployed web=$WEB_IMAGE ingress=aimposingress:8080"
