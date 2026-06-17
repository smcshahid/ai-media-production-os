#!/usr/bin/env bash
# US-V04 Olares verification — Flux storyboard + WAN i2v quality re-acceptance (D-62/D-61).
set -uo pipefail
NS=aimpos-mwayolares
: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT_ID:?set PROJECT_ID}"
: "${RUN_ID:?set RUN_ID — COMPLETED pipeline run}"
K="sudo k3s kubectl"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
WORKER_IMAGE=$($K get deploy aimpos-worker -n "$NS" -o jsonpath='{.spec.template.spec.containers[0].image}')

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

FAIL=0

echo "US-V04 verify start $(date -Iseconds)"
echo "API=$API PROJECT_ID=$PROJECT_ID RUN_ID=$RUN_ID"
echo "WORKER_IMAGE=$WORKER_IMAGE"

echo "========== V-04-01: worker quality env =========="
WORKER_ENV=$($K get deploy aimpos-worker -n "$NS" -o json | python3 - <<'PY'
import json,sys
d=json.load(sys.stdin)
env={e["name"]: e.get("value","") for e in d["spec"]["template"]["spec"]["containers"][0].get("env",[])}
print("COMFYUI_WORKFLOW="+env.get("COMFYUI_WORKFLOW","MISSING"))
print("VIDEO_I2V_ENABLED="+env.get("VIDEO_I2V_ENABLED","MISSING"))
print("COMFYUI_HOST="+env.get("COMFYUI_HOST","MISSING"))
PY
)
echo "$WORKER_ENV"
echo "$WORKER_ENV" | grep -q 'COMFYUI_WORKFLOW=flux_storyboard.json' || { echo "FAIL: expected flux_storyboard.json"; FAIL=1; }
echo "$WORKER_ENV" | grep -q 'VIDEO_I2V_ENABLED=true' || { echo "FAIL: expected VIDEO_I2V_ENABLED=true"; FAIL=1; }

echo "========== V-04-02: pipeline COMPLETED =========="
STATUS=$(curl -s -m 15 "$API/pipeline/status?project_id=$PROJECT_ID" -H "$AUTH")
echo "$STATUS"
echo "$STATUS" | grep -q '"status":"COMPLETED"' || { echo "FAIL: pipeline not COMPLETED"; FAIL=1; }

echo "========== V-04-03: STORYBOARD batch (4 frames) =========="
SB_VER=$(psql -c "SELECT COALESCE(MAX(version),0) FROM asset_versions WHERE project_id='$PROJECT_ID' AND stage='STORYBOARD';")
SB_COUNT=$(psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT_ID' AND stage='STORYBOARD' AND version=$SB_VER;")
echo "STORYBOARD_VERSION=$SB_VER FRAME_COUNT=$SB_COUNT"
if [ "$SB_COUNT" != "4" ]; then echo "FAIL: expected 4 storyboard frames"; FAIL=1; fi

echo "========== V-04-04: Flux workflow metadata =========="
FLUX_META=$(psql -c "SELECT COUNT(*) FROM asset_versions WHERE project_id='$PROJECT_ID' AND stage='STORYBOARD' AND version=$SB_VER AND metadata_json->>'workflow' LIKE '%flux%';")
echo "FLUX_FRAME_HINTS=$FLUX_META"
if [ "$FLUX_META" -lt "1" ]; then echo "WARN: no flux workflow metadata (worker may use legacy workflow name)"; fi

echo "========== V-04-05: VIDEO asset + i2v source =========="
VIDEO_META=$(psql -c "SELECT metadata_json->>'source' FROM asset_versions WHERE project_id='$PROJECT_ID' AND stage='VIDEO' ORDER BY version DESC LIMIT 1;")
echo "VIDEO_SOURCE=$VIDEO_META"
if [ "$VIDEO_META" = "comfyui_i2v" ]; then
  echo "I2V_PATH=PASS"
elif [ "$VIDEO_META" = "slideshow" ]; then
  FALLBACK=$(psql -c "SELECT metadata_json->>'fallback_reason' FROM asset_versions WHERE project_id='$PROJECT_ID' AND stage='VIDEO' ORDER BY version DESC LIMIT 1;")
  echo "I2V_FALLBACK reason=$FALLBACK"
  echo "WARN: WAN i2v fell back to slideshow — document fallback_reason"
else
  echo "FAIL: unknown VIDEO source"; FAIL=1
fi

echo "========== V-04-06: migration 0003 indexes =========="
IDX=$(psql -c "SELECT COUNT(*) FROM pg_indexes WHERE tablename='asset_versions' AND indexname LIKE 'uq_%';")
echo "STORYBOARD_INDEX_COUNT=$IDX"
if [ "$IDX" -lt "2" ]; then echo "FAIL: expected partial unique indexes"; FAIL=1; fi

echo "========== V-04-07: audit regression =========="
AHTTP=$(curl -s -m 30 -o /dev/null -w "%{http_code}" "$API/audit?project_id=$PROJECT_ID" -H "$AUTH")
echo "AUDIT http=$AHTTP"
if [ "$AHTTP" != "200" ]; then FAIL=1; fi

mkdir -p /tmp/usv04-sql
psql -c "SELECT version_num FROM alembic_version;" > /tmp/usv04-sql/v04-alembic.txt
psql -c "SELECT stage, version, metadata_json->>'workflow' FROM asset_versions WHERE project_id='$PROJECT_ID' AND stage='STORYBOARD' AND version=$SB_VER LIMIT 1;" > /tmp/usv04-sql/v04-storyboard-sample.txt
psql -c "SELECT version, metadata_json FROM asset_versions WHERE project_id='$PROJECT_ID' AND stage='VIDEO' ORDER BY version DESC LIMIT 1;" > /tmp/usv04-sql/v04-video-meta.txt

echo "DONE PROJECT_ID=$PROJECT_ID RUN_ID=$RUN_ID FAIL=$FAIL"
exit $FAIL
