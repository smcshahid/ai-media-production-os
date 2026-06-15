# Start SSH port-forwards on Olares for shared AI services.
# Run on Olares host (via SSH) before desktop tunnels, or use start-olares-desktop.ps1
# which handles the full chain.
$ErrorActionPreference = "Stop"
$OlaresHost = if ($env:OLARES_HOST) { $env:OLARES_HOST } else { "olares@10.0.0.34" }

Write-Host "Starting Olares in-cluster port-forwards for shared Ollama + ComfyUI..."
ssh $OlaresHost @'
set -e
pkill -f "kubectl port-forward.*ollamaserver-shared.*ollama" 2>/dev/null || true
pkill -f "kubectl port-forward.*comfyuisharev2server-shared.*comfyui" 2>/dev/null || true
nohup sudo -n k3s kubectl port-forward -n ollamaserver-shared svc/ollama 11434:11434 --address 127.0.0.1 >/tmp/pf-ollama.log 2>&1 &
nohup sudo -n k3s kubectl port-forward -n comfyuisharev2server-shared svc/comfyui 8190:8190 --address 127.0.0.1 >/tmp/pf-comfyui.log 2>&1 &
sleep 2
curl -fsS -m 5 http://127.0.0.1:11434/api/tags >/dev/null && echo "Ollama forward OK" || echo "Ollama forward PENDING"
curl -fsS -m 5 http://127.0.0.1:8190/ >/dev/null && echo "ComfyUI forward OK" || echo "ComfyUI forward PENDING"
'@

Write-Host "Done. Olares localhost:11434 and :8190 now proxy shared AI."
