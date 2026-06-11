#!/usr/bin/env bash
# US-16 Olares verification: STORYBOARD agent → 4 PNG frames + lineage + review gate.
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

resolve_run_id() {
  if [ -n "${RUN_ID:-}" ]; then return 0; fi
  RUN_ID=$(psql -c "SELECT id::text FROM pipeline_runs WHERE project_id='$PROJECT' ORDER BY created_at DESC LIMIT 1;")
  echo "RESOLVED_RUN_ID=$RUN_ID"
}

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

echo "========== SETUP: pipeline to STORYBOARD gate =========="
curl -s -m 30 -X POST "$API/ideas" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","title":"US-16 Olares Verify","paragraph":"A marine biologist on a remote station must decide whether to broadcast a discovery that could save the reef or keep it secret from corporate harvesters arriving at dawn.","style_note":"cinematic"}'
echo
START=$(curl -s -m 30 -w "\nHTTP_CODE:%{http_code}" -X POST "$API/pipeline/start" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'"}')
echo "START=$START"
HTTP_CODE=$(echo "$START" | sed -n 's/.*HTTP_CODE:\([0-9]*\).*/\1/p')
RUN_ID=$(echo "$START" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')

if [ "$HTTP_CODE" = "409" ]; then
  echo "WARN: active run blocks start — run complete_old_run.sh then re-run verify"
  resolve_run_id
  S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
  ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
  echo "ACTIVE status=$ST stage=$STG RUN_ID=$RUN_ID"
  exit 2
fi

SB_BEFORE=$(latest_storyboard_version)
echo "STORYBOARD_VERSION_BEFORE=$SB_BEFORE RUN_ID=$RUN_ID"

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

echo "========== Approve STORY =========="
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORY","decision":"APPROVED"}'
echo

DEADLINE=$(( $(date +%s) + 900 ))
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
  ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
  echo "  poll status=$ST stage=$STG"
  if [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "SCRIPT" ]; then break; fi
  if [ "$ST" = "FAILED" ]; then echo "FAILED=$S"; exit 1; fi
  sleep 15
done

echo "========== Approve SCRIPT → STORYBOARD generation =========="
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"SCRIPT","decision":"APPROVED"}'
echo

TARGET_VER=$(( SB_BEFORE + 1 ))
DEADLINE=$(( $(date +%s) + 1800 ))
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  S=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
  ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
  CUR=$(latest_storyboard_version)
  echo "  poll status=$ST stage=$STG storyboard_version=$CUR target>=$TARGET_VER"
  if [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "STORYBOARD" ] && [ "$CUR" -ge "$TARGET_VER" ]; then break; fi
  if [ "$ST" = "FAILED" ]; then echo "FAILED=$S"; exit 1; fi
  sleep 20
done

echo "========== V-01: frame count (D-45 = 4) =========="
FRAME_COUNT=$(count_latest_batch_frames)
echo "FRAME_COUNT=$FRAME_COUNT"
if [ "$FRAME_COUNT" != "4" ]; then echo "FAIL: expected 4 frames"; exit 1; fi

echo "========== V-02: STORYBOARD rows =========="
psql -c "
  WITH latest AS (SELECT COALESCE(MAX(version),0) AS v FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD')
  SELECT av.id, av.version, av.content_hash, av.metadata_json->>'frame_index' AS frame_index
  FROM asset_versions av, latest
  WHERE av.project_id='$PROJECT' AND av.stage='STORYBOARD' AND av.version=latest.v
  ORDER BY (av.metadata_json->>'frame_index')::int;
"

echo "========== V-03: lineage script → frames =========="
SCRIPT_ID=$(psql -c "SELECT id::text FROM asset_versions WHERE project_id='$PROJECT' AND stage='SCRIPT' ORDER BY version DESC LIMIT 1;")
LINEAGE_COUNT=$(psql -c "SELECT COUNT(*) FROM lineage_edges WHERE parent_id='$SCRIPT_ID';")
echo "SCRIPT_ID=$SCRIPT_ID LINEAGE_COUNT=$LINEAGE_COUNT"
if [ "$LINEAGE_COUNT" != "4" ]; then echo "FAIL: expected 4 lineage edges"; exit 1; fi

echo "========== V-04: pipeline status =========="
curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH"
echo

echo "========== V-05: worker log (GPU + storyboard) =========="
$K logs deploy/aimpos-worker -n "$NS" --tail=80 2>&1 | grep -Ei 'ollama_unloaded|comfyui_queued|storyboard_agent_completed' | grep -Ev 'Deprecation|JsonPlus' || true

echo "========== V-06: MinIO PNG sample =========="
SAMPLE_KEY=$(psql -c "
  WITH latest AS (SELECT COALESCE(MAX(version),0) AS v FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD')
  SELECT av.minio_key FROM asset_versions av, latest
  WHERE av.project_id='$PROJECT' AND av.stage='STORYBOARD' AND av.version=latest.v
  ORDER BY (av.metadata_json->>'frame_index')::int LIMIT 1;
")
$K exec deploy/aimpos-minio -n "$NS" -- mc alias set local http://127.0.0.1:9000 "$MINIO_USER" "$MINIO_PASS" 2>/dev/null || true
$K exec deploy/aimpos-minio -n "$NS" -- mc stat "local/$MINIO_BUCKET/$SAMPLE_KEY" 2>/dev/null || echo "WARN: mc stat failed"

echo "DONE RUN_ID=$RUN_ID"
