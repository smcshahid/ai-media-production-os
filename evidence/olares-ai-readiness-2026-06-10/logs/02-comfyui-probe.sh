#!/usr/bin/env bash
# ComfyUI readiness probe — queue, checkpoints, model paths
set -uo pipefail
KC="sudo -n k3s kubectl"
NS_SHARED=comfyuisharev2server-shared
NS_USER=comfyuisharev2-mwayolares
MPP_NS=mediapipeline-mwayolares
COMFY=http://comfyui.comfyuisharev2server-shared:8190

echo "=== ComfyUI probe $(date -Is 2>/dev/null || date) ==="

echo "--- comfyui pod processes ---"
$KC exec -n "$NS_SHARED" deploy/comfyuishare -c comfyui -- ps aux 2>&1 | grep -E 'main.py|PID' || true

echo "--- API from mediapipeline pod ---"
POD=$($KC get pods -n "$MPP_NS" -l app=media-pipeline -o jsonpath='{.items[0].metadata.name}')
for path in "/" "/queue" "/system_stats"; do
  $KC exec -n "$MPP_NS" "$POD" -c media-pipeline -- curl -s -m 15 -o /dev/null -w "GET ${COMFY}${path} -> HTTP %{http_code}\n" "${COMFY}${path}" 2>&1 || echo "FAIL ${path}"
done

echo "--- system_stats ---"
$KC exec -n "$MPP_NS" "$POD" -c media-pipeline -- curl -fsS -m 15 "${COMFY}/system_stats" 2>&1 | head -c 800 || echo "FAIL system_stats"

echo "--- checkpoints ---"
$KC exec -n "$MPP_NS" "$POD" -c media-pipeline -- curl -fsS -m 20 "${COMFY}/object_info/CheckpointLoaderSimple" 2>&1 \
  | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  ck=d['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0]
  print('all:', ', '.join(ck))
  sdxl=[c for c in ck if 'sdxl' in c.lower()]
  print('sdxl:', ', '.join(sdxl) if sdxl else 'NONE')
except Exception as e:
  print('FAIL', e)
" 2>&1 || echo "FAIL checkpoints"

echo "--- model paths on host ---"
for p in /olares/share/ai/model /olares/share/ai/model/main /olares/share/ai/output/comfyui; do
  echo "== $p =="
  ls -la "$p" 2>&1 | head -15 || true
done

echo "--- find safetensors on host (top 20) ---"
find /olares/share/ai -name '*.safetensors' 2>/dev/null | head -20 || echo "(none under /olares/share/ai)"

echo "--- inside comfyui pod model dirs ---"
$KC exec -n "$NS_SHARED" deploy/comfyuishare -c comfyui -- bash -c 'ls -la /runner-config/ 2>/dev/null; echo ---; cat /runner-config/extra_model_paths.yaml 2>/dev/null | head -40; echo ---; find / -maxdepth 5 -name "*.safetensors" 2>/dev/null | head -25' 2>&1 || true

echo "=== ComfyUI probe done ==="
