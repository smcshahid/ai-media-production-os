#!/usr/bin/env bash
# US-17 Olares verification: STORYBOARD batch review → approve COMPLETED or reject → regen v+1.
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
echo "API=$API PROJECT=$PROJECT MODE=${VERIFY_MODE:-approve}"

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

latest_storyboard_version() {
  psql -c "SELECT COALESCE(MAX(version),0) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD';"
}

count_latest_batch_frames() {
  psql -c "
    WITH latest AS (
      SELECT COALESCE(MAX(version),0) AS v FROM asset_versions
      WHERE project_id='$PROJECT' AND stage='STORYBOARD'
    )
    SELECT COUNT(*) FROM asset_versions av, latest
    WHERE av.project_id='$PROJECT' AND av.stage='STORYBOARD' AND av.version=latest.v;
  "
}

wait_for_status() {
  local want_status="$1"
  local want_stage="$2"
  local deadline=$(( $(date +%s) + ${3:-900} ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
    ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
    STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
    echo "  poll status=$ST stage=$STG"
    if [ "$ST" = "$want_status" ] && [ "$STG" = "$want_stage" ]; then return 0; fi
    if [ "$ST" = "FAILED" ]; then echo "FAILED=$S"; exit 1; fi
    sleep 15
  done
  echo "TIMEOUT waiting for status=$want_status stage=$want_stage"
  return 1
}

ensure_storyboard_gate() {
  S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
  ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
  RUN_ID=$(echo "$S" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
  echo "CURRENT status=$ST stage=$STG RUN_ID=$RUN_ID"
  if [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "STORYBOARD" ]; then
    return 0
  fi
  echo "Need AWAITING_APPROVAL/STORYBOARD — run verify_us16.sh first or set RUN_ID after pipeline reaches gate"
  exit 2
}

echo "========== V-01: storyboard gate present =========="
ensure_storyboard_gate
SB_VER=$(latest_storyboard_version)
FRAME_COUNT=$(count_latest_batch_frames)
echo "STORYBOARD_VERSION=$SB_VER FRAME_COUNT=$FRAME_COUNT"
if [ "$FRAME_COUNT" != "4" ]; then echo "FAIL: expected 4 frames at latest version"; exit 1; fi

echo "========== V-02: content-read PNG sample =========="
SAMPLE_ID=$(psql -c "
  WITH latest AS (SELECT COALESCE(MAX(version),0) AS v FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD')
  SELECT av.id::text FROM asset_versions av, latest
  WHERE av.project_id='$PROJECT' AND av.stage='STORYBOARD' AND av.version=latest.v
  ORDER BY (av.metadata_json->>'frame_index')::int LIMIT 1;
")
HTTP=$(curl -s -m 30 -o /tmp/us17-frame.png -w "%{http_code}" "$API/assets/$SAMPLE_ID/content" -H "$AUTH")
echo "CONTENT_READ id=$SAMPLE_ID http=$HTTP bytes=$(wc -c < /tmp/us17-frame.png 2>/dev/null || echo 0)"
if [ "$HTTP" != "200" ]; then echo "FAIL: content-read"; exit 1; fi
head -c 4 /tmp/us17-frame.png | od -An -tx1 | grep -q "89 50 4e 47" || { echo "FAIL: not PNG"; exit 1; }

VERIFY_MODE="${VERIFY_MODE:-approve}"
if [ "$VERIFY_MODE" = "regen" ]; then
  echo "========== V-03: reject batch + regenerate (D-47) =========="
  BASE_VER="$SB_VER"
  curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","stage":"STORYBOARD","decision":"REJECT","note":"US-17 Olares: increase contrast and wider shots."}'
  echo
  REGEN=$(curl -s -m 120 -w "\nHTTP_CODE:%{http_code}" -X POST "$API/pipeline/regenerate" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","stage":"STORYBOARD"}')
  echo "REGEN=$REGEN"
  TARGET=$((BASE_VER + 1))
  DEADLINE=$(( $(date +%s) + 1800 ))
  while [ "$(date +%s)" -lt "$DEADLINE" ]; do
    CUR=$(latest_storyboard_version)
    S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
    ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
    STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
    echo "  poll version=$CUR target>=$TARGET status=$ST stage=$STG"
    if [ "$CUR" -ge "$TARGET" ] && [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "STORYBOARD" ]; then break; fi
    if [ "$ST" = "FAILED" ]; then echo "FAILED=$S"; exit 1; fi
    sleep 20
  done
  OLD_ROWS=$(psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD' AND version=$BASE_VER;")
  NEW_ROWS=$(psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD' AND version=$TARGET;")
  echo "PRIOR_BATCH_ROWS=$OLD_ROWS NEW_BATCH_ROWS=$NEW_ROWS"
  if [ "$OLD_ROWS" != "4" ] || [ "$NEW_ROWS" != "4" ]; then echo "FAIL: batch immutability"; exit 1; fi
  REJ=$(psql -c "SELECT COUNT(*) FROM approvals WHERE pipeline_run_id='$RUN_ID' AND stage='STORYBOARD' AND decision='REJECTED';")
  echo "STORYBOARD_REJECTIONS=$REJ"
else
  echo "========== V-03: approve batch → COMPLETED (AC-3) =========="
  curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","stage":"STORYBOARD","decision":"APPROVED"}'
  echo
  wait_for_status "COMPLETED" "null" 120 || wait_for_status "COMPLETED" "" 120 || true
  S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
  ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  echo "FINAL_STATUS=$ST"
  if [ "$ST" != "COMPLETED" ]; then echo "FAIL: expected COMPLETED"; exit 1; fi
  APPR=$(psql -c "SELECT COUNT(*) FROM approvals WHERE pipeline_run_id='$RUN_ID' AND stage='STORYBOARD' AND decision='APPROVED';")
  echo "STORYBOARD_APPROVALS=$APPR"
  if [ "$APPR" != "1" ]; then echo "FAIL: expected single batch approval"; exit 1; fi
fi

echo "========== V-04: audit tail =========="
$K logs deploy/aimpos-worker -n "$NS" --tail=60 2>&1 | grep -Ei 'storyboard_agent_completed|regenerat' | grep -Ev 'Deprecation|JsonPlus' || true

echo "DONE RUN_ID=$RUN_ID"
