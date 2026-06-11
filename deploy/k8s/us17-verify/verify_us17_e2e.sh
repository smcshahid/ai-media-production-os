#!/usr/bin/env bash
# US-17 full Olares E2E: pipeline → STORYBOARD gate → reject/regen v+1 → approve COMPLETED.
set -uo pipefail
NS=aimpos-mwayolares
: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${MINIO_USER:?set MINIO_USER}"
: "${MINIO_PASS:?set MINIO_PASS}"
: "${PROJECT:?set PROJECT}"
MINIO_BUCKET="${MINIO_BUCKET:-aimpos-hot-assets}"
K="sudo k3s kubectl"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
echo "API=$API PROJECT=$PROJECT"

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

latest_storyboard_version() {
  psql -c "SELECT COALESCE(MAX(version),0) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD';"
}

count_batch_frames() {
  local ver="$1"
  psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD' AND version=$ver;"
}

poll_until() {
  local want_status="$1"
  local want_stage="$2"
  local deadline=$(( $(date +%s) + ${3:-900} ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
    ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
    STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
    echo "  poll status=$ST stage=${STG:-null}"
    if [ "$ST" = "$want_status" ]; then
      if [ -z "$want_stage" ] || [ "$STG" = "$want_stage" ]; then return 0; fi
      if [ "$want_stage" = "null" ] && [ -z "$STG" ]; then return 0; fi
    fi
    if [ "$ST" = "FAILED" ]; then echo "FAILED=$S"; exit 1; fi
    sleep 15
  done
  return 1
}

echo "========== SETUP: idea + pipeline start =========="
curl -s -m 30 -X POST "$API/ideas" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","title":"US-17 Olares Verify","paragraph":"A marine biologist on a remote station must decide whether to broadcast a discovery that could save the reef or keep it secret from corporate harvesters arriving at dawn.","style_note":"cinematic"}'
echo
START=$(curl -s -m 30 -w "\nHTTP_CODE:%{http_code}" -X POST "$API/pipeline/start" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'"}')
echo "START=$START"
HTTP_CODE=$(echo "$START" | sed -n 's/.*HTTP_CODE:\([0-9]*\).*/\1/p')
RUN_ID=$(echo "$START" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
if [ "$HTTP_CODE" = "409" ]; then
  echo "WARN: active run — complete_old_run.sh first"
  exit 2
fi

SB_BEFORE=$(latest_storyboard_version)
echo "STORYBOARD_BEFORE=$SB_BEFORE RUN_ID=$RUN_ID"

echo "========== Approve STORY =========="
poll_until "AWAITING_APPROVAL" "STORY" 900 || exit 1
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORY","decision":"APPROVED"}'
echo

echo "========== Approve SCRIPT → STORYBOARD v1 =========="
poll_until "AWAITING_APPROVAL" "SCRIPT" 900 || exit 1
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"SCRIPT","decision":"APPROVED"}'
echo

TARGET_V1=$((SB_BEFORE + 1))
DEADLINE=$(( $(date +%s) + 1800 ))
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  CUR=$(latest_storyboard_version)
  S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
  ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
  echo "  poll v1 status=$ST stage=$STG storyboard_version=$CUR target>=$TARGET_V1"
  if [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "STORYBOARD" ] && [ "$CUR" -ge "$TARGET_V1" ]; then break; fi
  if [ "$ST" = "FAILED" ]; then echo "FAILED=$S"; exit 1; fi
  sleep 20
done

echo "========== V-01: 4 frames at v$TARGET_V1 =========="
if [ "$(count_batch_frames "$TARGET_V1")" != "4" ]; then echo "FAIL: frame count"; exit 1; fi

echo "========== V-02: PNG content-read =========="
SAMPLE_ID=$(psql -c "
  SELECT av.id::text FROM asset_versions av
  WHERE av.project_id='$PROJECT' AND av.stage='STORYBOARD' AND av.version=$TARGET_V1
  ORDER BY (av.metadata_json->>'frame_index')::int LIMIT 1;
")
HTTP=$(curl -s -m 30 -o /tmp/us17-frame.png -w "%{http_code}" "$API/assets/$SAMPLE_ID/content" -H "$AUTH")
echo "CONTENT_READ http=$HTTP"
if [ "$HTTP" != "200" ]; then echo "FAIL: content-read"; exit 1; fi

echo "========== V-03: reject + regen → v$((TARGET_V1 + 1)) (AC-4, D-47) =========="
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORYBOARD","decision":"REJECT","note":"US-17 Olares: increase contrast and wider establishing shots."}'
echo
REGEN=$(curl -s -m 120 -w "\nHTTP_CODE:%{http_code}" -X POST "$API/pipeline/regenerate" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORYBOARD"}')
echo "REGEN=$REGEN"
TARGET_V2=$((TARGET_V1 + 1))
DEADLINE=$(( $(date +%s) + 1800 ))
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  CUR=$(latest_storyboard_version)
  S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
  ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
  echo "  poll regen status=$ST stage=$STG version=$CUR target>=$TARGET_V2"
  if [ "$CUR" -ge "$TARGET_V2" ] && [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "STORYBOARD" ]; then break; fi
  if [ "$ST" = "FAILED" ]; then echo "FAILED=$S"; exit 1; fi
  sleep 20
done
if [ "$(count_batch_frames "$TARGET_V1")" != "4" ] || [ "$(count_batch_frames "$TARGET_V2")" != "4" ]; then
  echo "FAIL: batch immutability"; exit 1
fi
echo "PRIOR_V$TARGET_V1=4 NEW_V$TARGET_V2=4"

echo "========== V-04: approve batch → COMPLETED (AC-3) =========="
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORYBOARD","decision":"APPROVED"}'
echo
poll_until "COMPLETED" "" 120 || poll_until "COMPLETED" "null" 60 || true
S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
echo "FINAL=$S"
if [ "$ST" != "COMPLETED" ]; then echo "FAIL: expected COMPLETED"; exit 1; fi

echo "========== V-05: approvals audit =========="
psql -c "SELECT stage, decision, LEFT(rationale,40) FROM approvals WHERE pipeline_run_id='$RUN_ID' AND stage='STORYBOARD' ORDER BY created_at;"

echo "DONE RUN_ID=$RUN_ID V1=$TARGET_V1 V2=$TARGET_V2"
