#!/usr/bin/env bash
set -uo pipefail
KC="sudo -n k3s kubectl"
NS=mediapipeline-mwayolares
POD=$($KC get pods -n "$NS" -l app=media-pipeline -o jsonpath='{.items[0].metadata.name}')
echo "pod=$POD"

echo "=== ollama /api/tags ==="
$KC exec -n "$NS" "$POD" -c media-pipeline -- curl -fsS -m 15 http://ollama.ollamaserver-shared:11434/api/tags
echo ""

echo "=== comfyui /queue ==="
$KC exec -n "$NS" "$POD" -c media-pipeline -- curl -s -m 15 -o /dev/null -w 'HTTP %{http_code}\n' http://comfyui.comfyuisharev2server-shared:8190/queue

echo "=== comfyui checkpoints ==="
$KC exec -n "$NS" "$POD" -c media-pipeline -- curl -fsS -m 15 http://comfyui.comfyuisharev2server-shared:8190/object_info/CheckpointLoaderSimple 2>&1 \
  | python3 -c "import sys,json; d=json.load(sys.stdin); ck=d['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0]; print('checkpoints:', ', '.join(ck)); print('sdxl:', ', '.join(c for c in ck if 'sdxl' in c.lower()) or 'NONE')" 2>&1 || echo "FAIL checkpoints"

echo "=== mpp-minio health ==="
$KC exec -n "$NS" "$POD" -c media-pipeline -- curl -fsS -m 10 http://mpp-minio:9000/minio/health/live && echo OK || echo FAIL

echo "=== mpp-postgres tcp ==="
$KC exec -n "$NS" "$POD" -c media-pipeline -- python3 -c "import socket; s=socket.create_connection(('mpp-postgres',5432),5); print('postgres tcp OK'); s.close()" 2>&1 || echo FAIL postgres
