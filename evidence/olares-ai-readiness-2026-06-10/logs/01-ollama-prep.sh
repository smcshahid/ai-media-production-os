#!/usr/bin/env bash
# Olares shared Ollama readiness — read-only verify + pull llama3.1:13b
set -uo pipefail
KC="sudo -n k3s kubectl"
NS=ollamaserver-shared
DEP=ollama
LOG=/tmp/aimpos-ollama-prep.log

exec > >(tee -a "$LOG") 2>&1
echo "=== Ollama readiness $(date -Is 2>/dev/null || date) ==="

echo "--- endpoint from mediapipeline pod ---"
MPP_NS=mediapipeline-mwayolares
POD=$($KC get pods -n "$MPP_NS" -l app=media-pipeline -o jsonpath='{.items[0].metadata.name}')
$KC exec -n "$MPP_NS" "$POD" -c media-pipeline -- curl -fsS -m 15 -o /dev/null -w 'ollama /api/tags HTTP %{http_code}\n' http://ollama.ollamaserver-shared:11434/api/tags

echo "--- ollama list (before pull) ---"
$KC exec -n "$NS" "deploy/$DEP" -- ollama list

echo "--- check llama3.1:13b ---"
if $KC exec -n "$NS" "deploy/$DEP" -- ollama list 2>/dev/null | grep -qi 'llama3.1:13b'; then
  echo "llama3.1:13b already present — skip pull"
else
  echo "--- ollama pull llama3.1:13b (this may take several minutes) ---"
  $KC exec -n "$NS" "deploy/$DEP" -- ollama pull llama3.1:13b
fi

echo "--- ollama list (after pull) ---"
$KC exec -n "$NS" "deploy/$DEP" -- ollama list

echo "--- verify via /api/tags from pod ---"
$KC exec -n "$MPP_NS" "$POD" -c media-pipeline -- curl -fsS -m 15 http://ollama.ollamaserver-shared:11434/api/tags \
  | python3 -c "import sys,json; m=[x.get('name','') for x in json.load(sys.stdin).get('models',[])]; print('models:', ', '.join(m)); print('llama3.1:13b:', 'YES' if any('llama3.1' in n.lower() and '13b' in n.lower() for n in m) else 'NO')"

echo "=== Ollama prep done ==="
