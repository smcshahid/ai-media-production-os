#!/usr/bin/env bash
# M1-DV — API secret, Alembic migrate job, aimpos-api Deployment.
set -euo pipefail

NS="${AIMPOS_NS:-aimpos-mwayolares}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KUBECTL="${KUBECTL:-sudo k3s kubectl}"
IMAGE="${AIMPOS_API_IMAGE:?Set AIMPOS_API_IMAGE (e.g. docker.io/user/aimpos-api:m1-dv)}"

log() { echo "[aimpos-m1-dv] $*"; }

if ! $KUBECTL get namespace "$NS" >/dev/null 2>&1; then
  log "ERROR: namespace $NS missing — run deploy-infra.sh first"
  exit 1
fi

PG_PASS="$($KUBECTL get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)"
MINIO_USER="$($KUBECTL get secret aimpos-minio-auth -n "$NS" -o jsonpath='{.data.root-user}' | base64 -d)"
MINIO_PASS="$($KUBECTL get secret aimpos-minio-auth -n "$NS" -o jsonpath='{.data.root-password}' | base64 -d)"
API_TOKEN="${AIMPOS_API_TOKEN:-aimpos-m1-dv-$(openssl rand -hex 8)}"

log "apply aimpos-api-env secret"
$KUBECTL create secret generic aimpos-api-env -n "$NS" \
  --from-literal=AIMPOS_API_TOKEN="$API_TOKEN" \
  --from-literal=DATABASE_URL="postgresql+psycopg://aimpos:${PG_PASS}@aimpos-postgres:5432/aimpos_spark" \
  --from-literal=MINIO_ROOT_USER="$MINIO_USER" \
  --from-literal=MINIO_ROOT_PASSWORD="$MINIO_PASS" \
  --from-literal=MINIO_ENDPOINT="aimpos-minio:9000" \
  --from-literal=MINIO_BUCKET="aimpos-hot-assets" \
  --from-literal=REDIS_URL="redis://aimpos-redis-master:6379/0" \
  --from-literal=ENVIRONMENT="olares-m1-dv" \
  --from-literal=LOG_LEVEL="INFO" \
  --dry-run=client -o yaml | $KUBECTL apply -f -

log "migrate (alembic upgrade head)"
$KUBECTL delete job aimpos-migrate -n "$NS" --ignore-not-found
sed "s|REPLACE_AIMPOS_API_IMAGE|$IMAGE|g" "$ROOT/job-migrate.yaml" | $KUBECTL apply -f -
$KUBECTL wait --for=condition=complete job/aimpos-migrate -n "$NS" --timeout=300s
$KUBECTL logs job/aimpos-migrate -n "$NS"

log "deploy aimpos-api"
sed "s|REPLACE_AIMPOS_API_IMAGE|$IMAGE|g" "$ROOT/api-deployment.yaml" | $KUBECTL apply -f -
$KUBECTL rollout status deployment/aimpos-api -n "$NS" --timeout=180s

log "API token (save for smoke/evidence): $API_TOKEN"
log "port-forward: $KUBECTL port-forward -n $NS svc/aimpos-api 8000:8000"
