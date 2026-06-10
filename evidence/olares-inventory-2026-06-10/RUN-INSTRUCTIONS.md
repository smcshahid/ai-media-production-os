# Olares Resource Inventory — Run Instructions

**Date folder:** `evidence/olares-inventory-2026-06-10/`  
**Purpose:** Decide whether M1-DV can use **existing Olares AI services** or must deploy **dedicated AIMPOS Ollama/ComfyUI**.

Run **on the Olares node** (SSH/console). Do not run on Windows dev host for decision-quality results.

---

## 1. Exact commands (Olares node)

```bash
# Clone or cd to repo on Olares
cd /path/to/ai-media-production-os   # adjust path

export EVIDENCE_DIR="evidence/olares-inventory-$(date +%Y-%m-%d)"
mkdir -p "$EVIDENCE_DIR/logs"

# Automated collection (preferred)
bash scripts/inventory/olares-inventory.sh
```

### Manual commands (if script unavailable)

```bash
EVIDENCE="evidence/olares-inventory-$(date +%Y-%m-%d)/logs"
mkdir -p "$EVIDENCE"

nvidia-smi | tee "$EVIDENCE/01-gpu.txt"
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu --format=csv | tee -a "$EVIDENCE/01-gpu.txt"
df -h | tee "$EVIDENCE/02-disk.txt"
docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | tee "$EVIDENCE/04-containers.txt"
ss -tlnp | tee "$EVIDENCE/05-ports.txt"

docker ps -a | grep -i postgres | tee "$EVIDENCE/06-postgresql.txt"
docker ps -a | grep -i minio | tee "$EVIDENCE/07-minio.txt"
curl -fsS http://127.0.0.1:9000/minio/health/live | tee -a "$EVIDENCE/07-minio.txt"

curl -fsS http://127.0.0.1:11434/api/tags | tee "$EVIDENCE/08-ollama.txt"
docker ps | grep -i ollama
docker exec <ollama-container> ollama list | tee -a "$EVIDENCE/08-ollama.txt"

curl -fsS http://127.0.0.1:8188/ | head -c 500 | tee "$EVIDENCE/09-comfyui.txt"
docker ps -a | grep -i comfy | tee -a "$EVIDENCE/09-comfyui.txt"

olares app list 2>/dev/null | tee "$EVIDENCE/03-olares-apps.txt" || true
kubectl get pods -A 2>/dev/null | tee -a "$EVIDENCE/03-olares-apps.txt" || true
```

---

## 2. Expected outputs

| Log file | Expected if healthy |
|----------|---------------------|
| `01-gpu.txt` | GPU name, ≥16 GB VRAM (recommended), utilization % |
| `02-disk.txt` | ≥50 GB free on Docker/volume mount |
| `03-olares-apps.txt` | List of Olares/k8s apps (VoiceDub, IPFS, etc.) |
| `04-containers.txt` | All running containers with ports |
| `05-ports.txt` | Listeners on 5432, 9000, 11434, 8188, 7233, 8000 |
| `06-postgresql.txt` | Postgres container names or 5432 listeners |
| `07-minio.txt` | MinIO container and/or `health/live` → OK |
| `08-ollama.txt` | JSON `models` array; `llama3.1:13b` listed |
| `09-comfyui.txt` | HTTP 200 from ComfyUI; optional `object_info` JSON |
| `10-gpu-consumers.txt` | Processes using GPU |
| `11-network-reachability.txt` | REACHABLE / NOT REACHABLE per endpoint |
| `12-aimpos-compose.txt` | AIMPOS compose ps if previously deployed |

---

## 3. Save outputs

All artifacts go under:

```
evidence/olares-inventory-YYYY-MM-DD/
  logs/
    00-session.log
    01-gpu.txt
    ...
  OLARES-INVENTORY-REPORT.md   ← fill after review
  RUN-INSTRUCTIONS.md
```

Copy from Olares to dev machine if needed:

```bash
tar -czf olares-inventory-YYYY-MM-DD.tgz evidence/olares-inventory-YYYY-MM-DD/
```

---

## 4. Decision question (single answer)

After filling the report:

> **Can M1-DV use existing Olares Ollama/ComfyUI for `--require-live` smokes, or must AIMPOS deploy dedicated `ollama` + `comfyui` compose services?**

- **USE EXISTING** — endpoints reachable, `llama3.1:13b` present, ComfyUI responds, GPU schedulable (D-08)
- **DEPLOY DEDICATED** — missing model, port conflict, unreachable API, or GPU not available without stopping other apps
- **UNKNOWN** — insufficient evidence; run trial `test_ollama.py --require-live --host <url>` only
