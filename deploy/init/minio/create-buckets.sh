#!/bin/sh
# T-02-03 — idempotent MinIO bucket bootstrap.
#
# Runs in the minio-init (mc) service once MinIO reports healthy. Creates the
# bucket named by MINIO_BUCKET (.env) if it does not already exist and keeps it
# private. Safe to run repeatedly.
set -eu

ALIAS=local
ENDPOINT="http://${MINIO_ENDPOINT:-minio:9000}"
BUCKET="${MINIO_BUCKET:-aimpos-spark}"

# Configure the client alias; retry briefly in case MinIO is still warming up.
i=0
until mc alias set "$ALIAS" "$ENDPOINT" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1; do
  i=$((i + 1))
  if [ "$i" -ge 30 ]; then
    echo "ERROR: MinIO not reachable at $ENDPOINT after 30 attempts" >&2
    exit 1
  fi
  echo "waiting for MinIO at $ENDPOINT ..."
  sleep 2
done

# Create the bucket if absent (idempotent) and ensure no anonymous access.
mc mb --ignore-existing "$ALIAS/$BUCKET"
mc anonymous set none "$ALIAS/$BUCKET" >/dev/null 2>&1 || true

echo "MinIO bucket ready: $BUCKET"
