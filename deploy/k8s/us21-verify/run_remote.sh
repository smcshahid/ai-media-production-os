#!/usr/bin/env bash
set -euo pipefail
export PGPW=$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.postgres-password}' | base64 -d)
export TOKEN=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
export PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
export RUN_ID="${RUN_ID:?set RUN_ID}"
LOG="/tmp/us21-verify-$(date +%Y%m%d-%H%M%S).log"
bash /tmp/verify_us21.sh 2>&1 | tee "$LOG"
RC=${PIPESTATUS[0]}
echo "LOG=$LOG VERIFY_RC=$RC"
exit $RC
