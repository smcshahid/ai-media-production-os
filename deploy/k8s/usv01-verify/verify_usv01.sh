#!/usr/bin/env bash
# US-V01 Visual MVP acceptance — full E2E S-00..S-16 incl. Amendment A-01 (D-47).
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

echo "US-V01 verify start $(date -Iseconds)"
echo "API=$API PROJECT=$PROJECT"
echo "API_IMAGE=$API_IMAGE WORKER_IMAGE=$WORKER_IMAGE"

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

pipeline_status() { curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH"; }

parse_status() {
  local json="$1"
  echo "$json" | sed -n 's/.*"status":"\([^"]*\)".*/ST=\1/p'
  echo "$json" | sed -n 's/.*"current_stage":"\([^"]*\)".*/STG=\1/p'
  echo "$json" | sed -n 's/.*"run_id":"\([^"]*\)".*/RUN=\1/p'
}

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

latest_storyboard_version() {
  psql -c "SELECT COALESCE(MAX(version),0) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD';"
}

count_sb_batch() {
  local ver="$1"
  psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD' AND version=$ver;"
}

latest_story_asset_id() {
  psql -c "
    SELECT id::text FROM asset_versions
    WHERE project_id='$PROJECT' AND stage='STORY'
    ORDER BY version DESC LIMIT 1;
  "
}

latest_storyboard_frame_id() {
  local ver="$1"
  psql -c "
    SELECT id::text FROM asset_versions
    WHERE project_id='$PROJECT' AND stage='STORYBOARD' AND version=$ver
    ORDER BY (metadata_json->>'frame_index')::int LIMIT 1;
  "
}

FAIL=0

echo "========== PF-01: deploy images =========="
echo "API_IMAGE=$API_IMAGE"
echo "WORKER_IMAGE=$WORKER_IMAGE"

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
  -d '{"project_id":"'"$PROJECT"'","title":"US-V01 Visual MVP Acceptance","paragraph":"A marine biologist on a remote station must decide whether to broadcast a discovery that could save the reef or keep it secret from corporate harvesters arriving at dawn.","style_note":"cinematic"}'
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
EDIT_JSON='{"text":"# US-V01 Human Edit\n\n**Logline:** The biologist chooses transparency.\n\n### Act I\nDiscovery at the reef station.\n\n### Act II\nCorporate pressure at dawn.\n\n### Act III\nThe broadcast decision."}'
curl -s -m 60 -X PUT "$API/assets/$STORY_ID" -H "$AUTH" -H 'Content-Type: application/json' -d "$EDIT_JSON"
echo

echo "========== S-06: approve STORY =========="
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORY","decision":"APPROVED"}'
echo

echo "========== S-07: poll SCRIPT gate =========="
poll_gate "SCRIPT" 900 15 || FAIL=1

echo "========== S-08: reject SCRIPT =========="
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"SCRIPT","decision":"REJECT","note":"US-V01: tighten dialogue in the second scene."}'
echo

echo "========== S-09: regenerate SCRIPT =========="
curl -s -m 120 -X POST "$API/pipeline/regenerate" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"SCRIPT"}'
echo

echo "========== S-10: poll SCRIPT gate (post-regen) =========="
poll_gate "SCRIPT" 900 15 || FAIL=1

echo "========== S-11: approve SCRIPT =========="
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"SCRIPT","decision":"APPROVED"}'
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
psql -c "SELECT version, metadata_json->>'frame_index' fi, content_hash FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD' AND version=$SB_V1 ORDER BY (metadata_json->>'frame_index')::int;" \
  | tee /tmp/usv01-v1-hashes.txt

echo "========== S-12a: reject STORYBOARD (A-01) =========="
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORYBOARD","decision":"REJECT","note":"US-V01 A-01: increase contrast and wider establishing shots."}'
echo

echo "========== S-12b: regenerate STORYBOARD (A-01 / D-47) =========="
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
psql -c "SELECT version, metadata_json->>'frame_index' fi, content_hash FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD' AND version=$SB_V1 ORDER BY (metadata_json->>'frame_index')::int;"

echo "========== S-13: PNG content-read =========="
FRAME_ID=$(latest_storyboard_frame_id "$SB_V2")
HTTP=$(curl -s -m 30 -o /tmp/usv01-frame.png -w "%{http_code}" "$API/assets/$FRAME_ID/content" -H "$AUTH")
echo "CONTENT_READ id=$FRAME_ID http=$HTTP bytes=$(wc -c < /tmp/usv01-frame.png 2>/dev/null || echo 0)"
if [ "$HTTP" != "200" ]; then FAIL=1; fi

echo "========== S-14: approve STORYBOARD → COMPLETED =========="
curl -s -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORYBOARD","decision":"APPROVED"}'
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
if [ "$FINAL_ST" != "COMPLETED" ]; then echo "FAIL: expected COMPLETED got $FINAL_ST"; FAIL=1; fi
SB_AFTER_S14=$(psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD';")
echo "STORYBOARD_ROWS_AFTER_S14=$SB_AFTER_S14"
if [ "$SB_BEFORE_S14" != "$SB_AFTER_S14" ]; then echo "FAIL: D-46 asset write on approve"; FAIL=1; fi

echo "========== S-15: worker restart durability (SC-V06) =========="
DR_BASE="$FINAL"
echo "DR-01 baseline=$DR_BASE" | tee /tmp/usv01-worker-restart.log
$K rollout restart deployment/aimpos-worker -n "$NS"
$K rollout status deployment/aimpos-worker -n "$NS" --timeout=300s | tee -a /tmp/usv01-worker-restart.log
sleep 30
for i in 1 2 3; do
  POST=$(pipeline_status)
  echo "DR-06 poll_$i=$POST" | tee -a /tmp/usv01-worker-restart.log
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

echo "========== S-16: inline SQL attestation =========="
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
echo "--- V-07 agent completions ---"
psql -c "SELECT event_type, payload->>'agent' agent, model_id FROM audit_events WHERE pipeline_run_id='$RUN_ID' AND event_type='AGENT_TASK_COMPLETED' ORDER BY created_at;"
echo "--- V-47 STORYBOARD regen audit ---"
psql -c "SELECT COUNT(*) FROM audit_events WHERE pipeline_run_id='$RUN_ID' AND event_type='REGENERATION_REQUESTED' AND payload->>'stage'='STORYBOARD';"

echo "========== worker log excerpt (storyboard) =========="
$K logs deploy/aimpos-worker -n "$NS" --tail=100 2>&1 | grep -Ei 'storyboard_agent_completed|regenerat' | grep -Ev 'Deprecation|JsonPlus' | tee /tmp/usv01-worker-tail.log || true

echo "DONE RUN_ID=$RUN_ID PROJECT=$PROJECT SB_V1=$SB_V1 SB_V2=$SB_V2 FAIL=$FAIL"
echo "SC-V07 delta_start_to_story_gate=$((T_STORY_GATE - T_START))s"
export RUN_ID PROJECT SB_V1 SB_V2
exit $FAIL
