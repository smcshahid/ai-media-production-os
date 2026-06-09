# AIMPOS-Spark Visual — GitHub Issues (Tasks 1–25)

**Document Type:** Task-level GitHub Issues (import-ready)  
**Version:** 1.0  
**Status:** FROZEN — Effective June 9, 2026. Milestones per [Sprint Reclassification.md](./Sprint%20Reclassification.md).  
**Date:** June 8, 2026  
**Scope:** [MVP Scope Freeze.md](./MVP%20Scope%20Freeze.md) · Idea → Story → Script → Storyboard  
**Source:** [MVP Backlog.md](./MVP%20Backlog.md) · [MVP Dependency Map.md](./MVP%20Dependency%20Map.md)  
**Import CSV:** [backlog/github-issues-tasks-01-25.csv](./backlog/github-issues-tasks-01-25.csv)

---

## Import setup

| GitHub element | Values |
|----------------|--------|
| **Milestones** | `Sprint 1`, `Sprint 2` |
| **Labels** | `aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `sprint:s2`, `devops`, `backend`, `frontend`, `ai`, `docs`, `test` |
| **Parent issues** | Link to user story `US-XX` via sub-issue or `Parent: #US-XX` in body |

```bash
gh issue create --title "[T-02-01] Write docker-compose.yml for all 9 services" \
  --label "aimpos-spark,visual-mvp,task,priority:p0,sprint:s1,devops" \
  --milestone "Sprint 1"
```

---

## Issue index

| Seq | ID | Title | Milestone | Parent |
|----:|-----|-------|-----------|--------|
| 1 | T-02-01 | Write docker-compose.yml for all 9 services | Sprint 1 | US-02 |
| 2 | T-02-02 | Configure PostgreSQL volume and init scripts | Sprint 1 | US-02 |
| 3 | T-02-03 | Configure MinIO bucket on startup | Sprint 1 | US-02 |
| 4 | T-02-04 | Pin Ollama model in compose init | Sprint 1 | US-02 |
| 5 | T-02-05 | Document Olares deployment in README | Sprint 1 | US-02 |
| 6 | T-02-06 | Verify zero egress during compose startup | Sprint 1 | US-02 |
| 7 | T-04-01 | Define SQLAlchemy models for core tables | Sprint 1 | US-04 |
| 8 | T-04-02 | Create initial Alembic migration | Sprint 1 | US-04 |
| 9 | T-04-03 | Add repository layer interfaces | Sprint 1 | US-04 |
| 10 | T-03-01 | Implement /health with dependency probes | Sprint 1 | US-03 |
| 11 | T-03-02 | Add structured logging middleware | Sprint 1 | US-03 |
| 12 | T-03-03 | Add request ID propagation | Sprint 1 | US-03 |
| 13 | T-05-01 | Implement MinIO client wrapper | Sprint 1 | US-05 |
| 14 | T-05-02 | Implement content-hash key generator | Sprint 1 | US-05 |
| 15 | T-05-03 | Implement AssetVersion create on upload | Sprint 1 | US-05 |
| 16 | T-05-04 | Integration test upload round-trip | Sprint 1 | US-05 |
| 17 | T-06-01 | Create Ollama connectivity test script | Sprint 1 | US-06 |
| 18 | T-06-02 | Pin and test ComfyUI SDXL workflow JSON | Sprint 1 | US-06 |
| 19 | T-06-03 | Document GPU sequencing rule in worker README | Sprint 1 | US-06 |
| 20 | T-01-01 | Create projects table migration | Sprint 1 | US-01 |
| 21 | T-01-02 | Implement seed script for default project | Sprint 1 | US-01 |
| 22 | T-01-03 | Add GET /projects endpoint | Sprint 1 | US-01 |
| 23 | T-01-04 | Unit test project repository | Sprint 1 | US-01 |
| 24 | T-26-01 | Build app shell with React Router | Sprint 2 | US-26 |
| 25 | T-26-02 | Implement nav bar and route guards | Sprint 2 | US-26 |

---

## Issue 1 — T-02-01

