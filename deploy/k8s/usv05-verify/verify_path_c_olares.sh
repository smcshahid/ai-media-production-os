#!/usr/bin/env bash
# US-V05 PATH C — backward compatibility on Olares (existing COMPLETED runs).
set -uo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
EVID="${EVID_DIR:-/tmp/usv05-evidence-pathc}"
mkdir -p "$EVID"

: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT:?set PROJECT}"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
FAIL=0

log() { echo "$(date -Iseconds) $*" | tee -a "$EVID/path-c.log"; }

psql() {
  $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"
}

log "PATH C regression API=$API PROJECT=$PROJECT"

LEGACY=$(psql -c "
  SELECT id::text FROM pipeline_runs
  WHERE project_id='$PROJECT' AND status='COMPLETED'
    AND (scene_count IS NULL OR scene_count <= 1)
  ORDER BY updated_at DESC LIMIT 1;
")
if [ -z "$LEGACY" ]; then
  log "FAIL no legacy COMPLETED run found"
  exit 1
fi
log "legacy_run=$LEGACY"

check() {
  local name="$1" url="$2" out="$3"
  local code
  code=$(curl -s -m 60 -o "$out" -w "%{http_code}" "$url" -H "$AUTH")
  log "$name http=$code -> $out"
  if [ "$code" != "200" ]; then FAIL=1; fi
}

check "export" "$API/export/$LEGACY" "$EVID/legacy-export.zip"
if [ -f "$EVID/legacy-export.zip" ]; then
  unzip -p "$EVID/legacy-export.zip" manifest.json > "$EVID/legacy-manifest.json" 2>/dev/null || true
  MV=$(grep -o '"manifest_version"[[:space:]]*:[[:space:]]*"[^"]*"' "$EVID/legacy-manifest.json" | head -1 || true)
  log "legacy manifest: $MV"
  if ! grep -q '"manifest_version"[[:space:]]*:[[:space:]]*"1"' "$EVID/legacy-manifest.json" 2>/dev/null; then
    log "WARN manifest may not be v1"
  fi
fi

check "history" "$API/assets/history?project_id=$PROJECT" "$EVID/history.json"
check "history-run" "$API/assets/history?project_id=$PROJECT&pipeline_run_id=$LEGACY" "$EVID/history-run.json"
check "audit" "$API/audit?project_id=$PROJECT&limit=20" "$EVID/audit.json"
check "audit-run" "$API/audit?project_id=$PROJECT&pipeline_run_id=$LEGACY&limit=20" "$EVID/audit-run.json"
check "lineage" "$API/lineage/$LEGACY" "$EVID/lineage.json"
check "runs" "$API/pipeline/runs?project_id=$PROJECT" "$EVID/runs.json"
check "status" "$API/pipeline/status?project_id=$PROJECT" "$EVID/status.json"

# Pipeline start with scene_count on current API (may fail if old image)
START=$(curl -s -m 30 -w "\nHTTP:%{http_code}" -X POST "$API/pipeline/start" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"project_id":"'"$PROJECT"'","scene_count":1}')
echo "$START" > "$EVID/start-scene-count-probe.json"
HTTP=$(echo "$START" | sed -n 's/.*HTTP:\([0-9]*\).*/\1/p')
log "scene_count start probe http=$HTTP (409=active run, 201=ok, 422=old API schema)"

log "DONE PATH C FAIL=$FAIL"
exit $FAIL
