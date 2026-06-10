# worker/ — Temporal Worker + LangGraph Agents

Durable orchestration and AI agents. No HTTP server.

## Service boundary (non-negotiable, coding-standards §23)

- **Never** exposes HTTP — polls the Temporal task queue.
- Workflow code is deterministic; side effects live in activities.
- LangGraph graphs live in `app/agents/` only.

## GPU sequencing rule (D-08 — mandatory on single-GPU hosts)

**Never run Ollama and ComfyUI concurrently.** A single Olares GPU does not have enough VRAM to hold both workloads at once.

| Step | Action |
|------|--------|
| 1 | Run the Ollama activity (story/script LLM inference). |
| 2 | **Unload** the Ollama model (`ollama stop <model>` or evict via the GPU sequencer in `app/infrastructure/gpu/`). |
| 3 | Confirm VRAM is free (no Ollama process holding the GPU). |
| 4 | Run the ComfyUI activity (SDXL storyboard generation). |
| 5 | Tear down or idle ComfyUI before any later Ollama call. |

Smoke tests (`scripts/smoke/test_ollama.py`, `scripts/smoke/test_comfyui.py`) must follow the same sequence: Ollama first, unload, then ComfyUI. The worker's `app/infrastructure/gpu/sequencer.py` (US-06) will enforce this in production paths.

**Fallback:** if VRAM is under 16 GB, prefer `mistral:7b` over `llama3.1:13b` (see D-02).

## Folder map (Repository Structure §4.5)

| Path | Purpose | Lands in |
|------|---------|----------|
| `app/temporal/workflows/` | `SparkPipelineWorkflow` | US-07 (Sprint 2) |
| `app/temporal/activities/` | `run_story_agent` (US-12), script/storyboard stubs | Sprint 3–5 |
| `app/agents/` | Story Architect, Screenwriter, Cinematography | Sprint 3–5 |
| `app/tools/` | Ollama / ComfyUI / asset-store adapters | Sprint 1+ |
| `app/infrastructure/gpu/` | GPU sequencer | US-06 (Sprint 1) |

## Sprint 1 runtime

The compose `worker` service is a **stub** (`app/main.py` logs and sleeps). Workflow registration lands in **US-07 (Sprint 2)**.
