# Olares AI Readiness — Status Report

**Date:** 2026-06-10  
**Host:** `olares@10.0.0.34`  
**Scope:** Shared Ollama + shared ComfyUI only (no M1-DV execution)

---

## Current status

| Service | Ready? | Summary |
|---------|--------|---------|
| **Shared Ollama** | **Partial** | Endpoint OK; `llama3.1:13b` **not installable** (tag absent from Ollama registry); `mistral:7b` installed (D-02 fallback) |
| **Shared ComfyUI** | **Yes** | `/queue` HTTP 200; `verify-comfyui.sh` **PASS**; `sdxl_base_1.0.safetensors` installed |

---

## Commands executed

### Ollama

```bash
# Via SSH pipe from evidence/olares-ai-readiness-2026-06-10/logs/01-ollama-prep.sh
kubectl exec -n ollamaserver-shared deploy/ollama -- ollama list
kubectl exec -n mediapipeline-mwayolares <pod> -c media-pipeline -- \
  curl http://ollama.ollamaserver-shared:11434/api/tags

kubectl exec -n ollamaserver-shared deploy/ollama -- ollama pull llama3.1:13b   # FAIL
kubectl exec -n ollamaserver-shared deploy/ollama -- ollama pull llama3:13b      # FAIL
kubectl exec -n ollamaserver-shared deploy/ollama -- ollama pull llama3.1:8b-instruct  # FAIL
kubectl exec -n ollamaserver-shared deploy/ollama -- ollama pull llama3.1:latest # OK (same as 8b)
kubectl exec -n ollamaserver-shared deploy/ollama -- ollama pull mistral:7b      # OK
kubectl exec -n ollamaserver-shared deploy/ollama -- ollama pull llama3.2:3b      # OK (diagnostic)
kubectl exec -n ollamaserver-shared deploy/ollama -- ollama pull llama3.2:1b      # OK (diagnostic)
kubectl exec -n ollamaserver-shared deploy/ollama -- ollama pull llama2:13b       # OK (7.4 GB — not D-02 pin)
```

### ComfyUI

```bash
# olares-one/scripts/diagnostics/verify-comfyui.sh (baseline → PASS after SDXL)
# evidence/.../logs/02-comfyui-probe.sh
# evidence/.../logs/04-sdxl-install.sh — wget HF checkpoint into pod

kubectl exec -n comfyuisharev2server-shared deploy/comfyuishare -c comfyui -- \
  wget -O /root/ComfyUI/models/checkpoints/sdxl_base_1.0.safetensors \
  https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors
```

**Note:** ComfyUI `/queue` 503 at inventory time self-resolved when `main.py` started (~08:40 UTC). No manual Launcher click was required in this session; launcher process was already running inside the shared GPU pod.

---

## Evidence collected

| File | Contents |
|------|----------|
| `logs/01-ollama-prep.txt` | Endpoint verify + failed `llama3.1:13b` pull |
| `logs/01-ollama-pull-retries.txt` | Retries: `llama3.1:13b`, `llama3:13b`, `llama3.1:8b-instruct` |
| `logs/01-ollama-pull-more.txt` | Successful `mistral:7b`, `llama3.2:*` pulls |
| `logs/02-comfyui-probe.txt` | In-cluster API probes, checkpoint list |
| `logs/03-verify-comfyui-baseline.txt` | First verify PASS (pre-SDXL, 2 checkpoints) |
| `logs/04-sdxl-install.txt` | 6.5 GB download + API confirms SDXL |
| `logs/05-verify-comfyui-pass.txt` | verify-comfyui.sh PASS (3 checkpoints incl. SDXL) |
| `logs/06-final-verify.txt` | Final Ollama + ComfyUI snapshot |
| `logs/01-ollama-pull-llama2.txt` | `llama2:13b` pull success (not `llama3.1:13b`) |

---

## Remaining blockers

1. **`llama3.1:13b` unavailable** — Ollama registry returns `file does not exist` for `llama3.1:13b`, `llama3:13b`, and `llama3.1:8b-instruct`. Meta Llama 3.1 on Ollama is offered in **8B / 70B / 405B** sizes only (no 13B variant). Registry pulls for `mistral:7b` and `llama2:13b` succeed, proving network/registry access is fine — the `llama3.1:13b` tag itself does not exist.

2. **M1-DV Ollama smoke** — Frozen criterion expects `llama3.1:13b` (D-02). Shared Ollama has `llama3.1:8b`, `mistral:7b` (new), and `qwen3:14b` (14B, already present). **Cannot mark Ollama fully ready** for the pinned model without a governance decision or M1-DV package exception (out of scope for this prep session).

3. **ComfyUI persistence** — `sdxl_base_1.0.safetensors` was installed inside the running pod at `/root/ComfyUI/models/checkpoints/`. If the pod restarts without a persistent volume on that path, SDXL may need re-download or Launcher resource-package install. Host path `/olares/share/ai/model/main/` is empty/missing; consider mirroring to shared model hub for durability (operator action, not done here).

4. **ComfyUI port** — API remains on **8190** in-cluster (not AIMPOS compose default 8188). M1-DV smokes must use `--host http://comfyui.comfyuisharev2server-shared:8190` from an Olares pod.

---

## M1-DV scheduling recommendation

| Component | Schedule M1-DV now? |
|-----------|---------------------|
| **ComfyUI** | **Yes** — ready for trial smoke with port/checkpoint overrides |
| **Ollama** | **No** — blocked on `llama3.1:13b` unless M1-DV session accepts documented D-02 fallback (`mistral:7b`) or an existing substitute (`qwen3:14b`) per frozen exit criteria |
| **Overall M1-DV** | **Do not schedule immediately** — one of two AI services fails the pinned Ollama model requirement |

**When unblocked:** After `llama3.1:13b` availability is resolved (or formal M1-DV criteria acknowledge an installed substitute), ComfyUI is already prepared — M1-DV can proceed on Olares with hybrid endpoints plus dedicated AIMPOS app/data plane deployment.

**Signed:** AI readiness prep session · 2026-06-10
