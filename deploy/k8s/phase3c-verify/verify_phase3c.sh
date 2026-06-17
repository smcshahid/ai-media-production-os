#!/usr/bin/env bash
# Phase 3C Olares verification — web entrance + audit pagination + regressions.
set -uo pipefail
NS=aimpos-mwayolares
: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT_ID:?set PROJECT_ID}"
: "${RUN_ID:?set RUN_ID}"
K="sudo k3s kubectl"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
WEB_IP=$($K get svc aimposingress -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
WEB="http://${WEB_IP}:8080"
AUTH="Authorization: Bearer ${TOKEN}"

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

FAIL=0
echo "Phase 3C Olares verify start $(date -Iseconds)"
echo "API=$API WEB=$WEB PROJECT_ID=$PROJECT_ID"

echo "========== P3C-01: web entrance =========="
WHTTP=$(curl -s -m 30 -o /tmp/p3c-web.html -w "%{http_code}" "$WEB/")
echo "WEB_ROOT http=$WHTTP"
if [ "$WHTTP" != "200" ]; then FAIL=1; fi
if ! grep -q "AIMPOS" /tmp/p3c-web.html 2>/dev/null && ! grep -qi "root" /tmp/p3c-web.html; then
  echo "WARN: web HTML may not contain expected SPA shell"
fi

echo "========== P3C-02: web API proxy health =========="
HHTTP=$(curl -s -m 30 -o /tmp/p3c-health.json -w "%{http_code}" "$WEB/health")
echo "WEB_PROXY_HEALTH http=$HHTTP"
if [ "$HHTTP" != "200" ]; then FAIL=1; fi

echo "========== P3C-03: audit pagination =========="
PHTTP=$(curl -s -m 30 -o /tmp/p3c-audit-page.json -w "%{http_code}" \
  "$API/audit?project_id=$PROJECT_ID&limit=10&offset=0" -H "$AUTH")
echo "AUDIT_PAGE http=$PHTTP"
if [ "$PHTTP" != "200" ]; then FAIL=1; fi
python3 - <<'PY' || FAIL=1
import json
m = json.load(open("/tmp/p3c-audit-page.json"))
for key in ("total", "limit", "offset", "has_more", "events"):
    assert key in m, m.keys()
assert m["limit"] == 10
print("AUDIT_PAGE total=", m["total"], "events=", len(m["events"]))
PY

echo "========== P3C-04: audit export regression =========="
EHTTP=$(curl -s -m 60 -o /tmp/p3c-export.json -w "%{http_code}" \
  "$API/audit/export?project_id=$PROJECT_ID&format=json" -H "$AUTH")
echo "AUDIT_EXPORT http=$EHTTP"
if [ "$EHTTP" != "200" ]; then FAIL=1; fi

echo "========== P3C-05: Olares Application registration =========="
APP_STATE=$($K get applications.app.bytetrade.io aimpos-mwayolares-aimpos -o jsonpath='{.status.state}' 2>/dev/null || echo missing)
INGRESS_READY=$($K get deploy aimposingress -n "$NS" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo 0)
echo "APPLICATION_STATE=$APP_STATE INGRESS_READY=$INGRESS_READY"
if [ "$APP_STATE" != "running" ]; then FAIL=1; fi
if [ "$INGRESS_READY" != "1" ]; then FAIL=1; fi

echo "========== P3C-06: phase3b regressions =========="
for path in "pipeline/runs?project_id=$PROJECT_ID" "assets/history?project_id=$PROJECT_ID"; do
  HTTP=$(curl -s -m 30 -o /dev/null -w "%{http_code}" "$API/$path" -H "$AUTH")
  echo "GET /$path http=$HTTP"
  if [ "$HTTP" != "200" ]; then FAIL=1; fi
done

echo "DONE FAIL=$FAIL"
exit $FAIL
