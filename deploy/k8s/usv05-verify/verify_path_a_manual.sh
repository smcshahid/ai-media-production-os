#!/usr/bin/env bash
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
TOKEN=$($K get secret aimpos-api-env -n "$NS" -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
API=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
PROJECT="${PROJECT:-ba0c4636-817c-423b-9771-20100e080b76}"
RUN="${RUN:-99e70e94-89f0-4cf9-b5e5-719108862d1b}"
EVID="${EVID:-/tmp/usv05-e2e-evidence}"
AUTH="Authorization: Bearer ${TOKEN}"

curl -sf -m 120 "http://${API}:8000/export/${RUN}" -H "$AUTH" -o "$EVID/path-A-export.zip"
unzip -p "$EVID/path-A-export.zip" manifest.json > "$EVID/path-A-manifest.json"
mv=$(sed -n 's/.*"manifest_version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$EVID/path-A-manifest.json" | head -1)
echo "manifest_version=$mv zip_size=$(wc -c < "$EVID/path-A-export.zip")"
[ "$mv" = "2" ] || { echo "FAIL expected manifest v2"; exit 1; }

curl -sf -m 30 "http://${API}:8000/audit?project_id=$PROJECT&pipeline_run_id=$RUN&limit=50" -H "$AUTH" > "$EVID/path-A-audit.json"
curl -sf -m 30 "http://${API}:8000/assets/history?project_id=$PROJECT&pipeline_run_id=$RUN" -H "$AUTH" > "$EVID/path-A-history.json"
curl -sf -m 30 "http://${API}:8000/lineage/$RUN" -H "$AUTH" > "$EVID/path-A-lineage.json"
curl -sf -m 30 "http://${API}:8000/pipeline/runs?project_id=$PROJECT" -H "$AUTH" > "$EVID/path-A-runs.json"
echo "PASS PATH A manual verify run=$RUN"
