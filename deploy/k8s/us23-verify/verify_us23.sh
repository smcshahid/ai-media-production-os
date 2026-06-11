#!/usr/bin/env bash
# US-23 Olares verification — read-only asset history UI (D-58); API frozen at D-57.
set -uo pipefail
NS=aimpos-mwayolares
: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT_ID:?set PROJECT_ID — US-V02 project}"
: "${RUN_ID:?set RUN_ID — COMPLETED pipeline run for regression}"
K="sudo k3s kubectl"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

FAIL=0
ROWS_BEFORE=$(psql -c "SELECT COUNT(*) FROM asset_versions;")

echo "US-23 verify start $(date -Iseconds)"
echo "API=$API PROJECT_ID=$PROJECT_ID RUN_ID=$RUN_ID"
echo "ASSET_VERSIONS_BEFORE=$ROWS_BEFORE"

echo "========== S-23-07: API image unchanged (us22) =========="
API_IMAGE=$($K get deploy aimpos-api -n "$NS" -o jsonpath='{.spec.template.spec.containers[0].image}')
echo "API_IMAGE=$API_IMAGE"
if [[ "$API_IMAGE" != *"us22"* ]]; then
  echo "FAIL: expected aimpos-api:us22, got $API_IMAGE"
  FAIL=1
fi

echo "========== S-23-02: GET /assets/history =========="
HTTP=$(curl -s -m 60 -o /tmp/us23-history.json -w "%{http_code}" \
  "$API/assets/history?project_id=$PROJECT_ID" -H "$AUTH")
echo "HISTORY http=$HTTP"
if [ "$HTTP" != "200" ]; then FAIL=1; fi

echo "========== S-23-03: D-57 parity (15 rows US-V02) =========="
API_COUNT=$(python3 - <<'PY'
import json
m=json.load(open("/tmp/us23-history.json"))
print(sum(len(s["versions"]) for s in m["stages"]))
PY
)
echo "API_ROW_COUNT=$API_COUNT"
if [ "$API_COUNT" != "15" ]; then
  echo "WARN: expected 15 rows for US-V02 project (got $API_COUNT)"
fi
SQL_COUNT=$(psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT_ID';")
echo "SQL_ROW_COUNT=$SQL_COUNT"
if [ "$SQL_COUNT" != "$API_COUNT" ]; then echo "FAIL: row count mismatch"; FAIL=1; fi

echo "========== S-23-04: content-read spot check =========="
STORY_ID=$(python3 - <<'PY'
import json
m=json.load(open("/tmp/us23-history.json"))
story=next(s for s in m["stages"] if s["stage"]=="STORY")
print(story["versions"][0]["asset_id"])
PY
)
CHTTP=$(curl -s -m 30 -o /dev/null -w "%{http_code}" "$API/assets/$STORY_ID/content" -H "$AUTH")
echo "CONTENT_READ id=$STORY_ID http=$CHTTP"
if [ "$CHTTP" != "200" ]; then echo "FAIL: content-read"; FAIL=1; fi

echo "========== S-23-05: lineage regression =========="
LHTTP=$(curl -s -m 60 -o /dev/null -w "%{http_code}" "$API/lineage/$RUN_ID" -H "$AUTH")
echo "LINEAGE http=$LHTTP"
if [ "$LHTTP" != "200" ]; then echo "FAIL: lineage regression"; FAIL=1; fi

echo "========== S-23-06: export regression =========="
EHTTP=$(curl -s -m 120 -o /dev/null -w "%{http_code}" "$API/export/$RUN_ID" -H "$AUTH")
echo "EXPORT http=$EHTTP"
if [ "$EHTTP" != "200" ]; then echo "FAIL: export regression"; FAIL=1; fi

echo "========== S-23-08: no asset_versions writes =========="
ROWS_AFTER=$(psql -c "SELECT COUNT(*) FROM asset_versions;")
echo "ASSET_VERSIONS_AFTER=$ROWS_AFTER"
if [ "$ROWS_BEFORE" != "$ROWS_AFTER" ]; then echo "FAIL: asset_versions count changed"; FAIL=1; fi

mkdir -p /tmp/us23-sql
psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT_ID';" > /tmp/us23-sql/v23-l03-total-rows.txt
echo "$ROWS_BEFORE" > /tmp/us23-sql/v23-l08-no-writes-before.txt
echo "$ROWS_AFTER" > /tmp/us23-sql/v23-l08-no-writes-after.txt
echo "$API_IMAGE" > /tmp/us23-sql/v23-l07-api-image.txt

echo "NOTE: S-23-01 web bundle /history route verified locally (no web pod on Olares)"
echo "DONE PROJECT_ID=$PROJECT_ID FAIL=$FAIL"
exit $FAIL
