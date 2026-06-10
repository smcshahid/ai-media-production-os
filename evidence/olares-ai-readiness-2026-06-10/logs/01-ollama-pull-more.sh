#!/usr/bin/env bash
set -uo pipefail
KC="sudo -n k3s kubectl"
NS=ollamaserver-shared

for tag in mistral:7b llama3.2:3b llama3.2:1b; do
  echo "=== pull $tag ==="
  if $KC exec -n "$NS" deploy/ollama -- ollama pull "$tag" 2>&1 | tail -8; then
    echo "SUCCESS $tag"
  else
    echo "FAIL $tag exit=$?"
  fi
  echo ""
done

echo "=== ollama list ==="
$KC exec -n "$NS" deploy/ollama -- ollama list
