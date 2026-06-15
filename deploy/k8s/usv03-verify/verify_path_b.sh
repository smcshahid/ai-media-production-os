#!/usr/bin/env bash
# US-V03 Path B — reference-project supplemental read-only regression.
set -uo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"

REF_PROJECT="${REF_PROJECT:-76aa4418-d92d-45f7-954c-a10383ea511a}"
REF_RUN="${REF_RUN:-042983f7-0f55-48c3-9d65-fce89a684625}"

export PROJECT_ID="$REF_PROJECT"
export RUN_ID="$REF_RUN"
export PROJECT="$REF_PROJECT"

FAIL=0
echo "========== Path B: reference project =========="
echo "REF_PROJECT=$REF_PROJECT REF_RUN=$REF_RUN"

for script in verify_us20.sh verify_us22.sh verify_us21.sh; do
  if [ -f "/tmp/$script" ]; then
    echo "========== Path B: $script =========="
    bash "/tmp/$script" || FAIL=1
  else
    echo "WARN: /tmp/$script not found — skip"
  fi
done

# US-23 checks inline (us21 image baseline; verify_us23.sh expects us22 tag)
echo "========== Path B: US-23 inline =========="
API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"
HHTTP=$(curl -s -m 60 -o /tmp/usv03b-history.json -w "%{http_code}" \
  "$API/assets/history?project_id=$REF_PROJECT" -H "$AUTH")
echo "HISTORY http=$HHTTP"
[ "$HHTTP" = "200" ] || FAIL=1
LHTTP=$(curl -s -m 60 -o /dev/null -w "%{http_code}" "$API/lineage/$REF_RUN" -H "$AUTH")
EHTTP=$(curl -s -m 120 -o /dev/null -w "%{http_code}" "$API/export/$REF_RUN" -H "$AUTH")
echo "LINEAGE=$LHTTP EXPORT=$EHTTP"
[ "$LHTTP" = "200" ] && [ "$EHTTP" = "200" ] || FAIL=1

echo "========== Path B: cross-feature (read-only) =========="
export API PROJECT_ID RUN_ID PGPW NS K
export EXPORT_ZIP="/tmp/usv03b-export.zip"
curl -s -m 120 -o "$EXPORT_ZIP" "$API/export/$REF_RUN" -H "$AUTH" || true
python3 /tmp/cross_feature.py || FAIL=1

echo "PATH_B FAIL=$FAIL"
exit $FAIL
