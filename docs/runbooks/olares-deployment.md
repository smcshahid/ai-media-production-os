# Runbook: Olares deployment (M1-DV)

Steps to validate **M1-DV** on an Olares GPU host. Software authoring is **S1-SW**; live proof closes US-02, US-06, EPIC-01.

## Prerequisites

- Olares node with NVIDIA GPU (16 GB+ VRAM recommended for `qwen3:14b` per D-02/D-36)
- Docker / Olares container runtime with GPU device mapping
- Repo cloned; `.env` configured from `.env.example` (rotate secrets for lab)

## Deploy stack

```bash
# from repo root — adjust paths if Olares mounts differ
docker compose -f deploy/compose/docker-compose.yml --env-file .env up -d
```

Wait for health: `postgresql`, `minio`, `redis`, `temporal`, `api`, `web`, `worker`, `ollama`, `comfyui`.

`ollama-init` must complete (model pull). Check: `docker compose logs ollama-init`.

## M1-DV validation sequence

Run in order (D-08: Ollama before ComfyUI; smokes enforce unload):

**Dedicated compose (dev/lab):**

```bash
python scripts/smoke/test_ollama.py --require-live --host http://127.0.0.1:11434
python scripts/smoke/test_comfyui.py --require-live --host http://127.0.0.1:8188
```

**Olares hybrid (shared AI services — see `m1-dv-execution.md`):**

```bash
python scripts/smoke/test_ollama.py --require-live --host http://ollama.ollamaserver-shared:11434
python scripts/smoke/test_comfyui.py --require-live \
  --host http://comfyui.comfyuisharev2server-shared:8190 \
  --ollama-host http://ollama.ollamaserver-shared:11434
```

Expected: both exit **0** with `PASS`. Any `FAIL` blocks M1-DV.

## Zero egress (#49)

On lab network, verify compose startup produces no outbound connections (governance zero-egress). Document capture method and result in issue #49 before closing M1-DV.

## Failure protocol

If US-06 cannot pass on hardware, invoke Sprint 0 failure protocol (stub PNGs, documented limitation). Do not mark M1-DV complete without SCR/PO sign-off.

## Close criteria

M1-DV closes when: live Ollama + ComfyUI smokes pass; US-02 live deploy proven; US-06 closed (or failure protocol invoked); EPIC-01 / FEAT-INFRA rollup.
