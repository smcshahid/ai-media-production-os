#!/usr/bin/env bash
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
TOKEN=$($K get secret aimpos-api-env -n "$NS" -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
API=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
PROJECT="${PROJECT:-ba0c4636-817c-423b-9771-20100e080b76}"
RUN="${RUN:-f8d89b35-f333-474c-a012-d3ab1d5864b3}"
EVID="${EVID:-/tmp/usv05-e2e-evidence}"
AUTH="Authorization: Bearer ${TOKEN}"

curl -sf -m 120 "http://${API}:8000/export/${RUN}" -H "$AUTH" -o "$EVID/path-B-export.zip"
unzip -p "$EVID/path-B-export.zip" manifest.json > "$EVID/path-B-manifest.json"
mv=$(sed -n 's/.*"manifest_version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$EVID/path-B-manifest.json" | head -1)
echo "manifest_version=$mv zip_size=$(wc -c < "$EVID/path-B-export.zip")"
[ "$mv" = "2" ] || { echo "FAIL expected manifest v2"; exit 1; }

curl -sf -m 30 "http://${API}:8000/audit?project_id=$PROJECT&pipeline_run_id=$RUN&limit=50" -H "$AUTH" > "$EVID/path-B-audit.json"
curl -sf -m 30 "http://${API}:8000/assets/history?project_id=$PROJECT&pipeline_run_id=$RUN" -H "$AUTH" > "$EVID/path-B-history.json"
curl -sf -m 30 "http://${API}:8000/lineage/$RUN" -H "$AUTH" > "$EVID/path-B-lineage.json"
curl -sf -m 30 "http://${API}:8000/pipeline/runs?project_id=$PROJECT" -H "$AUTH" > "$EVID/path-B-runs.json"
echo "PASS PATH B manual verify run=$RUN"
