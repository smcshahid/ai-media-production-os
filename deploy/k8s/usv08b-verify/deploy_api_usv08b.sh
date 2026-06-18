#!/usr/bin/env bash
# Roll API only for hotfix deploy on Olares.
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
CTR="sudo ctr -a /run/containerd/containerd.sock -n k8s.io"
TAG="${AIMPOS_USV08B_TAG:-usv08b-phase75}"
API_IMAGE="${AIMPOS_API_IMAGE:-docker.io/library/aimpos-api:${TAG}}"
TAR="${API_TAR:-/tmp/aimpos-api-${TAG}.tar}"
if [ -f "$TAR" ]; then
  $CTR images import "$TAR"
fi
$K set image deployment/aimpos-api api="$API_IMAGE" -n "$NS"
$K rollout status deployment/aimpos-api -n "$NS" --timeout=300s
$K delete pod -l app=aimpos-api -n "$NS" --wait=true
$K rollout status deployment/aimpos-api -n "$NS" --timeout=300s
echo "API rolled to $API_IMAGE"
