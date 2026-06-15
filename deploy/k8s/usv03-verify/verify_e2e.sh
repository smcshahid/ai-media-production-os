#!/usr/bin/env bash
# US-V02 Spark Full acceptance — full E2E S-00..S-28 (D-37..D-54).
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

echo "US-V02 verify start $(date -Iseconds)"
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

approve_stage() {
  local stage="$1"
  local decision="$2"
  local note="${3:-}"
  local max_attempts="${4:-12}"
  local attempt=1
  while [ "$attempt" -le "$max_attempts" ]; do
    if [ -n "$note" ]; then
      BODY='{"project_id":"'"$PROJECT"'","stage":"'"$stage"'","decision":"'"$decision"'","note":"'"$note"'"}'
    else
      BODY='{"project_id":"'"$PROJECT"'","stage":"'"$stage"'","decision":"'"$decision"'"}'
    fi
    RESP=$(curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' -d "$BODY")
    echo "$RESP"
    if echo "$RESP" | grep -q '"decision":"APPROVED"\|"decision":"REJECTED"'; then
      return 0
    fi
    if echo "$RESP" | grep -q 'not awaiting approval'; then
      echo "  approve retry $attempt/$max_attempts stage=$stage (async gate)"
      sleep 10
      poll_gate "$stage" 120 10 || true
      attempt=$((attempt + 1))
      continue
    fi
    return 1
  done
  echo "FAIL: approve $stage $decision after $max_attempts attempts"
  return 1
}

latest_storyboard_version() {
  psql -c "SELECT COALESCE(MAX(version),0) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD';"
}

count_sb_batch() {
  local ver="$1"
  psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD' AND version=$ver;"
}

latest_story_asset_id() {
  psql -c "SELECT id::text FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORY' ORDER BY version DESC LIMIT 1;"
}

latest_storyboard_frame_id() {
  local ver="$1"
  psql -c "SELECT id::text FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD' AND version=$ver ORDER BY (metadata_json->>'frame_index')::int LIMIT 1;"
}

latest_video_id() {
  psql -c "SELECT id::text FROM asset_versions WHERE project_id='$PROJECT' AND stage='VIDEO' ORDER BY version DESC LIMIT 1;"
}

latest_video_version() {
  psql -c "SELECT COALESCE(MAX(version),0) FROM asset_versions WHERE project_id='$PROJECT' AND stage='VIDEO';"
}

FAIL=0

echo "========== PF-01: deploy images =========="
echo "API_IMAGE=$API_IMAGE WORKER_IMAGE=$WORKER_IMAGE"

echo "========== PF-07: ffmpeg in worker =========="
$K exec deploy/aimpos-worker -n "$NS" -- ffmpeg -version | head -1 || { echo "FAIL: ffmpeg missing"; FAIL=1; }

echo "========== PF-04: health =========="
curl -s -m 15 "$API/health" || true
echo

echo "========== PF-06: no active run =========="
PRE=$(pipeline_status)
PRE_ST=$(echo "$PRE" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
if [ "$PRE_ST" = "RUNNING" ] || [ "$PRE_ST" = "AWAITING_APPROVAL" ]; then
  echo "FAIL: project has active run status=$PRE_ST"
  exit 2
fi

echo "========== S-02: POST /ideas =========="
curl -s -m 30 -X POST "$API/ideas" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","title":"US-V02 Spark Full Acceptance","paragraph":"A marine biologist on a remote station must decide whether to broadcast a discovery that could save the reef or keep it secret from corporate harvesters arriving at dawn.","style_note":"cinematic"}'
echo

echo "========== S-03: POST /pipeline/start =========="
T_START=$(date +%s)
START=$(curl -s -m 30 -w "\nHTTP_CODE:%{http_code}" -X POST "$API/pipeline/start" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'"}')
echo "START=$START"
HTTP_CODE=$(echo "$START" | sed -n 's/.*HTTP_CODE:\([0-9]*\).*/\1/p')
RUN_ID=$(echo "$START" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
if [ "$HTTP_CODE" != "201" ]; then echo "FAIL: pipeline start HTTP=$HTTP_CODE"; exit 1; fi
echo "RUN_ID=$RUN_ID"

echo "========== S-04: poll STORY gate =========="
poll_gate "STORY" 900 15 || FAIL=1
T_STORY_GATE=$(date +%s)
echo "T_STORY_GATE=$T_STORY_GATE delta_start=$((T_STORY_GATE - T_START))s"

echo "========== S-05: human edit STORY =========="
STORY_ID=$(latest_story_asset_id)
echo "STORY_ID=$STORY_ID"
EDIT_JSON='{"text":"# US-V02 Human Edit\n\n**Logline:** The biologist chooses transparency.\n\n### Act I\nDiscovery at the reef station.\n\n### Act II\nCorporate pressure at dawn.\n\n### Act III\nThe broadcast decision."}'
curl -s -m 60 -X PUT "$API/assets/$STORY_ID" -H "$AUTH" -H 'Content-Type: application/json' -d "$EDIT_JSON"
echo

echo "========== S-06: approve STORY =========="
approve_stage "STORY" "APPROVED" || FAIL=1
echo

echo "========== S-07: poll SCRIPT gate =========="
poll_gate "SCRIPT" 900 15 || FAIL=1

echo "========== S-08: reject SCRIPT =========="
approve_stage "SCRIPT" "REJECT" "US-V02: tighten dialogue in the second scene." || FAIL=1
echo

echo "========== S-09: regenerate SCRIPT =========="
curl -s -m 120 -X POST "$API/pipeline/regenerate" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"SCRIPT"}'
echo

echo "========== S-10: poll SCRIPT gate (post-regen) =========="
poll_gate "SCRIPT" 900 15 || FAIL=1

echo "========== S-11: approve SCRIPT =========="
approve_stage "SCRIPT" "APPROVED" || FAIL=1
echo

echo "========== S-12: poll STORYBOARD gate (batch v1) =========="
DEADLINE=$(( $(date +%s) + 1800 ))
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  CUR=$(latest_storyboard_version)
  S=$(pipeline_status)
  ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
  echo "  poll sb_version=$CUR status=$ST stage=$STG"
  if [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "STORYBOARD" ] && [ "$CUR" -ge 1 ]; then
    FC=$(count_sb_batch "$CUR")
    if [ "$FC" = "4" ]; then break; fi
  fi
  if [ "$ST" = "FAILED" ]; then echo "FAILED=$S"; FAIL=1; break; fi
  sleep 20
done
SB_V1=$(latest_storyboard_version)
echo "SB_V1=$SB_V1 frames=$(count_sb_batch "$SB_V1")"

echo "========== S-12a: reject STORYBOARD (A-01) =========="
approve_stage "STORYBOARD" "REJECT" "US-V02 A-01: increase contrast and wider establishing shots." || FAIL=1
echo

echo "========== S-12b: regenerate STORYBOARD (D-47) =========="
curl -s -m 120 -X POST "$API/pipeline/regenerate" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORYBOARD"}'
echo

echo "========== S-12c: poll STORYBOARD gate (batch v2) =========="
TARGET_V2=$((SB_V1 + 1))
DEADLINE=$(( $(date +%s) + 1800 ))
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  CUR=$(latest_storyboard_version)
  S=$(pipeline_status)
  ST=$(echo "$S" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  STG=$(echo "$S" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
  echo "  poll sb_version=$CUR target>=$TARGET_V2 status=$ST stage=$STG"
  if [ "$CUR" -ge "$TARGET_V2" ] && [ "$ST" = "AWAITING_APPROVAL" ] && [ "$STG" = "STORYBOARD" ]; then
    FC=$(count_sb_batch "$CUR")
    if [ "$FC" = "4" ]; then break; fi
  fi
  if [ "$ST" = "FAILED" ]; then echo "FAILED=$S"; FAIL=1; break; fi
  sleep 20
done
SB_V2=$(latest_storyboard_version)
echo "SB_V2=$SB_V2 frames=$(count_sb_batch "$SB_V2")"
SB_BEFORE_S14=$(psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD';")
echo "STORYBOARD_ROWS_BEFORE_S14=$SB_BEFORE_S14"

echo "========== V-47 inline: v1 intact =========="
V1_COUNT=$(count_sb_batch "$SB_V1")
if [ "$V1_COUNT" = "4" ]; then echo "V-47 v1 batch count=4: PASS"; else echo "FAIL V-47 v1 count=$V1_COUNT"; FAIL=1; fi

echo "========== S-13: PNG content-read =========="
FRAME_ID=$(latest_storyboard_frame_id "$SB_V2")
HTTP=$(curl -s -m 30 -o /tmp/usv02-frame.png -w "%{http_code}" "$API/assets/$FRAME_ID/content" -H "$AUTH")
echo "CONTENT_READ id=$FRAME_ID http=$HTTP bytes=$(wc -c < /tmp/usv02-frame.png 2>/dev/null || echo 0)"
if [ "$HTTP" != "200" ]; then FAIL=1; fi

echo "========== S-14: approve STORYBOARD (D-51 — NOT terminal) =========="
approve_stage "STORYBOARD" "APPROVED" || FAIL=1
echo
POST_SB=$(pipeline_status)
POST_SB_ST=$(echo "$POST_SB" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
echo "POST_SB_STATUS=$POST_SB_ST"
if [ "$POST_SB_ST" = "COMPLETED" ]; then echo "FAIL D-51: COMPLETED at STORYBOARD"; FAIL=1; fi
SB_AFTER_S14=$(psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD';")
echo "STORYBOARD_ROWS_AFTER_S14=$SB_AFTER_S14"
if [ "$SB_BEFORE_S14" != "$SB_AFTER_S14" ]; then echo "FAIL: D-46 asset write on approve"; FAIL=1; fi

echo "========== S-15: poll VIDEO gate =========="
poll_gate "VIDEO" 1200 20 || FAIL=1
T_VIDEO_GATE=$(date +%s)
echo "T_VIDEO_GATE=$T_VIDEO_GATE"

echo "========== S-16: VIDEO asset + metadata (D-48) =========="
VID=$(latest_video_id)
VV=$(latest_video_version)
META=$(psql -c "SELECT metadata_json::text FROM asset_versions WHERE id='$VID';")
echo "VIDEO_ID=$VID VIDEO_V1=$VV META=$META"
if [ -z "$VID" ]; then echo "FAIL: no VIDEO asset"; FAIL=1; fi

echo "========== S-17: MP4 content-read (SC-F02) =========="
HTTP=$(curl -s -m 60 -o /tmp/usv02-video.mp4 -w "%{http_code}" "$API/assets/$VID/content" -H "$AUTH")
BYTES=$(wc -c < /tmp/usv02-video.mp4 2>/dev/null || echo 0)
echo "CONTENT_READ http=$HTTP bytes=$BYTES"
if [ "$HTTP" != "200" ]; then FAIL=1; fi
python3 -c "d=open('/tmp/usv02-video.mp4','rb').read(12); assert len(d)>=8 and d[4:8]==b'ftyp', d; print('MP4_MAGIC=PASS')" || { echo "FAIL: no ftyp"; FAIL=1; }

echo "========== S-18: reject VIDEO (D-50 setup) =========="
approve_stage "VIDEO" "REJECT" "US-V02: slightly longer hold on frame 2." || FAIL=1
echo

echo "========== S-19: regenerate VIDEO (D-50) =========="
curl -s -m 120 -X POST "$API/pipeline/regenerate" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"VIDEO"}'
echo

echo "========== S-20: poll VIDEO gate (post-regen) =========="
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
VIDEO_V2=$(latest_video_version)
echo "VIDEO_V2=$VIDEO_V2"
if [ "$VIDEO_V2" -le "$VV" ]; then echo "FAIL: VIDEO version did not increment"; FAIL=1; fi

echo "========== S-21: approve VIDEO → COMPLETED (D-51) =========="
poll_gate "VIDEO" 120 5 || true
approve_stage "VIDEO" "APPROVED" || FAIL=1
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
echo "FINAL_STATUS=$FINAL_ST"
if [ "$FINAL_ST" != "COMPLETED" ]; then echo "FAIL: expected COMPLETED after VIDEO approve"; FAIL=1; fi

echo "========== S-22: lineage STORYBOARD→VIDEO (SC-F03) =========="
FINAL_VID=$(latest_video_id)
LC=$(psql -c "
SELECT COUNT(*) FROM lineage_edges le
JOIN asset_versions p ON le.parent_id = p.id
JOIN asset_versions c ON le.child_id = c.id
WHERE c.id='$FINAL_VID' AND p.stage='STORYBOARD';
")
echo "LINEAGE_COUNT=$LC"
if [ "$LC" != "4" ]; then echo "FAIL: expected 4 STORYBOARD→VIDEO edges"; FAIL=1; fi

echo "========== S-23: GET /export (D-52) =========="
HTTP=$(curl -s -m 120 -o /tmp/usv02-export.zip -w "%{http_code}" "$API/export/$RUN_ID" -H "$AUTH")
ZIP_BYTES=$(wc -c < /tmp/usv02-export.zip 2>/dev/null || echo 0)
echo "EXPORT http=$HTTP bytes=$ZIP_BYTES"
if [ "$HTTP" != "200" ]; then FAIL=1; fi
head -c 2 /tmp/usv02-export.zip | od -An -tx1 | grep -q "50 4b" && echo "ZIP_MAGIC=PASS" || { echo "FAIL: no PK"; FAIL=1; }

echo "========== S-24: unzip + manifest + hash verify (D-53) =========="
rm -rf /tmp/usv02-export
mkdir -p /tmp/usv02-export
unzip -q -o /tmp/usv02-export.zip -d /tmp/usv02-export
COUNT=$(find /tmp/usv02-export -type f | wc -l)
echo "FILE_COUNT=$COUNT"
if [ "$COUNT" != "9" ]; then echo "FAIL: expected 9 files"; FAIL=1; fi
python3 - <<'PY' || FAIL=1
import json, sys
m=json.load(open("/tmp/usv02-export/manifest.json"))
for k in ("manifest_version","pipeline_run_id","project_id","exported_at","files"):
    assert k in m, k
assert m["manifest_version"]=="1"
assert len(m["files"])==8
print("MANIFEST=PASS")
PY
python3 - <<'PY' || FAIL=1
import hashlib, json, pathlib
m=json.load(open("/tmp/usv02-export/manifest.json"))
root=pathlib.Path("/tmp/usv02-export")
for f in m["files"]:
    data=(root/f["path"]).read_bytes()
    h=hashlib.sha256(data).hexdigest()
    assert h==f["content_hash"], f["path"]
print("HASH_VERIFY=PASS")
PY

echo "========== S-25: BUNDLE_EXPORTED audit (D-54) =========="
AUDIT=$(psql -c "SELECT COUNT(*) FROM audit_events WHERE pipeline_run_id='$RUN_ID' AND event_type='BUNDLE_EXPORTED';")
echo "BUNDLE_EXPORTED_COUNT=$AUDIT"
if [ "$AUDIT" -lt "1" ]; then echo "FAIL: no BUNDLE_EXPORTED"; FAIL=1; fi
psql -c "SELECT event_type, payload->>'manifest_hash' mh, payload->>'file_count' fc, payload->>'zip_size_bytes' sz FROM audit_events WHERE pipeline_run_id='$RUN_ID' AND event_type='BUNDLE_EXPORTED' ORDER BY created_at DESC LIMIT 1;"

echo "========== S-26: negative export 409 (D-52 gate) =========="
ACTIVE=$(psql -c "SELECT id::text FROM pipeline_runs WHERE status='AWAITING_APPROVAL' ORDER BY created_at DESC LIMIT 1;")
if [ -n "$ACTIVE" ]; then
  NHTTP=$(curl -s -m 30 -o /dev/null -w "%{http_code}" "$API/export/$ACTIVE" -H "$AUTH")
  echo "NEGATIVE_RUN=$ACTIVE http=$NHTTP"
  if [ "$NHTTP" != "409" ]; then echo "FAIL: expected 409 for non-COMPLETED"; FAIL=1; fi
else
  echo "SKIP negative (no AWAITING_APPROVAL run in cluster)"
fi

echo "========== S-27: inline SQL attestation =========="
echo "--- V-01 terminal ---"
psql -c "SELECT id, status, current_stage FROM pipeline_runs WHERE id='$RUN_ID';"
echo "--- V-02 approvals ---"
psql -c "SELECT stage, decision, LEFT(rationale,60) FROM approvals WHERE pipeline_run_id='$RUN_ID' ORDER BY created_at;"
echo "--- V-04 SCRIPT versions ---"
psql -c "SELECT version, branch, content_hash FROM asset_versions WHERE project_id='$PROJECT' AND stage='SCRIPT' ORDER BY version;"
echo "--- V-05 STORYBOARD batches ---"
psql -c "SELECT version, COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD' GROUP BY version ORDER BY version;"
echo "--- V-06 lineage ---"
psql -c "SELECT p.stage, c.stage, COUNT(*) FROM lineage_edges le JOIN asset_versions p ON le.parent_id=p.id JOIN asset_versions c ON le.child_id=c.id WHERE p.project_id='$PROJECT' GROUP BY p.stage, c.stage ORDER BY 1,2;"
echo "--- V-08 agent completions ---"
psql -c "SELECT event_type, payload->>'agent' agent, model_id FROM audit_events WHERE pipeline_run_id='$RUN_ID' AND event_type='AGENT_TASK_COMPLETED' ORDER BY created_at;"
echo "--- V-20 D-51 POST_SB not terminal ---"
echo "POST_SB_STATUS=$POST_SB_ST (logged at S-14)"

echo "========== S-28: worker restart durability (SC-F05 / SC-V06) =========="
DR_BASE="$FINAL"
echo "DR-01 baseline=$DR_BASE" | tee /tmp/usv02-worker-restart.log
$K rollout restart deployment/aimpos-worker -n "$NS"
$K rollout status deployment/aimpos-worker -n "$NS" --timeout=300s | tee -a /tmp/usv02-worker-restart.log
sleep 30
for i in 1 2 3; do
  POST=$(pipeline_status)
  echo "DR-06 poll_$i=$POST" | tee -a /tmp/usv02-worker-restart.log
  sleep 10
done
POST_ST=$(echo "$POST" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
POST_RUN=$(echo "$POST" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
if [ "$POST_ST" = "COMPLETED" ] && [ "$POST_RUN" = "$RUN_ID" ]; then
  echo "SC-V06 worker restart: PASS"
else
  echo "FAIL: SC-V06 post-restart status=$POST_ST run=$POST_RUN"
  FAIL=1
fi

echo "DONE RUN_ID=$RUN_ID PROJECT=$PROJECT SB_V1=$SB_V1 SB_V2=$SB_V2 VIDEO_V2=$VIDEO_V2 FAIL=$FAIL"
echo "SC-V07 delta_start_to_story_gate=$((T_STORY_GATE - T_START))s"
export RUN_ID PROJECT SB_V1 SB_V2 VIDEO_V2
exit $FAIL
