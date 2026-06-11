#!/usr/bin/env bash
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
for URL in \
  "http://comfyui.comfyuisharev2server-shared:8190/system_stats" \
  "http://comfyui.comfyuisharev2server-shared.svc.cluster.local:8190/system_stats" \
  "http://comfyuientrance.comfyuisharev2-mwayolares:8080/system_stats" \
  "http://10.233.53.251:8190/system_stats"
do
  echo "=== $URL ==="
  $K exec deploy/aimpos-worker -n "$NS" -- python -c "
import httpx
try:
    r = httpx.get('$URL', timeout=15)
    print(r.status_code, r.text[:200])
except Exception as e:
    print('ERR', e)
" 2>/dev/null || echo "exec failed"
done
