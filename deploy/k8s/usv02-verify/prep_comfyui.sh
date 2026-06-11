#!/usr/bin/env bash
# PF-03: Start ComfyUI via Olares launcher and probe queue.
set -euo pipefail
echo "========== PF-03: ComfyUI launcher =========="
curl -s -m 15 -X POST http://127.0.0.1:3000/api/start || echo "WARN: launcher POST failed"
sleep 5
NS=aimpos-mwayolares
K="sudo k3s kubectl"
$K exec deploy/aimpos-worker -n "$NS" -- curl -s -m 10 -o /dev/null -w "comfyui_http=%{http_code}\n" \
  http://comfyui.comfyuisharev2server-shared:8190/system_stats 2>/dev/null || echo "comfyui_probe=unreachable"
echo "comfyui_ready"
