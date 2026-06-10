#!/usr/bin/env bash
set -uo pipefail
KC="sudo -n k3s kubectl"
NS=ollamaserver-shared
echo "=== pull llama2:13b ==="
$KC exec -n "$NS" deploy/ollama -- ollama pull llama2:13b 2>&1 | tail -8
echo "=== list ==="
$KC exec -n "$NS" deploy/ollama -- ollama list
