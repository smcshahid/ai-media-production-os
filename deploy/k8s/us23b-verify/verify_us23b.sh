#!/usr/bin/env bash
# US-23b Olares verification — read-only audit trail API (D-64).
set -uo pipefail
NS=aimpos-mwayolares
: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT_ID:?set PROJECT_ID}"
: "${RUN_ID:?set RUN_ID — pipeline run with audit events}"
K="sudo k3s kubectl"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

FAIL=0
ROWS_BEFORE=$(psql -c "SELECT COUNT(*) FROM audit_events;")

echo "US-23b verify start $(date -Iseconds)"
echo "API=$API PROJECT_ID=$PROJECT_ID RUN_ID=$RUN_ID"
echo "AUDIT_EVENTS_BEFORE=$ROWS_BEFORE"

echo "========== S-23b-01: GET /audit =========="
HTTP=$(curl -s -m 60 -o /tmp/us23b-audit.json -w "%{http_code}" \
  "$API/audit?project_id=$PROJECT_ID" -H "$AUTH")
echo "AUDIT http=$HTTP"
if [ "$HTTP" != "200" ]; then FAIL=1; fi

echo "========== S-23b-02: API vs SQL row parity =========="
SQL_COUNT=$(psql -c "SELECT COUNT(*) FROM audit_events WHERE project_id='$PROJECT_ID';")
API_COUNT=$(python3 - <<'PY'
import json
m=json.load(open("/tmp/us23b-audit.json"))
print(len(m["events"]))
PY
)
echo "SQL_AUDIT_COUNT=$SQL_COUNT API_AUDIT_COUNT=$API_COUNT"
if [ "$SQL_COUNT" != "$API_COUNT" ]; then echo "FAIL: audit count mismatch"; FAIL=1; fi

echo "========== S-23b-03: run filter =========="
HTTP=$(curl -s -m 60 -o /tmp/us23b-audit-run.json -w "%{http_code}" \
  "$API/audit?project_id=$PROJECT_ID&pipeline_run_id=$RUN_ID" -H "$AUTH")
echo "AUDIT_RUN http=$HTTP"
if [ "$HTTP" != "200" ]; then FAIL=1; fi
RUN_ID="$RUN_ID" python3 - <<'PY' || FAIL=1
import json, os
run_id = os.environ["RUN_ID"]
m = json.load(open("/tmp/us23b-audit-run.json"))
for e in m["events"]:
    assert e.get("pipeline_run_id") == run_id, e
print("RUN_FILTER=PASS count=", len(m["events"]))
PY

echo "========== S-23b-04: required event types =========="
python3 - <<'PY' || FAIL=1
import json
m=json.load(open("/tmp/us23b-audit-run.json"))
types={e["event_type"] for e in m["events"]}
for req in ("PIPELINE_STARTED","STAGE_STARTED","AGENT_TASK_COMPLETED","ASSET_STORED"):
    assert req in types, types
print("EVENT_TYPES=PASS", sorted(types))
PY

echo "========== S-23b-05: history regression =========="
HHTTP=$(curl -s -m 60 -o /dev/null -w "%{http_code}" \
  "$API/assets/history?project_id=$PROJECT_ID" -H "$AUTH")
echo "HISTORY http=$HHTTP"
if [ "$HHTTP" != "200" ]; then FAIL=1; fi

echo "========== S-23b-06: no audit writes =========="
ROWS_AFTER=$(psql -c "SELECT COUNT(*) FROM audit_events;")
echo "AUDIT_EVENTS_AFTER=$ROWS_AFTER"
if [ "$ROWS_BEFORE" != "$ROWS_AFTER" ]; then echo "FAIL: audit_events count changed"; FAIL=1; fi

echo "DONE PROJECT_ID=$PROJECT_ID FAIL=$FAIL"
exit $FAIL
