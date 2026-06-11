#!/usr/bin/env bash
# US-14 Olares evidence collector (post verify_us14.sh).
set -uo pipefail
NS=aimpos-mwayolares
: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT:?set PROJECT}"
RUN_ID="${1:?usage: collect_us14.sh RUN_ID}"
MINIO_BUCKET="${MINIO_BUCKET:-aimpos-hot-assets}"
K="sudo k3s kubectl"
API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

echo "=== PIPELINE STATUS (V-06) ==="
curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH"
echo

echo "=== RUN ROW ==="
psql -c "SELECT 'RUN|'||id||'|'||status||'|'||COALESCE(current_stage,'')||'|'||COALESCE(temporal_workflow_id,'') FROM pipeline_runs WHERE id='$RUN_ID';"
echo

echo "=== SCRIPT asset_versions (V-02) ==="
psql -c "SELECT id||'|'||version||'|'||branch||'|'||is_ai_generated||'|'||content_hash||'|'||minio_key||'|'||created_at FROM asset_versions WHERE project_id='$PROJECT' AND stage='SCRIPT' ORDER BY version;"
echo

echo "=== STORY parent (D-37) ==="
psql -c "SELECT id||'|'||version||'|'||branch FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORY' ORDER BY version DESC LIMIT 1;"
echo

echo "=== lineage_edges (V-05) ==="
psql -c "SELECT le.parent_id||'|'||le.child_id||'|'||p.stage||'|'||c.stage||'|'||le.created_at FROM lineage_edges le JOIN asset_versions p ON p.id=le.parent_id JOIN asset_versions c ON c.id=le.child_id WHERE p.project_id='$PROJECT' AND c.stage='SCRIPT' ORDER BY le.created_at;"
echo

echo "=== APPROVALS ==="
psql -c "SELECT id||'|'||stage||'|'||decision||'|'||COALESCE(rationale,'')||'|'||created_at FROM approvals WHERE pipeline_run_id='$RUN_ID' ORDER BY created_at;"
echo

echo "=== AUDIT EVENTS ==="
psql -c "SELECT event_type||'|'||COALESCE(model_id,'')||'|'||COALESCE(payload::text,'')||'|'||created_at FROM audit_events WHERE pipeline_run_id='$RUN_ID' ORDER BY created_at;"
echo

MINIO_KEY=$(psql -c "SELECT minio_key FROM asset_versions WHERE project_id='$PROJECT' AND stage='SCRIPT' ORDER BY version DESC LIMIT 1;")
echo "=== FOUNTAIN SAMPLE (V-01, first 40 lines) ==="
$K exec deploy/aimpos-minio -n "$NS" -- mc cat "local/$MINIO_BUCKET/$MINIO_KEY" 2>/dev/null | head -40 || echo "(mc unavailable)"
echo

echo "=== WORKER LOG (V-07) ==="
$K logs deploy/aimpos-worker -n "$NS" --tail=80 2>&1 | grep -Ei 'script|screenwriter|run_script|qwen3|ASSET_STORED' | grep -Ev 'Deprecation|JsonPlus' || true
