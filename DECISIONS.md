# AIMPOS-Spark Visual — Implementation Decisions Log

Append-only record of implementation decisions made during build. Architectural decisions remain frozen in the planning documents; this log captures code-level and execution choices.

Format: `D-NN | Decision | Date | Rationale`

---

## Sprint 0

### D-01 — Develop on local Docker Desktop in Week 1
**Date:** 2026-06-09  
**Decision:** Build and verify on local Docker Desktop before deploying to Olares One.  
**Rationale:** Faster iteration; Olares-specific config (GPU, volumes) is isolated to Sprint 1 (US-02 full stack). Per Sprint 0 plan §6 D-01.

### D-11 — US-26 ships in Sprint 0 against a 4-service compose
**Date:** 2026-06-09  
**Decision:** The frontend nav shell (US-26) is delivered in Sprint 0 even though `aimpos-spark-dependencies.csv` lists `US-02 → US-26` (frontend needs running stack).  
**Rationale:** Sprint 0 uses a Sprint-0-scoped compose (PostgreSQL, MinIO, Redis, API) created in T-02-02 — not the full 9-service stack (US-02, Sprint 1). The frontend only needs the API base URL, which the 4-service compose provides. This override is intentional and conservative; it does not pull GPU/Temporal work forward. See Sprint Reclassification §risks R2.  
**Clarification (2026-06-09 — see D-16):** "created in T-02-02" should read *introduced* in T-02-02. T-02-02 authors the Sprint-0 compose file with the **PostgreSQL** service only. The remaining Sprint-0 services are appended incrementally on the same `aimpos-spark` network by their owning tasks (MinIO by T-02-03; the API and Redis service entries by their respective Sprint-0 tasks). D-11's decision is unaffected: US-26 depends only on the API base URL, which is available once the API service entry lands — at or before the Sprint-0 exit gate, not necessarily within T-02-02.

### D-12 — Tooling pinned for the monorepo
**Date:** 2026-06-09  
**Decision:** Python uses Ruff (lint + format) and mypy; TypeScript uses ESLint + Prettier. Versions pinned in each service's `pyproject.toml` / `package.json` when introduced (US-04, US-03, US-26).  
**Rationale:** Single source of truth per coding-standards §66–73. Repository Setup declares intent; manifests land with the first code in each service.

### D-13 — Repository Setup committed as bootstrap to `main`
**Date:** 2026-06-09  
**Decision:** The monorepo skeleton (folders, `.gitkeep`, governance files, templates) is committed directly to `main` as a bootstrap commit.  
**Rationale:** Permitted by branching-strategy §73–81 for "empty repo skeleton with no application logic." All subsequent application code merges via `feature/*` PRs.

