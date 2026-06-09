# worker/ — Temporal Worker + LangGraph Agents

Durable orchestration and AI agents. No HTTP server.

## Service boundary (non-negotiable, coding-standards §23)

- **Never** exposes HTTP — polls the Temporal task queue.
- Workflow code is deterministic; side effects live in activities.
- LangGraph graphs live in `app/agents/` only.
- GPU rule: never run Ollama and ComfyUI concurrently (D-08, documented here when US-06 lands).

## Folder map (Repository Structure §4.5)

| Path | Purpose | Lands in |
|------|---------|----------|
| `app/temporal/workflows/` | `SparkPipelineWorkflow` | US-07 (Sprint 2) |
| `app/temporal/activities/` | story/script/storyboard activities | Sprint 3–5 |
| `app/agents/` | Story Architect, Screenwriter, Cinematography | Sprint 3–5 |
| `app/tools/` | Ollama / ComfyUI / asset-store adapters | Sprint 1+ |
| `app/infrastructure/gpu/` | GPU sequencer | US-06 (Sprint 1) |

Worker is **not** part of Sprint 0 runtime. Folders exist now so later extraction needs no rename.
