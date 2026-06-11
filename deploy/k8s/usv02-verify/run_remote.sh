#!/usr/bin/env bash
set -euo pipefail
export PGPW=$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.postgres-password}' | base64 -d)
export TOKEN=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)

echo "========== PF-03 ComfyUI =========="
bash /tmp/prep_comfyui.sh

echo "========== PF-05 Fresh project =========="
eval "$(bash /tmp/create_project.sh | grep '^PROJECT=')"
export PROJECT
echo "Using PROJECT=$PROJECT"

LOG="/tmp/usv02-verify-$(date +%Y%m%d-%H%M%S).log"
bash /tmp/verify_usv02.sh 2>&1 | tee "$LOG"
RC=${PIPESTATUS[0]}

if [ -z "${RUN_ID:-}" ]; then
  RUN_ID=$(grep '^RUN_ID=' "$LOG" | tail -1 | cut -d= -f2-)
  export RUN_ID
fi

echo "========== SQL collect =========="
export EVIDENCE_SQL_DIR="/tmp/usv02-sql-$(date +%Y%m%d)"
bash /tmp/collect_usv02.sh 2>&1 | tee "/tmp/usv02-collect.log"

echo "LOG=$LOG"
echo "VERIFY_RC=$RC"
echo "PROJECT=$PROJECT RUN_ID=$RUN_ID"
exit $RC
