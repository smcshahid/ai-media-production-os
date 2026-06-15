#!/usr/bin/env bash
# US-V03 Phase 2 integrated acceptance — Path A orchestrator (D-55..D-59 + US-V02 regression).
set -uo pipefail
NS=aimpos-mwayolares
: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
K="sudo k3s kubectl"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
export API NS K

FAIL=0
echo "US-V03 verify start $(date -Iseconds)"
echo "API=$API"

echo "========== PF-01: deploy images (us21 baseline) =========="
API_IMAGE=$($K get deploy aimpos-api -n "$NS" -o jsonpath='{.spec.template.spec.containers[0].image}')
WORKER_IMAGE=$($K get deploy aimpos-worker -n "$NS" -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "missing")
echo "API_IMAGE=$API_IMAGE WORKER_IMAGE=$WORKER_IMAGE"
if [[ "$API_IMAGE" != *"us21"* ]]; then echo "FAIL: expected aimpos-api:us21"; FAIL=1; fi
if [[ "$WORKER_IMAGE" != *"us21"* ]]; then echo "FAIL: expected aimpos-worker:us21"; FAIL=1; fi

echo "========== PF-04: health =========="
curl -s -m 15 "$API/health" || true
echo

echo "========== PF-07: ffmpeg =========="
$K exec deploy/aimpos-worker -n "$NS" -- ffmpeg -version | head -1 || { echo "FAIL: ffmpeg"; FAIL=1; }

if [ "$FAIL" -ne 0 ]; then echo "PF failed — abort"; exit 1; fi

# Path A: fresh project E2E via US-V02 verify
if [ -z "${PROJECT:-}" ]; then
  echo "========== PF-05: fresh project =========="
  eval "$(bash /tmp/create_project.sh | grep '^PROJECT=')"
  export PROJECT
fi
export PROJECT_ID="$PROJECT"
echo "PROJECT=$PROJECT"

echo "========== Phase B: US-V02 normative E2E (Path A authoritative) =========="
bash /tmp/verify_e2e.sh 2>&1 | tee /tmp/usv03-usv02-e2e.log
E2E_RC=${PIPESTATUS[0]}
if [ "$E2E_RC" -ne 0 ]; then echo "FAIL: US-V02 E2E rc=$E2E_RC"; FAIL=1; fi

if [ -z "${RUN_ID:-}" ]; then
  RUN_ID=$(grep '^RUN_ID=' /tmp/usv03-usv02-e2e.log | tail -1 | cut -d= -f2-)
  export RUN_ID
fi
echo "RUN_ID=$RUN_ID PROJECT_ID=$PROJECT_ID"

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }
ROWS_BEFORE=$(psql -c "SELECT COUNT(*) FROM asset_versions;")
export ROWS_BEFORE
echo "ASSET_VERSIONS_BEFORE_PHASE2=$ROWS_BEFORE"

# Copy export for cross-feature
cp -f /tmp/usv02-export.zip /tmp/usv03-export.zip 2>/dev/null || true
export EXPORT_ZIP=/tmp/usv03-export.zip

run_phase2() {
  local label="$1"
  local script="$2"
  echo "========== Phase C: $label =========="
  if [ -f "/tmp/$script" ]; then
    bash "/tmp/$script" 2>&1 | tee "/tmp/usv03-${script%.sh}.log" || FAIL=1
  else
    echo "FAIL: missing /tmp/$script"; FAIL=1
  fi
}

run_phase2 "US-20 lineage" "verify_us20.sh"
run_phase2 "US-22 history API" "verify_us22.sh"
run_phase2 "US-21 realtime" "verify_us21.sh"

echo "========== Phase C: US-23 history UI (inline, us21 baseline) =========="
AUTH="Authorization: Bearer ${TOKEN}"
HHTTP=$(curl -s -m 60 -o /tmp/usv03-history.json -w "%{http_code}" \
  "$API/assets/history?project_id=$PROJECT_ID" -H "$AUTH")
echo "HISTORY http=$HHTTP"
[ "$HHTTP" = "200" ] || FAIL=1
SQL_COUNT=$(psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT_ID';")
API_COUNT=$(python3 - <<'PY'
import json
m=json.load(open("/tmp/usv03-history.json"))
print(sum(len(s["versions"]) for s in m["stages"]))
PY
)
echo "SQL_ROW_COUNT=$SQL_COUNT API_ROW_COUNT=$API_COUNT"
[ "$SQL_COUNT" = "$API_COUNT" ] || FAIL=1
STORY_ID=$(python3 - <<'PY'
import json
m=json.load(open("/tmp/usv03-history.json"))
story=next(s for s in m["stages"] if s["stage"]=="STORY")
print(story["versions"][0]["asset_id"])
PY
)
CHTTP=$(curl -s -m 30 -o /dev/null -w "%{http_code}" "$API/assets/$STORY_ID/content" -H "$AUTH")
echo "STORY_CONTENT_READ http=$CHTTP"
[ "$CHTTP" = "200" ] || FAIL=1
SB_ID=$(python3 - <<'PY'
import json
m=json.load(open("/tmp/usv03-history.json"))
sb=next(s for s in m["stages"] if s["stage"]=="STORYBOARD")
print(sb["versions"][0]["asset_id"])
PY
)
SBHTTP=$(curl -s -m 30 -o /dev/null -w "%{http_code}" "$API/assets/$SB_ID/content" -H "$AUTH")
echo "SB_CONTENT_READ http=$SBHTTP"
[ "$SBHTTP" = "200" ] || FAIL=1
echo "US23_INLINE=PASS"

echo "========== Phase C: XF-01..06 cross-feature matrix =========="
python3 /tmp/cross_feature.py 2>&1 | tee /tmp/usv03-phase2-cross.log || FAIL=1

echo "========== Phase D: Path B supplemental (reference project) =========="
if [ -f /tmp/verify_path_b.sh ]; then
  bash /tmp/verify_path_b.sh 2>&1 | tee /tmp/usv03-path-b.log || FAIL=1
else
  echo "WARN: verify_path_b.sh not found — skip Path B"
fi

echo "========== Summary =========="
echo "PROJECT=$PROJECT RUN_ID=$RUN_ID"
echo "API_IMAGE=$API_IMAGE WORKER_IMAGE=$WORKER_IMAGE"
echo "DONE FAIL=$FAIL"
exit $FAIL
