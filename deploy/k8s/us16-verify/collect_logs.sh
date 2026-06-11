#!/usr/bin/env bash
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
RUN_ID="${1:-e8dd92d9-ac6b-41f0-bd58-3cf4b2b05482}"
echo "=== worker logs (storyboard) ==="
$K logs deploy/aimpos-worker -n "$NS" --tail=120 2>&1 | grep -Ei 'storyboard|cinematography|comfyui|ollama_unloaded|PIPELINE_FAILED|error|failed' | grep -Ev 'Deprecation|JsonPlus' || true
echo "=== audit events ==="
PGPW=$($K get secret aimpos-postgres-auth -n "$NS" -o jsonpath='{.data.postgres-password}' | base64 -d)
$K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A \
  -c "SELECT event_type||'|'||COALESCE(payload::text,'') FROM audit_events WHERE pipeline_run_id='$RUN_ID' ORDER BY created_at DESC LIMIT 15;"