### Title
`[T-02-01] Write docker-compose.yml for all 9 services`

### Description
Create the primary Docker Compose file for AIMPOS-Spark Visual at `deploy/compose/docker-compose.yml`.

Define all nine MVP services on a single internal network `aimpos-spark`:

- `api` (FastAPI)
- `worker` (Temporal worker stub)
- `web` (React/nginx stub)
- `temporal`
- `postgresql`
- `minio`
- `redis`
- `ollama`
- `comfyui`

Align with [Repository Structure.md](./Repository%20Structure.md). Application containers may use stub images initially; infrastructure services must be fully configured.

**Parent user story:** US-02 — Deploy MVP stack on Olares  
**Implementation sequence:** 1

### Acceptance criteria
- [ ] `deploy/compose/docker-compose.yml` exists and validates with `docker compose config`
- [ ] All 9 services defined with `aimpos-spark` network
- [ ] Each service has a `healthcheck` or documented startup order
- [ ] `.env.compose.example` documents required environment variables
- [ ] `docker compose up -d postgresql minio redis` starts without error

### Dependencies
- None (first task in sequence)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `devops`, `parent:US-02`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 2 — T-02-02

### Title
`[T-02-02] Configure PostgreSQL volume and init scripts`

### Description
Add persistent volume configuration and initialization for PostgreSQL in Docker Compose.

Place init scripts under `deploy/init/postgres/`. Ensure database `aimpos_spark` is created and extensions (if any) are applied on first boot.

**Parent user story:** US-02  
**Implementation sequence:** 2

### Acceptance criteria
- [ ] Named volume `aimpos-postgres-data` persists data across restarts
- [ ] PostgreSQL container exposes port 5432 to API on internal network only
- [ ] Init script creates database and user matching `.env.example`
- [ ] `psql` connection from `api` network succeeds after `docker compose up`

### Dependencies
- #T-02-01 (must be closed first)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `devops`, `parent:US-02`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 3 — T-02-03

### Title
`[T-02-03] Configure MinIO bucket aimpos-hot-assets on startup`

### Description
Configure MinIO in compose with persistent volume and an init script that creates the `aimpos-hot-assets` bucket on first startup.

Script location: `deploy/init/minio/create-buckets.sh` (or equivalent entrypoint hook).

**Parent user story:** US-02  
**Implementation sequence:** 3

### Acceptance criteria
- [ ] MinIO container starts with persistent volume
- [ ] Bucket `aimpos-hot-assets` exists after first `docker compose up`
- [ ] S3 API accessible from `api` container using credentials in `.env`
- [ ] Init script is idempotent (safe on restart)

### Dependencies
- #T-02-01 (must be closed first)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `devops`, `parent:US-02`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 4 — T-02-04

### Title
`[T-02-04] Pin Ollama model llama3.1:13b in compose init`

### Description
Configure the Ollama service to pull and pin `llama3.1:13b` (or documented fallback `mistral:7b` if VRAM insufficient) on container initialization.

Document model choice in `configs/ollama/models.json` and README.

**Parent user story:** US-02  
**Implementation sequence:** 4

### Acceptance criteria
- [ ] Ollama service defined in compose with GPU device mapping (where available)
- [ ] Model pull documented in README or init script
- [ ] `ollama list` shows pinned model after startup
- [ ] Fallback model documented if 13B does not fit target hardware

### Dependencies
- #T-02-01 (must be closed first)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `devops`, `ai`, `parent:US-02`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 5 — T-02-05

### Title
`[T-02-05] Document Olares deployment in README`

### Description
Write deployment documentation covering local Docker Compose and Olares One deployment paths.

Include: prerequisites, `make up` / `docker compose up`, service URLs, health check verification, and troubleshooting common port/GPU issues.

**Parent user story:** US-02  
**Implementation sequence:** 5

### Acceptance criteria
- [ ] Root `README.md` includes Quick Start section
- [ ] `docs/runbooks/local-development.md` created or updated
- [ ] `docs/runbooks/olares-deployment.md` stub with Olares-specific notes
- [ ] All 9 services listed with ports and purpose

