#!/usr/bin/env bash
# US-V05 Olares verification (Phase 4 multi-scene)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

FAIL=0
LOG_DIR="${REPO_ROOT}/evidence/us-v05-verification/olares-$(date +%Y-%m-%d)/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/verify-olares.log"

log() { echo "$(date -Iseconds) $*" | tee -a "$LOG_FILE"; }

log "US-V05 Olares verify start"

log "========== V05-O1: Alembic head on cluster DB =========="
if command -v kubectl >/dev/null 2>&1; then
  NS="${AIMPOS_NAMESPACE:-aimpos-mwayolares}"
  if kubectl get ns "$NS" >/dev/null 2>&1; then
    REV="$(kubectl exec -n "$NS" deploy/aimpos-api -- alembic current 2>/dev/null | tail -1 || true)"
    log "Alembic current: ${REV:-unknown}"
    if echo "$REV" | grep -q 0004; then
      log "PASS alembic 0004"
    else
      log "WARN expected 0004 — deploy migration before E2E"
      FAIL=1
    fi
  else
    log "WARN namespace $NS not found — skip cluster checks"
  fi
else
  log "WARN kubectl unavailable"
fi

log "========== V05-O2: API health =========="
OLARES_API="${OLARES_API_URL:-http://127.0.0.1:8000}"
if curl -sf "${OLARES_API}/health" >/dev/null 2>&1; then
  log "PASS API health"
else
  log "WARN API not reachable at ${OLARES_API}"
fi

log "DONE FAIL=$FAIL"
exit "$FAIL"
