#!/usr/bin/env bash
# Olares Resource Inventory — collect facts for M1-DV AI service decision.
# Run ON the Olares node (bash). Does not modify AIMPOS or M1-DV.
#
# Usage (from repo root on Olares):
#   export EVIDENCE_DIR="evidence/olares-inventory-$(date +%Y-%m-%d)"
#   bash scripts/inventory/olares-inventory.sh
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EVIDENCE_DIR="${EVIDENCE_DIR:-$REPO_ROOT/evidence/olares-inventory-$(date +%Y-%m-%d)}"
LOGS="$EVIDENCE_DIR/logs"
mkdir -p "$LOGS"

log() { echo "[inventory] $*" | tee -a "$LOGS/00-session.log"; }

run_to() {
  local out="$1"
  shift
  log ">>> $*"
  {
    echo "=== COMMAND: $* ==="
    echo "=== TIME: $(date -Is 2>/dev/null || date) ==="
    "$@" 2>&1 || echo "(exit $?)"
    echo ""
  } >>"$out" 2>&1
}

try_to() {
  local out="$1"
  shift
  {
    echo "=== COMMAND: $* ==="
    echo "=== TIME: $(date -Is 2>/dev/null || date) ==="
    "$@" 2>&1 || echo "(exit $?)"
    echo ""
  } >>"$out" 2>&1
}

log "Evidence directory: $EVIDENCE_DIR"
log "Hostname: $(hostname 2>/dev/null || echo unknown)"
log "User: $(whoami 2>/dev/null || echo unknown)"

# --- 1. GPU ---
{
  echo "=== uname ==="
  uname -a 2>/dev/null || true
  echo ""
} >"$LOGS/01-gpu.txt"
try_to "$LOGS/01-gpu.txt" nvidia-smi
try_to "$LOGS/01-gpu.txt" nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu --format=csv
try_to "$LOGS/01-gpu.txt" nvidia-smi pmon -c 1

# --- 2. Disk ---
run_to "$LOGS/02-disk.txt" df -h
try_to "$LOGS/02-disk.txt" docker system df

# --- 3. Olares / orchestration hints ---
{
  echo "=== olares CLI ==="
  command -v olares 2>/dev/null || echo "olares CLI not in PATH"
  echo ""
} >"$LOGS/03-olares-apps.txt"
try_to "$LOGS/03-olares-apps.txt" olares version
try_to "$LOGS/03-olares-apps.txt" olares app list
try_to "$LOGS/03-olares-apps.txt" kubectl get pods -A
try_to "$LOGS/03-olares-apps.txt" kubectl get svc -A

# --- 4. Containers ---
run_to "$LOGS/04-containers.txt" docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
try_to "$LOGS/04-containers.txt" docker compose ls

# --- 5. Open ports (listening) ---
if command -v ss >/dev/null 2>&1; then
  run_to "$LOGS/05-ports.txt" ss -tlnp
elif command -v netstat >/dev/null 2>&1; then
  run_to "$LOGS/05-ports.txt" netstat -tlnp
else
  echo "ss/netstat not available" >"$LOGS/05-ports.txt"
fi

# --- 6. PostgreSQL discovery ---
{
  echo "=== docker postgres containers ==="
  docker ps -a --format "{{.Names}}\t{{.Image}}\t{{.Ports}}" 2>/dev/null | grep -i postgres || echo "(none found)"
  echo ""
  echo "=== listeners on 5432 ==="
  (ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null) | grep 5432 || echo "(none)"
} >"$LOGS/06-postgresql.txt"

# --- 7. MinIO discovery ---
{
  echo "=== docker minio containers ==="
  docker ps -a --format "{{.Names}}\t{{.Image}}\t{{.Ports}}" 2>/dev/null | grep -i minio || echo "(none found)"
  echo ""
  echo "=== listeners on 9000/9001 ==="
  (ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null) | grep -E '9000|9001' || echo "(none)"
  echo ""
  for url in "http://127.0.0.1:9000/minio/health/live" "http://localhost:9000/minio/health/live"; do
    echo "=== curl $url ==="
    curl -fsS -m 5 "$url" && echo " OK" || echo " FAIL"
  done
} >"$LOGS/07-minio.txt"

