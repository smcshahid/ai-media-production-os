#!/usr/bin/env bash
# US-13 focused Olares verification (V1–V4). Runs on the Olares node.
set -uo pipefail
NS=aimpos-mwayolares
: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT:?set PROJECT}"
K="sudo k3s kubectl"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
echo "API=$API PROJECT=$PROJECT"

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

story_row() {
  psql -c "SELECT id||'|'||version||'|'||branch||'|'||is_ai_generated||'|'||left(content_hash,16) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORY' ORDER BY version;"
}

run_row() {
  psql -c "SELECT id||'|'||status||'|'||COALESCE(current_stage,'') FROM pipeline_runs WHERE project_id='$PROJECT' ORDER BY created_at DESC LIMIT 1;"
}

echo "========== SETUP: ensure STORY review gate =========="
# If no active AWAITING_APPROVAL/STORY run, create one.
CUR=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
ST=$(echo "$CUR" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
STG=$(echo "$CUR" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
echo "CURRENT_STATUS=$CUR"

if [ "$ST" != "AWAITING_APPROVAL" ] || [ "$STG" != "STORY" ]; then
  echo "Starting fresh pipeline for US-13 verification..."
  curl -s -m 30 -X POST "$API/ideas" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","title":"US-13 Olares Verify","paragraph":"An astronaut tends a secret garden on Mars while the colony council debates whether discovery belongs to one person or everyone. The garden holds a message from the first settlers.","style_note":"reflective sci-fi"}'
  echo
  START=$(curl -s -m 30 -X POST "$API/pipeline/start" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'"}')
  echo "START=$START"
  RUN_ID=$(echo "$START" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
  DEADLINE=$(( $(date +%s) + 900 ))
  while [ "$(date +%s)" -lt "$DEADLINE" ]; do
    S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
    ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
    STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
    echo "  poll status=$ST stage=$STG"
    if [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "STORY" ]; then break; fi
    if [ "$ST" = "FAILED" ]; then echo "PIPELINE_FAILED"; exit 1; fi
    sleep 10
  done
else
  RUN_ID=$(echo "$CUR" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
fi
echo "RUN_ID=$RUN_ID"
echo

echo "========== V1: Load STORY asset into editor (API) =========="
ASSET_ID=$(psql -c "SELECT id FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORY' ORDER BY version DESC LIMIT 1;")
echo "ASSET_ID=$ASSET_ID"
echo "--- GET /assets (metadata) ---"
curl -s -m 30 "$API/assets?project_id=$PROJECT" -H "$AUTH"
echo
echo "--- GET /assets/${ASSET_ID}/content ---"
CONTENT=$(curl -s -m 30 "$API/assets/${ASSET_ID}/content" -H "$AUTH" -w "\nHTTP_CODE:%{http_code}")
echo "$CONTENT" | head -c 2000
echo
echo "... (truncated preview above)"
echo "$CONTENT" | tail -1
echo

echo "========== V2: Save edited story (before rows) =========="
echo "STORY_ROWS_BEFORE"
story_row
echo "RUN_BEFORE"
run_row
echo "--- PUT /assets/${ASSET_ID} ---"
EDITED='# US-13 Human Edit (Olares)\n\n**Logline:** The gardener chooses transparency.\n\n### Act I\nDiscovery.\n\n### Act II\nCouncil debate.\n\n### Act III\nShared stewardship.'
PUT_RESP=$(curl -s -m 30 -X PUT "$API/assets/${ASSET_ID}" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"text":"# US-13 Human Edit (Olares)\n\n**Logline:** The gardener chooses transparency.\n\n### Act I\nDiscovery.\n\n### Act II\nCouncil debate.\n\n### Act III\nShared stewardship."}')
echo "$PUT_RESP"
NEW_ASSET_ID=$(echo "$PUT_RESP" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')
echo "NEW_ASSET_ID=$NEW_ASSET_ID"
echo "STORY_ROWS_AFTER"
story_row
echo "RUN_AFTER_SAVE"
run_row
echo

echo "========== V4: Reject story =========="
echo "--- POST /pipeline/approve REJECT ---"
REJ=$(curl -s -m 30 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORY","decision":"REJECT","note":"US-13 Olares verify: treatment needs stronger third act."}')
echo "$REJ"
echo "RUN_AFTER_REJECT"
run_row
echo "APPROVALS_REJECT"
psql -c "SELECT stage||'|'||decision||'|'||COALESCE(left(rationale,80),'') FROM approvals WHERE pipeline_run_id='$RUN_ID' AND decision='REJECTED' ORDER BY created_at DESC LIMIT 1;"
echo "AUDIT_REJECT"
psql -c "SELECT event_type||'|'||left(payload::text,120) FROM audit_events WHERE pipeline_run_id='$RUN_ID' AND event_type='APPROVAL_RECORDED' ORDER BY created_at DESC LIMIT 1;"
echo "STATUS_AFTER_REJECT"
curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH"
echo
echo

echo "========== V3: Approve story (after reject, same run) =========="
echo "--- POST /pipeline/approve GRANT ---"
APR=$(curl -s -m 30 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORY","decision":"GRANT"}')
echo "$APR"
sleep 5
echo "RUN_AFTER_APPROVE"
run_row
echo "APPROVALS_GRANT"
psql -c "SELECT stage||'|'||decision FROM approvals WHERE pipeline_run_id='$RUN_ID' AND decision='APPROVED' ORDER BY created_at DESC LIMIT 1;"
echo "AUDIT_APPROVE"
psql -c "SELECT event_type||'|'||left(payload::text,120) FROM audit_events WHERE pipeline_run_id='$RUN_ID' AND event_type='APPROVAL_RECORDED' ORDER BY created_at DESC LIMIT 2;"
echo "STATUS_AFTER_APPROVE"
curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH"
echo
echo "DONE RUN_ID=$RUN_ID ASSET_ID=$ASSET_ID NEW_ASSET_ID=$NEW_ASSET_ID"
