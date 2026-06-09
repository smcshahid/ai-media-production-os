# configs/ — Runtime Configuration (not secrets)

Version-controlled configuration. Secrets stay in `.env` (gitignored).

| Path | Purpose | Lands in |
|------|---------|----------|
| `ollama/models.json` | Pinned model tags per stage | Sprint 1 (US-06) |
| `comfyui/workflows/*.json` | Pinned ComfyUI workflow graphs | Sprint 1 (US-06) |
| `temporal/development.yaml` | Temporal dev settings | Sprint 2 (US-07) |

No config files in Sprint 0 — placeholders only. Model/workflow choices recorded in `DECISIONS.md` (D-02, D-03).
