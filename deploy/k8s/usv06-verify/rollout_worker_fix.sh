#!/usr/bin/env bash
# Import fixed US-V06 worker image and rollout (operator helper).
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
CTR="sudo ctr -a /run/containerd/containerd.sock -n k8s.io"
TAG="${AIMPOS_USV06_TAG:-usv06-phase5}"
TAR="${WORKER_TAR:-/tmp/aimpos-worker-${TAG}.tar}"
IMG="docker.io/library/aimpos-worker:${TAG}"

echo "Importing $TAR -> $IMG"
$CTR images import "$TAR"

echo "Rolling worker -> $IMG"
$K set image deployment/aimpos-worker worker="$IMG" -n "$NS" 2>/dev/null || \
  $K set image deployment/aimpos-worker aimpos-worker="$IMG" -n "$NS"
$K set env deployment/aimpos-worker -n "$NS" NARRATION_ENABLED=true NARRATION_TTS_PROVIDER=espeak
$K rollout restart deployment/aimpos-worker -n "$NS"
$K rollout status deployment/aimpos-worker -n "$NS" --timeout=300s

echo "Verify TTS module"
$K exec deploy/aimpos-worker -n "$NS" -- python -c \
  "from app.agents.narration.tts import generate_narration_wav; from app.agents.narration.constants import SOURCE_ESPEAK; print(SOURCE_ESPEAK)"
echo "Worker rollout complete"
