#!/usr/bin/env bash
set -uo pipefail
NS=aimpos-mwayolares
# Secrets from environment (never hardcode). See verify.sh header for sourcing.
: "${TOKEN:?set TOKEN to the AIMPOS_API_TOKEN}"
: "${PGPW:?set PGPW to the aimpos-postgres password}"
PROJECT="${PROJECT:?set PROJECT to the target project UUID}"
RUN_ID="${1:?usage: collect.sh RUN_ID}"
K="sudo k3s kubectl"
API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

echo "=== AC-3/8: poll status until AWAITING_APPROVAL/STORY ==="
DEADLINE=$(( $(date +%s) + 600 ))
FINAL=""
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
  ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
  echo "  poll status=$ST stage=$STG"
  if [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "STORY" ]; then FINAL="$S"; break; fi
  if [ "$ST" = "FAILED" ]; then FINAL="$S"; break; fi
  sleep 8
done
echo "FINAL_STATUS_JSON=$FINAL"
echo

echo "=== AC-5: STORY asset_versions row ==="
psql -c "SELECT 'STORY_ROW|'||id||'|'||stage||'|'||version||'|'||branch||'|'||is_ai_generated||'|'||content_hash||'|'||minio_key FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORY' ORDER BY version DESC LIMIT 1;"
MINIO_KEY=$(psql -c "SELECT minio_key FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORY' ORDER BY version DESC LIMIT 1;")
echo

echo "=== AC-6/7: audit events ==="
psql -c "SELECT 'AUDIT|'||event_type||'|'||COALESCE(model_id,'') FROM audit_events WHERE pipeline_run_id='$RUN_ID' ORDER BY created_at;"
echo

echo "=== run row ==="
psql -c "SELECT 'RUN|'||status||'|'||COALESCE(current_stage,'') FROM pipeline_runs WHERE id='$RUN_ID';"
echo

echo "=== AC-4: MinIO object for STORY key ==="
echo "STORY_MINIO_KEY=$MINIO_KEY"
$K exec -i aimpos-minio-5fddf9db6b-r6c2v -n "$NS" -- sh -lc '
  mc alias set local http://127.0.0.1:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1 || true
  mc stat "local/'"$MINIO_BUCKET"'/'"$MINIO_KEY"'" 2>&1 | head -20
' 2>&1 || echo "minio mc check skipped/failed"
echo

echo "=== worker log tail ==="
$K logs deploy/aimpos-worker -n "$NS" --tail=25 2>&1 | grep -Ev 'Deprecation|JsonPlus' || true
