#!/usr/bin/env bash
# Launch US-V08 E2E on Olares (nohup wrapper).
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
export TOKEN=$($K get secret aimpos-api-env -n $NS -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
export PGPW=$($K get secret aimpos-postgres-auth -n $NS -o jsonpath='{.data.postgres-password}' | base64 -d)
export PROJECT=ba0c4636-817c-423b-9771-20100e080b76
export EVID_DIR=/tmp/usv08-evidence
mkdir -p "$EVID_DIR"
nohup bash /tmp/verify_usv08_e2e.sh > /tmp/usv08-e2e-nohup.log 2>&1 &
echo "E2E_PID=$!"
