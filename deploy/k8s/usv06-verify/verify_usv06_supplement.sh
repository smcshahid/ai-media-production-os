#!/usr/bin/env bash
# US-V06 supplemental — PATH A and PATH D only (after main E2E partial pass).
set -uo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
EVID="${EVID_DIR:-/tmp/usv06-evidence-supplement}"
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

# shellcheck source=verify_usv06_e2e.sh
source /tmp/verify_usv06_e2e.sh 2>/dev/null || true

# Re-define helpers if sourcing failed (minimal subset)
if ! declare -F poll_until >/dev/null; then
  poll_until() {
    local want_status="$1" want_stage="$2" want_scene="${3:-}" max="${4:-1200}"
    local deadline=$(( $(date +%s) + max ))
    while [ "$(date +%s)" -lt "$deadline" ]; do
      local body st stg scn
      body=$(curl -sf -m 20 "$API/pipeline/status?project_id=$PROJECT" -H "$AUTH" || echo '{}')
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
    return 1
  }
fi

log "US-V06 supplement: PATH A + PATH D"
run_path A 1 || FAIL=1
path_d_regression || FAIL=1
log "DONE FAIL=$FAIL"
exit $FAIL
