#!/usr/bin/env bash
# Ensure worker secret includes COMFYUI_HOST for Olares (M1-DV ComfyUI service).
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
COMFYUI_HOST="${COMFYUI_HOST:-http://comfyui.comfyuisharev2server-shared:8190}"

PGPW="${PGPW:-$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)}"
MINIO_USER="${MINIO_USER:-$($K get secret aimpos-api-env -n "$NS" -o jsonpath='{.data.MINIO_ROOT_USER}' | base64 -d)}"
MINIO_PASSWORD="${MINIO_PASSWORD:-$($K get secret aimpos-api-env -n "$NS" -o jsonpath='{.data.MINIO_ROOT_PASSWORD}' | base64 -d)}"

$K create secret generic aimpos-worker-env -n "$NS" \
  --from-literal=DATABASE_URL="postgresql+psycopg://aimpos:${PGPW}@aimpos-postgres:5432/aimpos_spark" \
  --from-literal=MINIO_ENDPOINT="aimpos-minio:9000" \
  --from-literal=MINIO_ROOT_USER="${MINIO_USER}" \
  --from-literal=MINIO_ROOT_PASSWORD="${MINIO_PASSWORD}" \
  --from-literal=MINIO_BUCKET="aimpos-hot-assets" \
  --from-literal=MINIO_SECURE="false" \
  --from-literal=OLLAMA_HOST="http://ollama.ollamaserver-shared:11434" \
  --from-literal=COMFYUI_HOST="${COMFYUI_HOST}" \
  --from-literal=REDIS_URL="redis://aimpos-redis-master:6379/0" \
  --from-literal=TEMPORAL_ADDRESS="temporal:7233" \
  --from-literal=AIMPOS_CONFIG_ROOT="/srv/configs" \
  --dry-run=client -o yaml | $K apply -f -

$K rollout restart deployment/aimpos-worker -n "$NS"
$K rollout status deployment/aimpos-worker -n "$NS" --timeout=300s
echo "Worker env patched COMFYUI_HOST=$COMFYUI_HOST"
