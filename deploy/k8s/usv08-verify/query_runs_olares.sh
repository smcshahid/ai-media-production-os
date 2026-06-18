#!/usr/bin/env bash
set -uo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A <<'SQL'
SELECT id::text, name FROM characters
WHERE id IN (
  'c2d70807-392f-4d49-80d8-7b862c1a2a77',
  'e8451dcf-aa97-4c64-8ce4-1e419f804419',
  '9255a380-b7b0-41a3-b5a6-a6d51a2f2732'
);
SQL
