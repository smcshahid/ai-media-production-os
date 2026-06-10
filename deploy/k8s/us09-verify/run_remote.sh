#!/usr/bin/env bash
# Run US-09 Olares verification on-node (sources secrets from cluster).
set -euo pipefail
export PGPW=$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.postgres-password}' | base64 -d)
export TOKEN=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
export PROJECT="${PROJECT:-ba0c4636-817c-423b-9771-20100e080b76}"
LOG="/tmp/us09-verify-$(date +%Y%m%d-%H%M%S).log"
bash /tmp/verify_us09.sh 2>&1 | tee "$LOG"
echo "LOG=$LOG"
