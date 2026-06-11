#!/usr/bin/env bash
# PF-05: Bootstrap fresh project row for US-V02 acceptance.
set -euo pipefail
NS=aimpos-mwayolares
: "${PGPW:?set PGPW}"
K="sudo k3s kubectl"
PROJECT="${PROJECT:-$(cat /proc/sys/kernel/random/uuid)}"
NAME="${PROJECT_NAME:-US-V02 Spark Full Acceptance}"

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

psql -c "INSERT INTO projects (id, name, status, created_at) VALUES ('$PROJECT', '$NAME', 'ACTIVE', NOW()) ON CONFLICT (id) DO NOTHING;"
echo "PROJECT=$PROJECT"
echo "PF-05 fresh project created (verify bootstrap — not demo-path DB intervention)"
