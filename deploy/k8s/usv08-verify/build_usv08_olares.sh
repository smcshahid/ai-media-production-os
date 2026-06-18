#!/usr/bin/env bash
# Build US-V08 Phase 7 images on Olares host from synced source.
set -euo pipefail
REPO="${REPO_DIR:-/tmp/aimpos-usv08-src}"
TAG="${AIMPOS_USV08_TAG:-usv08-phase7}"
cd "$REPO"

DOCKER="${DOCKER:-docker}"
if ! command -v docker >/dev/null 2>&1; then
  DOCKER="/usr/local/bin/nerdctl"
fi

echo "Building from $REPO tag=$TAG using $DOCKER"
$DOCKER build -f api/Dockerfile -t "aimpos-api:${TAG}" .
$DOCKER build -f worker/Dockerfile -t "aimpos-worker:${TAG}" .
$DOCKER build -f web/Dockerfile --build-arg VITE_API_URL= -t "aimpos-web:${TAG}" .

$DOCKER save "aimpos-api:${TAG}" -o "/tmp/aimpos-api-${TAG}.tar"
$DOCKER save "aimpos-worker:${TAG}" -o "/tmp/aimpos-worker-${TAG}.tar"
$DOCKER save "aimpos-web:${TAG}" -o "/tmp/aimpos-web-${TAG}.tar"
echo "Built and saved tars in /tmp"
