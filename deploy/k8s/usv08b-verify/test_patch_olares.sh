#!/usr/bin/env bash
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
TOKEN=$($K get secret aimpos-api-env -n "$NS" -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)
API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
PROJECT=ba0c4636-817c-423b-9771-20100e080b76
CHAR=f01f12ce-a5e0-4ed7-ab10-bf68db4c2a39

resp=$(curl -s -m 30 -w "\nHTTP:%{http_code}" -X PATCH "$API/characters/$CHAR?project_id=$PROJECT" \
  -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' \
  -d '{"name":"Maya-D-a1-Edited","visual_traits":"edited silver lab coat"}')
echo "$resp"
name=$($K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A -c "SELECT name FROM characters WHERE id='$CHAR';")
echo "db_name=$name"
