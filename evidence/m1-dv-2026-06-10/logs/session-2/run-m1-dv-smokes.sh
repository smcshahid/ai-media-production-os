#!/usr/bin/env bash
# M1-DV Phase B/C smokes inside mediapipeline pod (Olares hybrid)
set -uo pipefail
KC="sudo -n k3s kubectl"
NS=mediapipeline-mwayolares
POD=$($KC get pods -n "$NS" -l app=media-pipeline -o jsonpath='{.items[0].metadata.name}')
OLLAMA=http://ollama.ollamaserver-shared:11434
COMFY=http://comfyui.comfyuisharev2server-shared:8190
MODEL=qwen3:14b

echo "=== M1-DV smoke pod=$POD ==="

echo "--- test_ollama equivalent ---"
$KC exec -n "$NS" "$POD" -c media-pipeline -- python3 - <<PY
import json, time, urllib.request
host = "$OLLAMA"
model = "$MODEL"
tags = json.loads(urllib.request.urlopen(host+"/api/tags", timeout=15).read())
names = {m.get("name","") for m in tags.get("models",[])}
if model not in names:
    raise SystemExit(f"FAIL model {model} not in {names}")
started = time.monotonic()
req = urllib.request.Request(host+"/api/generate", data=json.dumps({
    "model": model, "prompt": "Reply with exactly: OK", "stream": False,
    "options": {"num_predict": 8, "temperature": 0}
}).encode(), headers={"Content-Type":"application/json"}, method="POST")
resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
elapsed = time.monotonic()-started
text = str(resp.get("response","")).strip()
if not text:
    raise SystemExit("FAIL empty response")
if elapsed >= 30:
    raise SystemExit(f"FAIL slow {elapsed:.1f}s")
print(f"PASS ollama model={model} elapsed={elapsed:.1f}s response={text[:40]!r}")
PY

echo "--- comfyui queue + checkpoint ---"
$KC exec -n "$NS" "$POD" -c media-pipeline -- curl -s -m 10 -o /dev/null -w 'queue HTTP %{http_code}\n' "$COMFY/queue"
$KC exec -n "$NS" "$POD" -c media-pipeline -- curl -fsS -m 15 "$COMFY/object_info/CheckpointLoaderSimple" \
  | python3 -c "import sys,json; ck=json.load(sys.stdin)['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0]; print('checkpoints', ck); assert any('sdxl_base_1.0' in c for c in ck), 'no sdxl'"

echo "=== done ==="
