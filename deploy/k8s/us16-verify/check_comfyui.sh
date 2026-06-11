#!/usr/bin/env bash
set -euo pipefail
NS=aimpos-mwayolares
K="sudo k3s kubectl"
HOST="${COMFYUI_HOST:-http://comfyui.comfyuisharev2server-shared:8190}"
echo "COMFYUI_HOST=$HOST"
echo "=== pods ==="
$K get pods -A 2>/dev/null | grep -i comfy || true
echo "=== curl system_stats ==="
$K run comfyui-curl --rm -i --restart=Never -n "$NS" --image=curlimages/curl:8.5.0 -- \
  curl -s -m 30 "${HOST}/system_stats" || echo "curl failed"
echo
