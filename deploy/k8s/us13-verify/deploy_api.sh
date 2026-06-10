#!/usr/bin/env bash
# Import US-13 API image and rollout on Olares.
set -euo pipefail
NS=aimpos-mwayolares
IMAGE="${AIMPOS_API_IMAGE:-docker.io/library/aimpos-api:us13}"
TAR="${API_TAR:?set API_TAR to path of aimpos-api-us13.tar on Olares node}"
K="sudo k3s kubectl"
CTR="sudo ctr -a /run/containerd/containerd.sock -n k8s.io"

echo "Importing $TAR as $IMAGE"
$CTR images import "$TAR"
$K set image deployment/aimpos-api api="$IMAGE" -n "$NS"
$K rollout status deployment/aimpos-api -n "$NS" --timeout=180s
echo "API deployed: $IMAGE"
