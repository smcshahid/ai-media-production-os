#!/usr/bin/env bash
# Import fixed US-V06 worker + API images and rollout (operator helper).
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
CTR="sudo ctr -a /run/containerd/containerd.sock -n k8s.io"
TAG="${AIMPOS_USV06_TAG:-usv06-phase5}"

import_if_present() {
  local tar="$1" image="$2"
  if [ -f "$tar" ]; then
    echo "Importing $tar -> $image"
    $CTR images import "$tar"
  else
    echo "WARN missing $tar"
  fi
}

WORKER_TAR="${WORKER_TAR:-/tmp/aimpos-worker-${TAG}.tar}"
API_TAR="${API_TAR:-/tmp/aimpos-api-${TAG}.tar}"
WORKER_IMG="docker.io/library/aimpos-worker:${TAG}"
API_IMG="docker.io/library/aimpos-api:${TAG}"

import_if_present "$API_TAR" "$API_IMG"
import_if_present "$WORKER_TAR" "$WORKER_IMG"

if [ -f "$API_TAR" ]; then
  echo "Rolling API -> $API_IMG"
  $K set image deployment/aimpos-api api="$API_IMG" -n "$NS"
  $K rollout restart deployment/aimpos-api -n "$NS"
  $K rollout status deployment/aimpos-api -n "$NS" --timeout=300s
fi

if [ -f "$WORKER_TAR" ]; then
  echo "Rolling worker -> $WORKER_IMG"
  $K set image deployment/aimpos-worker worker="$WORKER_IMG" -n "$NS" 2>/dev/null || \
    $K set image deployment/aimpos-worker aimpos-worker="$WORKER_IMG" -n "$NS"
  $K set env deployment/aimpos-worker -n "$NS" NARRATION_ENABLED=true NARRATION_TTS_PROVIDER=espeak
  $K rollout restart deployment/aimpos-worker -n "$NS"
  $K rollout status deployment/aimpos-worker -n "$NS" --timeout=300s
  echo "Verify TTS module"
  $K exec deploy/aimpos-worker -n "$NS" -- python -c \
    "from app.agents.narration.tts import generate_narration_wav; from app.agents.narration.constants import SOURCE_ESPEAK; print(SOURCE_ESPEAK)"
fi

echo "US-V06 hotfix rollout complete"
