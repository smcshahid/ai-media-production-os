#!/usr/bin/env bash
# Final readiness verification snapshot
set -uo pipefail
KC="sudo -n k3s kubectl"
MPP_NS=mediapipeline-mwayolares
POD=$($KC get pods -n "$MPP_NS" -l app=media-pipeline -o jsonpath='{.items[0].metadata.name}')

echo "=== FINAL Ollama ==="
$KC exec -n ollamaserver-shared deploy/ollama -- ollama list
$KC exec -n "$MPP_NS" "$POD" -c media-pipeline -- curl -fsS -m 15 http://ollama.ollamaserver-shared:11434/api/tags \
  | python3 -c "import sys,json; m=[x.get('name','') for x in json.load(sys.stdin).get('models',[])]; print('llama3.1:13b:', 'YES' if 'llama3.1:13b' in m else 'NO'); print('mistral:7b:', 'YES' if 'mistral:7b' in m else 'NO'); print('qwen3:14b:', 'YES' if 'qwen3:14b' in m else 'NO')"

echo "=== FINAL ComfyUI checkpoints ==="
$KC exec -n "$MPP_NS" "$POD" -c media-pipeline -- curl -fsS -m 20 http://comfyui.comfyuisharev2server-shared:8190/object_info/CheckpointLoaderSimple \
  | python3 -c "import sys,json; ck=json.load(sys.stdin)['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0]; print('sdxl_base_1.0:', 'YES' if any('sdxl_base_1.0' in c for c in ck) else 'NO'); print('all:', ', '.join(ck))"
$KC exec -n "$MPP_NS" "$POD" -c media-pipeline -- curl -s -m 10 -o /dev/null -w 'queue HTTP %{http_code}\n' http://comfyui.comfyuisharev2server-shared:8190/queue
