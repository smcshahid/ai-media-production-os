#!/usr/bin/env bash
# US-09 Olares evidence collector (post verify_us09.sh).
set -uo pipefail
NS=aimpos-mwayolares
: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT:?set PROJECT}"
RUN_ID="${1:?usage: collect_us09.sh RUN_ID}"
K="sudo k3s kubectl"
API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

echo "=== PIPELINE STATUS ==="
curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH"
echo

echo "=== RUN ROW ==="
psql -c "SELECT 'RUN|'||id||'|'||status||'|'||COALESCE(current_stage,'')||'|'||COALESCE(temporal_workflow_id,'') FROM pipeline_runs WHERE id='$RUN_ID';"
echo

echo "=== STORY VERSION CHAIN (D-38) ==="
psql -c "SELECT id||'|'||version||'|'||branch||'|'||is_ai_generated||'|'||content_hash||'|'||created_at FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORY' ORDER BY version;"
echo

echo "=== APPROVALS ==="
psql -c "SELECT id||'|'||stage||'|'||decision||'|'||COALESCE(rationale,'')||'|'||created_at FROM approvals WHERE pipeline_run_id='$RUN_ID' ORDER BY created_at;"
echo

echo "=== AUDIT EVENTS ==="
psql -c "SELECT event_type||'|'||COALESCE(model_id,'')||'|'||COALESCE(payload::text,'')||'|'||created_at FROM audit_events WHERE pipeline_run_id='$RUN_ID' ORDER BY created_at;"
echo

echo "=== REGEN COUNT ==="
psql -c "SELECT COUNT(*) FROM audit_events WHERE pipeline_run_id='$RUN_ID' AND event_type='REGENERATION_REQUESTED' AND payload->>'stage'='STORY';"
echo

echo "=== WORKER LOG (regenerate/story) ==="
$K logs deploy/aimpos-worker -n "$NS" --tail=80 2>&1 | grep -Ei 'regenerat|story|reject|AGENT|signal' | grep -Ev 'Deprecation|JsonPlus' || true
echo

echo "=== API LOG (regenerate/429) ==="
$K logs deploy/aimpos-api -n "$NS" --tail=40 2>&1 | grep -Ei 'regenerat|429|REJECT' || true
