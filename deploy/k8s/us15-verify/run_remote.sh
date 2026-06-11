#!/usr/bin/env bash
set -euo pipefail
export PGPW=$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.postgres-password}' | base64 -d)
export TOKEN=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
export MINIO_USER=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.MINIO_ROOT_USER}' | base64 -d)
export MINIO_PASS=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.MINIO_ROOT_PASSWORD}' | base64 -d)
export PROJECT="${PROJECT:-ba0c4636-817c-423b-9771-20100e080b76}"
export MINIO_BUCKET="${MINIO_BUCKET:-aimpos-hot-assets}"
LOG="/tmp/us15-verify-$(date +%Y%m%d-%H%M%S).log"
bash /tmp/verify_us15.sh 2>&1 | tee "$LOG"
echo "LOG=$LOG"
