#!/usr/bin/env bash
# US-V06 Audio Narration E2E acceptance on Olares (Paths A–D).
# Requires: TOKEN, PGPW, PROJECT env vars; Phase 5 worker with espeak-ng.
set -uo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
EVID="${EVID_DIR:-/tmp/usv06-evidence}"
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
  local label="$1" scene_count="$2"
  local paragraph
  case "$scene_count" in
    1) paragraph="A researcher discovers bioluminescent coral that sings at midnight. Write exactly one scene with clear dialogue for narration. The coral voice must be heard." ;;
    2) paragraph="A researcher discovers bioluminescent coral that sings at midnight. Write exactly two scenes with clear dialogue in each scene for narration. Scene one: discovery. Scene two: allies debate protecting the reef." ;;
    3) paragraph="A researcher discovers bioluminescent coral that sings at midnight. Write exactly three scenes with clear dialogue in each scene for narration. Scene one: discovery. Scene two: debate. Scene three: resolution at the reef." ;;
    *) paragraph="A researcher discovers bioluminescent coral that sings at midnight with clear dialogue for narration." ;;
  esac
  curl -sf -m 30 -X POST "$API/ideas" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","title":"US-V06 '"$label"'","paragraph":"'"$paragraph"'","style_note":"cinematic documentary narration test"}' \
    >> "$EVID/e2e.log" 2>&1
  echo >> "$EVID/e2e.log"
}

