# api/ — FastAPI Monolith

REST API for AIMPOS-Spark Visual. Single deployable application container.

## Service boundary (non-negotiable, coding-standards §23)

- **Never** calls Ollama, ComfyUI, or LangGraph directly — starts Temporal workflows and sends signals only.
- `app/domain/` has **no** FastAPI, SQLAlchemy, or HTTP-client imports.
- SQLAlchemy models live in `app/infrastructure/db/` only.

## Folder map (Repository Structure §4.4)

| Path | Purpose | Lands in |
|------|---------|----------|
| `app/routes/` | Thin HTTP controllers | US-01, US-03, US-05 |
| `app/domain/` | Business logic (framework-free) | US-01, US-04 |
| `app/infrastructure/db/` | SQLAlchemy models + repositories | US-04 |
| `app/infrastructure/storage/` | MinIO client | US-05 |
| `app/middleware/` | auth, request-id, logging | US-03, US-25 |
| `app/seed/` | Default project seed | US-01 |
| `alembic/` | Migrations | US-04 |
| `tests/` | Unit + integration | per issue |

`pyproject.toml` (FastAPI, SQLAlchemy, Alembic, Ruff, mypy) is introduced with US-04.
