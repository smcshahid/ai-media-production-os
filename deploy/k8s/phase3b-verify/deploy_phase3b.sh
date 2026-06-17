#!/usr/bin/env bash
# Deploy Phase 3B API image to Olares k3s (read-only verification path).
set -euo pipefail
NS=aimpos-mwayolares
API_IMAGE="${AIMPOS_API_IMAGE:-docker.io/library/aimpos-api:dev}"
API_TAR="${API_TAR:?set API_TAR path to docker save tarball on Olares host}"
K="sudo k3s kubectl"
CTR="sudo ctr -a /run/containerd/containerd.sock -n k8s.io"

echo "Importing API $API_TAR as $API_IMAGE"
$CTR images import "$API_TAR"
$K set image deployment/aimpos-api api="$API_IMAGE" -n "$NS"
$K rollout restart deployment/aimpos-api -n "$NS"
$K rollout status deployment/aimpos-api -n "$NS" --timeout=300s
echo "Deployed API=$API_IMAGE"