### Dependencies
- #T-02-01, #T-02-02, #T-02-03 (must be closed first)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `docs`, `parent:US-02`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 6 — T-02-06

### Title
`[T-02-06] Verify zero egress during compose startup`

### Description
Verify that the full compose stack starts and reaches healthy state without outbound internet egress (sovereign AI requirement SC-02).

Document verification method and results in README or runbook.

**Parent user story:** US-02  
**Implementation sequence:** 6

### Acceptance criteria
- [ ] Documented test procedure for zero-egress verification on Olares/lab network
- [ ] All 9 containers reach healthy/running state within 5 minutes
- [ ] No required outbound calls except documented model pull (one-time, optional air-gap note)
- [ ] US-02 parent story acceptance criteria can be checked off after this task

### Dependencies
- #T-02-01 through #T-02-05 (must be closed first)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `devops`, `parent:US-02`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 7 — T-04-01

### Title
`[T-04-01] Define SQLAlchemy models for core tables`

### Description
Define SQLAlchemy ORM models for all MVP core tables per [MVP Definition.md](./MVP%20Definition.md) §6.5:

`projects`, `pipeline_runs`, `asset_versions`, `approvals`, `audit_events`, `lineage_edges`

Location: `api/app/infrastructure/db/models/`

**Parent user story:** US-04 — Database schema foundation  
**Implementation sequence:** 7

### Acceptance criteria
- [ ] Model file(s) exist for all 6 tables
- [ ] `asset_versions` includes: `stage`, `version`, `minio_key`, `content_hash`, `is_ai_generated`, `branch`
- [ ] Foreign keys and indexes defined for `pipeline_run_id`, `project_id`
- [ ] Models importable without circular dependency errors

### Dependencies
- #T-02-02 (PostgreSQL must be running)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `backend`, `parent:US-04`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 8 — T-04-02

### Title
`[T-04-02] Create initial Alembic migration`

### Description
Create the initial Alembic migration from SQLAlchemy models. Configure `alembic.ini` and env.py to read database URL from environment.

**Parent user story:** US-04  
**Implementation sequence:** 8

### Acceptance criteria
- [ ] `alembic upgrade head` creates all 6 tables on empty database
- [ ] `alembic downgrade -1` rolls back cleanly on empty database
- [ ] Migration is committed under `api/alembic/versions/`
- [ ] Documented in README: `make migrate`

### Dependencies
- #T-04-01 (must be closed first)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `backend`, `parent:US-04`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 9 — T-04-03

### Title
`[T-04-03] Add repository layer interfaces`

### Description
Add repository interfaces and base implementations for core aggregates. Follow DDD layout in [Repository Structure.md](./Repository%20Structure.md).

Suggested: `ProjectRepository`, `PipelineRunRepository`, `AssetVersionRepository`, `ApprovalRepository`, `AuditEventRepository`.

**Parent user story:** US-04  
**Implementation sequence:** 9

### Acceptance criteria
- [ ] Repository interfaces defined in `api/app/infrastructure/db/repositories/`
- [ ] CRUD or query methods for each aggregate root
- [ ] Repositories use async SQLAlchemy session pattern
- [ ] At least one smoke test instantiates each repository against test DB

### Dependencies
- #T-04-02 (must be closed first)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `backend`, `parent:US-04`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 10 — T-03-01

### Title
`[T-03-01] Implement /health with dependency probes`

### Description
Implement `GET /health` on the FastAPI application with live probes for PostgreSQL, MinIO, and Redis.

Return JSON with per-dependency status. Return `503` when any critical dependency is down.

**Parent user story:** US-03 — API health and logging  
**Implementation sequence:** 10

### Acceptance criteria
- [ ] `GET /health` returns `200` when postgresql, minio, redis are reachable
- [ ] Response JSON includes `status`, `dependencies` object with per-service state
- [ ] Returns `503` when PostgreSQL is down
- [ ] Endpoint registered in OpenAPI schema

### Dependencies
- #T-02-01, #T-04-02 (stack and schema ready)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `backend`, `parent:US-03`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 11 — T-03-02

