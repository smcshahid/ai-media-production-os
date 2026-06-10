#!/usr/bin/env bash
pkill -f 'kubectl port-forward.*ollama' 2>/dev/null || true
pkill -f 'kubectl port-forward.*comfyui' 2>/dev/null || true
nohup sudo -n k3s kubectl port-forward -n ollamaserver-shared svc/ollama 11434:11434 --address 127.0.0.1 >/tmp/pf-ollama.log 2>&1 &
nohup sudo -n k3s kubectl port-forward -n comfyuisharev2server-shared svc/comfyui 8190:8190 --address 127.0.0.1 >/tmp/pf-comfyui.log 2>&1 &
sleep 3
curl -fsS -m 5 http://127.0.0.1:11434/api/tags >/dev/null && echo ollama_pf_OK || echo ollama_pf_FAIL
curl -s -m 5 -o /dev/null -w 'comfyui %{http_code}\n' http://127.0.0.1:8190/queue
