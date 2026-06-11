#!/usr/bin/env bash
# US-18 Olares verification — VIDEO stage after approved storyboard (D-48..D-51).
set -uo pipefail
NS=aimpos-mwayolares
: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT:?set PROJECT}"
K="sudo k3s kubectl"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
API_IMAGE=$($K get deploy aimpos-api -n "$NS" -o jsonpath='{.spec.template.spec.containers[0].image}')
WORKER_IMAGE=$($K get deploy aimpos-worker -n "$NS" -o jsonpath='{.spec.template.spec.containers[0].image}')

echo "US-18 verify start $(date -Iseconds)"
echo "API=$API PROJECT=$PROJECT"
echo "API_IMAGE=$API_IMAGE WORKER_IMAGE=$WORKER_IMAGE"

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

pipeline_status() { curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH"; }

poll_gate() {
  local want_stage="$1"
  local max_sec="${2:-900}"
  local interval="${3:-15}"
  local deadline=$(( $(date +%s) + max_sec ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    S=$(pipeline_status)
    ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
    STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
    echo "  poll status=$ST stage=${STG:-null} want=$want_stage"
    if [ "$ST" = "FAILED" ]; then echo "FAILED=$S"; return 1; fi
    if [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "$want_stage" ]; then return 0; fi
    sleep "$interval"
  done
  echo "TIMEOUT waiting for AWAITING_APPROVAL/$want_stage"
  return 1
}

latest_story_asset_id() {
  psql -c "SELECT id::text FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORY' ORDER BY version DESC LIMIT 1;"
}

latest_storyboard_version() {
  psql -c "SELECT COALESCE(MAX(version),0) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD';"
}

count_sb_batch() {
  psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD' AND version=$1;"
}

latest_video_id() {
  psql -c "SELECT id::text FROM asset_versions WHERE project_id='$PROJECT' AND stage='VIDEO' ORDER BY version DESC LIMIT 1;"
}

latest_video_version() {
  psql -c "SELECT COALESCE(MAX(version),0) FROM asset_versions WHERE project_id='$PROJECT' AND stage='VIDEO';"
}

FAIL=0

echo "========== PF-02: ffmpeg in worker pod =========="
$K exec deploy/aimpos-worker -n "$NS" -- ffmpeg -version | head -1 || { echo "FAIL: ffmpeg missing"; FAIL=1; }

echo "========== PF-04: health =========="
curl -s -m 15 "$API/health" || true
echo

echo "========== S-02: POST /ideas =========="
curl -s -m 30 -X POST "$API/ideas" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","title":"US-18 Video Verify","paragraph":"A marine biologist on a remote station must decide whether to broadcast a discovery that could save the reef or keep it secret from corporate harvesters arriving at dawn.","style_note":"cinematic"}'
echo

echo "========== S-03: POST /pipeline/start =========="
START=$(curl -s -m 30 -w "\nHTTP_CODE:%{http_code}" -X POST "$API/pipeline/start" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'"}')
echo "START=$START"
RUN_ID=$(echo "$START" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
echo "RUN_ID=$RUN_ID"

echo "========== S-04..S-06: STORY gate + approve =========="
poll_gate "STORY" 900 15 || FAIL=1
STORY_ID=$(latest_story_asset_id)
curl -s -m 60 -X PUT "$API/assets/$STORY_ID" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"text":"# US-18 Edit\n\nA biologist faces dawn and the broadcast decision."}'
echo
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORY","decision":"APPROVED"}'
echo

echo "========== S-07..S-11: SCRIPT gate + approve =========="
poll_gate "SCRIPT" 900 15 || FAIL=1
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"SCRIPT","decision":"APPROVED"}'
echo

echo "========== S-12: poll STORYBOARD gate (4 frames required) =========="
SB_READY=0
DEADLINE=$(( $(date +%s) + 1800 ))
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  CUR=$(latest_storyboard_version)
  S=$(pipeline_status)
  ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
  FC=$(count_sb_batch "$CUR")
  echo "  poll sb=$CUR frames=$FC status=$ST stage=$STG"
  if [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "STORYBOARD" ] && [ "$FC" = "4" ]; then SB_READY=1; break; fi
  if [ "$ST" = "FAILED" ]; then FAIL=1; break; fi
  sleep 20
done
if [ "$SB_READY" != "1" ]; then echo "FAIL: STORYBOARD gate not ready (need 4 frames)"; FAIL=1; fi

echo "========== S-18-01: approve STORYBOARD (D-51 — not COMPLETED) =========="
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORYBOARD","decision":"APPROVED"}'
echo
POST_SB=$(pipeline_status)
POST_SB_ST=$(echo "$POST_SB" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
echo "POST_STORYBOARD_APPROVE status=$POST_SB_ST"
if [ "$POST_SB_ST" = "COMPLETED" ]; then echo "FAIL D-51: COMPLETED at STORYBOARD"; FAIL=1; fi

echo "========== S-18-02: poll VIDEO gate =========="
poll_gate "VIDEO" 1200 20 || FAIL=1
T_VIDEO=$(date +%s)
echo "T_VIDEO_GATE=$T_VIDEO"

echo "========== S-18-03: VIDEO asset + metadata =========="
VID=$(latest_video_id)
VV=$(latest_video_version)
META=$(psql -c "SELECT metadata_json::text FROM asset_versions WHERE id='$VID';")
echo "VIDEO_ID=$VID VERSION=$VV META=$META"
if [ -z "$VID" ]; then echo "FAIL: no VIDEO asset"; FAIL=1; fi

echo "========== S-18-04: MP4 content-read =========="
HTTP=$(curl -s -m 60 -o /tmp/us18-video.mp4 -w "%{http_code}" "$API/assets/$VID/content" -H "$AUTH")
BYTES=$(wc -c < /tmp/us18-video.mp4 2>/dev/null || echo 0)
echo "CONTENT_READ http=$HTTP bytes=$BYTES"
if [ "$HTTP" != "200" ]; then FAIL=1; fi
python3 -c "d=open('/tmp/us18-video.mp4','rb').read(12); assert len(d)>=8 and d[4:8]==b'ftyp', d; print('MP4_MAGIC=PASS')" || { echo "FAIL: no ftyp"; FAIL=1; }

echo "========== S-18-05: lineage STORYBOARD→VIDEO =========="
LC=$(psql -c "
SELECT COUNT(*) FROM lineage_edges le
JOIN asset_versions p ON le.parent_id = p.id
JOIN asset_versions c ON le.child_id = c.id
WHERE c.id='$VID' AND p.stage='STORYBOARD';
")
echo "LINEAGE_COUNT=$LC"
if [ "$LC" != "4" ]; then echo "FAIL: expected 4 lineage edges"; FAIL=1; fi

echo "========== S-18-06: VIDEO reject + regen (D-50) =========="
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"VIDEO","decision":"REJECT","note":"US-18: slightly longer hold on frame 2."}'
echo
curl -s -m 120 -X POST "$API/pipeline/regenerate" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"VIDEO"}'
echo
REGEN_DEADLINE=$(( $(date +%s) + 600 ))
while [ "$(date +%s)" -lt "$REGEN_DEADLINE" ]; do
  VV2=$(latest_video_version)
  S=$(pipeline_status)
  ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
  echo "  regen poll version=$VV2 want>$VV status=$ST stage=$STG"
  if [ "$VV2" -gt "$VV" ] && [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "VIDEO" ]; then break; fi
  if [ "$ST" = "FAILED" ]; then FAIL=1; break; fi
  sleep 10
done
VV2=$(latest_video_version)
echo "VIDEO_V2=$VV2"
if [ "$VV2" -le "$VV" ]; then echo "FAIL: VIDEO version did not increment"; FAIL=1; fi

echo "========== S-18-07: approve VIDEO → COMPLETED (D-51) =========="
poll_gate "VIDEO" 120 5 || true
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"VIDEO","decision":"APPROVED"}'
echo
FINAL=$(pipeline_status)
FINAL_ST=$(echo "$FINAL" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
deadline=$(( $(date +%s) + 60 ))
while [ "$FINAL_ST" != "COMPLETED" ] && [ "$(date +%s)" -lt "$deadline" ]; do
  sleep 5
  FINAL=$(pipeline_status)
  FINAL_ST=$(echo "$FINAL" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  echo "  poll post-approve status=$FINAL_ST"
done
echo "FINAL=$FINAL"
if [ "$FINAL_ST" != "COMPLETED" ]; then echo "FAIL: expected COMPLETED after VIDEO approve"; FAIL=1; fi

echo "========== S-18-08: inline SQL =========="
echo "--- V-18-01 terminal ---"
psql -c "SELECT id, status, current_stage FROM pipeline_runs WHERE id='$RUN_ID';"
echo "--- V-18-02 VIDEO versions ---"
psql -c "SELECT version, content_hash, metadata_json->>'source' src FROM asset_versions WHERE project_id='$PROJECT' AND stage='VIDEO' ORDER BY version;"
echo "--- V-18-03 approvals VIDEO ---"
psql -c "SELECT stage, decision, LEFT(rationale,60) FROM approvals WHERE pipeline_run_id='$RUN_ID' AND stage='VIDEO' ORDER BY created_at;"

echo "DONE RUN_ID=$RUN_ID PROJECT=$PROJECT FAIL=$FAIL"
exit $FAIL
