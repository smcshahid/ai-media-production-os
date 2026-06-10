# Olares Resource Inventory Report

**Date:** 2026-06-10  
**Host:** `olares` @ `10.0.0.34` (SSH `olares@10.0.0.34`)  
**Operator:** Cursor agent (live collection via `olares-one` diagnostics + k3s probes)  
**Evidence:** `evidence/olares-inventory-2026-06-10/logs/`  
**Config source of truth:** `olares-one/configs/services/mwayolares-endpoints.yaml` (verified 2026-06-06–09)

---

## 1. GPU

| Field | Value |
|-------|-------|
| GPU model | NVIDIA GeForce RTX 5090 Laptop GPU |
| VRAM total | 24,463 MiB (~24 GB) |
| VRAM free | 23,646 MiB |
| GPU utilization % | 0 % |
| **Classification** | **Reusable** |

**Active GPU consumers:** `speaches` TTS process ~312 MiB (`10-gpu-consumers` / `nvidia-smi` in `00-k3s-inventory.txt`). Plenty of headroom for `llama3.1:13b` + ComfyUI SDXL (sequenced per D-08).

---

## 2. Disk

| Mount | Total | Used | Avail | % |
|-------|-------|------|-------|---|
| `/` (root) | 98G | 12G | 86G | 13% |
| `/var` (data) | 1.8T | 536G | 1.2T | 31% |

**Classification:** **Reusable**

---

## 3. Olares applications (k3s — not Docker Compose)

| App / namespace | Status | Notes |
|-----------------|--------|-------|
| `ollamaserver-shared` / `ollama` | Running | Shared Ollama `docker.io/ollama/ollama:0.30.6` |
| `comfyuisharev2server-shared` / `comfyuishare` | Running | GPU API port **8190** (not AIMPOS default 8188) |
| `comfyuisharev2-mwayolares` / `comfyuisharev2` | Running | Web entrance / launcher |
| `mediapipeline-mwayolares` | Running | MPP app + **mpp-postgres** + **mpp-minio** |
| `ollamav2-mwayolares` | Running | User entrance (not used for headless API) |

**Source:** `00-k3s-inventory.txt`, `03-mpp-env-verify.txt`

**AIMPOS:** No `aimpos-*` pods or services on cluster. App/data plane must be deployed for M1-DV.

---

## 4. Running containers

Olares AI services run under **k3s**, not host Docker. Relevant workloads:

| Name | Image | Status | Ports (ClusterIP) |
|------|-------|--------|-------------------|
| `ollama-7649f9bf54-sjss8` | `ollama/ollama:0.30.6` | Running | 11434 |
| `comfyuishare-d467cb9f8-vs87p` | `beclab/comfyui:v0.21.0-…` | Running | **8190**, 8080, 3000 |
| `mpp-postgres-0` | (MPP chart) | Running | 5432 |
| `mpp-minio-67c4d6cf76-c6vgq` | (MPP chart) | Running | 9000 |

**Source:** `00-k3s-inventory.txt`

---

## 5. Open ports (relevant)

| Port | Process / container | Service guess |
|------|---------------------|---------------|
| 5432 | `mpp-postgres` (in-cluster only) | MPP PostgreSQL — **not** on host |
| 9000 | `mpp-minio` (in-cluster only) | MPP MinIO — **not** on host |
| 11434 | `ollama` pod (in-cluster only) | Shared Ollama — **not** on host |
| 8188 | — | **Not exposed** on Olares |
| **8190** | `comfyui` shared pod | **Olares ComfyUI GPU API** |
| 7233 | — | Temporal **not present** |
| 8000 | various app pods | MPP API, not AIMPOS |

**Note:** Cluster DNS (`*.namespace`) resolves **inside pods only**, not from the Olares SSH shell. Probes must run from a pod (see `probe-incluster.sh`).

**Source:** `00-k3s-inventory.txt`, `08-ollama-incluster.txt`

---

## 6. Service inventory

### PostgreSQL

| Instance | Endpoint | AIMPOS schema? | Classification |
|----------|----------|----------------|----------------|
| `mpp-postgres` | `mpp-postgres.mediapipeline-mwayolares:5432` / DB `media-platform` | No — MPP-owned | **Not reusable** |
| (none) | AIMPOS `aimpos-spark` DB | Required | **Deploy dedicated** |

### MinIO

| Instance | Endpoint | Bucket known? | Classification |
|----------|----------|---------------|----------------|
| `mpp-minio` | `http://mpp-minio:9000` (in MPP ns) | `mpp-media-cold`, `mpp-catalog` | **Not reusable** for AIMPOS hot assets |
| (none) | `aimpos-hot-assets` | Required per compose | **Deploy dedicated** |

In-cluster health: `mpp-minio` **OK** from mediapipeline pod (`08-ollama-incluster.txt`).

### Ollama

