#!/usr/bin/env bash
# Complete orphaned PATH C1 run and verify manifest v5 export.
set -uo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
EVID="${EVID_DIR:-/tmp/usv08-evidence/path-c1}"

: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT:?set PROJECT}"
RUN_ID="${RUN_ID:-2dacd911-853d-497f-a3f1-9b5f7332dcdc}"
EPISODE_ID="${EPISODE_ID:-19f77d4a-9874-4dea-862c-4ec18be1cea0}"
EPISODE_NUM="${EPISODE_NUM:-53}"

mkdir -p "$EVID"
API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"

log() { echo "$(date -Iseconds) $*" | tee -a "$EVID/c1-supplement.log"; }

approve() {
  curl -sf -m 60 -X POST "$API/pipeline/approve" -H "$AUTH" -H 'Content-Type: application/json' \
    -d '{"project_id":"'"$PROJECT"'","stage":"'"$1"'","decision":"APPROVED"}' >> "$EVID/c1-supplement.log" 2>&1
  echo >> "$EVID/c1-supplement.log"
}

poll_until() {
  local want_status="$1" want_stage="$2" want_scene="${3:-}" max="${4:-3600}"
  local deadline=$(( $(date +%s) + max ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    local url="$API/pipeline/status?project_id=$PROJECT&episode_id=$EPISODE_ID"
    local body st stg scn
    body=$(curl -sf -m 20 "$url" -H "$AUTH" || echo '{}')
    st=$(echo "$body" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
    stg=$(echo "$body" | sed -n 's/.*"current_stage":"\([^"]*\)".*/\1/p')
    scn=$(echo "$body" | sed -n 's/.*"current_scene_index":\([0-9]*\).*/\1/p')
    log "poll status=$st stage=${stg:-null} scene=${scn:-null}"
    if [ "$st" = "FAILED" ]; then log "FAIL pipeline FAILED"; return 1; fi
    if [ "$st" = "$want_status" ]; then
      if [ -n "$want_stage" ] && [ "$stg" != "$want_stage" ]; then sleep 10; continue; fi
      if [ -n "$want_scene" ] && [ "$scn" != "$want_scene" ]; then sleep 10; continue; fi
      return 0
    fi
    sleep 15
  done
  return 1
}

log "PATH C1 supplemental complete run=$RUN_ID ep=$EPISODE_NUM"
poll_until AWAITING_APPROVAL SCRIPT "" 60 || true
approve SCRIPT
poll_until AWAITING_APPROVAL STORYBOARD 1 2400 || exit 1
approve STORYBOARD
poll_until AWAITING_APPROVAL VIDEO 1 5400 || exit 1
approve VIDEO
poll_until COMPLETED "" "" 120 || exit 1

# Reuse export verification from main script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
VERIFY="/tmp/verify_usv08_e2e.sh"
export EVID_DIR="$(dirname "$EVID")"
export API AUTH PROJECT PGPW NS K

# shellcheck disable=SC1090
source "$VERIFY"
verify_character_export C1 "$RUN_ID" "$EPISODE_ID" "$EPISODE_NUM" 1 3
echo "PATH_C1=$RUN_ID|$EPISODE_ID|$EPISODE_NUM" | tee "$EVID/summary.txt"
log "PASS PATH C1 supplemental"