# --- 8. Ollama endpoints + models ---
{
  OLLAMA_URLS=(
    "http://127.0.0.1:11434"
    "http://localhost:11434"
    "http://ollama:11434"
  )
  for base in "${OLLAMA_URLS[@]}"; do
    echo "=== GET $base/api/tags ==="
    curl -fsS -m 10 "$base/api/tags" 2>&1 || echo " FAIL"
    echo ""
  done
  echo "=== docker ollama containers ==="
  docker ps -a --format "{{.Names}}\t{{.Image}}\t{{.Ports}}" 2>/dev/null | grep -i ollama || echo "(none found)"
  echo ""
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -qi ollama; then
    OLLAMA_CTN="$(docker ps --format '{{.Names}}' | grep -i ollama | head -1)"
    echo "=== ollama list in $OLLAMA_CTN ==="
    docker exec "$OLLAMA_CTN" ollama list 2>&1 || echo " FAIL"
  fi
} >"$LOGS/08-ollama.txt"

# --- 9. ComfyUI endpoints + checkpoints hint ---
{
  COMFY_URLS=(
    "http://127.0.0.1:8188"
    "http://localhost:8188"
  )
  for base in "${COMFY_URLS[@]}"; do
    echo "=== GET $base/ ==="
    curl -fsS -m 10 "$base/" 2>&1 | head -c 500 || echo " FAIL"
    echo ""
    echo "=== GET $base/object_info (truncated) ==="
    curl -fsS -m 15 "$base/object_info" 2>&1 | head -c 2000 || echo " FAIL"
    echo ""
  done
  echo "=== docker comfyui containers ==="
  docker ps -a --format "{{.Names}}\t{{.Image}}\t{{.Ports}}" 2>/dev/null | grep -i comfy || echo "(none found)"
} >"$LOGS/09-comfyui.txt"

# --- 10. Active GPU consumers ---
try_to "$LOGS/10-gpu-consumers.txt" nvidia-smi
try_to "$LOGS/10-gpu-consumers.txt" fuser -v /dev/nvidia0 2>/dev/null
try_to "$LOGS/10-gpu-consumers.txt" docker ps --format "{{.Names}}\t{{.Image}}" | while read -r line; do echo "$line"; done

# --- 11. Network reachability (host → services) ---
{
  echo "=== ping-less HTTP probes (AIMPOS smoke targets) ==="
  for spec in \
    "ollama:11434:/api/tags" \
    "comfyui:8188:/" \
    "minio:9000:/minio/health/live"; do
    IFS=: read -r host port path <<<"$spec"
    echo "--- http://127.0.0.1:$port$path ---"
    curl -fsS -m 8 "http://127.0.0.1:$port$path" >/dev/null && echo "REACHABLE" || echo "NOT REACHABLE"
  done
  echo ""
  echo "=== aimpos-spark docker network ==="
  docker network inspect aimpos-spark 2>&1 || echo "(network not present)"
  if docker network inspect aimpos-spark >/dev/null 2>&1; then
    echo "=== curl from aimpos-spark network ==="
    for url in "http://ollama:11434/api/tags" "http://comfyui:8188/" "http://minio:9000/minio/health/live"; do
      echo "--- $url ---"
      docker run --rm --network aimpos-spark curlimages/curl:8.5.0 -fsS -m 10 "$url" >/dev/null && echo "REACHABLE" || echo "NOT REACHABLE"
    done
  fi
} >"$LOGS/11-network-reachability.txt"

# --- 12. AIMPOS compose state (if repo present) ---
if [[ -f "$REPO_ROOT/deploy/compose/docker-compose.yml" ]]; then
  try_to "$LOGS/12-aimpos-compose.txt" docker compose -f "$REPO_ROOT/deploy/compose/docker-compose.yml" ps -a
else
  echo "compose file not found at $REPO_ROOT" >"$LOGS/12-aimpos-compose.txt"
fi

log "Inventory complete. Logs in $LOGS"
log "Fill report: $EVIDENCE_DIR/OLARES-INVENTORY-REPORT.md"