| Endpoint | Reachable? | Models installed | `llama3.1:13b` present? | Classification |
|----------|------------|------------------|-------------------------|----------------|
| `http://ollama.ollamaserver-shared:11434` | **Yes** (in-cluster HTTP 200) | `llama3.1:8b`, `qwen3:8b`, `qwen3:14b`, `maternion/hy-mt2:1.8b`, `nomic-embed-text` | **No** | **Possibly reusable** — pull `llama3.1:13b` before M1-DV |

**Source:** `08-ollama-list.txt`, `08-ollama-incluster.txt`

### ComfyUI

| Endpoint | Reachable? | SDXL checkpoint hint | Classification |
|----------|------------|----------------------|----------------|
| `http://comfyui.comfyuisharev2server-shared:8190` | Pod running; **`/queue` HTTP 503** | **None** — launcher not started; config default `v1-5-pruned-emaonly.safetensors` | **Possibly reusable** after operator prep |

`verify-comfyui.sh`: deployments ready; API probe **FAIL** (503, no checkpoints). Output dir has 18 historical PNGs — service has worked when launcher was started.

**AIMPOS mismatch:** smoke defaults to port **8188** and checkpoint **`sdxl_base_1.0.safetensors`** (D-03). Olares uses port **8190** and `beclab/comfyui` image, not `yanwk/comfyui-boot:cu124-sdxl-20240919`.

**Source:** `09-comfyui-verify.txt`, `08-ollama-incluster.txt`, `mwayolares-endpoints.yaml`

---

## 7. Network reachability (AIMPOS perspective)

| Target | From Olares SSH host | From pod (mediapipeline) |
|--------|----------------------|---------------------------|
| Ollama `/api/tags` | NOT REACHABLE (DNS) | **REACHABLE** HTTP 200 |
| ComfyUI `/queue` | NOT REACHABLE (DNS) | **HTTP 503** (not started) |
| MinIO `/minio/health/live` | NOT REACHABLE (DNS) | **REACHABLE** (MPP minio) |

**M1-DV implication:** AIMPOS API/worker pods on Olares must use **in-cluster FQDNs**, not `127.0.0.1:8188` / `:11434`.

**Source:** `00-k3s-inventory.txt`, `08-ollama-incluster.txt`, `probe-incluster.sh`

---

## 8. Classification summary

| Service | Classification | Rationale |
|---------|----------------|-----------|
| Ollama | **Possibly reusable → Reusable after pull** | Shared service healthy in-cluster; missing pinned model only |
| ComfyUI | **Possibly reusable** | GPU pod up; needs Launcher START + SDXL (or workflow retarget) + port **8190** |
| MinIO | **Not reusable** | MPP buckets/schema; deploy AIMPOS MinIO |
| PostgreSQL | **Not reusable** | MPP `media-platform` DB; deploy AIMPOS Postgres |
| Redis | **Not reusable** | No AIMPOS instance; deploy with compose |
| Temporal | **Not reusable** | Not on cluster; deploy with compose |
| GPU capacity | **Reusable** | RTX 5090 24 GB, ~23.6 GB free |

---

## 9. Decision (one answer only)

**M1-DV AI services:**

- [x] **USE EXISTING** Olares Ollama + ComfyUI for smoke validation  
- [ ] **DEPLOY DEDICATED** AIMPOS `ollama` + `comfyui` compose services  
- [ ] **UNKNOWN** — trial smoke required: `test_ollama.py --require-live --host <url>`

**Rationale:** Olares already runs shared GPU workloads used by Media Pipeline and other apps. Deploying duplicate Ollama/ComfyUI would contend for the same GPU without benefit. **App/data plane** (Postgres, MinIO, Redis, Temporal, API, worker) remains **AIMPOS-dedicated**.

**Conditions / blockers (must complete before M1-DV session):**

1. **Ollama:** `ollama pull llama3.1:13b` on shared instance (VRAM sufficient per D-02; 24 GB available).
2. **ComfyUI:** In Olares UI — press Launcher **START**; install **SDXL** checkpoint package (or confirm `sdxl_base_1.0.safetensors` in `/olares/share/ai/model`). Re-run `olares-one/scripts/diagnostics/verify-comfyui.sh` until `/queue` → HTTP 200 and checkpoints listed.
3. **Smoke URLs:** From AIMPOS pods, not host:
   - `OLLAMA_HOST=http://ollama.ollamaserver-shared:11434`
   - `COMFY_HOST=http://comfyui.comfyuisharev2server-shared:8190`
   - Run `test_ollama.py` / `test_comfyui.py` with `--host` overrides; ComfyUI workflow may need checkpoint name adjustment if not `sdxl_base_1.0.safetensors`.
4. **Fallback:** If ComfyUI cannot satisfy D-03 SDXL smoke after prep, **DEPLOY DEDICATED** `comfyui` only (keep shared Ollama).

**Signed:** Shahid / agent inventory · 2026-06-10
