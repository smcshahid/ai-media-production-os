#!/usr/bin/env bash
# US-V09 supplemental attestation — export manifest v5 from a COMPLETED platform run.
set -uo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
EVID="${EVID_DIR:-/tmp/usv09-evidence}"
RUN_ID="${1:?run_id}"

: "${TOKEN:?set TOKEN}"
: "${PGPW:?set PGPW}"
: "${PROJECT:?set PROJECT}"

mkdir -p "$EVID"
API_IP=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
API="http://${API_IP}:8000"
AUTH="Authorization: Bearer ${TOKEN}"

psql() {
  $K exec -i aimpos-postgres-0 -n "$NS" -- env PGPASSWORD="$PGPW" psql -U aimpos -d aimpos_spark -t -A "$@"
}

echo "US-V09 supplement run_id=$RUN_ID"
status=$(psql -c "SELECT status FROM pipeline_runs WHERE id='$RUN_ID';")
snap=$(psql -c "SELECT CASE WHEN character_snapshot IS NULL THEN 0 ELSE json_array_length(character_snapshot::json) END FROM pipeline_runs WHERE id='$RUN_ID';")
echo "status=$status snapshot_len=$snap"
[ "$status" = "COMPLETED" ] || exit 1
[ "${snap:-0}" -ge 1 ] || exit 1

curl -sf -m 120 "$API/export/$RUN_ID" -H "$AUTH" -o "$EVID/platform-export.zip"
unzip -p "$EVID/platform-export.zip" manifest.json > "$EVID/platform-manifest.json"
mv=$(sed -n 's/.*"manifest_version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$EVID/platform-manifest.json" | head -1)
echo "manifest_version=$mv"
[ "$mv" = "5" ] || exit 1
grep -q '"characters"' "$EVID/platform-manifest.json" || exit 1
grep -q '"episode_number"' "$EVID/platform-manifest.json" || exit 1
grep -q 'scenes/' "$EVID/platform-manifest.json" || exit 1
echo "$RUN_ID" > "$EVID/platform-run-id.txt"
echo "SUPPLEMENT PASS run_id=$RUN_ID manifest v5"
