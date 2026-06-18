#!/usr/bin/env bash
# US-V08B PATH D/E supplemental attestation (uses primary E2E run artifacts).
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
EVID="${EVID_DIR:-/tmp/usv08b-evidence}"
mkdir -p "$EVID"

: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT:?set PROJECT}"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
FAIL=0

log() { echo "$(date -Iseconds) $*" >> "$EVID/e2e-de-supplement.log"; echo "$(date -Iseconds) $*" >&2; }

psql() {
  $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"
}

# Primary E2E PATH D runs (2026-06-18)
RUN1="${USV08B_RUN1:-5d99fc7b-2a59-4b59-be86-f048b4cdd9d4}"
RUN2="${USV08B_RUN2:-a6a92786-6e55-499d-9d15-39153af62f81}"

log "========== PATH D supplement: snapshot name isolation =========="
ORIG_NAME=$(psql -c "SELECT character_snapshot::json->0->>'name' FROM pipeline_runs WHERE id='$RUN1';")
EDIT_NAME=$(psql -c "SELECT character_snapshot::json->0->>'name' FROM pipeline_runs WHERE id='$RUN2';")
log "run1 snapshot name=$ORIG_NAME run2 snapshot name=$EDIT_NAME"

if [ -z "$ORIG_NAME" ] || [ -z "$EDIT_NAME" ]; then
  log "FAIL PATH D supplement missing snapshot names"
  exit 1
fi
if [ "$ORIG_NAME" = "$EDIT_NAME" ]; then
  log "FAIL PATH D supplement names identical"
  exit 1
fi
if [[ "$EDIT_NAME" != *"-Edited" ]]; then
  log "FAIL PATH D supplement run2 name not edited: $EDIT_NAME"
  exit 1
fi

curl -sf -m 120 "$API/export/$RUN1" -H "$AUTH" -o "$EVID/path-D-run1-export.zip"
unzip -p "$EVID/path-D-run1-export.zip" manifest.json > "$EVID/path-D-run1-manifest.json"
curl -sf -m 120 "$API/export/$RUN2" -H "$AUTH" -o "$EVID/path-D-run2-export.zip"
unzip -p "$EVID/path-D-run2-export.zip" manifest.json > "$EVID/path-D-run2-manifest.json"

python3 -c "
import json
m1=json.load(open('$EVID/path-D-run1-manifest.json'))
m2=json.load(open('$EVID/path-D-run2-manifest.json'))
assert m1['characters'][0]['name'] == '''$ORIG_NAME'''
assert m2['characters'][0]['name'] == '''$EDIT_NAME'''
assert m1['manifest_version']=='5' and m2['manifest_version']=='5'
"
log "PASS PATH D supplement run1=$RUN1 run2=$RUN2"

CHAR_ID=$(psql -c "SELECT character_ids::json->>0 FROM pipeline_runs WHERE id='$RUN1';")
log "========== PATH E supplement: delete after export =========="
curl -sf -m 120 "$API/export/$RUN1" -H "$AUTH" -o "$EVID/path-E-before-export.zip"
unzip -p "$EVID/path-E-before-export.zip" manifest.json > "$EVID/path-E-before-manifest.json"

curl -sf -m 30 -X DELETE "$API/characters/$CHAR_ID?project_id=$PROJECT" -H "$AUTH" \
  >> "$EVID/e2e-de-supplement.log" 2>&1

curl -sf -m 120 "$API/export/$RUN1" -H "$AUTH" -o "$EVID/path-E-after-export.zip"
unzip -p "$EVID/path-E-after-export.zip" manifest.json > "$EVID/path-E-after-manifest.json"

python3 -c "
import json
b=json.load(open('$EVID/path-E-before-manifest.json'))
a=json.load(open('$EVID/path-E-after-manifest.json'))
assert b['characters']==a['characters']
assert b['manifest_version']=='5'
"
log "PASS PATH E supplement run=$RUN1 char=$CHAR_ID"
echo "PATH_D_SUPPLEMENT=PASS|$RUN1|$RUN2"
echo "PATH_E_SUPPLEMENT=PASS|$RUN1|$CHAR_ID"
log "DONE FAIL=0"
exit 0
