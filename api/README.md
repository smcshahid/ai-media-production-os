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

## Running the API + health check (US-03)

The API is a service in the Sprint-0 compose stack (built from `api/Dockerfile`).

```bash
make up-dev        # build + start postgresql, minio, redis, api (ports published)
make health        # GET /health (pretty-printed)  ·  make logs-api  to tail logs
```

- Docs/OpenAPI: <http://localhost:8000/docs> · health: <http://localhost:8000/health>
- `GET /health` runs concurrent reachability probes for **postgresql**, **redis**,
  and **minio** and returns **200** (`status: healthy`) when all are reachable,
  otherwise **503** (`status: unhealthy`) with a per-dependency breakdown.
- Configuration loads via the shared `aimpos-config` package (`Settings`) — no
  `os.getenv` in application code. `temporal`/`ollama` join `/health` in Sprint 1.

### Logging & request correlation (US-03)

- Logs are single-line **JSON** (`aimpos-config` `configure_logging`). Each request
  gets a **`request_id`** (inbound `X-Request-ID` header if present, else a UUID4),
  echoed on the response and attached to **every** log line emitted while handling
  the request (access log, in-handler library logs) for correlation.
- One structured access line per request: `http_method`, `path`, `status_code`,
  `duration_ms`, `client`, `request_id` (uvicorn's plaintext access log is disabled).

### Authentication (US-25)

Every endpoint **except `GET /health`** requires a static Bearer token:

```bash
curl http://localhost:8000/projects                       # 401 {"detail":"Unauthorized"}
curl -H "Authorization: Bearer $AIMPOS_API_TOKEN" \
     http://localhost:8000/projects                       # 200
```

- The token is `AIMPOS_API_TOKEN` (`.env`); read via `aimpos-config` `Settings`.
- Header only — no `?token=` fallback. Missing/invalid → **401** `{"detail":"Unauthorized"}`.
- `/health` is exempt (Docker health checks); `/docs` + `/openapi.json` are
  **protected** — pass the token to fetch the schema.
- Keycloak/OIDC is deferred to Phase 1 (DECISIONS D-09). The React login page and
  token interceptor (T-25-03) ship with the frontend (US-26).

### Projects & default seed (US-01)

- `GET /projects` returns the project list as `[{ "id", "name", "status" }]`
  (field is `name`, per Sprint 0 plan §4.6 / DECISIONS D-18).
- A default project **"AIMPOS Spark Demo"** (`status=ACTIVE`) is seeded
  idempotently on API startup. On a **fresh** stack the schema must exist first:

```bash
make up-dev          # start the stack (api boots; seed is deferred if unmigrated)
make migrate         # create the tables
make seed            # seed the default project (or: docker compose restart api)
curl localhost:8000/projects
```

  The seed only inserts when the table is empty, so restarts never duplicate it.

### Asset storage (US-05)

Content-addressable storage exposed over HTTP:

- **`POST /assets`** — `multipart/form-data` with `project_id`, `stage`
  (`IDEA`/`STORY`/`SCRIPT`/`STORYBOARD`), and `file`. Validates the project
  (**404** if missing), stores the bytes via `store_asset`, and returns **201**
  with the created version. Human uploads are always `is_ai_generated=False`.
- **`GET /assets?project_id=<uuid>`** — the project's asset versions, newest first.

```bash
curl -X POST http://localhost:8000/assets \
  -F project_id=<uuid> -F stage=IDEA -F file=@idea.txt
curl "http://localhost:8000/assets?project_id=<uuid>"
```

Re-uploading identical bytes returns a **new version** that reuses the same
content-addressed `minio_key` (blob dedup). Underlying service:

- **`app/domain/assets/content.py`** (pure): `compute_content_hash(bytes)` →
  SHA-256 hex; `build_object_key(project_id, stage, content_hash)` →
  `"{project_id}/{stage}/{content_hash}"`.
- **`app/domain/assets/service.py`**: `store_asset(...)` hashes the bytes, uploads
  via a `BlobStore` port, appends a version row via an `AssetVersionStore` port, and
  returns a framework-free `StoredAsset`. The domain imports **no** SQLAlchemy/SDK —
  adapters are injected (ports & adapters; see DECISIONS D-25).
- **`app/infrastructure/storage/minio_client.py`**: `MinioClient` (the `BlobStore`
  adapter) wraps the sync `minio` SDK with `asyncio.to_thread`; `upload_bytes`
  verifies the object against MinIO's MD5 ETag and raises typed `StorageError` /
  `ObjectNotFoundError`. Credentials/bucket come from `aimpos-config` `Settings`.
- **Dedup:** identical bytes for a `(project, stage)` reuse the same `minio_key`
  (one stored blob) but always create a **new version row** (version increments
  along the chain). `content_hash` is SHA-256 (the content address); MinIO's ETag
  is the body MD5 and is used only for the post-upload integrity check.

Round-trip integration test (`tests/integration/test_asset_upload.py`) is skipped
unless services are up:

```bash
# from api/ — point settings at the dev-published ports, then run the integration mark
$env:AIMPOS_RUN_INTEGRATION="1"; $env:MINIO_ENDPOINT="localhost:9000"
$env:DATABASE_URL="postgresql+psycopg://aimpos:<pw>@localhost:5432/aimpos_spark"
pytest -m integration tests/integration/test_asset_upload.py
```

### Pipeline status (dashboard)

`GET /pipeline/status?project_id=<uuid>` feeds the dashboard's 4-stage stepper.
Read-only (no pipeline start/approve in Sprint 0):

```bash
curl -H "Authorization: Bearer $AIMPOS_API_TOKEN" \
     "http://localhost:8000/pipeline/status?project_id=<uuid>"
# {"project_id":"...","run_id":null,"status":"IDLE","current_stage":null,
#  "stages":["IDEA","STORY","SCRIPT","STORYBOARD"],"updated_at":null}
```

With no runs yet it returns `IDLE` plus the canonical stage order; once pipelines
start (US-07) it reflects the latest run's `status`/`current_stage`. Unknown
project → `404`.

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
