#!/usr/bin/env bash
# US-22 Olares verification — read-only asset history API (D-57).
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

echo "US-22 verify start $(date -Iseconds)"
echo "API=$API PROJECT_ID=$PROJECT_ID RUN_ID=$RUN_ID"
echo "ASSET_VERSIONS_BEFORE=$ROWS_BEFORE"

echo "========== S-22-01: GET /assets/history =========="
HTTP=$(curl -s -m 60 -o /tmp/us22-history.json -w "%{http_code}" \
  "$API/assets/history?project_id=$PROJECT_ID" -H "$AUTH")
echo "HISTORY http=$HTTP"
if [ "$HTTP" != "200" ]; then FAIL=1; fi

echo "========== S-22-02: stage groups =========="
python3 - <<'PY' || FAIL=1
import json
m=json.load(open("/tmp/us22-history.json"))
stages=[s["stage"] for s in m["stages"]]
for req in ("IDEA","STORY","SCRIPT","STORYBOARD","VIDEO"):
    assert req in stages, stages
print("STAGES=PASS", stages)
PY

echo "========== S-22-03: API vs SQL row parity =========="
SQL_COUNT=$(psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT_ID';")
API_COUNT=$(python3 - <<'PY'
import json
m=json.load(open("/tmp/us22-history.json"))
print(sum(len(s["versions"]) for s in m["stages"]))
PY
)
echo "SQL_ROW_COUNT=$SQL_COUNT API_ROW_COUNT=$API_COUNT"
if [ "$SQL_COUNT" != "$API_COUNT" ]; then echo "FAIL: row count mismatch"; FAIL=1; fi

echo "========== S-22-04: STORY newest first + regen history =========="
python3 - <<'PY' || FAIL=1
import json
m=json.load(open("/tmp/us22-history.json"))
story=next(s for s in m["stages"] if s["stage"]=="STORY")
assert len(story["versions"])>=2, len(story["versions"])
versions=[v["version"] for v in story["versions"]]
assert versions==sorted(versions, reverse=True), versions
print("STORY_REGEN=PASS count=", len(story["versions"]), "versions=", versions)
PY

echo "========== S-22-05: STORYBOARD frame_index =========="
python3 - <<'PY' || FAIL=1
import json
m=json.load(open("/tmp/us22-history.json"))
sb=next(s for s in m["stages"] if s["stage"]=="STORYBOARD")
for v in sb["versions"]:
    assert "frame_index" in v.get("metadata", {}), v
print("STORYBOARD_FRAMES=PASS count=", len(sb["versions"]))
PY

echo "========== S-22-06: content-read spot check =========="
STORY_ID=$(python3 - <<'PY'
import json
m=json.load(open("/tmp/us22-history.json"))
story=next(s for s in m["stages"] if s["stage"]=="STORY")
print(story["versions"][0]["asset_id"])
PY
)
CHTTP=$(curl -s -m 30 -o /dev/null -w "%{http_code}" "$API/assets/$STORY_ID/content" -H "$AUTH")
echo "CONTENT_READ id=$STORY_ID http=$CHTTP"
if [ "$CHTTP" != "200" ]; then echo "FAIL: content-read"; FAIL=1; fi

echo "========== S-22-07: lineage regression =========="
LHTTP=$(curl -s -m 60 -o /dev/null -w "%{http_code}" "$API/lineage/$RUN_ID" -H "$AUTH")
echo "LINEAGE http=$LHTTP"
if [ "$LHTTP" != "200" ]; then echo "FAIL: lineage regression"; FAIL=1; fi

echo "========== S-22-08: export regression =========="
EHTTP=$(curl -s -m 120 -o /dev/null -w "%{http_code}" "$API/export/$RUN_ID" -H "$AUTH")
echo "EXPORT http=$EHTTP"
if [ "$EHTTP" != "200" ]; then echo "FAIL: export regression"; FAIL=1; fi

echo "========== V-22-L05: no asset_versions writes =========="
ROWS_AFTER=$(psql -c "SELECT COUNT(*) FROM asset_versions;")
echo "ASSET_VERSIONS_AFTER=$ROWS_AFTER"
if [ "$ROWS_BEFORE" != "$ROWS_AFTER" ]; then echo "FAIL: asset_versions count changed"; FAIL=1; fi

mkdir -p /tmp/us22-sql
psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT_ID';" > /tmp/us22-sql/v22-l01-total-rows.txt
psql -c "SELECT stage, COUNT(*) FROM asset_versions WHERE project_id='$PROJECT_ID' GROUP BY stage ORDER BY stage;" > /tmp/us22-sql/v22-l02-by-stage.txt
psql -c "SELECT MAX(version), COUNT(*) FROM asset_versions WHERE project_id='$PROJECT_ID' AND stage='STORY';" > /tmp/us22-sql/v22-l03-story-versions.txt
psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT_ID' AND stage='STORYBOARD';" > /tmp/us22-sql/v22-l04-storyboard-frames.txt
echo "$ROWS_BEFORE" > /tmp/us22-sql/v22-l05-no-writes-before.txt
echo "$ROWS_AFTER" > /tmp/us22-sql/v22-l05-no-writes-after.txt

echo "DONE PROJECT_ID=$PROJECT_ID FAIL=$FAIL"
exit $FAIL