### Title
`[T-03-02] Add structured logging middleware`

### Description
Add structured JSON logging middleware to the FastAPI application using the shared logging config from `packages/aimpos-config` (or equivalent).

Every request logs: `request_id`, `path`, `method`, `status`, `duration_ms`.

**Parent user story:** US-03  
**Implementation sequence:** 11

### Acceptance criteria
- [ ] Middleware emits one JSON log line per request
- [ ] Log fields: `timestamp`, `level`, `request_id`, `path`, `status`, `duration_ms`
- [ ] Errors log at `ERROR` with exception type
- [ ] Log format documented in `api/README.md`

### Dependencies
- #T-03-01 (health route can be used to verify logging)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `backend`, `parent:US-03`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 12 — T-03-03

### Title
`[T-03-03] Add request ID propagation`

### Description
Generate or accept `X-Request-ID` header on every API request. Propagate `request_id` to structured logs and (future) downstream calls.

**Parent user story:** US-03  
**Implementation sequence:** 12

### Acceptance criteria
- [ ] Incoming `X-Request-ID` preserved; new UUID generated if absent
- [ ] `request_id` appears in all log lines for that request
- [ ] `X-Request-ID` returned in response headers
- [ ] Unit test covers generate and preserve paths

### Dependencies
- #T-03-02 (must be closed first)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `backend`, `parent:US-03`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 13 — T-05-01

### Title
`[T-05-01] Implement MinIO client wrapper`

### Description
Implement a reusable MinIO/S3 client wrapper in `api/app/infrastructure/storage/minio_client.py`.

Expose connect, upload, download, and head-object operations using credentials from settings.

**Parent user story:** US-05 — MinIO asset upload service  
**Implementation sequence:** 13

### Acceptance criteria
- [ ] Client reads endpoint, access key, secret key from environment
- [ ] `upload_bytes(key, data, content_type)` stores object in `aimpos-hot-assets`
- [ ] `download_bytes(key)` returns original bytes
- [ ] Connection errors raise typed exceptions with clear messages

### Dependencies
- #T-02-03, #T-04-02 (MinIO bucket and DB ready)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `backend`, `parent:US-05`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 14 — T-05-02

### Title
`[T-05-02] Implement content-hash key generator`

### Description
Implement SHA-256 content-addressable key generation for MinIO objects.

Key format: `{project_id}/{stage}/{content_hash}` or equivalent documented scheme.

**Parent user story:** US-05  
**Implementation sequence:** 14

### Acceptance criteria
- [ ] `compute_hash(bytes) -> str` returns SHA-256 hex digest
- [ ] `build_object_key(project_id, stage, content_hash) -> str` is deterministic
- [ ] Same bytes always produce same hash and key
- [ ] Unit tests cover empty, small, and large payloads

### Dependencies
- #T-05-01 (must be closed first)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `backend`, `parent:US-05`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 15 — T-05-03

### Title
`[T-05-03] Implement AssetVersion create on upload`

### Description
Implement `store_asset(bytes, stage, project_id, ...)` domain function that:

1. Computes content hash
2. Uploads to MinIO
3. Creates `asset_versions` row with metadata

**Parent user story:** US-05  
**Implementation sequence:** 15

### Acceptance criteria
- [ ] `store_asset` returns `AssetVersion` record with `id`, `version`, `content_hash`, `minio_key`
- [ ] Version number increments per `(project_id, stage)` chain
- [ ] `is_ai_generated` and `branch` fields settable by caller
- [ ] `content_hash` matches MinIO object ETag or verified after upload

### Dependencies
- #T-05-02, #T-04-03 (must be closed first)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `backend`, `parent:US-05`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 16 — T-05-04

### Title
`[T-05-04] Integration test upload round-trip`

### Description
Write an integration test that exercises the full asset upload path: `store_asset` → MinIO → `asset_versions` row → download → hash verify.

**Parent user story:** US-05  
**Implementation sequence:** 16

