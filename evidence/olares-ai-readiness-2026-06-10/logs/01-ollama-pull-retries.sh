#!/usr/bin/env bash
set -uo pipefail
KC="sudo -n k3s kubectl"
NS=ollamaserver-shared

for tag in llama3.1:13b llama3:13b llama3.1:8b-instruct; do
  echo "=== pull $tag ==="
  $KC exec -n "$NS" deploy/ollama -- ollama pull "$tag" 2>&1 | tail -5
  echo ""
done

echo "=== ollama list ==="
$KC exec -n "$NS" deploy/ollama -- ollama list

echo "=== api tags check ==="
MPP_NS=mediapipeline-mwayolares
POD=$($KC get pods -n "$MPP_NS" -l app=media-pipeline -o jsonpath='{.items[0].metadata.name}')
$KC exec -n "$MPP_NS" "$POD" -c media-pipeline -- curl -fsS -m 15 http://ollama.ollamaserver-shared:11434/api/tags \
  | python3 -c "
import sys,json
m=[x.get('name','') for x in json.load(sys.stdin).get('models',[])]
for needle in ('llama3.1:13b','llama3:13b','llama3.1:8b'):
    print(f'{needle}:', 'YES' if needle in m else 'NO')
print('all:', ', '.join(m))
"
