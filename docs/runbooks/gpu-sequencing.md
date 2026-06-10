# Runbook: GPU sequencing (D-08)

Single-GPU Olares hosts cannot run Ollama and ComfyUI concurrently.

## Rule

1. Run Ollama inference (story/script LLM).
2. Unload Ollama model (`keep_alive: 0` or `ollama stop <model>`).
3. Confirm VRAM is free.
4. Run ComfyUI (SDXL storyboard).
5. Idle ComfyUI before any later Ollama call.

## Smoke tests

`test_ollama.py` then `test_comfyui.py`. ComfyUI smoke calls Ollama unload best-effort before queuing the workflow.

## M1-DV order

```bash
python scripts/smoke/test_ollama.py --require-live
python scripts/smoke/test_comfyui.py --require-live
```

## VRAM fallback

If VRAM &lt; 16 GB, use `mistral:7b` instead of `llama3.1:13b` (D-02). Set `OLLAMA_MODEL` in `.env`.

## Production

Worker `app/infrastructure/gpu/sequencer.py` (US-06) will enforce sequencing in pipeline paths.
