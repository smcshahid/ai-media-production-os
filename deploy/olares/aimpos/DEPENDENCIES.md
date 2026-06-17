# AIMPOS Olares — Dependency Inventory

**Release:** `v0.13.0-phase3d`  
**Namespace:** `aimpos-mwayolares`

---

## Platform dependencies

| Dependency | Version / image | Required | Notes |
|------------|-----------------|----------|-------|
| Olares OS | `>= 1.12.0` | Yes | `OlaresManifest.yaml` options |
| k3s | Olares-managed | Yes | Container runtime |
| Helm | 3.x | Yes | Web chart install |
| NVIDIA GPU | 16 GB+ VRAM (24 GB recommended) | Yes for AI | Shared Olares AI services |

---

## AIMPOS container images (pinned)

| Service | Image | Role |
|---------|-------|------|
| API | `docker.io/library/aimpos-api:v0.13.0-phase3d` | FastAPI REST + WebSocket |
| Web | `docker.io/library/aimpos-web:v0.13.0-phase3d` | React SPA + nginx API proxy |
| Worker | `docker.io/library/aimpos-worker:v0.13.0-phase3d` | Temporal worker + AI agents |
| Ingress | `docker.io/beclab/aboveos-bitnami-openresty:1.25.3-2` | Olares web entrance |

Source of truth: `deploy/release/manifest.yaml`

---

## Backend stack (pre-existing in namespace)

Deployed by M1-DV / story verify scripts; web chart assumes these are running:

| Service | Purpose |
|---------|---------|
| `aimpos-postgres-0` | PostgreSQL 16 — system of record |
| `aimpos-minio` | S3-compatible asset storage |
| `aimpos-redis` | Cache + WebSocket pub/sub |
| `temporal` | Workflow engine |
| `aimpos-api` | API deployment |
| `aimpos-worker` | Worker deployment |

---

## Shared Olares AI services (external to namespace)

| Service | Endpoint (typical) | Purpose |
|---------|-------------------|---------|
| Ollama | `ollama.ollamaserver-shared:11434` | Story + Script LLM (`qwen3:14b`) |
| ComfyUI | `comfyui.comfyuisharev2server-shared:8190` | Flux stills + WAN 2.2 i2v |

Worker env (D-63): `COMFYUI_WORKFLOW=flux_storyboard.json`, `VIDEO_I2V_ENABLED=true`

---

## ComfyUI model weights (Olares host)

Provision via `scripts/dev/provision-olares-comfyui-models.ps1`:

- Flux.1-dev (storyboard default)
- WAN 2.2 I2V weights (not T2V)
- SDXL / RealVisXL / Z-Image (optional engines)

See `docs/runbooks/comfyui-quality.md`.

---

## Database schema

| Alembic revision | Required |
|------------------|----------|
| `0003` | Yes — STORYBOARD multi-frame partial indexes |

Verify: `make verify-bootstrap`

---

## Kubernetes secrets

| Secret | Keys |
|--------|------|
| `aimpos-api-env` | `AIMPOS_API_TOKEN`, app config |
| `aimpos-postgres-auth` | `postgres-password` |

Login token for web UI: decode `AIMPOS_API_TOKEN` from `aimpos-api-env`.

---

## Network

| Port | Service | Access |
|------|---------|--------|
| 8080 | `aimposingress` | Olares launcher / desktop |
| 8000 | `aimpos-api` | Internal + nginx proxy |
| 5432 | PostgreSQL | Internal only |

---

## Verification dependencies

| Script | Purpose |
|--------|---------|
| `make verify-all` | Local consolidated verify |
| `make verify-all-olares` | Olares consolidated verify |
| `make check-drift-olares` | Image tag drift detection |