verify_narrated_export() {
  local label="$1" run_id="$2" scene_count="$3"
  local zip="$EVID/path-${label}-export.zip"
  curl -sf -m 120 "$API/export/$run_id" -H "$AUTH" -o "$zip"
  unzip -p "$zip" manifest.json > "$EVID/path-${label}-manifest.json"
  local mv narr_count
  mv=$(sed -n 's/.*"manifest_version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$EVID/path-${label}-manifest.json" | head -1)
  log "export manifest_version=$mv size=$(wc -c < "$zip")"
  if [ "$mv" != "3" ]; then log "FAIL PATH $label expected manifest v3 got $mv"; return 1; fi
  if ! grep -q 'narration.wav' "$EVID/path-${label}-manifest.json"; then
    log "FAIL PATH $label manifest missing narration.wav entry"; return 1
  fi
  narr_count=$(psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' AND stage='NARRATION' AND pipeline_run_id='$run_id';")
  log "NARRATION assets for run: $narr_count (expect >= $scene_count)"
  if [ "${narr_count:-0}" -lt "$scene_count" ]; then
    log "FAIL PATH $label insufficient NARRATION assets"; return 1
  fi
  local narrated_videos
  narrated_videos=$(psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT' AND stage='VIDEO' AND pipeline_run_id='$run_id' AND (metadata_json->>'has_narration')='true';")
  log "VIDEO assets with has_narration=true: $narrated_videos (expect >= $scene_count)"
  if [ "${narrated_videos:-0}" -lt "$scene_count" ]; then
    log "FAIL PATH $label insufficient narrated VIDEO assets"; return 1
  fi
  curl -sf -m 30 "$API/audit?project_id=$PROJECT&pipeline_run_id=$run_id&limit=50" -H "$AUTH" \
    > "$EVID/path-${label}-audit.json"
  curl -sf -m 30 "$API/lineage/$run_id" -H "$AUTH" > "$EVID/path-${label}-lineage.json"
  log "PASS PATH $label narrated run $run_id"
  return 0
}

run_path() {
  local label="$1" scene_count="$2"
  local attempt run_id start http s ok
  for attempt in 1 2 3 4 5; do
    log "========== PATH $label: ${scene_count}-scene narrated run (attempt $attempt) =========="
    cancel_active_runs
    submit_idea "$label" "$scene_count"

    start=$(curl -s -m 30 -w "\nHTTP:%{http_code}" -X POST "$API/pipeline/start" -H "$AUTH" -H 'Content-Type: application/json' \
      -d '{"project_id":"'"$PROJECT"'","scene_count":'"$scene_count"'}')
    http=$(echo "$start" | sed -n 's/.*HTTP:\([0-9]*\).*/\1/p')
    run_id=$(echo "$start" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
    log "start http=$http run_id=$run_id"
    echo "$start" > "$EVID/path-${label}-start-attempt${attempt}.json"
    if [ "$http" != "201" ]; then log "WARN pipeline start failed attempt $attempt"; continue; fi

    poll_until AWAITING_APPROVAL STORY "" 900 || continue
    approve STORY
    poll_until AWAITING_APPROVAL SCRIPT "" 900 || continue
    approve SCRIPT

    ok=1
    for s in $(seq 1 "$scene_count"); do
      log "--- Scene $s / $scene_count STORYBOARD ---"
      poll_until AWAITING_APPROVAL STORYBOARD "$s" 2400 || { ok=0; break; }
      approve STORYBOARD
      log "--- Scene $s / $scene_count VIDEO (narration) ---"
      poll_until AWAITING_APPROVAL VIDEO "$s" 5400 || { ok=0; break; }
      approve VIDEO
    done
    [ "$ok" = "1" ] || continue

    poll_until COMPLETED "" "" 120 || continue
    if verify_narrated_export "$label" "$run_id" "$scene_count"; then
      echo "$run_id"
      return 0
    fi
  done
  log "FAIL PATH $label after 5 attempts"
  return 1
}

path_d_regression() {
  log "========== PATH D: backward compatibility (silent / v1/v2) =========="
  local legacy_run
  legacy_run=$(psql -c "
    SELECT id::text FROM pipeline_runs
    WHERE project_id='$PROJECT' AND status='COMPLETED'
      AND (scene_count IS NULL OR scene_count <= 1)
      AND id NOT IN (
        SELECT DISTINCT pipeline_run_id FROM asset_versions
        WHERE stage='NARRATION' AND pipeline_run_id IS NOT NULL
      )
    ORDER BY updated_at DESC LIMIT 1;
  ")
  if [ -z "$legacy_run" ]; then
    log "WARN no pre-narration legacy run — checking any COMPLETED single-scene export"
    legacy_run=$(psql -c "
      SELECT id::text FROM pipeline_runs
      WHERE project_id='$PROJECT' AND status='COMPLETED'
        AND (scene_count IS NULL OR scene_count=1)
      ORDER BY created_at ASC LIMIT 1;
    ")
  fi
  if [ -z "$legacy_run" ]; then
    log "FAIL PATH D no legacy run found"; return 1
  fi
  log "legacy run=$legacy_run"
  curl -sf -m 120 "$API/export/$legacy_run" -H "$AUTH" -o "$EVID/path-D-legacy-export.zip" || {
    log "FAIL legacy export"; return 1; }
  unzip -p "$EVID/path-D-legacy-export.zip" manifest.json > "$EVID/path-D-legacy-manifest.json"
  local mv
  mv=$(sed -n 's/.*"manifest_version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$EVID/path-D-legacy-manifest.json" | head -1)
  log "legacy manifest_version=$mv (expect 1 or 2, not 3)"
  if [ "$mv" = "3" ]; then log "FAIL PATH D legacy export is v3"; return 1; fi
  curl -sf -m 30 "$API/assets/history?project_id=$PROJECT" -H "$AUTH" > "$EVID/path-D-history.json" || return 1
  curl -sf -m 30 "$API/pipeline/runs?project_id=$PROJECT" -H "$AUTH" > "$EVID/path-D-runs.json" || return 1
  log "PASS PATH D backward compatibility on $legacy_run manifest=$mv"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  log "US-V06 E2E start PROJECT=$PROJECT API=$API"
  run_path A 1 || FAIL=1
  run_path B 2 || FAIL=1
  run_path C 3 || FAIL=1
  path_d_regression || FAIL=1

  log "DONE FAIL=$FAIL"
  exit $FAIL
fi