### Acceptance criteria
- [ ] Test runs against compose MinIO and PostgreSQL (or testcontainers)
- [ ] Upload and download bytes are identical
- [ ] `content_hash` in DB matches computed SHA-256
- [ ] Duplicate upload of same bytes creates new version row (dedup blob policy per MVP)

### Dependencies
- #T-05-03 (must be closed first)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `backend`, `test`, `parent:US-05`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 17 — T-06-01

### Title
`[T-06-01] Create Ollama connectivity test script`

### Description
Create `scripts/smoke/test_ollama.py` that calls the local Ollama API and verifies text generation completes in under 30 seconds.

**Parent user story:** US-06 — Ollama and ComfyUI smoke test  
**Implementation sequence:** 17

### Acceptance criteria
- [ ] Script runs with `python scripts/smoke/test_ollama.py`
- [ ] Generates response from pinned model within 30 s
- [ ] Exits `0` on success, non-zero on failure with error message
- [ ] Documented in README smoke test section

### Dependencies
- #T-02-04, #T-02-06 (Ollama in compose)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `ai`, `test`, `parent:US-06`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 18 — T-06-02

### Title
`[T-06-02] Pin and test ComfyUI SDXL workflow JSON`

### Description
Pin a ComfyUI SDXL workflow JSON under `configs/comfyui/workflows/sdxl_storyboard.json`. Create `scripts/smoke/test_comfyui.py` that executes the workflow and stores output PNG via MinIO upload path.

**Parent user story:** US-06  
**Implementation sequence:** 18

### Acceptance criteria
- [ ] Workflow JSON committed and version-pinned in `configs/comfyui/`
- [ ] Smoke script produces valid PNG file
- [ ] PNG stored in MinIO via `store_asset` or direct upload
- [ ] Script exits `0` on success against compose ComfyUI

### Dependencies
- #T-06-01, #T-05-03 (Ollama verified; MinIO upload works)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `ai`, `test`, `parent:US-06`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 19 — T-06-03

### Title
`[T-06-03] Document GPU sequencing rule in worker README`

### Description
Document the mandatory GPU sequencing rule in `worker/README.md`: unload Ollama model before starting ComfyUI GPU jobs. Never run both concurrently on Olares single GPU.

Reference [MVP Scope Freeze.md](./MVP%20Scope%20Freeze.md) and DECISIONS.md entry D-08.

**Parent user story:** US-06  
**Implementation sequence:** 19

### Acceptance criteria
- [ ] `worker/README.md` documents GPU sequencing rule
- [ ] `docs/runbooks/gpu-sequencing.md` created with step-by-step procedure
- [ ] Sequential Ollama → ComfyUI test documented with expected outcome (no OOM)
- [ ] US-06 parent story can be closed after #T-06-01, #T-06-02, this task

### Dependencies
- #T-06-01, #T-06-02 (must be closed first)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `docs`, `ai`, `parent:US-06`, `feature:F-INFRA`, `epic:EPIC-01`

### Milestone
**Sprint 1**

---

## Issue 20 — T-01-01

### Title
`[T-01-01] Create projects table migration`

### Description
Ensure `projects` table is fully defined and migrated. If covered by initial migration (T-04-02), add any project-specific constraints, indexes, or seed prerequisites.

Verify `projects` supports: `id`, `title`, `status`, `created_at`.

**Parent user story:** US-01 — Create default project  
**Implementation sequence:** 20

### Acceptance criteria
- [ ] `projects` table exists after `alembic upgrade head`
- [ ] `status` enum or check constraint includes `ACTIVE`
- [ ] Primary key and `created_at` timestamp present
- [ ] Migration idempotent on re-run

### Dependencies
- #T-04-02 (must be closed first)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `backend`, `parent:US-01`, `feature:F-01`, `epic:EPIC-03`

### Milestone
**Sprint 1**

---

## Issue 21 — T-01-02

### Title
`[T-01-02] Implement seed script for default project`

### Description
Implement startup seed in `api/app/seed/default_project.py` that creates project `AIMPOS Spark Demo` with `status=ACTIVE` if no projects exist.

Must be idempotent on API restart.

