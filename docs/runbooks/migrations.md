# Runbook — Database migrations (Alembic)

**Issue:** T-04-02 · **Parent:** US-04 · **Sprint:** 0

PostgreSQL is the system of record. Every schema change is an Alembic migration
under `api/alembic/versions/`. Migrations are the **only** source of truth for
the schema — there are no `CREATE TABLE` statements in application code.

## At a glance

| Property | Value |
|----------|-------|
| Config | `api/alembic.ini` (URL overridden by `DATABASE_URL`) |
| Env | `api/alembic/env.py` — `target_metadata = Base.metadata` |
| Versions | `api/alembic/versions/` |
| Initial migration | `0001_initial_core_tables` — the six MVP core tables |
| Connection | `DATABASE_URL` from `.env` (`postgresql+psycopg://…@postgresql:5432/…`) |

## Apply / roll back

```bash
make up            # PostgreSQL must be running
make migrate       # alembic upgrade head
make migrate-down  # alembic downgrade -1  (rollback last migration)
```

Until the API image exists (US-03), `make migrate` runs Alembic in a one-off
`python:3.12-slim` container attached to the `aimpos-spark` network (so the
in-network host `postgresql` resolves) and installs the migration deps plus the
editable `aimpos-core` package. Once the API image lands this becomes
`docker compose run --rm api alembic upgrade head` (see `DECISIONS.md` D-20).

## Authoring a new migration

1. Add/modify SQLAlchemy models in `api/app/infrastructure/db/models/` and make
   sure they are imported in that package's `__init__.py` (so they register on
   `Base.metadata`).
2. With PostgreSQL running and `DATABASE_URL` exported, autogenerate:
   ```bash
   cd api && alembic revision --autogenerate -m "describe change"
   ```
3. **Review the generated file** — confirm the diff matches intent, constraint
   names follow the convention (D-19), and `downgrade()` is correct.
4. Never edit a migration already merged to `main`; add a new one instead
   (coding-standards.md §181-187).

## Verifying

The initial migration was verified against PostgreSQL 16:

- `alembic upgrade head` creates all six tables (`projects`, `pipeline_runs`,
  `asset_versions`, `approvals`, `audit_events`, `lineage_edges`);
- `alembic downgrade base` removes every table cleanly;
- Alembic `compare_metadata` reports **no drift** between the migration result
  and the models;
- re-running `upgrade head` from empty succeeds.

## Troubleshooting

- **`Target database is not up to date`:** run `make migrate` before generating
  a new revision.
- **Autogenerate produces an empty migration:** the models already match the DB,
  or the model module is not imported in `models/__init__.py`.
- **`could not translate host name "postgresql"`:** the migrate container is not
  on the `aimpos-spark` network — start the stack with `make up` first.
