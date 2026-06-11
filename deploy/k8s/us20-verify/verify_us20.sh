#!/usr/bin/env bash
# US-20 Olares verification — read-only lineage API (D-55/D-56, C-01).
set -uo pipefail
NS=aimpos-mwayolares
: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${RUN_ID:?set RUN_ID — COMPLETED pipeline run (US-V02)}"
K="sudo k3s kubectl"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

FAIL=0
PROJECT=$(psql -c "SELECT project_id::text FROM pipeline_runs WHERE id='$RUN_ID';")
STATUS=$(psql -c "SELECT status FROM pipeline_runs WHERE id='$RUN_ID';")
EDGE_TOTAL_BEFORE=$(psql -c "SELECT COUNT(*) FROM lineage_edges;")

echo "US-20 verify start $(date -Iseconds)"
echo "API=$API RUN_ID=$RUN_ID PROJECT=$PROJECT STATUS=$STATUS"
echo "LINEAGE_EDGES_BEFORE=$EDGE_TOTAL_BEFORE"

if [ "$STATUS" != "COMPLETED" ]; then echo "FAIL: RUN_ID not COMPLETED"; exit 1; fi

echo "========== S-20-01: GET /lineage =========="
HTTP=$(curl -s -m 60 -o /tmp/us20-lineage.json -w "%{http_code}" "$API/lineage/$RUN_ID" -H "$AUTH")
echo "LINEAGE http=$HTTP"
if [ "$HTTP" != "200" ]; then FAIL=1; fi

echo "========== S-20-02: display chain stages =========="
python3 - <<'PY' || FAIL=1
import json, sys
m=json.load(open("/tmp/us20-lineage.json"))
stages=[n["stage"] for n in m["nodes"]]
assert "IDEA" in stages and stages[0]=="IDEA", stages
assert "STORY" in stages and "SCRIPT" in stages
assert stages.count("STORYBOARD")>=4
assert "VIDEO" in stages
print("DISPLAY_CHAIN=PASS stages=", stages)
PY

echo "========== S-20-03: API vs SQL edge parity =========="
SQL_COUNT=$(psql -c "
SELECT COUNT(*)
FROM lineage_edges le
JOIN asset_versions p ON le.parent_id = p.id
JOIN asset_versions c ON le.child_id = c.id
WHERE p.project_id='$PROJECT'
  AND c.project_id='$PROJECT'
  AND (p.pipeline_run_id='$RUN_ID' OR c.pipeline_run_id='$RUN_ID');
")
API_COUNT=$(python3 - <<'PY'
import json
m=json.load(open("/tmp/us20-lineage.json"))
print(len(m["edges"]))
PY
)
echo "SQL_EDGE_COUNT=$SQL_COUNT API_EDGE_COUNT=$API_COUNT"
if [ "$SQL_COUNT" != "$API_COUNT" ]; then echo "FAIL: edge count mismatch"; FAIL=1; fi

echo "========== S-20-04: synthetic IDEA =========="
python3 - <<'PY' || FAIL=1
import json
m=json.load(open("/tmp/us20-lineage.json"))
idea=next(n for n in m["nodes"] if n["stage"]=="IDEA")
assert idea.get("synthetic") is True, idea
assert idea.get("parent_asset_ids")==[], idea
idea_id=idea["asset_id"]
for e in m["edges"]:
    assert idea_id not in (e["parent_asset_id"], e["child_asset_id"]), e
print("SYNTHETIC_IDEA=PASS")
PY

echo "========== S-20-05: STORYBOARD→VIDEO edges =========="
VIDEO_ID=$(python3 - <<'PY'
import json
m=json.load(open("/tmp/us20-lineage.json"))
v=next(n for n in m["nodes"] if n["stage"]=="VIDEO")
print(v["asset_id"])
PY
)
SB_VIDEO=$(psql -c "
SELECT COUNT(*) FROM lineage_edges le
JOIN asset_versions p ON le.parent_id = p.id
JOIN asset_versions c ON le.child_id = c.id
WHERE c.id='$VIDEO_ID' AND p.stage='STORYBOARD';
")
echo "STORYBOARD_TO_VIDEO=$SB_VIDEO (expect 4)"
if [ "$SB_VIDEO" != "4" ]; then echo "FAIL: expected 4 STORYBOARD→VIDEO edges"; FAIL=1; fi

echo "========== S-20-06: unknown run 404 =========="
MISSING="00000000-0000-0000-0000-000000000099"
NHTTP=$(curl -s -m 30 -o /dev/null -w "%{http_code}" "$API/lineage/$MISSING" -H "$AUTH")
echo "UNKNOWN http=$NHTTP"
if [ "$NHTTP" != "404" ]; then echo "FAIL: expected 404"; FAIL=1; fi

echo "========== S-20-07: export regression =========="
EHTTP=$(curl -s -m 120 -o /tmp/us20-export.zip -w "%{http_code}" "$API/export/$RUN_ID" -H "$AUTH")
echo "EXPORT http=$EHTTP"
if [ "$EHTTP" != "200" ]; then echo "FAIL: export regression"; FAIL=1; fi

echo "========== V-20-L04: no lineage writes =========="
EDGE_TOTAL_AFTER=$(psql -c "SELECT COUNT(*) FROM lineage_edges;")
echo "LINEAGE_EDGES_AFTER=$EDGE_TOTAL_AFTER"
if [ "$EDGE_TOTAL_BEFORE" != "$EDGE_TOTAL_AFTER" ]; then echo "FAIL: lineage row count changed"; FAIL=1; fi

mkdir -p /tmp/us20-sql
psql -c "SELECT COUNT(*) FROM lineage_edges le JOIN asset_versions p ON le.parent_id=p.id JOIN asset_versions c ON le.child_id=c.id WHERE p.project_id='$PROJECT' AND c.project_id='$PROJECT' AND (p.pipeline_run_id='$RUN_ID' OR c.pipeline_run_id='$RUN_ID');" > /tmp/us20-sql/v20-l01-edges.txt
psql -c "SELECT p.stage||'->'||c.stage, COUNT(*) FROM lineage_edges le JOIN asset_versions p ON le.parent_id=p.id JOIN asset_versions c ON le.child_id=c.id WHERE p.project_id='$PROJECT' AND (p.pipeline_run_id='$RUN_ID' OR c.pipeline_run_id='$RUN_ID') GROUP BY 1 ORDER BY 1;" > /tmp/us20-sql/v20-l02-stage-pairs.txt
psql -c "SELECT COUNT(*) FROM lineage_edges le JOIN asset_versions p ON le.parent_id=p.id JOIN asset_versions c ON le.child_id=c.id WHERE c.id='$VIDEO_ID' AND p.stage='STORYBOARD';" > /tmp/us20-sql/v20-l03-sb-video.txt
echo "$EDGE_TOTAL_BEFORE" > /tmp/us20-sql/v20-l04-no-writes-before.txt
echo "$EDGE_TOTAL_AFTER" > /tmp/us20-sql/v20-l04-no-writes-after.txt

echo "DONE RUN_ID=$RUN_ID PROJECT=$PROJECT FAIL=$FAIL"
exit $FAIL
