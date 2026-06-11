#!/usr/bin/env bash
set -euo pipefail
export PGPW=$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.postgres-password}' | base64 -d)
export TOKEN=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
export MINIO_USER=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.MINIO_ROOT_USER}' | base64 -d)
export MINIO_PASS=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.MINIO_ROOT_PASSWORD}' | base64 -d)
export PROJECT="${PROJECT:-ba0c4636-817c-423b-9771-20100e080b76}"
export MINIO_BUCKET="${MINIO_BUCKET:-aimpos-hot-assets}"

echo "Starting ComfyUI launcher..."
curl -s -m 10 -X POST http://127.0.0.1:3000/api/start || echo "WARN: launcher start skipped"

if [ -f /tmp/complete_old_run.sh ]; then
  echo "Completing any active run at STORYBOARD gate..."
  bash /tmp/complete_old_run.sh || true
fi

LOG="/tmp/us17-e2e-$(date +%Y%m%d-%H%M%S).log"
bash /tmp/verify_us17_e2e.sh 2>&1 | tee "$LOG"
echo "LOG=$LOG"
