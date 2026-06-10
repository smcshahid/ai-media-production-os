# M1-DV FAIL — 2026-06-10

**Classification:** Hardware limitation (primary) + Environment / Deployment (contributing)
**Host:** Windows 10 Docker Desktop — not Olares
**Commit:** 207f80ac116d7f7551a2dbc7670550d5a30d661e
**Evidence:** `evidence/m1-dv-2026-06-10/logs/`

## Failed step

Phase B — `test_ollama.py --require-live` (first M1-DV gate). Session stopped per time-box rule; ComfyUI smoke not attempted.

## Evidence summary

| Check | Result |
|-------|--------|
| Olares GPU host | **NO** — Windows dev workstation |
| nvidia-smi / GPU | **Not available** |
| ollama/comfyui running | **NO** at session start |
| `test_ollama.py --require-live` | **FAIL** exit 1 — connection refused :11434 |
| `test_comfyui.py --require-live` | **Not run** (blocked by Phase B failure) |
| GPU service bring-up | ComfyUI image `yanwk/comfyui-boot:cu124-sdxl-20240919` **not found** |
| API `/health` | **Not verified** — API restarting (`DATABASE_URL` empty in container) |

## Classification rationale

1. **Hardware limitation (primary):** M1-DV requires Olares + GPU. This session ran on a CPU-only Windows dev host with no Ollama endpoint. Inference validation cannot pass without GPU hardware access.

2. **Environment (contributing):** API container received empty `DATABASE_URL` despite `.env` value — likely shell/compose interpolation override. Blocks US-02 deploy proof on this host.

3. **Deployment (contributing):** ComfyUI image pull failed (`not found`). One remediation attempted (explicit `up ollama comfyui`); did not proceed to extended troubleshooting.

**Not classified as product architecture** at this stage — failures are prerequisites (host, GPU, image availability) not smoke logic on valid hardware.

## Remediation recommendation

| Action | Owner |
|--------|-------|
| Schedule M1-DV on **Olares GPU node** per frozen checklist | Operator |
| Pre-flight: `nvidia-smi`, disk, model selection, evidence folder | Operator |
| On Olares: fix `DATABASE_URL` compose pass-through if reproduced (`--env-file .env`; clear empty shell `DATABASE_URL`) | Environment |
| Verify ComfyUI image availability on Olares registry/network before session | Deployment |
| Re-run full validation sequence; collect PASS evidence | Operator |

**Do not authorize US-12** until a subsequent session delivers M1-DV PASS report.

## Gate status

| Item | Status |
|------|--------|
| M1-DV | **OPEN** |
| US-12 / US-13 / US-09 | **NOT AUTHORIZED** |
