#!/usr/bin/env bash
# Olares k3s inventory — run on Olares host via SSH (read-only).
set -uo pipefail
KC="sudo -n k3s kubectl"
OUT="${1:-/tmp/aimpos-olares-inventory}"

mkdir -p "$OUT"

section() { echo ""; echo "========== $* =========="; }

section "HOST"
hostname
uname -a
date -Is 2>/dev/null || date

section "GPU"
nvidia-smi 2>&1 || true
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu --format=csv 2>&1 || true

section "DISK"
df -h 2>&1

section "K3S PODS (AI + data)"
$KC get pods -A 2>&1 | grep -iE 'ollama|comfy|minio|postgres|aimpos|temporal|redis|mediapipeline|mpp-' || true

section "K3S SERVICES (AI + data)"
$KC get svc -A 2>&1 | grep -iE 'ollama|comfy|minio|postgres|aimpos|temporal|redis|mediapipeline|mpp-' || true

section "OLLAMA shared FQDN"
OLLAMA="http://ollama.ollamaserver-shared:11434"
curl -fsS -m 15 "${OLLAMA}/api/tags" 2>&1 | tee "$OUT/ollama-tags.json" || echo "FAIL ollama tags"
echo "--- model names ---"
python3 - <<'PY' 2>/dev/null || true
import json, pathlib
p = pathlib.Path("/tmp/aimpos-olares-inventory/ollama-tags.json")
if p.exists():
    d = json.loads(p.read_text())
    for m in d.get("models", []):
        print(m.get("name", ""))
PY

section "COMFYUI shared GPU (port 8190)"
COMFY="http://comfyui.comfyuisharev2server-shared:8190"
for path in "/" "/queue" "/system_stats"; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 10 "${COMFY}${path}" 2>/dev/null || echo "000")
  echo "GET ${COMFY}${path} -> HTTP ${code}"
done
curl -fsS -m 15 "${COMFY}/object_info/CheckpointLoaderSimple" 2>/dev/null \
  | python3 -c "import sys,json; d=json.load(sys.stdin); ck=d['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0]; print('checkpoints:', ', '.join(ck))" 2>/dev/null \
  || echo "FAIL checkpoint list"

section "MPP MINIO"
curl -fsS -m 8 "http://mpp-minio.mediapipeline-mwayolares:9000/minio/health/live" && echo " OK" || echo " FAIL mpp-minio health"

section "MPP POSTGRES pod"
$KC get pods -n mediapipeline-mwayolares -l app=mpp-postgres 2>&1 || $KC get pods -n mediapipeline-mwayolares 2>&1 | grep postgres || true

section "HOST PORT LISTENERS (5432 9000 11434 8188 8190 7233 8000)"
(ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null) | grep -E ':5432|:9000|:11434|:8188|:8190|:7233|:8000' || echo "(no matching listeners on host)"

section "OLLAMA deployment"
$KC get deploy -n ollamaserver-shared -o wide 2>&1 || true
$KC get pods -n ollamaserver-shared -o wide 2>&1 || true

section "COMFYUI deployments"
$KC get deploy -n comfyuisharev2server-shared -o wide 2>&1 || true
$KC get deploy -n comfyuisharev2-mwayolares -o wide 2>&1 || true

section "AIMPOS llama3.1:13b check"
python3 - <<'PY' 2>/dev/null || true
import json, pathlib
p = pathlib.Path("/tmp/aimpos-olares-inventory/ollama-tags.json")
if not p.exists():
    print("UNKNOWN — no tags file")
else:
    names = [m.get("name","").lower() for m in json.loads(p.read_text()).get("models",[])]
    hits = [n for n in names if "llama3.1" in n and "13b" in n]
    print("llama3.1:13b present:", "YES" if hits else "NO")
    print("all models:", ", ".join(names) if names else "(none)")
PY

section "AIMPOS SDXL checkpoint check"
python3 - <<'PY' 2>/dev/null || true
import urllib.request, json
url = "http://comfyui.comfyuisharev2server-shared:8190/object_info/CheckpointLoaderSimple"
try:
    with urllib.request.urlopen(url, timeout=15) as r:
        d = json.loads(r.read())
    ck = d["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
    sdxl = [c for c in ck if "sdxl" in c.lower()]
    print("sdxl checkpoints:", ", ".join(sdxl) if sdxl else "NONE")
    print("all checkpoints:", ", ".join(ck))
except Exception as e:
    print("FAIL:", e)
PY

echo ""
echo "Inventory written under $OUT"
