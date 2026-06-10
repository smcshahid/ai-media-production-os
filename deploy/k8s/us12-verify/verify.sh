#!/usr/bin/env bash
# US-12 E2E verification on Olares. Runs on the node; hits API via ClusterIP.
set -uo pipefail
NS=aimpos-mwayolares
# Secrets from environment (never hardcode). Source before running, e.g.:
#   export TOKEN=$(sudo k3s kubectl get secret aimpos-api-env -n aimpos-mwayolares -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
#   export PGPW=$(sudo k3s kubectl get secret aimpos-postgres-auth -n aimpos-mwayolares -o jsonpath='{.data.password}' | base64 -d)
: "${TOKEN:?set TOKEN to the AIMPOS_API_TOKEN}"
: "${PGPW:?set PGPW to the aimpos-postgres password}"
PROJECT="${PROJECT:?set PROJECT to the target project UUID}"
K="sudo k3s kubectl"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
echo "API=$API  PROJECT=$PROJECT"

echo "=== AC-1: POST /ideas ==="
curl -s -m 30 -X POST "$API/ideas" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","title":"Mars Garden US-12","paragraph":"A lone astronaut discovers a hidden garden on Mars and must decide whether to share it with Earth before the colony council arrives to claim the discovery.","style_note":"cinematic sci-fi"}'
echo

echo "=== AC-2: POST /pipeline/start ==="
START=$(curl -s -m 30 -X POST "$API/pipeline/start" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'"}')
echo "$START"
RUN_ID=$(echo "$START" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
echo "RUN_ID=$RUN_ID"
echo

echo "=== AC-3/8: poll status (cold model load tolerated) ==="
DEADLINE=$(( $(date +%s) + 900 ))
FINAL=""
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
  ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
  echo "  poll status=$ST stage=$STG"
  if [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "STORY" ]; then FINAL="$S"; break; fi
  if [ "$ST" = "FAILED" ]; then FINAL="$S"; break; fi
  sleep 10
done
echo "FINAL_STATUS=$FINAL"
echo

echo "=== worker log tail ==="
$K logs deploy/aimpos-worker -n "$NS" --tail=20 2>&1 | grep -Ev 'Deprecation|JsonPlus' || true
echo

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

echo "=== AC-5: STORY asset_versions ==="
psql -c "SELECT id||'|'||stage||'|'||version||'|'||branch||'|'||is_ai_generated||'|'||content_hash||'|'||minio_key FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORY' ORDER BY version DESC LIMIT 1;"
echo

echo "=== AC-6/7: audit events for run ==="
psql -c "SELECT event_type||'|'||COALESCE(model_id,'') FROM audit_events WHERE pipeline_run_id='$RUN_ID' ORDER BY created_at;"
echo

echo "=== run row ==="
psql -c "SELECT status||'|'||COALESCE(current_stage,'') FROM pipeline_runs WHERE id='$RUN_ID';"
echo "RUN_ID_RECORDED=$RUN_ID"
