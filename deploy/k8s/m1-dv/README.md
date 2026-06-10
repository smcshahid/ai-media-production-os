# M1-DV minimal Olares deployment (raw Kubernetes)

**Purpose:** Close **M1-DV** with the smallest legitimate path — AIMPOS app/data plane on Olares, shared AI services unchanged, no Marketplace packaging.

**Authority:** `docs/runbooks/m1-dv-execution.md`, D-36, D-31  
**Evidence root:** `evidence/m1-dv-YYYY-MM-DD/`

---

## Is Kubernetes packaging strictly required?

| Criterion | Requires K8s deploy? | Notes |
|-----------|----------------------|-------|
| AIMPOS app/data plane on Olares | **Yes** | Olares node has k3s only (`docker` absent on host). Compose on-node is not viable. |
| `GET /health` → 200 | **Yes** | Needs API + Postgres + Redis + MinIO reachable in-cluster. |
| AIMPOS MinIO round-trip | **Yes** | Dedicated `aimpos-minio` in this namespace. |
| ComfyUI smoke → AIMPOS MinIO | **Partial** | ComfyUI/Ollama are **shared** (no deploy). Smoke runs from operator workstation with port-forwards **or** from an in-cluster job pod. |
| Zero-egress capture | **Yes** | Observe pod/network during **this** namespace install (T-02-06 method adapted for K8s). |
| M1-DV PASS report | No | Documentation only. |

**Not required for M1-DV:** Olares Marketplace manifest, ingress polish, Helm application chart, Temporal, worker, web SPA, duplicate Ollama/ComfyUI.

**`/health` scope (current API):** `postgresql`, `redis`, `minio` only — Temporal is **not** probed (`api/app/dependencies.py`).

---

## Exact minimal artifacts (this directory)

| File | Role |
|------|------|
| `namespace.yaml` | `aimpos-mwayolares` namespace |
| `postgres-values.yaml` | Bitnami PostgreSQL (Helm) |
| `minio-values.yaml` | Bitnami MinIO standalone (Helm) |
| `redis-values.yaml` | Bitnami Redis standalone (Helm) |
| `api-secret.yaml.template` | Non-committed template for DB/MinIO/API token wiring |
| `api-deployment.yaml` | `aimpos-api` Deployment + Service `:8000` |
| `job-migrate.yaml` | One-shot Alembic `upgrade head` |
| `scripts/deploy-infra.sh` | Namespace + secrets + Helm infra + MinIO bucket bootstrap |
| `scripts/deploy-api.sh` | API secret, migrate job, API rollout |
| `scripts/capture-zero-egress.sh` | Phase D evidence helper |
| `scripts/run-m1-dv-evidence.sh` | Health capture + MinIO round-trip + smoke command hints |

**External (not in git):** Built/pushed container image `AIMPOS_API_IMAGE` (default `docker.io/<your-user>/aimpos-api:m1-dv`).

**Consumed as-is (shared Olares AI):**

- Ollama: `http://ollama.ollamaserver-shared:11434` (`qwen3:14b`)
- ComfyUI: `http://comfyui.comfyuisharev2server-shared:8190`

---

## Estimated effort

| Step | Effort |
|------|--------|
| Build + push `aimpos-api` image (Windows/CI) | 30–45 min |
| `deploy-infra.sh` on Olares | 20–40 min (Helm waits) |
| `deploy-api.sh` + migrate | 15–25 min |
| Phase A health evidence | 10 min |
| Phase B Ollama smoke (reuse prior PASS if same day/model) | 5–10 min |
| Phase C ComfyUI smoke (port-forward MinIO + tunnels) | 15–30 min |
| Phase D zero-egress | 15–20 min |
| `M1-DV-PASS-REPORT.md` | 20–30 min |
| **Total** | **~2–4 hours** (single focused session) |

Compare: Marketplace Helm chart + ingress hardening ≈ **3–5 days** — deferred post-M1-DV.

---

## Step-by-step execution plan

### 0. Pre-flight (on Olares `olares@10.0.0.34`)

```bash
sudo k3s kubectl get nodes
nvidia-smi   # shared AI already validated
mkdir -p evidence/m1-dv-$(date +%Y-%m-%d)/logs
```

Confirm shared AI (reuse prior evidence if still valid):

```bash
sudo k3s kubectl exec -n ollamaserver-shared deploy/ollama -- ollama list | grep qwen3:14b
# ComfyUI: prior verify-comfyui / test_comfyui PASS on :8190
```

