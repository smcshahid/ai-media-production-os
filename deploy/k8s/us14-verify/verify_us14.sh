#!/usr/bin/env bash
# US-14 Olares verification: idea → STORY gate → approve → SCRIPT gate + evidence.
set -uo pipefail
NS=aimpos-mwayolares
: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT:?set PROJECT}"
MINIO_BUCKET="${MINIO_BUCKET:-aimpos-hot-assets}"
K="sudo k3s kubectl"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
echo "API=$API PROJECT=$PROJECT"

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

echo "========== PREP: clear active run if present =========="
CUR=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
CUR_ST=$(echo "$CUR" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
if [ "$CUR_ST" = "AWAITING_APPROVAL" ] || [ "$CUR_ST" = "RUNNING" ] || [ "$CUR_ST" = "PENDING" ]; then
  CUR_STG=$(echo "$CUR" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
  echo "active run status=$CUR_ST stage=$CUR_STG — completing to allow fresh start"
  while [ "$CUR_ST" = "AWAITING_APPROVAL" ] || [ "$CUR_ST" = "RUNNING" ]; do
    curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
      -d '{"project_id":"'"$PROJECT"'","stage":"'"$CUR_STG"'","decision":"APPROVED"}' || true
    echo
    sleep 15
    CUR=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
    CUR_ST=$(echo "$CUR" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
    CUR_STG=$(echo "$CUR" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
    echo "after approve $CUR_STG: status=$CUR_ST stage=$CUR_STG"
    if [ "$CUR_ST" = "COMPLETED" ] || [ "$CUR_ST" = "FAILED" ] || [ "$CUR_ST" = "CANCELLED" ]; then break; fi
    if [ "$CUR_ST" = "AWAITING_APPROVAL" ] && [ "$CUR_STG" = "$CUR_STG" ]; then
      # same stage after approve — avoid infinite loop
      break
    fi
  done
fi

echo "========== SETUP: fresh pipeline to STORY gate =========="
curl -s -m 30 -X POST "$API/ideas" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","title":"US-14 Olares Verify","paragraph":"A marine biologist on a remote station must choose whether to broadcast a discovery that could save the reef or keep it secret from corporate harvesters arriving at dawn.","style_note":"cinematic"}'
echo
START=$(curl -s -m 30 -X POST "$API/pipeline/start" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'"}')
echo "START=$START"
RUN_ID=$(echo "$START" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
if [ -z "$RUN_ID" ]; then
  echo "pipeline/start blocked — fetch active run_id from status"
  S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
  RUN_ID=$(echo "$S" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
fi
echo "RUN_ID=$RUN_ID"

DEADLINE=$(( $(date +%s) + 900 ))
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
  ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
  echo "  poll status=$ST stage=$STG"
  if [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "STORY" ]; then break; fi
  if [ "$ST" = "FAILED" ]; then echo "FAILED=$S"; exit 1; fi
  sleep 10
done

STORY_ASSET=$(psql -c "SELECT id FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORY' ORDER BY version DESC LIMIT 1;")
echo "STORY_ASSET=$STORY_ASSET"

echo "========== V6-prep: Approve STORY → SCRIPT generation =========="
APPR=$(curl -s -m 60 -w "\nHTTP_CODE:%{http_code}" -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORY","decision":"APPROVED"}')
echo "$APPR"

echo "========== V6: Poll SCRIPT review gate =========="
DEADLINE=$(( $(date +%s) + 600 ))
SCRIPT_STATUS=""
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
  ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
  echo "  poll status=$ST stage=$STG"
  if [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "SCRIPT" ]; then SCRIPT_STATUS="$S"; break; fi
  if [ "$ST" = "FAILED" ]; then echo "FAILED=$S"; exit 1; fi
  sleep 15
done
echo "SCRIPT_GATE=$SCRIPT_STATUS"

echo "========== V2: SCRIPT asset_versions =========="
psql -c "SELECT id||'|'||version||'|'||branch||'|'||is_ai_generated||'|'||content_hash||'|'||minio_key||'|'||created_at FROM asset_versions WHERE project_id='$PROJECT' AND stage='SCRIPT' ORDER BY version;"

echo "========== V5: lineage_edges (story → script) =========="
psql -c "SELECT le.parent_id||'|'||le.child_id||'|'||p.stage||'|'||c.stage FROM lineage_edges le JOIN asset_versions p ON p.id=le.parent_id JOIN asset_versions c ON c.id=le.child_id WHERE p.project_id='$PROJECT' AND c.stage='SCRIPT' ORDER BY le.created_at DESC LIMIT 3;"

echo "========== V3: MinIO stat =========="
MINIO_KEY=$(psql -c "SELECT minio_key FROM asset_versions WHERE project_id='$PROJECT' AND stage='SCRIPT' ORDER BY version DESC LIMIT 1;")
echo "MINIO_KEY=$MINIO_KEY"
$K exec deploy/aimpos-minio -n "$NS" -- mc alias set local http://127.0.0.1:9000 "$MINIO_USER" "$MINIO_PASS" 2>/dev/null || true
$K exec deploy/aimpos-minio -n "$NS" -- mc stat "local/$MINIO_BUCKET/$MINIO_KEY" 2>&1 || echo "(mc stat skipped — set MINIO_USER/MINIO_PASS if needed)"

echo "========== V1: Fountain sample (first 40 lines) =========="
$K exec deploy/aimpos-minio -n "$NS" -- mc cat "local/$MINIO_BUCKET/$MINIO_KEY" 2>/dev/null | head -40 || echo "(content read skipped)"

echo "========== V7: Worker log (script agent) =========="
$K logs deploy/aimpos-worker -n "$NS" --tail=60 2>&1 | grep -Ei 'script_agent|screenwriter|run_script|qwen3' | grep -Ev 'Deprecation|JsonPlus' || true

echo "========== AUDIT EVENTS (SCRIPT) =========="
psql -c "SELECT event_type||'|'||COALESCE(model_id,'')||'|'||COALESCE(payload::text,'')||'|'||created_at FROM audit_events WHERE pipeline_run_id='$RUN_ID' AND (payload->>'stage'='SCRIPT' OR event_type IN ('STAGE_STARTED','AGENT_TASK_COMPLETED','ASSET_STORED','PIPELINE_FAILED')) ORDER BY created_at;"

echo "========== APPROVALS =========="
psql -c "SELECT stage||'|'||decision||'|'||COALESCE(rationale,'')||'|'||created_at FROM approvals WHERE pipeline_run_id='$RUN_ID' ORDER BY created_at;"

echo "DONE RUN_ID=$RUN_ID"
