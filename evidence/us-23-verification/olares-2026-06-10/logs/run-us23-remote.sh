#!/usr/bin/env bash
set -euo pipefail
export PGPW=$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.postgres-password}' | base64 -d)
export TOKEN=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
export PROJECT_ID=76aa4418-d92d-45f7-954c-a10383ea511a
export RUN_ID=042983f7-0f55-48c3-9d65-fce89a684625
bash /tmp/verify_us23.sh
