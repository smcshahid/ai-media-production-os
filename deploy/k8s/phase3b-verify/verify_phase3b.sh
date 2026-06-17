#!/usr/bin/env bash
# Phase 3B Olares verification — audit export, run history, read regressions (D-66–D-68).
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

echo "Phase 3B Olares verify start $(date -Iseconds)"
echo "API=$API PROJECT_ID=$PROJECT_ID RUN_ID=$RUN_ID"
echo "AUDIT_EVENTS_BEFORE=$ROWS_BEFORE"

echo "========== P3B-01: audit export JSON =========="
HTTP=$(curl -s -m 60 -o /tmp/p3b-audit.json -w "%{http_code}" \
  "$API/audit/export?project_id=$PROJECT_ID&format=json" -H "$AUTH")
echo "AUDIT_EXPORT_JSON http=$HTTP"
if [ "$HTTP" != "200" ]; then FAIL=1; fi

echo "========== P3B-02: audit export CSV =========="
HTTP=$(curl -s -m 60 -o /tmp/p3b-audit.csv -w "%{http_code}" \
  "$API/audit/export?project_id=$PROJECT_ID&format=csv" -H "$AUTH")
head -1 /tmp/p3b-audit.csv
echo "AUDIT_EXPORT_CSV http=$HTTP"
if [ "$HTTP" != "200" ]; then FAIL=1; fi

echo "========== P3B-03: run-scoped export =========="
HTTP=$(curl -s -m 60 -o /tmp/p3b-audit-run.json -w "%{http_code}" \
  "$API/audit/export?project_id=$PROJECT_ID&pipeline_run_id=$RUN_ID&format=json" -H "$AUTH")
echo "AUDIT_EXPORT_RUN http=$HTTP"
if [ "$HTTP" != "200" ]; then FAIL=1; fi

echo "========== P3B-04: pipeline run list =========="
HTTP=$(curl -s -m 60 -o /tmp/p3b-runs.json -w "%{http_code}" \
  "$API/pipeline/runs?project_id=$PROJECT_ID" -H "$AUTH")
echo "PIPELINE_RUNS http=$HTTP"
if [ "$HTTP" != "200" ]; then FAIL=1; fi
python3 - <<'PY' || FAIL=1
import json
m = json.load(open("/tmp/p3b-runs.json"))
assert "runs" in m and len(m["runs"]) >= 1, m
print("RUN_COUNT=", len(m["runs"]))
PY

echo "========== P3B-05: audit API regression =========="
HTTP=$(curl -s -m 60 -o /tmp/p3b-audit-read.json -w "%{http_code}" \
  "$API/audit?project_id=$PROJECT_ID" -H "$AUTH")
echo "AUDIT_READ http=$HTTP"
if [ "$HTTP" != "200" ]; then FAIL=1; fi

echo "========== P3B-06: asset history regression =========="
HHTTP=$(curl -s -m 60 -o /dev/null -w "%{http_code}" \
  "$API/assets/history?project_id=$PROJECT_ID" -H "$AUTH")
echo "HISTORY http=$HHTTP"
if [ "$HHTTP" != "200" ]; then FAIL=1; fi

echo "========== P3B-07: no audit writes =========="
ROWS_AFTER=$(psql -c "SELECT COUNT(*) FROM audit_events;")
echo "AUDIT_EVENTS_AFTER=$ROWS_AFTER"
if [ "$ROWS_BEFORE" != "$ROWS_AFTER" ]; then echo "FAIL: audit_events count changed"; FAIL=1; fi

echo "DONE PROJECT_ID=$PROJECT_ID FAIL=$FAIL"
exit $FAIL