### D-14 — GitHub milestones relabeled to Sprint 0–5 + Future Release
**Date:** 2026-06-09  
**Decision:** Created milestones Sprint 0 (#10), Sprint 5 (#11), Future Release (#12); reused existing Sprint 1–4 (#6–9); reassigned all 68 issues per `Sprint Reclassification.md` via `backlog/reassign_milestones.py`. Final distribution: S0=26, S1=11, S2=6, S3=7, S4=7, S5=9, Future=2.  
**Rationale:** Single source of truth for sprint scope is the frozen reclassification. The old architectural milestones M1–M5 (#1–5) were already closed/empty and are left closed for history. Corrected an arithmetic slip in the reclassification doc: Sprint 0 is 26 issues, not 24 (T-02-02/03 belong to S0).

### D-15 — Branch protection on `main` deferred (free private plan)
**Date:** 2026-06-09  
**Decision:** Branch protection could not be enabled via API — GitHub returned 403 "Upgrade to GitHub Pro or make this repository public." The PR workflow is therefore enforced by governance convention (branching-strategy.md), not by a server-side rule, until the repo is on GitHub Pro or made public.  
**Rationale:** As a solo founder this is low risk; the bootstrap exception (D-13) already allows direct-to-`main` skeleton commits. Revisit when upgrading to Pro or when collaborators join. Re-run `backlog/protect_and_audit.py` to apply protection once the plan supports it.

### D-16 — PostgreSQL service: internal-only base, dev overlay publishes the port
**Date:** 2026-06-09
**Decision:** The Sprint-0 compose (`deploy/compose/docker-compose.yml`) runs `postgres:16-alpine` on the internal `aimpos-spark` network with no host port published; a separate `docker-compose.dev.yml` overlay publishes `5432` for local tooling. The database/user are created by the image from `.env`; `deploy/init/postgres/01-extensions.sql` enables `uuid-ossp` + `pgcrypto`. Compose project, network, and volume use explicit fixed names (`aimpos-spark`, `aimpos-postgres-data`) for deterministic verification.
**Rationale:** Satisfies T-02-02 AC ("exposes 5432 to API on internal network only") while keeping a developer escape hatch. T-02-02 is Sprint 0 but its dependency T-02-01 (full 9-service compose) is Sprint 1 per Sprint Reclassification, so this task creates a PostgreSQL-only Sprint-0 compose; later tasks (T-02-03 MinIO, API) append services to the same file. Extensions chosen for the US-04 schema's UUID primary keys. Verified by `scripts/smoke/test_postgres.py`.  
**Relationship to D-11:** This entry refines D-11's phrase "Sprint-0-scoped compose … created in T-02-02." T-02-02 *introduces* the compose file with PostgreSQL only and does not author the MinIO/Redis/API services; those are added by their own Sprint-0 tasks (MinIO = T-02-03). The multi-service Sprint-0 stack that D-11 relies on is reached by the Sprint-0 exit gate, not by T-02-02 alone. D-16 supersedes only the task-attribution clause of D-11; the rest of D-11 stands.

### D-17 — MinIO bucket bootstrap via a one-shot mc init container; bucket name is env-driven
**Date:** 2026-06-09
**Decision:** The Sprint-0 compose adds `minio` (RELEASE-pinned) on the internal `aimpos-spark` network with named volume `aimpos-minio-data`, internal-only (dev overlay publishes 9000/9001). A one-shot `minio-init` (`minio/mc`) service waits for MinIO to be healthy, then runs `deploy/init/minio/create-buckets.sh` to create the bucket idempotently and keep it private. The bucket name is read from `MINIO_BUCKET` (`.env`) — the single source of truth — and is not hardcoded anywhere.
**Rationale:** MinIO has no `/docker-entrypoint-initdb.d` hook, so a dedicated `mc` init container is the idiomatic, idempotent bootstrap. Internal-only networking mirrors D-16. Health-gated startup uses MinIO's `/minio/health/live` endpoint (curl is present in the server image). Verified by `scripts/smoke/test_minio.py`.
**Naming note (resolved 2026-06-09):** issues #46 and #56 and the T-05 tasks reference the bucket `aimpos-hot-assets`, while `.env.example` originally shipped a placeholder `aimpos-spark`. Resolved by aligning `.env.example` to `MINIO_BUCKET=aimpos-hot-assets` (the name AC2 and the T-05 asset tasks require). The bucket remains env-driven — all code must read `MINIO_BUCKET` rather than a literal — so the value can still change without code edits. The Sprint 0 plan's `aimpos-spark` mention is superseded by this alignment.

### D-18 — `projects` system-of-record column is `name`; `asset_versions` key column is `minio_key`
**Date:** 2026-06-09
**Decision:** The SQLAlchemy models (T-04-01) name the project label column **`name`** and the asset object-key column **`minio_key`**.
**Rationale:** Two planning inconsistencies were surfaced while authoring the models and resolved in favour of the higher-authority documents:
- **`name` vs `title`:** Sprint 0 plan §4.6 specifies `GET /projects` returns `{ "id", "name": "AIMPOS Spark Demo", "status" }` and the exit gate refers to the project *name*. The task cards T-01-01/T-01-03 say `title`. The Sprint plan (doc authority #4) and MVP success criteria outrank the task markdown, so the column is `name`. **Follow-up for US-01:** T-01-03 must expose the field as `name` (or map it) so the API matches the Sprint 0 plan; the task wording is stale.
- **`minio_key` vs `storage_key`:** MVP Definition §6.5 and T-04-01 AC both say `minio_key`; Sprint 0 plan §4.3 says `storage_key`. The data-model document (§6.5) is the source of truth for column names, and T-04-01's own AC agrees, so the column is `minio_key`. The Sprint 0 plan §4.3 `storage_key` mention is superseded for naming purposes.
**Scope note:** No architecture change — these are field-name reconciliations within the frozen 6-table model (MVP Definition §6.5). Recorded so US-01 (name) and US-05 (minio_key) inherit the resolved names.

### D-19 — Enum columns use portable `VARCHAR + CHECK` (`native_enum=False`), keys are app-side UUIDs
**Date:** 2026-06-09
**Decision:** Status/stage/decision/event-type columns are SQLAlchemy `Enum(..., native_enum=False)` (renders as `VARCHAR` + `CHECK` constraint, not a native PostgreSQL `ENUM` type). Primary keys are `uuid4` generated in the application; `created_at`/`updated_at` default to the DB clock (`func.now()`). A constraint **naming convention** is set on `Base.metadata` so the T-04-02 migration and all future autogenerate output have stable, reviewable names.
**Rationale:** Native PG enums are painful to migrate (every value add is a DDL dance); a checked VARCHAR keeps the enum contract while staying migration-friendly and portable (the importability test builds the schema on SQLite). App-side UUIDs avoid depending on `gen_random_uuid()` at insert time and keep the models DB-agnostic for unit tests. The enums themselves live in `packages/aimpos-core` (Sprint 0 plan §4.3) as the single source of truth shared by api and worker. Verified by `api/tests/unit/test_models_importable.py` (5 tests pass; `create_all` succeeds).

### D-20 — Migrations are generated from models; `make migrate` runs in a one-off container until the API image exists
**Date:** 2026-06-09
**Decision:** The initial Alembic migration (`0001_initial_core_tables`, T-04-02) is **autogenerated from the SQLAlchemy models** (T-04-01) against PostgreSQL and committed under `api/alembic/versions/`. `alembic/env.py` reads `DATABASE_URL` from the environment and sets `target_metadata = Base.metadata`. Because the API image does not exist until US-03/T-03-01, `make migrate` / `make migrate-down` run Alembic in a one-off `python:3.12-slim` container attached to the `aimpos-spark` network (installing the migration deps + editable `aimpos-core`); when the API image lands this becomes `docker compose run --rm api alembic <cmd>`.
**Rationale:** Generating from models keeps the migration and the ORM in lock-step (verified: Alembic `compare_metadata` reports zero drift). Reading `DATABASE_URL` directly in `env.py` is acceptable because migration tooling is not application code (the `os.getenv` ban in coding-standards §345 targets app code; settings still load via `aimpos-config` in US-03). The one-off container avoids adding a migration service to the Sprint-0 compose (no infra/scope change) while making `make migrate` work today; `DATABASE_URL`'s in-network host `postgresql:5432` resolves only inside the `aimpos-spark` network, which is why the command joins it. **Verification:** `upgrade head` creates all six tables, `downgrade base` removes them, re-`upgrade` succeeds, and the tables were confirmed in the live compose database.

### D-21 — Repositories: generic async SQLAlchemy adapter + Protocol port; caller owns the transaction
**Date:** 2026-06-09
**Decision:** T-04-03 adds one repository per aggregate root (`Project`, `PipelineRun`, `AssetVersion`, `Approval`, `AuditEvent`) under `api/app/infrastructure/db/repositories/`, built on a generic `SQLAlchemyRepository[ModelT]` and a `Repository` `Protocol` (the port). Repositories use `AsyncSession` and **`flush`, never `commit`** — the transaction boundary belongs to the caller (request scope / unit of work). Session plumbing (`session.py`) exposes pure `build_engine(url)` / `build_sessionmaker(engine)` builders with **no global engine and no env reads**; wiring to settings happens in US-03 via `aimpos-config`. `aimpos-core` ships a `py.typed` marker so its types flow to `api`/`worker` (mypy strict passes on `aimpos-core`; clean on `api`).
**Rationale:** A generic base keeps the five repositories tiny and consistent; the Protocol lets future domain/application services depend on an abstraction without importing SQLAlchemy (preserves domain purity, coding-standards §32). `flush`-not-`commit` avoids partial commits and lets `store_asset` (US-05) compose multiple writes atomically. `LineageEdge` gets no repository yet — it is a relation, not an aggregate root (added when US-14+ writes edges) — avoiding speculative scope. **Verification:** async round-trip test per repository on in-memory SQLite (`aiosqlite`) — 5/5 pass (10/10 with the model tests); `ruff` + `mypy` clean. This closes **US-04** (T-04-01/02/03 all done pending merge).

---

<!-- New decisions appended below. Do not edit prior entries; supersede with a new D-NN. -->
