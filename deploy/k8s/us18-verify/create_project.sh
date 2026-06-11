#!/usr/bin/env bash
# PF-05: Bootstrap fresh project row (no POST /projects API).
set -euo pipefail
NS=aimpos-mwayolares
: "${PGPW:?set PGPW}"
K="sudo k3s kubectl"
PROJECT="${PROJECT:-$(cat /proc/sys/kernel/random/uuid)}"
NAME="${PROJECT_NAME:-US-18 Video Verify}"

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

psql -c "INSERT INTO projects (id, name, status, created_at) VALUES ('$PROJECT', '$NAME', 'ACTIVE', NOW()) ON CONFLICT (id) DO NOTHING;"
echo "PROJECT=$PROJECT"
