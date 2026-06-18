#!/usr/bin/env bash
set -euo pipefail
export TOKEN=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
export PGPW=$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.postgres-password}' | base64 -d)
export PROJECT=ba0c4636-817c-423b-9771-20100e080b76
export EVID_DIR=/tmp/usv08b-evidence
export USV08B_ONLY_PATH=D
bash /tmp/verify_usv08b_e2e.sh
