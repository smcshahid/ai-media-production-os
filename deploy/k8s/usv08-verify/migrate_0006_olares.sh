#!/usr/bin/env bash
# Run Alembic 0006 via API migration job on Olares (when SQL apply not used).
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)

echo "Current revision:"
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT version_num FROM alembic_version;"

echo "Apply via apply_0006_sql_olares.sh (preferred for acceptance evidence)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$SCRIPT_DIR/apply_0006_sql_olares.sh"
