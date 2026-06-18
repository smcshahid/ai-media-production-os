#!/usr/bin/env bash
# US-V09 Full Platform Re-attestation on Olares (Phase 8).
# Coverage: drift governance, multi-scene, narration, episode, character snapshot, export v5.
set -uo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
EVID="${EVID_DIR:-/tmp/usv09-evidence}"
mkdir -p "$EVID"

: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT:?set PROJECT}"

LIB="/tmp/verify_common.sh"
if [ ! -f "$LIB" ]; then
  LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/verify_common.sh"
fi
# shellcheck source=/dev/null
source "$LIB"
verify_common_source_helpers

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
FAIL=0

log "US-V09 Olares platform re-attestation start"
verify_common_acquire_lock

# --- V09-01: Alembic head from manifest ---
log "========== V09-01: Alembic head =========="
MANIFEST="${MANIFEST_PATH:-/tmp/aimpos-manifest.yaml}"
LOADER="${MANIFEST_LOADER:-/tmp/load-manifest-env.sh}"
  if [ -f "$LOADER" ] && [ -f "$MANIFEST" ]; then
  # shellcheck source=/dev/null
  source "$LOADER" "$MANIFEST"
  ALEMBIC=$(psql -c "SELECT version_num FROM alembic_version;" | tr -d '\r\n')
  log "cluster alembic=$ALEMBIC expected=$EXPECTED_ALEMBIC"
  if [ "$ALEMBIC" != "$EXPECTED_ALEMBIC" ]; then log "FAIL alembic drift"; FAIL=1; else log "PASS alembic"; fi
else
  log "WARN manifest loader missing — skip alembic manifest check"
fi

# --- V09-02: Worker narration env ---
log "========== V09-02: Narration enabled =========="
NARR=$($K get deploy aimpos-worker -n "$NS" -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="NARRATION_ENABLED")].value}' 2>/dev/null || echo "")
log "NARRATION_ENABLED=${NARR:-unset}"
if [ "${NARR:-false}" != "true" ]; then log "FAIL narration not enabled on worker"; FAIL=1; else log "PASS narration env"; fi

# --- V09-03: Governance API reads ---
log "========== V09-03: Governance reads =========="
for path in "pipeline/runs?project_id=$PROJECT" "characters?project_id=$PROJECT" "episodes?project_id=$PROJECT"; do
  http=$(curl -s -m 20 -o /dev/null -w "%{http_code}" "$API/$path" -H "$AUTH" || echo 000)
  log "GET /$path http=$http"
  if [ "$http" != "200" ]; then log "FAIL governance read $path"; FAIL=1; fi
done

# --- V09-04: Consolidated platform path (2-scene episode + character → manifest v5) ---
run_platform_path() {
  cancel_active_runs || true
  psql -c "DELETE FROM characters WHERE project_id='$PROJECT';" >> "$EVID/e2e-olares.log" 2>&1 || true

  local ep_resp ep_id ep_num char_id start http run_id s
  ep_resp=$(curl -sf -m 30 -X POST "$API/episodes" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","title":"US-V09 Platform"}')
  ep_id=$(echo "$ep_resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['episode']['id'])")
  ep_num=$(echo "$ep_resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['episode']['episode_number'])")
  log "episode id=$ep_id number=$ep_num"

  char_id=$(curl -sf -m 30 -X POST "$API/characters" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","name":"Maya-V09","role":"lead","description":"US-V09","visual_traits":"silver hair","personality_notes":"calm"}' \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['character']['id'])")
  log "character id=$char_id"

  curl -sf -m 30 -X POST "$API/ideas" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","title":"US-V09","paragraph":"Maya discovers bioluminescent coral across two connected scenes with dialogue.","style_note":"platform attestation"}' \
    >> "$EVID/e2e-olares.log" 2>&1

  start=$(curl -s -m 30 -w "\nHTTP:%{http_code}" -X POST "$API/pipeline/start" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","episode_id":"'"$ep_id"'","scene_count":2,"character_ids":["'"$char_id"'"]}')
  http=$(echo "$start" | sed -n 's/.*HTTP:\([0-9]*\).*/\1/p')
  run_id=$(echo "$start" | sed -n 's/.*"run_id":"\([^"]*\)".*/\1/p')
  log "start http=$http run_id=$run_id"
  if [ "$http" != "201" ]; then return 1; fi

  poll_until AWAITING_APPROVAL STORY "" "$ep_id" 900 || return 1
  approve STORY "$ep_id" || return 1
  poll_until AWAITING_APPROVAL SCRIPT "" "$ep_id" 900 || return 1
  approve SCRIPT "$ep_id" || return 1

  for s in 1 2; do
    poll_until AWAITING_APPROVAL STORYBOARD "$s" "$ep_id" 2400 || return 1
    approve STORYBOARD "$ep_id" || return 1
    poll_until AWAITING_APPROVAL VIDEO "$s" "$ep_id" 5400 || return 1
    approve VIDEO "$ep_id" || return 1
  done

  poll_until COMPLETED "" "" "$ep_id" 120 || return 1
  log "platform path COMPLETED run_id=$run_id"

  local snap_count
  snap_count=$(psql -c "
    SELECT CASE
      WHEN character_snapshot IS NULL THEN 0
      ELSE json_array_length(character_snapshot::json)
    END
    FROM pipeline_runs WHERE id='$run_id';
  ")
  log "character_snapshot length=$snap_count"
  if [ "${snap_count:-0}" -lt 1 ] 2>/dev/null; then log "FAIL missing character_snapshot"; return 1; fi

  verify_common_export_manifest_version "$run_id" "5" "$EVID/platform-export.zip" "$EVID/platform-manifest.json" || return 1

  grep -q '"characters"' "$EVID/platform-manifest.json" || { log "FAIL manifest missing characters"; return 1; }
  grep -q '"episode_number"' "$EVID/platform-manifest.json" || { log "FAIL manifest missing episode_number"; return 1; }
  grep -q 'scenes/' "$EVID/platform-manifest.json" || { log "FAIL manifest missing multi-scene paths"; return 1; }
  log "PASS platform consolidated path (manifest v5)"
  echo "$run_id" > "$EVID/platform-run-id.txt"
  return 0
}

log "========== V09-04: Consolidated platform path =========="
path_ok=0
if verify_common_retry 3 "platform-path" run_platform_path; then
  path_ok=1
  log "PASS V09-04"
else
  log "FAIL V09-04 platform path"
  FAIL=1
fi
if [ "$path_ok" -ne 1 ]; then FAIL=1; fi

log "US-V09 DONE FAIL=$FAIL"
echo "$FAIL" > "$EVID/FAIL"
exit $FAIL
