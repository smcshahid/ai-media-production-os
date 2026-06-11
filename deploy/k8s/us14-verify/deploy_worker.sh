#!/usr/bin/env bash
# Import US-14 worker image and rollout on Olares.
set -euo pipefail
NS=aimpos-mwayolares
IMAGE="${AIMPOS_WORKER_IMAGE:-docker.io/library/aimpos-worker:us14}"
TAR="${WORKER_TAR:?set WORKER_TAR to path of aimpos-worker-us14.tar on Olares node}"
K="sudo k3s kubectl"
CTR="sudo ctr -a /run/containerd/containerd.sock -n k8s.io"

echo "Importing $TAR as $IMAGE"
$CTR images import "$TAR"
$K set image deployment/aimpos-worker worker="$IMAGE" -n "$NS"
$K rollout status deployment/aimpos-worker -n "$NS" --timeout=180s
echo "Worker deployed: $IMAGE"
