#!/usr/bin/env bash
# US-V08B — deploy Phase 7.5 images using shared Olares rollout pattern (TD-P75-01).
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
CTR="sudo ctr -a /run/containerd/containerd.sock -n k8s.io"

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/olares_deploy_common.sh"
# shellcheck source=/dev/null
source "$LIB"

TAG="${AIMPOS_USV08B_TAG:-usv08b-phase75}"
API_IMAGE="${AIMPOS_API_IMAGE:-docker.io/library/aimpos-api:${TAG}}"
WEB_IMAGE="${AIMPOS_WEB_IMAGE:-docker.io/library/aimpos-web:${TAG}}"
WORKER_IMAGE="${AIMPOS_WORKER_IMAGE:-docker.io/library/aimpos-worker:${TAG}}"

for pair in "${API_TAR:-/tmp/aimpos-api-${TAG}.tar}:${API_IMAGE}" \
             "${WEB_TAR:-/tmp/aimpos-web-${TAG}.tar}:${WEB_IMAGE}" \
             "${WORKER_TAR:-/tmp/aimpos-worker-${TAG}.tar}:${WORKER_IMAGE}"; do
  tar="${pair%%:*}"
  img="${pair#*:}"
  if [ -f "$tar" ]; then olares_deploy_import_tar "$tar" "$img"; else echo "WARN missing $tar"; fi
done

olares_deploy_rollout aimpos-api api "$API_IMAGE"
olares_deploy_rollout aimpos-worker worker "$WORKER_IMAGE"
$K set env deployment/aimpos-worker -n "$NS" NARRATION_ENABLED=true NARRATION_TTS_PROVIDER=espeak
olares_deploy_rollout aimpos-web web "$WEB_IMAGE"

echo "US-V08B deploy complete: API=$API_IMAGE WORKER=$WORKER_IMAGE WEB=$WEB_IMAGE"
