#!/usr/bin/env bash
set -euo pipefail
export PGPW=$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.postgres-password}' | base64 -d)
export TOKEN=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)

echo "========== PF-05 Fresh project =========="
eval "$(bash /tmp/create_project.sh | grep '^PROJECT=')"
export PROJECT
echo "Using PROJECT=$PROJECT"

LOG="/tmp/us18-verify-$(date +%Y%m%d-%H%M%S).log"
bash /tmp/verify_us18.sh 2>&1 | tee "$LOG"
RC=${PIPESTATUS[0]}
grep '^RUN_ID=' "$LOG" | tail -1 | cut -d= -f2- > /tmp/us18-run-id.txt || true
export RUN_ID=$(cat /tmp/us18-run-id.txt 2>/dev/null || true)
echo "LOG=$LOG VERIFY_RC=$RC PROJECT=$PROJECT RUN_ID=$RUN_ID"
exit $RC
