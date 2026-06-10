#!/usr/bin/env bash
set -uo pipefail
NS=aimpos-mwayolares
# Secrets + key from environment (never hardcode):
#   export MINIO_USER=...; export MINIO_PASSWORD=...   # MinIO access/secret keys
#   export KEY=<project>/STORY/<content_hash>          # object key to verify
: "${MINIO_USER:?set MINIO_USER to the MinIO access key}"
: "${MINIO_PASSWORD:?set MINIO_PASSWORD to the MinIO secret key}"
KEY="${KEY:?set KEY to the STORY object key (<project>/STORY/<content_hash>)}"
POD=$(sudo k3s kubectl get pods -n "$NS" -o name | grep aimpos-minio | head -1 | cut -d/ -f2)
echo "minio pod=$POD key=$KEY"
MINIO_USER="$MINIO_USER" MINIO_PASSWORD="$MINIO_PASSWORD" \
sudo k3s kubectl exec -i "$POD" -n "$NS" -- sh -c '
  mc alias set loc http://127.0.0.1:9000 "'"$MINIO_USER"'" "'"$MINIO_PASSWORD"'" >/dev/null 2>&1
  echo "--- mc stat ---"
  mc stat "loc/aimpos-hot-assets/'"$KEY"'"
  echo "--- head of object ---"
  mc cat "loc/aimpos-hot-assets/'"$KEY"'" | head -15
'
