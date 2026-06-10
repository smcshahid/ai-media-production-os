#!/usr/bin/env bash
set -uo pipefail
NS=aimpos-mwayolares
# Secret from environment (never hardcode):
#   export PGPW=$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.password}' | base64 -d)
: "${PGPW:?set PGPW to the aimpos-postgres password}"
psql() { sudo k3s kubectl exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark "$@"; }

echo "=== projects schema ==="
psql -c '\d projects'
echo "=== existing projects ==="
psql -c 'SELECT id, name FROM projects LIMIT 10;'
