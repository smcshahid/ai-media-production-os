#!/usr/bin/env bash
# US-15 Olares verification: SCRIPT review, reject/regen, approve → STORYBOARD.
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

latest_script_version() {
  psql -c "SELECT COALESCE(MAX(version),0) FROM asset_versions WHERE project_id='$PROJECT' AND stage='SCRIPT';"
}

wait_for_script_version() {
  local target="$1"
  local deadline=$(( $(date +%s) + 600 ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    local cur
    cur=$(latest_script_version)
    echo "  poll script version=$cur target>=$target"
    if [ "$cur" -ge "$target" ]; then return 0; fi
    sleep 15
  done
  echo "  WARN: timed out waiting for script version >= $target"
  return 1
}

echo "========== SETUP: fresh pipeline to SCRIPT gate =========="
curl -s -m 30 -X POST "$API/ideas" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","title":"US-15 Olares Verify","paragraph":"A marine biologist on a remote station must decide whether to broadcast a discovery that could save the reef or keep it secret from corporate harvesters arriving at dawn.","style_note":"cinematic"}'
echo
START=$(curl -s -m 30 -X POST "$API/pipeline/start" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'"}')
echo "START=$START"
RUN_ID=$(echo "$START" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
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

echo "========== Approve STORY → SCRIPT =========="
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORY","decision":"APPROVED"}'
echo

DEADLINE=$(( $(date +%s) + 600 ))
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
  ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
  echo "  poll status=$ST stage=$STG"
  if [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "SCRIPT" ]; then break; fi
  if [ "$ST" = "FAILED" ]; then echo "FAILED=$S"; exit 1; fi
  sleep 15
done

SCRIPT_V1=$(latest_script_version)
SCRIPT_ASSET=$(psql -c "SELECT id FROM asset_versions WHERE project_id='$PROJECT' AND stage='SCRIPT' ORDER BY version DESC LIMIT 1;")
echo "SCRIPT_V1=$SCRIPT_V1 ASSET=$SCRIPT_ASSET"

echo "========== V-01: SCRIPT content (Fountain sample) =========="
MINIO_KEY=$(psql -c "SELECT minio_key FROM asset_versions WHERE id='$SCRIPT_ASSET';")
$K exec deploy/aimpos-minio -n "$NS" -- mc alias set local http://127.0.0.1:9000 "$MINIO_USER" "$MINIO_PASS" 2>/dev/null || true
$K exec deploy/aimpos-minio -n "$NS" -- mc cat "local/$MINIO_BUCKET/$MINIO_KEY" 2>/dev/null | head -30

echo "========== V-02-prep: Reject SCRIPT =========="
REJ=$(curl -s -m 30 -w "\nHTTP_CODE:%{http_code}" -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"SCRIPT","decision":"REJECTED","note":"US-15 verify: deepen dialogue and clarify stakes."}')
echo "$REJ"

for N in 1 2 3; do
  echo "========== V-$((N+1)): Regenerate SCRIPT #$N =========="
  VER_BEFORE=$(latest_script_version)
  RESP=$(curl -s -m 120 -w "\nHTTP_CODE:%{http_code}" -X POST "$API/pipeline/regenerate" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","stage":"SCRIPT"}')
  echo "$RESP"
  TARGET_VER=$((VER_BEFORE + 1))
  wait_for_script_version "$TARGET_VER" || true
  psql -c "SELECT id||'|'||version||'|'||content_hash FROM asset_versions WHERE project_id='$PROJECT' AND stage='SCRIPT' ORDER BY version;"
done

echo "========== V-05: 4th SCRIPT regenerate (expect 429) =========="
RESP4=$(curl -s -m 30 -w "\nHTTP_CODE:%{http_code}" -X POST "$API/pipeline/regenerate" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"SCRIPT"}')
echo "$RESP4"

echo "========== V-06: Approve SCRIPT → STORYBOARD =========="
APPR=$(curl -s -m 60 -w "\nHTTP_CODE:%{http_code}" -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"SCRIPT","decision":"APPROVED"}')
echo "$APPR"
sleep 15
curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH"
echo

echo "========== V-07: D-41 approved script resolution =========="
psql -c "SELECT a.stage||'|'||a.decision||'|'||COALESCE(a.rationale,'') FROM approvals a WHERE a.pipeline_run_id='$RUN_ID' AND a.stage='SCRIPT' ORDER BY a.created_at;"
psql -c "SELECT av.id||'|'||av.version||'|'||av.content_hash FROM asset_versions av WHERE av.project_id='$PROJECT' AND av.stage='SCRIPT' ORDER BY av.version DESC LIMIT 1;"

echo "========== V-08: D-42 regen audit + worker log =========="
psql -c "SELECT event_type||'|'||COALESCE(payload::text,'') FROM audit_events WHERE pipeline_run_id='$RUN_ID' AND payload->>'stage'='SCRIPT' ORDER BY created_at;"
$K logs deploy/aimpos-worker -n "$NS" --tail=40 2>&1 | grep -Ei 'script_agent|screenwriter|qwen3' | grep -Ev 'Deprecation|JsonPlus' || true

echo "DONE RUN_ID=$RUN_ID"