### 1. Build and push API image (operator workstation with Docker)

From repo root:

```bash
docker build -f api/Dockerfile -t <DOCKER_USER>/aimpos-api:m1-dv .
docker push <DOCKER_USER>/aimpos-api:m1-dv
```

### 2. Copy deploy bundle to Olares

```bash
scp -r deploy/k8s/m1-dv olares@10.0.0.34:/tmp/aimpos-m1-dv
```

### 3. Deploy infra (Olares)

```bash
cd /tmp/aimpos-m1-dv
chmod +x scripts/*.sh
./scripts/deploy-infra.sh
```

Creates secrets, installs `aimpos-postgres`, `aimpos-minio`, `aimpos-redis`, bootstraps bucket `aimpos-hot-assets`.

### 4. Deploy API (Olares)

```bash
export AIMPOS_API_IMAGE=docker.io/<DOCKER_USER>/aimpos-api:m1-dv
./scripts/deploy-api.sh
```

Waits for migrate job, rolls `aimpos-api`, checks pod ready.

### 5. Phase A — `/health` evidence

```bash
./scripts/run-m1-dv-evidence.sh phase-a
```

Or manually:

```bash
sudo k3s kubectl port-forward -n aimpos-mwayolares svc/aimpos-api 8000:8000 &
curl -sS http://127.0.0.1:8000/health | tee evidence/m1-dv-.../logs/health.json
# Expect HTTP 200, postgresql/redis/minio status ok
```

### 6. Phase B — Ollama (reuse or re-run)

From workstation with repo + Python 3.12, tunnel Ollama if needed:

```bash
# Optional tunnel: ssh -L 11434:127.0.0.1:11434 olares@10.0.0.34 -N
python scripts/smoke/test_ollama.py --require-live \
  --host http://127.0.0.1:11434
# Or in-cluster from a debug pod on Olares — see m1-dv-execution.md
```

Copy log to `evidence/m1-dv-.../logs/test_ollama.txt`. Prior PASS (`qwen3:14b`, <30s) may be cited if same session constraints.

### 7. Phase C — ComfyUI → **AIMPOS** MinIO

`test_comfyui.py` uses Docker for `mc`. Run from **Windows workstation** (Docker Desktop) with port-forwards:

```bash
# Terminal 1 — on Olares or via ssh:
sudo k3s kubectl port-forward -n aimpos-mwayolares svc/aimpos-minio 9000:9000

# Terminal 2 — ComfyUI tunnel (if not in-cluster from pod):
ssh -L 8190:comfyui.comfyuisharev2server-shared.svc.cluster.local:8190 olares@10.0.0.34 -N

# Terminal 3 — repo root, credentials from aimpos-minio-auth secret:
python scripts/smoke/test_comfyui.py --require-live \
  --host http://127.0.0.1:8190 \
  --ollama-host http://127.0.0.1:11434 \
  --minio-host 127.0.0.1:9000
```

Set `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` in environment or `.env` from cluster secret before run.

**PASS:** exit 0; object `aimpos-hot-assets/smoke/comfyui/sdxl_storyboard.png` exists (verified by script).

### 8. Phase D — zero egress

During step 3–4 install window:

```bash
./scripts/capture-zero-egress.sh | tee evidence/m1-dv-.../logs/zero-egress.txt
```

Document: method (pod network observation / node firewall / no outbound SYN during bootstrap), timestamp, PASS/FAIL.

### 9. Close — `M1-DV-PASS-REPORT.md`

When Phases A–D PASS, write `evidence/m1-dv-YYYY-MM-DD/M1-DV-PASS-REPORT.md` per `docs/runbooks/m1-dv-execution.md` template. Attach:

- `logs/health.json`
- `logs/test_ollama.txt` (or reference prior session with same model)
- `logs/test_comfyui.txt`
- `logs/zero-egress.txt`
- `logs/minio-roundtrip.txt` (from `run-m1-dv-evidence.sh phase-minio`)

---

## Teardown (optional)

```bash
helm uninstall aimpos-postgres aimpos-minio aimpos-redis -n aimpos-mwayolares
sudo k3s kubectl delete namespace aimpos-mwayolares
```

PVCs may remain until explicitly deleted — intentional for lab reuse.

---

## Post-M1-DV (explicitly out of scope here)

- Olares Marketplace / OlaresManifest packaging
- Ingress + TLS polish
- Full 9-service compose parity chart
- Temporal + worker production hardening
- Production deployment assets
