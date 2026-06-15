#!/usr/bin/env bash
# US-V03 Olares remote orchestration — Path A + Path B + evidence collect.
set -euo pipefail
export PGPW=$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.postgres-password}' | base64 -d)
export TOKEN=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)

echo "========== PF-03 ComfyUI =========="
bash /tmp/prep_comfyui.sh

LOG="/tmp/usv03-verify-$(date +%Y%m%d-%H%M%S).log"
echo "LOG=$LOG"

bash /tmp/verify_usv03.sh 2>&1 | tee "$LOG"
RC=${PIPESTATUS[0]}

if [ -z "${PROJECT:-}" ]; then
  PROJECT=$(grep '^PROJECT=' "$LOG" | tail -1 | cut -d= -f2-)
  export PROJECT
fi
if [ -z "${RUN_ID:-}" ]; then
  RUN_ID=$(grep '^RUN_ID=' "$LOG" | tail -1 | cut -d= -f2-)
  export RUN_ID
fi

echo "========== SQL collect =========="
export EVIDENCE_SQL_DIR="/tmp/usv03-sql-$(date +%Y%m%d)"
bash /tmp/collect_usv03.sh 2>&1 | tee "/tmp/usv03-collect.log"

echo "LOG=$LOG"
echo "VERIFY_RC=$RC"
echo "PROJECT=$PROJECT RUN_ID=$RUN_ID"
echo "SQL_DIR=$EVIDENCE_SQL_DIR"
exit $RC
