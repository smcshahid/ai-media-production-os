#!/usr/bin/env bash
# Install SDXL base checkpoint for AIMPOS M1-DV prep (sdxl_base_1.0.safetensors)
set -uo pipefail
KC="sudo -n k3s kubectl"
NS=comfyuisharev2server-shared
CKPT_NAME="sdxl_base_1.0.safetensors"
# HuggingFace stabilityai/stable-diffusion-xl-base-1.0 single-file checkpoint mirror
HF_URL="https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors"

echo "=== SDXL install $(date -Is 2>/dev/null || date) ==="

echo "--- current checkpoints via API (in pod) ---"
$KC exec -n "$NS" deploy/comfyuishare -c comfyui -- curl -fsS -m 15 http://127.0.0.1:8188/object_info/CheckpointLoaderSimple 2>&1 \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(', '.join(d['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0]))" 2>&1 || true

echo "--- target paths ---"
$KC exec -n "$NS" deploy/comfyuishare -c comfyui -- bash -c '
  set -e
  for d in /root/ComfyUI/models/checkpoints /mnt/olares-shared-model/main; do
    echo "dir $d: $(ls -la "$d" 2>/dev/null | wc -l) entries"
    ls -la "$d" 2>/dev/null | head -5 || echo "  (missing)"
  done
  if [ -f "/root/ComfyUI/models/checkpoints/'"$CKPT_NAME"'" ]; then
    echo "ALREADY_INSTALLED in checkpoints"
    exit 0
  fi
  if [ -f "/mnt/olares-shared-model/main/'"$CKPT_NAME"'" ]; then
    echo "ALREADY_INSTALLED in shared main"
    exit 0
  fi
  mkdir -p /root/ComfyUI/models/checkpoints
  echo "Downloading to /root/ComfyUI/models/checkpoints/'"$CKPT_NAME"' (~6.9GB)..."
  if command -v wget >/dev/null; then
    wget -q --show-progress -O "/root/ComfyUI/models/checkpoints/'"$CKPT_NAME"'" "'"$HF_URL"'"
  elif command -v curl >/dev/null; then
    curl -fL --progress-bar -o "/root/ComfyUI/models/checkpoints/'"$CKPT_NAME"'" "'"$HF_URL"'"
  else
    echo "FAIL: no wget/curl"
    exit 1
  fi
  ls -lh "/root/ComfyUI/models/checkpoints/'"$CKPT_NAME"'"
'

echo "--- checkpoints after install ---"
$KC exec -n "$NS" deploy/comfyuishare -c comfyui -- curl -fsS -m 20 http://127.0.0.1:8188/object_info/CheckpointLoaderSimple 2>&1 \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
ck=d['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0]
print('all:', ', '.join(ck))
sdxl=[c for c in ck if 'sdxl' in c.lower()]
print('sdxl:', ', '.join(sdxl) if sdxl else 'NONE')
print('has sdxl_base_1.0:', 'YES' if any('sdxl_base_1.0' in c for c in ck) else 'NO')
"

echo "=== SDXL install done ==="
