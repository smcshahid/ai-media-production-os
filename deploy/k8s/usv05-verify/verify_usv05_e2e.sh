#!/usr/bin/env bash
# US-V05 Multi-Scene E2E acceptance on Olares (Paths A, B, C).
# Requires: TOKEN, PGPW, PROJECT env vars; Phase 4 deployed; Alembic 0004.
set -uo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
EVID="${EVID_DIR:-/tmp/usv05-evidence}"
mkdir -p "$EVID"

: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT:?set PROJECT}"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
FAIL=0

log() { echo "$(date -Iseconds) $*" | tee -a "$EVID/e2e.log"; }

psql() {
  $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"
}

poll_until() {
  local want_status="$1" want_stage="$2" want_scene="${3:-}" max="${4:-1200}"
  local deadline=$(( $(date +%s) + max ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    local body
    body=$(curl -sf -m 20 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH" || echo '{}')
    local st stg scn
    st=$(echo "$body" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
    stg=$(echo "$body" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
    scn=$(echo "$body" | sed -n 's/.*"current_scene_index":\([0-9]*\).*/\1/p')
    log "  poll status=$st stage=${stg:-null} scene=${scn:-null}"
    if [ "$st" = "FAILED" ]; then log "FAIL pipeline FAILED: $body"; return 1; fi
    if [ "$st" = "$want_status" ]; then
      if [ -n "$want_stage" ] && [ "$stg" != "$want_stage" ]; then sleep 10; continue; fi
      if [ -n "$want_scene" ] && [ "$scn" != "$want_scene" ]; then sleep 10; continue; fi
      return 0
    fi
    sleep 15
  done
  log "FAIL poll timeout want=$want_status/$want_stage scene=$want_scene"
  return 1
}

approve() {
  local stage="$1"
  curl -sf -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","stage":"'"$stage"'","decision":"APPROVED"}' >> "$EVID/e2e.log" 2>&1
  echo >> "$EVID/e2e.log"
}

cancel_active_runs() {
  log "Cancelling non-terminal active runs for project"
  psql -c "
    UPDATE pipeline_runs SET status='CANCELLED', current_stage=NULL, updated_at=NOW()
    WHERE project_id='$PROJECT' AND status IN ('PENDING','RUNNING','AWAITING_APPROVAL');
  " >> "$EVID/e2e.log" 2>&1 || true
}

submit_idea() {
  curl -sf -m 30 -X POST "$API/ideas" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","title":"US-V05 '"$1"'","paragraph":"A researcher discovers bioluminescent coral that sings at midnight. Corporate harvesters approach. Two allies debate broadcast vs secrecy across connected scenes.","style_note":"cinematic documentary"}' \
    >> "$EVID/e2e.log" 2>&1
  echo >> "$EVID/e2e.log"
}

run_path() {
  local label="$1" scene_count="$2"
  log "========== PATH $label: ${scene_count}-scene run =========="
  cancel_active_runs
  submit_idea "$label"

  local start http run_id
  start=$(curl -s -m 30 -w "\nHTTP:%{http_code}" -X POST "$API/pipeline/start" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","scene_count":'"$scene_count"'}')
  http=$(echo "$start" | sed -n 's/.*HTTP:\([0-9]*\).*/\1/p')
  run_id=$(echo "$start" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
  log "start http=$http run_id=$run_id"
  echo "$start" > "$EVID/path-${label}-start.json"
  if [ "$http" != "201" ]; then log "FAIL pipeline start"; return 1; fi

  # STORY
  poll_until AWAITING_APPROVAL STORY "" 900 || return 1
  approve STORY
  # SCRIPT
  poll_until AWAITING_APPROVAL SCRIPT "" 900 || return 1
  approve SCRIPT

  local s
  for s in $(seq 1 "$scene_count"); do
    log "--- Scene $s / $scene_count STORYBOARD ---"
    poll_until AWAITING_APPROVAL STORYBOARD "$s" 2400 || return 1
    local frames
    frames=$(psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' AND stage='STORYBOARD' AND COALESCE((metadata_json->>'scene_index')::int,1)=$s;")
    log "storyboard frames for scene $s: $frames"
    approve STORYBOARD

    log "--- Scene $s / $scene_count VIDEO ---"
    poll_until AWAITING_APPROVAL VIDEO "$s" 5400 || return 1
    approve VIDEO
  done

  poll_until COMPLETED "" "" 120 || return 1
  log "PATH $label pipeline COMPLETED run_id=$run_id"

  # Export
  local zip manifest
  zip="$EVID/path-${label}-export.zip"
  curl -sf -m 120 "$API/export/$run_id" -H "$AUTH" -o "$zip"
  unzip -p "$zip" manifest.json > "$EVID/path-${label}-manifest.json"
  local mv
  mv=$(sed -n 's/.*"manifest_version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$EVID/path-${label}-manifest.json" | head -1)
  log "export manifest_version=$mv size=$(wc -c < "$zip")"
  if [ "$scene_count" -gt 1 ] && [ "$mv" != "2" ]; then log "FAIL expected manifest v2"; return 1; fi
  if [ "$scene_count" -eq 1 ] && [ "$mv" != "1" ]; then log "FAIL expected manifest v1"; return 1; fi

  # Governance reads
  curl -sf -m 30 "$API/audit?project_id=$PROJECT&pipeline_run_id=$run_id&limit=50" -H "$AUTH" \
    > "$EVID/path-${label}-audit.json"
  curl -sf -m 30 "$API/assets/history?project_id=$PROJECT&pipeline_run_id=$run_id" -H "$AUTH" \
    > "$EVID/path-${label}-history.json"
  curl -sf -m 30 "$API/lineage/$run_id" -H "$AUTH" \
    > "$EVID/path-${label}-lineage.json"
  curl -sf -m 30 "$API/pipeline/runs?project_id=$PROJECT" -H "$AUTH" \
    > "$EVID/path-${label}-runs.json"

  log "PASS PATH $label"
  echo "$run_id"
}

path_c_regression() {
  log "========== PATH C: backward compatibility =========="
  local legacy_run
  legacy_run=$(psql -c "
    SELECT id::text FROM pipeline_runs
    WHERE project_id='$PROJECT' AND status='COMPLETED' AND (scene_count IS NULL OR scene_count=1)
    ORDER BY updated_at DESC LIMIT 1;
  ")
  if [ -z "$legacy_run" ]; then
    log "WARN no legacy COMPLETED single-scene run — running PATH C as new 1-scene E2E"
    run_path C 1 || return 1
    return 0
  fi
  log "legacy run=$legacy_run"
  curl -sf -m 120 "$API/export/$legacy_run" -H "$AUTH" -o "$EVID/path-C-legacy-export.zip" || { log "FAIL legacy export"; return 1; }
  unzip -p "$EVID/path-C-legacy-export.zip" manifest.json > "$EVID/path-C-legacy-manifest.json"
  local mv
  mv=$(sed -n 's/.*"manifest_version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$EVID/path-C-legacy-manifest.json" | head -1)
  log "legacy manifest_version=$mv (expect 1)"
  if [ "$mv" != "1" ]; then log "FAIL legacy manifest not v1"; return 1; fi
  curl -sf -m 30 "$API/assets/history?project_id=$PROJECT" -H "$AUTH" > "$EVID/path-C-history.json" || return 1
  curl -sf -m 30 "$API/audit?project_id=$PROJECT&limit=20" -H "$AUTH" > "$EVID/path-C-audit.json" || return 1
  curl -sf -m 30 "$API/lineage/$legacy_run" -H "$AUTH" > "$EVID/path-C-lineage.json" || return 1
  curl -sf -m 30 "$API/pipeline/runs?project_id=$PROJECT" -H "$AUTH" > "$EVID/path-C-runs.json" || return 1
  log "PASS PATH C regression on legacy run $legacy_run"
}

log "US-V05 E2E start PROJECT=$PROJECT API=$API"
run_path A 2 || FAIL=1
run_path B 3 || FAIL=1
path_c_regression || FAIL=1

log "DONE FAIL=$FAIL"
exit $FAIL
