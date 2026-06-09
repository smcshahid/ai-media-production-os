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

## Database migrations (US-04)

PostgreSQL is the system of record; all schema changes go through Alembic
(`alembic/versions/`). The initial migration `0001_initial_core_tables` creates
the six core tables (MVP Definition §6.5) and is generated from the SQLAlchemy
models in `app/infrastructure/db/models/`.

```bash
make up            # start the Sprint-0 stack (PostgreSQL must be running)
make migrate       # alembic upgrade head  — apply all migrations
make migrate-down  # alembic downgrade -1  — roll back the last migration
```

Until the API image lands (US-03), `make migrate` runs Alembic in a one-off
container on the `aimpos-spark` network so `DATABASE_URL` (`postgresql:5432`
from `.env`) resolves; afterwards it becomes `docker compose run --rm api
alembic upgrade head` (see `DECISIONS.md` D-20). The migration is verified
against PostgreSQL: `upgrade head` creates all six tables, `downgrade` removes
them, and Alembic autogenerate reports no drift from the models.

See [docs/runbooks/migrations.md](../docs/runbooks/migrations.md).
