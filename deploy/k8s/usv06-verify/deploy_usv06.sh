#!/usr/bin/env bash
# US-V06 — deploy Phase 5 audio narration images to Olares.
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
CTR="sudo ctr -a /run/containerd/containerd.sock -n k8s.io"

TAG="${AIMPOS_USV06_TAG:-usv06-phase5}"
API_IMAGE="${AIMPOS_API_IMAGE:-docker.io/library/aimpos-api:${TAG}}"
WEB_IMAGE="${AIMPOS_WEB_IMAGE:-docker.io/library/aimpos-web:${TAG}}"
WORKER_IMAGE="${AIMPOS_WORKER_IMAGE:-docker.io/library/aimpos-worker:${TAG}}"

import_tar() {
  local tar="$1" image="$2"
  echo "Importing $tar -> $image"
  $CTR images import "$tar"
}

for pair in "${API_TAR:-/tmp/aimpos-api-${TAG}.tar}:${API_IMAGE}" \
             "${WEB_TAR:-/tmp/aimpos-web-${TAG}.tar}:${WEB_IMAGE}" \
             "${WORKER_TAR:-/tmp/aimpos-worker-${TAG}.tar}:${WORKER_IMAGE}"; do
  tar="${pair%%:*}"
  img="${pair#*:}"
  if [ -f "$tar" ]; then import_tar "$tar" "$img"; else echo "WARN missing $tar"; fi
done

echo "Rolling API -> $API_IMAGE"
$K set image deployment/aimpos-api api="$API_IMAGE" -n "$NS"
$K rollout status deployment/aimpos-api -n "$NS" --timeout=300s

echo "Rolling worker -> $WORKER_IMAGE"
$K set image deployment/aimpos-worker worker="$WORKER_IMAGE" -n "$NS" 2>/dev/null || \
  $K set image deployment/aimpos-worker aimpos-worker="$WORKER_IMAGE" -n "$NS"
$K rollout status deployment/aimpos-worker -n "$NS" --timeout=300s

echo "Setting worker narration env"
$K set env deployment/aimpos-worker -n "$NS" NARRATION_ENABLED=true NARRATION_TTS_PROVIDER=espeak

echo "Rolling web -> $WEB_IMAGE"
$K set image deployment/aimpos-web web="$WEB_IMAGE" -n "$NS" 2>/dev/null || \
  $K set image deployment/aimpos-web aimpos-web="$WEB_IMAGE" -n "$NS"
$K rollout status deployment/aimpos-web -n "$NS" --timeout=300s

echo "US-V06 deploy complete: API=$API_IMAGE WORKER=$WORKER_IMAGE WEB=$WEB_IMAGE"