**Parent user story:** US-01  
**Implementation sequence:** 21

### Acceptance criteria
- [ ] On fresh DB, exactly one project `AIMPOS Spark Demo` is created
- [ ] On API restart, no duplicate project created
- [ ] Seed runs automatically on application startup (or documented `make seed`)
- [ ] Log line confirms seed action

### Dependencies
- #T-01-01, #T-04-03 (must be closed first)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `backend`, `parent:US-01`, `feature:F-01`, `epic:EPIC-03`

### Milestone
**Sprint 1**

---

## Issue 22 — T-01-03

### Title
`[T-01-03] Add GET /projects endpoint`

### Description
Implement `GET /projects` REST endpoint returning list of projects with `id`, `title`, `status`.

For MVP, returns single seeded project.

**Parent user story:** US-01  
**Implementation sequence:** 22

### Acceptance criteria
- [ ] `GET /projects` returns `200` with JSON array
- [ ] Each project includes `id`, `title`, `status`
- [ ] Fresh deployment returns one `ACTIVE` project
- [ ] Endpoint documented in OpenAPI

### Dependencies
- #T-01-02 (must be closed first)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `backend`, `parent:US-01`, `feature:F-01`, `epic:EPIC-03`

### Milestone
**Sprint 1**

---

## Issue 23 — T-01-04

### Title
`[T-01-04] Unit test project repository`

### Description
Write unit tests for `ProjectRepository` covering create, get-by-id, list, and idempotent seed behavior.

**Parent user story:** US-01  
**Implementation sequence:** 23

### Acceptance criteria
- [ ] Tests in `api/tests/unit/test_project_repository.py`
- [ ] Coverage: list returns seeded project
- [ ] Coverage: duplicate seed does not create second row
- [ ] Tests pass in CI (`ci-api.yml`)

### Dependencies
- #T-01-03 (must be closed first)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s1`, `backend`, `test`, `parent:US-01`, `feature:F-01`, `epic:EPIC-03`

### Milestone
**Sprint 1**

---

## Issue 24 — T-26-01

### Title
`[T-26-01] Build app shell with React Router`

### Description
Initialize React + TypeScript + Vite app in `web/`. Configure React Router with route placeholders for Dashboard, Review, Assets, and Audit.

Per [MVP Scope Freeze.md](./MVP%20Scope%20Freeze.md): Export screen deferred — route may exist as stub only.

**Parent user story:** US-26 — App navigation shell  
**Implementation sequence:** 24

### Acceptance criteria
- [ ] `web/` app builds with `npm run build`
- [ ] React Router configured with routes: `/`, `/review`, `/assets`, `/audit`
- [ ] Each route renders placeholder or empty-state component
- [ ] `web` container serves app in compose (dev or nginx)

### Dependencies
- #T-02-01 (web service in compose)
- #T-02-06 (Sprint 1 platform gate passed)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s2`, `frontend`, `parent:US-26`, `feature:F-16`, `epic:EPIC-06`

### Milestone
**Sprint 2**

---

## Issue 25 — T-26-02

### Title
`[T-26-02] Implement nav bar and route guards`

### Description
Implement `AppShell` with navigation bar linking Dashboard, Review, Assets, and Audit. Add route guards that show empty-state when pipeline has not started.

**Parent user story:** US-26  
**Implementation sequence:** 25

### Acceptance criteria
- [ ] Nav bar visible on all routes with four links
- [ ] Active route highlighted in nav
- [ ] Review and Audit show empty-state when no `pipeline_run_id` in context
- [ ] Layout usable at viewport width ≥ 768px
- [ ] API client module stub created in `web/src/api/client.ts`

### Dependencies
- #T-26-01 (must be closed first)

### Labels
`aimpos-spark`, `visual-mvp`, `task`, `priority:p0`, `sprint:s2`, `frontend`, `parent:US-26`, `feature:F-16`, `epic:EPIC-06`

### Milestone
**Sprint 2**

---

## Document control

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-08 | First 25 tasks ordered by dependency map implementation sequence |

*End of document*
