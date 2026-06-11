#!/usr/bin/env bash
# US-19 Olares verification — export bundle for COMPLETED run (D-52..D-54).
set -uo pipefail
NS=aimpos-mwayolares
: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${RUN_ID:?set RUN_ID — COMPLETED pipeline run}"
K="sudo k3s kubectl"

API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"

psql() { $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"; }

FAIL=0
PROJECT=$(psql -c "SELECT project_id::text FROM pipeline_runs WHERE id='$RUN_ID';")
STATUS=$(psql -c "SELECT status FROM pipeline_runs WHERE id='$RUN_ID';")

echo "US-19 verify start $(date -Iseconds)"
echo "API=$API RUN_ID=$RUN_ID PROJECT=$PROJECT STATUS=$STATUS"

if [ "$STATUS" != "COMPLETED" ]; then echo "FAIL: RUN_ID not COMPLETED"; exit 1; fi

echo "========== S-19-01: GET /export =========="
HTTP=$(curl -s -m 120 -o /tmp/us19-export.zip -w "%{http_code}" "$API/export/$RUN_ID" -H "$AUTH")
BYTES=$(wc -c < /tmp/us19-export.zip 2>/dev/null || echo 0)
echo "EXPORT http=$HTTP bytes=$BYTES"
if [ "$HTTP" != "200" ]; then FAIL=1; fi
head -c 2 /tmp/us19-export.zip | od -An -tx1 | grep -q "50 4b" && echo "ZIP_MAGIC=PASS" || { echo "FAIL: no PK"; FAIL=1; }

echo "========== S-19-02: unzip + count =========="
rm -rf /tmp/us19-export
mkdir -p /tmp/us19-export
unzip -q -o /tmp/us19-export.zip -d /tmp/us19-export
COUNT=$(find /tmp/us19-export -type f | wc -l)
echo "FILE_COUNT=$COUNT"
if [ "$COUNT" != "9" ]; then echo "FAIL: expected 9 files"; FAIL=1; fi

echo "========== S-19-03: manifest fields =========="
python3 - <<'PY' || FAIL=1
import json, sys
m=json.load(open("/tmp/us19-export/manifest.json"))
for k in ("manifest_version","pipeline_run_id","project_id","exported_at","files"):
    assert k in m, k
assert m["manifest_version"]=="1"
assert len(m["files"])==8
print("MANIFEST=PASS")
PY

echo "========== S-19-04: hash verify =========="
python3 - <<'PY' || FAIL=1
import hashlib, json, pathlib, sys
m=json.load(open("/tmp/us19-export/manifest.json"))
root=pathlib.Path("/tmp/us19-export")
for f in m["files"]:
    data=(root/f["path"]).read_bytes()
    h=hashlib.sha256(data).hexdigest()
    assert h==f["content_hash"], f["path"]
print("HASH_VERIFY=PASS")
PY

echo "========== S-19-05: audit BUNDLE_EXPORTED =========="
AUDIT=$(psql -c "SELECT COUNT(*) FROM audit_events WHERE pipeline_run_id='$RUN_ID' AND event_type='BUNDLE_EXPORTED';")
echo "BUNDLE_EXPORTED_COUNT=$AUDIT"
if [ "$AUDIT" -lt "1" ]; then echo "FAIL: no BUNDLE_EXPORTED"; FAIL=1; fi

echo "========== S-19-06: negative non-COMPLETED (409) =========="
ACTIVE=$(psql -c "SELECT id::text FROM pipeline_runs WHERE status='AWAITING_APPROVAL' ORDER BY created_at DESC LIMIT 1;")
if [ -n "$ACTIVE" ]; then
  NHTTP=$(curl -s -m 30 -o /dev/null -w "%{http_code}" "$API/export/$ACTIVE" -H "$AUTH")
  echo "NEGATIVE_RUN=$ACTIVE http=$NHTTP"
  if [ "$NHTTP" != "409" ]; then echo "FAIL: expected 409 for non-COMPLETED"; FAIL=1; fi
else
  echo "SKIP negative (no AWAITING_APPROVAL run in cluster)"
fi

echo "========== V-19 SQL =========="
psql -c "SELECT status FROM pipeline_runs WHERE id='$RUN_ID';"
psql -c "SELECT event_type, payload->>'manifest_hash' AS mh FROM audit_events WHERE pipeline_run_id='$RUN_ID' AND event_type='BUNDLE_EXPORTED' ORDER BY created_at DESC LIMIT 1;"

echo "DONE RUN_ID=$RUN_ID PROJECT=$PROJECT FAIL=$FAIL"
exit $FAIL
