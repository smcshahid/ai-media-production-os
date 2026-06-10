# M1-DV execution package (frozen — amended 2026-06-10 per D-36)

**Authority:** D-31, D-36, `docs/governance/development-workflow.md`  
**Blocks until closed:** US-12, US-13, US-09, Sprint 3B  
**Evidence root:** `evidence/m1-dv-YYYY-MM-DD/`

---

## Pre-flight checklist (before session)

| # | Check | PASS criterion |
|---|--------|----------------|
| 1 | **Olares access** | SSH `olares@10.0.0.34` (or VPN); `sudo k3s kubectl get nodes` OK |
| 2 | **GPU** | `nvidia-smi` — RTX class, ≥16 GB VRAM free for inference |
| 3 | **Disk** | ≥50 GB free on `/var` or data mount |
| 4 | **Model (D-36)** | Shared Ollama lists **`qwen3:14b`** (`ollama list` in `ollamaserver-shared` pod) |
| 5 | **ComfyUI** | `verify-comfyui.sh` → `/queue` HTTP 200; **`sdxl_base_1.0.safetensors`** in checkpoint API |
| 6 | **Evidence folder** | `mkdir -p evidence/m1-dv-$(date +%Y-%m-%d)/logs` |

---

## Olares hybrid endpoints (inventory 2026-06-10)

Use **in-cluster FQDNs** from an Olares pod or port-forward on the node:

| Service | Endpoint | Notes |
|---------|----------|-------|
| Ollama | `http://ollama.ollamaserver-shared:11434` | Shared — do not deploy duplicate |
| ComfyUI | `http://comfyui.comfyuisharev2server-shared:8190` | Port **8190**, not 8188 |
| AIMPOS app plane | **`deploy/k8s/m1-dv/`** (raw K8s on Olares) | Postgres/MinIO/Redis/API — no duplicate AI; Temporal/worker optional |

---

## Validation sequence

### Phase A — Platform (US-02)

1. Deploy AIMPOS app/data plane via `deploy/k8s/m1-dv/scripts/deploy-infra.sh` + `deploy-api.sh` (see `deploy/k8s/m1-dv/README.md`).
2. `GET /health` → 200; `postgresql`, `redis`, `minio` ok.
3. Capture `kubectl get pods -n aimpos-mwayolares` + health JSON in `logs/health.json`.

### Phase B — Ollama (US-06 / T-06-01)

```bash
python scripts/smoke/test_ollama.py --require-live \
  --host http://ollama.ollamaserver-shared:11434
```

**PASS:** exit 0; model **`qwen3:14b`** (from `configs/ollama/models.json`); completion &lt;30s.  
**FAIL:** exit 1. **SKIP forbidden** with `--require-live`.

### Phase C — ComfyUI (US-06 / T-06-02)

Run **after** Ollama smoke (D-08 sequencing). Unload uses `OLLAMA_MODEL` from env / `models.json` default.

```bash
python scripts/smoke/test_comfyui.py --require-live \
  --host http://comfyui.comfyuisharev2server-shared:8190 \
  --ollama-host http://ollama.ollamaserver-shared:11434 \
  --minio-host <aimpos-minio-host>:9000
```

**PASS:** exit 0; PNG in `aimpos-hot-assets/smoke/comfyui/sdxl_storyboard.png`.

### Phase D — Zero egress (#49)

Document capture method + result in `logs/zero-egress.txt`.

---

## Exit decision matrix

| Outcome | Classification | Action |
|---------|----------------|--------|
| Phase B+C PASS, Phase A PASS | **M1-DV PASS** | Close M1-DV; authorize US-12 planning |
| GPU missing | Hardware limitation | FAIL report; remain blocked |
| Endpoint/DNS/port wrong | Deployment | FAIL report; fix hybrid URLs |
| Model tag wrong | Configuration | Amend D-02/models.json (D-36 path) |
| Smoke logic on valid hardware | Product architecture | FAIL report; engineering fix |

---

## Go / No-Go for US-12

| | Requirement |
|---|-------------|
| **GO** | Formal **M1-DV PASS** report; evidence folder complete |
| **NO-GO** | Any FAIL report; US-12/13/09 remain blocked |

---

## PASS / FAIL report templates

Deliver exactly one:

- `evidence/m1-dv-YYYY-MM-DD/M1-DV-PASS-REPORT.md`
- `evidence/m1-dv-YYYY-MM-DD/M1-DV-FAIL-REPORT.md`

---

## Amendment log

| Date | Change |
|------|--------|
| 2026-06-10 | **D-36:** Ollama pin `llama3.1:13b` → `qwen3:14b`; ComfyUI port 8190 on Olares hybrid |
