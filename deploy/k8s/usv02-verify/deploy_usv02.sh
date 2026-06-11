#!/usr/bin/env bash
# Import US-V02 baseline images (api:us19 + worker:us18) and rollout on Olares.
set -euo pipefail
NS=aimpos-mwayolares
API_IMAGE="${AIMPOS_API_IMAGE:-docker.io/library/aimpos-api:us19}"
WORKER_IMAGE="${AIMPOS_WORKER_IMAGE:-docker.io/library/aimpos-worker:us18}"
API_TAR="${API_TAR:-}"
WORKER_TAR="${WORKER_TAR:-}"
K="sudo k3s kubectl"
CTR="sudo ctr -a /run/containerd/containerd.sock -n k8s.io"

if [ -n "$API_TAR" ]; then
  echo "Importing API $API_TAR as $API_IMAGE"
  $CTR images import "$API_TAR"
  $K set image deployment/aimpos-api api="$API_IMAGE" -n "$NS"
fi
if [ -n "$WORKER_TAR" ]; then
  echo "Importing worker $WORKER_TAR as $WORKER_IMAGE"
  $CTR images import "$WORKER_TAR"
  $K set image deployment/aimpos-worker worker="$WORKER_IMAGE" -n "$NS"
fi

$K rollout restart deployment/aimpos-api -n "$NS" 2>/dev/null || true
$K rollout restart deployment/aimpos-worker -n "$NS" 2>/dev/null || true
$K rollout status deployment/aimpos-api -n "$NS" --timeout=300s
$K rollout status deployment/aimpos-worker -n "$NS" --timeout=300s
echo "Deployed API=$API_IMAGE WORKER=$WORKER_IMAGE"
