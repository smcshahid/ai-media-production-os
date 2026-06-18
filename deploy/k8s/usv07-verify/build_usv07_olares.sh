#!/usr/bin/env bash
# Build US-V07 Phase 6 images on Olares host from synced source.
set -euo pipefail
REPO="${REPO_DIR:-/tmp/aimpos-usv07-src}"
TAG="${AIMPOS_USV07_TAG:-usv07-phase6}"
cd "$REPO"

echo "Building from $REPO tag=$TAG"
docker build -f api/Dockerfile -t "aimpos-api:${TAG}" .
docker build -f worker/Dockerfile -t "aimpos-worker:${TAG}" .
docker build -f web/Dockerfile --build-arg VITE_API_URL= -t "aimpos-web:${TAG}" .

docker save "aimpos-api:${TAG}" -o "/tmp/aimpos-api-${TAG}.tar"
docker save "aimpos-worker:${TAG}" -o "/tmp/aimpos-worker-${TAG}.tar"
docker save "aimpos-web:${TAG}" -o "/tmp/aimpos-web-${TAG}.tar"
echo "Built and saved tars in /tmp"
