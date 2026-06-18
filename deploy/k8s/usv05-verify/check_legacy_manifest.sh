#!/usr/bin/env bash
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
TOKEN=$($K get secret aimpos-api-env -n "$NS" -o jsonpath='{.data.AIMPOS_API_TOKEN}' | base64 -d)
API=$($K get svc aimpos-api -n "$NS" -o jsonpath='{.spec.clusterIP}')
AUTH="Authorization: Bearer ${TOKEN}"

for RUN in 7e8699d1-35c6-4135-9a2b-404a737ad622 e5da4992-226c-4969-b95d-e7a2c6415b30; do
  code=$(curl -s -m 60 -o "/tmp/exp-${RUN}.zip" -w "%{http_code}" "http://${API}:8000/export/${RUN}" -H "$AUTH")
  mv=$(unzip -p "/tmp/exp-${RUN}.zip" manifest.json 2>/dev/null | sed -n 's/.*"manifest_version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
  echo "run=$RUN http=$code manifest_version=${mv:-unknown}"
done
