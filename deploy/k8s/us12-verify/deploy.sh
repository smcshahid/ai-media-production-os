#!/usr/bin/env bash
# Create the worker env secret + deploy ephemeral Temporal for US-12 verification.
#
# Secrets are read from the environment (never hardcode). Source them from the
# live cluster secret before running, e.g.:
#   export PGPW=$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.password}' | base64 -d)
#   export MINIO_USER=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.MINIO_ROOT_USER}' | base64 -d)
#   export MINIO_PASSWORD=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.MINIO_ROOT_PASSWORD}' | base64 -d)
set -euo pipefail
K="sudo k3s kubectl"
NS=aimpos-mwayolares

: "${PGPW:?set PGPW to the aimpos-postgres password}"
: "${MINIO_USER:?set MINIO_USER to the MinIO access key}"
: "${MINIO_PASSWORD:?set MINIO_PASSWORD to the MinIO secret key}"
PGUSER="${PGUSER:-aimpos}"
PGHOST="${PGHOST:-aimpos-postgres}"
PGDB="${PGDB:-aimpos_spark}"

$K create secret generic aimpos-worker-env -n "$NS" \
  --from-literal=DATABASE_URL="postgresql+psycopg://${PGUSER}:${PGPW}@${PGHOST}:5432/${PGDB}" \
  --from-literal=MINIO_ENDPOINT="aimpos-minio:9000" \
  --from-literal=MINIO_ROOT_USER="${MINIO_USER}" \
  --from-literal=MINIO_ROOT_PASSWORD="${MINIO_PASSWORD}" \
  --from-literal=MINIO_BUCKET="aimpos-hot-assets" \
  --from-literal=MINIO_SECURE="false" \
  --from-literal=OLLAMA_HOST="http://ollama.ollamaserver-shared:11434" \
  --from-literal=TEMPORAL_ADDRESS="temporal:7233" \
  --from-literal=AIMPOS_CONFIG_ROOT="/srv/configs" \
  --dry-run=client -o yaml | $K apply -f -

$K apply -f /tmp/temporal.yaml
echo "=== applied ==="
$K get deploy,svc,secret -n "$NS" | grep -E 'temporal|worker|NAME'
