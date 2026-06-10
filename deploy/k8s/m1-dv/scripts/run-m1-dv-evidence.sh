#!/usr/bin/env bash
# M1-DV evidence helpers — Phase A health + MinIO round-trip.
set -euo pipefail

NS="${AIMPOS_NS:-aimpos-mwayolares}"
KUBECTL="${KUBECTL:-sudo k3s kubectl}"
PHASE="${1:-all}"

log() { echo "[evidence] $*"; }

phase_a() {
  log "Phase A — GET /health via port-forward"
  $KUBECTL port-forward -n "$NS" svc/aimpos-api 18000:8000 >/tmp/aimpos-pf.log 2>&1 &
  PF_PID=$!
  trap 'kill $PF_PID 2>/dev/null || true' EXIT
  sleep 2
  curl -sS -w "\nhttp_code:%{http_code}\n" "http://127.0.0.1:18000/health"
  kill $PF_PID 2>/dev/null || true
  trap - EXIT
}

phase_minio() {
  log "MinIO round-trip (put + stat via mc pod)"
  MINIO_USER="$($KUBECTL get secret aimpos-minio-auth -n "$NS" -o jsonpath='{.data.root-user}' | base64 -d)"
  MINIO_PASS="$($KUBECTL get secret aimpos-minio-auth -n "$NS" -o jsonpath='{.data.root-password}' | base64 -d)"
  $KUBECTL delete pod aimpos-minio-roundtrip -n "$NS" --ignore-not-found --wait=true 2>/dev/null || true
  $KUBECTL run aimpos-minio-roundtrip --restart=Never -n "$NS" \
    --image=docker.io/minio/mc:latest --command -- sh -c \
    "mc alias set local http://aimpos-minio:9000 '$MINIO_USER' '$MINIO_PASS' && \
     echo 'm1-dv-roundtrip' | mc pipe local/aimpos-hot-assets/smoke/m1-dv-roundtrip.txt && \
     mc stat local/aimpos-hot-assets/smoke/m1-dv-roundtrip.txt && \
     mc cat local/aimpos-hot-assets/smoke/m1-dv-roundtrip.txt"
  for _ in $(seq 1 30); do
    phase="$($KUBECTL get pod aimpos-minio-roundtrip -n "$NS" -o jsonpath='{.status.phase}' 2>/dev/null || echo "")"
    [[ "$phase" == "Succeeded" || "$phase" == "Failed" ]] && break
    sleep 2
  done
  $KUBECTL logs aimpos-minio-roundtrip -n "$NS"
  $KUBECTL delete pod aimpos-minio-roundtrip -n "$NS" --ignore-not-found
  [[ "$phase" == "Succeeded" ]] || exit 1
}

case "$PHASE" in
  phase-a) phase_a ;;
  phase-minio) phase_minio ;;
  all)
    phase_a
    echo ""
    phase_minio
    ;;
  *)
    echo "usage: $0 [phase-a|phase-minio|all]"
    exit 1
    ;;
esac
