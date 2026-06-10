#!/usr/bin/env bash
# US-09 focused Olares verification (reject → regenerate ×3 → 429).
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

story_versions() {
  psql -c "SELECT id||'|'||version||'|'||branch||'|'||is_ai_generated FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORY' ORDER BY version;"
}

regen_count() {
  psql -c "SELECT COUNT(*) FROM audit_events WHERE pipeline_run_id='$RUN_ID' AND event_type='REGENERATION_REQUESTED' AND payload->>'stage'='STORY';"
}

latest_story_version() {
  psql -c "SELECT COALESCE(MAX(version),0) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORY';"
}

wait_for_story_version() {
  local target="$1"
  local deadline=$(( $(date +%s) + 600 ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    local cur
    cur=$(latest_story_version)
    echo "  poll story version=$cur target>=$target"
    if [ "$cur" -ge "$target" ]; then return 0; fi
    sleep 15
  done
  echo "  WARN: timed out waiting for story version >= $target"
  return 1
}

echo "========== SETUP: STORY review gate =========="
CUR=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH")
ST=$(echo "$CUR" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
STG=$(echo "$CUR" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
if [ "$ST" != "AWAITING_APPROVAL" ] || [ "$STG" != "STORY" ]; then
  echo "Need AWAITING_APPROVAL/STORY — run ui_capture_prep or start pipeline first"
  exit 1
fi
RUN_ID=$(echo "$CUR" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
echo "RUN_ID=$RUN_ID"

echo "========== V1: Reject with note =========="
REJ=$(curl -s -m 30 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORY","decision":"REJECT","note":"US-09 Olares verify: deepen Act III."}')
echo "$REJ"
VERS_BEFORE=$(story_versions)
echo "STORY_BEFORE"
echo "$VERS_BEFORE"
echo "REGEN_COUNT_BEFORE=$(regen_count)"

BASE_VER=$(latest_story_version)
echo "BASE_STORY_VERSION=$BASE_VER"

for N in 1 2 3; do
  echo "========== V$((N+1)): Regenerate #$N =========="
  VER_BEFORE=$(latest_story_version)
  RESP=$(curl -s -m 120 -w "\nHTTP_CODE:%{http_code}" -X POST "$API/pipeline/regenerate" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","stage":"STORY"}')
  echo "$RESP"
  TARGET_VER=$((VER_BEFORE + 1))
  wait_for_story_version "$TARGET_VER" || true
  echo "STORY_AFTER_$N"
  story_versions
  echo "REGEN_COUNT=$N observed=$(regen_count)"
done

echo "========== V4: 4th regenerate (expect 429) =========="
VERS_PRE_429=$(story_versions)
COUNT_PRE=$(regen_count)
AUDIT_PRE=$(psql -c "SELECT COUNT(*) FROM audit_events WHERE pipeline_run_id='$RUN_ID';")
WORKER_LOG_PRE=$($K logs deploy/aimpos-worker -n "$NS" --tail=5 2>&1 | wc -l)
RESP4=$(curl -s -m 30 -w "\nHTTP_CODE:%{http_code}" -X POST "$API/pipeline/regenerate" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORY"}')
echo "$RESP4"
COUNT_AFTER=$(regen_count)
AUDIT_AFTER=$(psql -c "SELECT COUNT(*) FROM audit_events WHERE pipeline_run_id='$RUN_ID';")
echo "REGEN_COUNT_BEFORE=$COUNT_PRE REGEN_COUNT_AFTER=$COUNT_AFTER"
echo "AUDIT_COUNT_BEFORE=$AUDIT_PRE AUDIT_COUNT_AFTER=$AUDIT_AFTER"
echo "STORY_AFTER_429"
story_versions
echo "VERSIONS_UNCHANGED=$([ "$(story_versions)" = "$VERS_PRE_429" ] && echo YES || echo NO)"
echo "AUDIT_UNCHANGED=$([ "$AUDIT_PRE" = "$AUDIT_AFTER" ] && echo YES || echo NO)"
sleep 5
echo "WORKER_LOG_TAIL_POST_429"
$K logs deploy/aimpos-worker -n "$NS" --tail=15 2>&1 | grep -Ei 'regenerat|signal|story architect|run_story' | grep -Ev 'Deprecation|JsonPlus' || echo "(no new regenerate/agent lines)"

echo "========== V5: Approve final draft → SCRIPT =========="
APPR=$(curl -s -m 60 -w "\nHTTP_CODE:%{http_code}" -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","stage":"STORY","decision":"APPROVE"}')
echo "$APPR"
sleep 5
echo "PIPELINE_AFTER_APPROVE"
curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH"
echo
echo "APPROVAL_ROWS"
psql -c "SELECT stage||'|'||decision||'|'||COALESCE(note,'')||'|'||created_at FROM approvals WHERE pipeline_run_id='$RUN_ID' ORDER BY created_at;"

echo "========== V6: D-38 version chain =========="
psql -c "SELECT id||'|'||version||'|'||branch||'|'||is_ai_generated||'|'||content_hash||'|'||created_at FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORY' ORDER BY version;"

echo "DONE RUN_ID=$RUN_ID"
