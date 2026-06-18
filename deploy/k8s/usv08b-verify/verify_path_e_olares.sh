#!/usr/bin/env bash
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
EVID="${EVID_DIR:-/tmp/usv08b-evidence}"
: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT:?set PROJECT}"
: "${USV08B_RUN1:?set USV08B_RUN1}"
: "${USV08B_CHAR:?set USV08B_CHAR}"
API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
log() { echo "$(date -Iseconds) $*" >> "$EVID/e2e-path-e.log"; echo "$(date -Iseconds) $*" >&2; }

log "========== PATH E: character delete after export =========="
curl -sf -m 120 "$API/export/$USV08B_RUN1" -H "$AUTH" -o "$EVID/path-E-before-export.zip"
unzip -p "$EVID/path-E-before-export.zip" manifest.json > "$EVID/path-E-before-manifest.json"
curl -sf -m 30 -X DELETE "$API/characters/$USV08B_CHAR?project_id=$PROJECT" -H "$AUTH" >> "$EVID/e2e-path-e.log" 2>&1
curl -sf -m 120 "$API/export/$USV08B_RUN1" -H "$AUTH" -o "$EVID/path-E-after-export.zip"
unzip -p "$EVID/path-E-after-export.zip" manifest.json > "$EVID/path-E-after-manifest.json"
python3 -c "
import json
b=json.load(open('$EVID/path-E-before-manifest.json'))
a=json.load(open('$EVID/path-E-after-manifest.json'))
assert b.get('manifest_version')=='5'
assert b['characters']==a['characters']
"
log "PASS PATH E delete-after-export run=$USV08B_RUN1 char=$USV08B_CHAR"
exit 0
