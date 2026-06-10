#!/usr/bin/env bash
# M1-DV — namespace + Bitnami infra (Postgres, MinIO, Redis) + MinIO bucket bootstrap.
set -euo pipefail

NS="${AIMPOS_NS:-aimpos-mwayolares}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KUBECTL="${KUBECTL:-sudo k3s kubectl}"

log() { echo "[aimpos-m1-dv] $*"; }

log "namespace: $NS"
$KUBECTL apply -f "$ROOT/namespace.yaml"

create_secret() {
  local name="$1"
  if $KUBECTL get secret "$name" -n "$NS" >/dev/null 2>&1; then
    log "secret $name exists"
    return
  fi
  case "$name" in
    aimpos-postgres-auth)
      local pass
      pass="$(openssl rand -base64 24 | tr -d '/+=' | head -c 32)"
      $KUBECTL create secret generic aimpos-postgres-auth -n "$NS" \
        --from-literal=postgres-password="$pass"
      ;;
    aimpos-minio-auth)
      local user pass
      user="aimpos$(openssl rand -hex 3)"
      pass="$(openssl rand -base64 24 | tr -d '/+=' | head -c 32)"
      $KUBECTL create secret generic aimpos-minio-auth -n "$NS" \
        --from-literal=root-user="$user" \
        --from-literal=root-password="$pass"
      ;;
    *)
      log "ERROR: unknown secret $name"
      exit 1
      ;;
  esac
}

create_secret aimpos-postgres-auth
create_secret aimpos-minio-auth

helm repo add bitnami https://charts.bitnami.com/bitnami 2>/dev/null || true
helm repo update bitnami

log "helm: aimpos-postgres"
helm upgrade --install aimpos-postgres bitnami/postgresql \
  -n "$NS" -f "$ROOT/postgres-values.yaml" --wait --timeout 15m

log "helm: aimpos-minio"
helm upgrade --install aimpos-minio bitnami/minio \
  -n "$NS" -f "$ROOT/minio-values.yaml" --wait --timeout 15m

log "helm: aimpos-redis"
helm upgrade --install aimpos-redis bitnami/redis \
  -n "$NS" -f "$ROOT/redis-values.yaml" --wait --timeout 15m

log "bootstrap MinIO bucket aimpos-hot-assets"
MINIO_USER="$($KUBECTL get secret aimpos-minio-auth -n "$NS" -o jsonpath='{.data.root-user}' | base64 -d)"
MINIO_PASS="$($KUBECTL get secret aimpos-minio-auth -n "$NS" -o jsonpath='{.data.root-password}' | base64 -d)"
$KUBECTL delete pod aimpos-minio-bootstrap -n "$NS" --ignore-not-found --wait=true 2>/dev/null || true
$KUBECTL run aimpos-minio-bootstrap --restart=Never -n "$NS" \
  --image=docker.io/minio/mc:latest --command -- sh -c \
  "mc alias set local http://aimpos-minio:9000 '$MINIO_USER' '$MINIO_PASS' && \
   mc mb --ignore-existing local/aimpos-hot-assets && mc anonymous set none local/aimpos-hot-assets"

phase=""
for _ in $(seq 1 30); do
  phase="$($KUBECTL get pod aimpos-minio-bootstrap -n "$NS" -o jsonpath='{.status.phase}' 2>/dev/null || echo "")"
  [[ "$phase" == "Succeeded" || "$phase" == "Failed" ]] && break
  sleep 2
done
$KUBECTL logs aimpos-minio-bootstrap -n "$NS" || true
$KUBECTL delete pod aimpos-minio-bootstrap -n "$NS" --ignore-not-found
if [[ "$phase" != "Succeeded" ]]; then
  log "ERROR: MinIO bucket bootstrap failed (phase=${phase:-unknown})"
  exit 1
fi

log "infra ready in $NS"
$KUBECTL get pods -n "$NS"
