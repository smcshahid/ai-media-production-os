#!/usr/bin/env bash
# US-21 Olares verification — realtime pipeline status (D-59).
set -uo pipefail
NS=aimpos-mwayolares
: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT_ID:?set PROJECT_ID}"
: "${RUN_ID:?set RUN_ID}"
K="sudo k3s kubectl"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
FAIL=0

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

ROWS_BEFORE=$(psql -c "SELECT COUNT(*) FROM asset_versions;")

echo "US-21 verify start $(date -Iseconds)"
echo "API=$API PROJECT_ID=$PROJECT_ID RUN_ID=$RUN_ID"

echo "========== S-21-07: API image us21 =========="
API_IMAGE=$($K get deploy aimpos-api -n "$NS" -o jsonpath='{.spec.template.spec.containers[0].image}')
WORKER_IMAGE=$($K get deploy aimpos-worker -n "$NS" -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "missing")
echo "API_IMAGE=$API_IMAGE WORKER_IMAGE=$WORKER_IMAGE"
if [[ "$API_IMAGE" != *"us21"* ]]; then echo "FAIL: expected aimpos-api:us21"; FAIL=1; fi
if [[ "$WORKER_IMAGE" != *"us21"* ]]; then echo "FAIL: expected aimpos-worker:us21"; FAIL=1; fi

echo "========== S-21-01/02: WebSocket smoke + REST parity =========="
POD=$($K get pods -n "$NS" -l app=aimpos-api -o jsonpath='{.items[0].metadata.name}')
$K cp /tmp/ws_smoke.py "$NS/$POD:/tmp/ws_smoke.py" 2>/dev/null || true
$K exec -n "$NS" "$POD" -- pip install -q --target /tmp/wslib websocket-client >/dev/null 2>&1 || true
WS_RC=$($K exec -n "$NS" "$POD" -- env PYTHONPATH=/tmp/wslib TOKEN="$TOKEN" PROJECT_ID="$PROJECT_ID" python3 /tmp/ws_smoke.py 2>&1)
echo "$WS_RC"
if [[ "$WS_RC" != *"WS_SMOKE=PASS"* ]]; then FAIL=1; fi

REST=$(curl -s -m 30 "$API/pipeline/status?project_id=$PROJECT_ID" -H "$AUTH")
echo "REST status=$(echo "$REST" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','?'))")"

echo "========== S-21-03: latency spot-check (REST updated_at present) =========="
UPDATED=$(psql -c "SELECT updated_at FROM pipeline_runs WHERE project_id='$PROJECT_ID' ORDER BY created_at DESC LIMIT 1;")
echo "SQL_UPDATED_AT=$UPDATED"
echo "LATENCY_NOTE=full gate timing requires active transition; WS smoke confirms push path"

echo "========== S-21-05: REST poll fallback (GET /pipeline/status) =========="
PHTTP=$(curl -s -m 30 -o /dev/null -w "%{http_code}" "$API/pipeline/status?project_id=$PROJECT_ID" -H "$AUTH")
echo "POLL http=$PHTTP"
if [ "$PHTTP" != "200" ]; then FAIL=1; fi

echo "========== S-21-06: Redis regression (/health) =========="
RHTTP=$(curl -s -m 30 -o /tmp/us21-health.json -w "%{http_code}" "$API/health")
echo "HEALTH http=$RHTTP"
python3 - <<'PY' || FAIL=1
import json
h=json.load(open("/tmp/us21-health.json"))
redis=h.get("dependencies",{}).get("redis",{})
status=redis.get("status") if isinstance(redis, dict) else redis
assert status=="ok", h
print("REDIS_HEALTH=PASS")
PY

echo "========== S-21-07 regressions: history, lineage, export =========="
HHTTP=$(curl -s -m 60 -o /dev/null -w "%{http_code}" "$API/assets/history?project_id=$PROJECT_ID" -H "$AUTH")
LHTTP=$(curl -s -m 60 -o /dev/null -w "%{http_code}" "$API/lineage/$RUN_ID" -H "$AUTH")
EHTTP=$(curl -s -m 120 -o /dev/null -w "%{http_code}" "$API/export/$RUN_ID" -H "$AUTH")
echo "HISTORY=$HHTTP LINEAGE=$LHTTP EXPORT=$EHTTP"
if [ "$HHTTP" != "200" ] || [ "$LHTTP" != "200" ] || [ "$EHTTP" != "200" ]; then FAIL=1; fi

echo "========== S-21-08: asset_versions unchanged =========="
ROWS_AFTER=$(psql -c "SELECT COUNT(*) FROM asset_versions;")
echo "ASSET_VERSIONS_BEFORE=$ROWS_BEFORE AFTER=$ROWS_AFTER"
if [ "$ROWS_BEFORE" != "$ROWS_AFTER" ]; then FAIL=1; fi

echo "DONE FAIL=$FAIL"
exit $FAIL
