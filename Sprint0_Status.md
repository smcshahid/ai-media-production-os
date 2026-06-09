# AIMPOS-Spark Visual — Sprint 0 Status

**Document Type:** Execution Tracker (living)
**Sprint:** 0 — Platform Skeleton
**Last updated:** 2026-06-09
**Sources of truth:** [Sprint 0 — Platform Skeleton.md](./Sprint%200%20%E2%80%94%20Platform%20Skeleton.md) · [Sprint Reclassification.md](./Sprint%20Reclassification.md) · [DECISIONS.md](./DECISIONS.md)

This tracker reflects build progress only. Scope, AC, and gates remain governed by the frozen planning documents.

---

## Progress summary

| Metric | Value |
|--------|------:|
| Sprint 0 issues (class A) | 26 |
| Complete | 2 |
| In progress | 6 |
| Not started | 18 |

*In progress on `feature/T-04-01-sqlalchemy-models`: US-04 + T-04-01/02/03 (committed `791a94b`, pending merge) and US-03 + T-03-01 (`/health`, committed-pending). US-03's T-03-02/03 not yet started.*

**Issue closure policy:** an issue is marked **Done** here when implementation is complete and PR-reviewed. The GitHub issue is **closed on merge to `main`** per [definition-of-done.md](./docs/governance/definition-of-done.md). "Done (pending merge)" means code + review are complete but the PR has not yet landed.

---

## Issue status

Legend: ✅ Done · 🟡 In progress · ⬜ Not started

### Backend foundation
| Issue | # | Title | Status |
|-------|---|-------|--------|
| US-04 | 4 | Database schema foundation | 🟡 All tasks done; committed `791a94b`, pending merge |
| US-03 | 5 | API health and logging | 🟡 T-03-01 done; T-03-02/03 pending |
| T-02-02 | 45 | Configure PostgreSQL volume and init scripts | ✅ Done (merged, #72) |
| T-02-03 | 46 | Configure MinIO bucket on startup | ✅ Done (pending merge) |
| T-03-01 | 53 | Implement /health with dependency probes | 🟡 Done (pending merge) |
| T-03-02 | 54 | Add structured logging middleware | ⬜ |
| T-03-03 | 55 | Request ID propagation | ⬜ |
| T-04-01 | 50 | SQLAlchemy models for core tables | 🟡 In progress (code + tests done; PR open) |
| T-04-02 | 51 | Initial Alembic migration | 🟡 In progress (migration + verify done; PR open) |
| T-04-03 | 52 | Repository layer interfaces | 🟡 Done (repos + async tests; PR open) |

### Create Project
| Issue | # | Title | Status |
|-------|---|-------|--------|
| US-01 | 8 | Create default project | ⬜ |
| FEAT-01 | 20 | Project Bootstrap | ⬜ |
| T-01-01 | 63 | Projects table migration | ⬜ |
| T-01-02 | 64 | Seed default project | ⬜ |
| T-01-03 | 65 | GET /projects endpoint | ⬜ |
| T-01-04 | 66 | Unit test project repository | ⬜ |

### Upload Asset
| Issue | # | Title | Status |
|-------|---|-------|--------|
| US-05 | 6 | MinIO asset upload service | ⬜ |
| T-05-01 | 56 | MinIO client wrapper | ⬜ |
| T-05-02 | 57 | Content-hash keys | ⬜ |
| T-05-03 | 58 | AssetVersion on upload | ⬜ |
| T-05-04 | 59 | Upload round-trip test | ⬜ |

### Login + Dashboard shell
| Issue | # | Title | Status |
|-------|---|-------|--------|
| US-25 | 17 | Bearer token auth | ⬜ |
| US-26 | 12 | Nav shell + idle routes | ⬜ |
| T-26-01 | 67 | App shell with React Router | ⬜ |
| T-26-02 | 68 | Nav bar and route guards | ⬜ |

### Governance umbrella
| Issue | # | Title | Status |
|-------|---|-------|--------|
| EPIC-06 | 42 | Governance umbrella | ⬜ (open through Sprint 5) |

---

## T-02-02 — completion record

**Issue:** #45 · **Parent:** US-02 · **Branch:** `feature/T-02-02-postgres-init`
**Status:** ✅ Done (pending merge) · **Review:** Approve with comments (resolved)

### Acceptance criteria
| AC | Result |
|----|--------|
| Named volume `aimpos-postgres-data` persists across restarts | ✅ Verified by smoke test |
| Exposes 5432 to API on internal network only | ✅ No host binding in base compose |
| Init creates DB + user matching `.env.example` | ✅ Image-created from `.env`; extensions via init script |
| `psql` connects from the api network after `up` | ✅ One-off client on `aimpos-spark` network |

### Delivered
- `deploy/compose/docker-compose.yml` — PostgreSQL service, named volume, internal `aimpos-spark` network
- `deploy/compose/docker-compose.dev.yml` — dev overlay publishing 5432
- `deploy/init/postgres/01-extensions.sql` + `README.md` — `uuid-ossp`, `pgcrypto`
- `Makefile` — `up`/`down`/`logs`/`db-shell`/`db-smoke`/`env` targets wired
- `scripts/smoke/test_postgres.py` — verifies all four AC (stdlib-only, reproducible)
- `docs/runbooks/postgres.md` — operations runbook
- `DECISIONS.md` — D-16 (with D-11 reconciliation)

### Verification
`python scripts/smoke/test_postgres.py` → PASS (all four AC), ~30s, exits 0.

### Review outcome
Approve with comments. Decision-log inconsistency (D-11 vs D-16) reconciled in `DECISIONS.md`. Remaining comments captured as technical debt below.

---

## T-02-03 — completion record

**Issue:** #46 · **Parent:** US-02 · **Branch:** `feature/T-02-03-minio-bucket`
**Status:** ✅ Done (pending merge) · **Review:** Approve with comments (resolved)

### Acceptance criteria
| AC | Result |
|----|--------|
| MinIO starts with persistent volume | ✅ `aimpos-minio-data`; object survives recreation |
| Bucket `aimpos-hot-assets` exists after first `up` | ✅ Created by `minio-init`; `.env.example` aligned to `aimpos-hot-assets` (see D-17) |
| S3 API accessible from the api network using `.env` creds | ✅ One-off `mc` over `aimpos-spark` network |
| Init script is idempotent | ✅ Re-ran init service cleanly; bucket count = 1 |

### Delivered
- `deploy/compose/docker-compose.yml` — `minio` (internal-only, healthcheck) + one-shot `minio-init` (mc); `aimpos-minio-data` volume
- `deploy/compose/docker-compose.dev.yml` — dev overlay publishing 9000/9001
- `deploy/init/minio/create-buckets.sh` + `README.md` — idempotent, env-driven bucket
- `scripts/smoke/test_minio.py` — verifies all four AC (stdlib-only, reproducible)
- `docs/runbooks/minio.md` — operations runbook
- `Makefile` — `minio-smoke` target
- `.env.example` — `MINIO_BUCKET=aimpos-hot-assets` (AC2 alignment)
- `DECISIONS.md` — D-17 (with bucket-name resolution)

### Verification
`python scripts/smoke/test_minio.py` → PASS (all four AC), ~20s, exits 0.

### Review outcome
Approve with comments. AC2 bucket-name conflict (`aimpos-spark` placeholder vs `aimpos-hot-assets`) resolved by aligning `.env.example`; recorded in D-17. Remaining items captured as technical debt below.

---

## T-04-01 — completion record

**Issue:** #50 · **Parent:** US-04 · **Branch:** `feature/T-04-01-sqlalchemy-models`
**Status:** 🟡 Done (pending review/merge) · **First application code in `api/` and `packages/`**

### Acceptance criteria
| AC | Result |
|----|--------|
| Model file(s) exist for all 6 tables | ✅ `projects`, `pipeline_runs`, `asset_versions`, `approvals`, `audit_events`, `lineage_edges` |
| `asset_versions` includes `stage`, `version`, `minio_key`, `content_hash`, `is_ai_generated`, `branch` | ✅ Verified by `test_asset_versions_required_columns` |
| FKs and indexes for `pipeline_run_id`, `project_id` | ✅ Verified by `test_foreign_keys_and_indexes_present` |
| Models importable without circular dependency errors | ✅ Import + `create_all` on SQLite pass (5/5 tests) |

### Delivered
- `packages/aimpos-core/` — first shared package: enums (`PipelineStage`, `PipelineRunStatus`, `AssetStage`, `ProjectStatus`, `ApprovalDecision`) + `events/AuditEventType`, `pyproject.toml`
- `api/pyproject.toml` — api service manifest (FastAPI, SQLAlchemy 2.0, Alembic, asyncpg/psycopg, Pydantic; Ruff/mypy/pytest dev) per D-12; majors pinned
- `api/app/infrastructure/db/base.py` — `DeclarativeBase` + constraint naming convention + `uuid_pk`/`created_at` helpers
- `api/app/infrastructure/db/models/` — 6 ORM models + aggregating `__init__` (full `Base.metadata`)
- `api/tests/unit/test_models_importable.py` — 5 tests (schema completeness, AC columns, FK/index, SQLite build)
- `.gitignore` — Python tooling artifacts (`.pytest_cache`, `*.egg-info`, caches)
- `DECISIONS.md` — D-18 (name/minio_key reconciliation), D-19 (enum/UUID/migration strategy)

### Verification
`pytest api/tests/unit/test_models_importable.py` → 5 passed. `ruff check` clean; `ruff format --check` clean.

### Self-review notes
- Domain purity preserved: SQLAlchemy lives only in `api/app/infrastructure/db/` (coding-standards §32-33); `api/app/domain/` not touched.
- Shared enums in `aimpos-core` (not duplicated in api) per Sprint 0 plan §4.3.
- `pipeline_runs.temporal_workflow_id` added as **nullable** forward-field (TD-10) — bound in US-07.
- Migration (T-04-02) and repositories (T-04-03) are the remaining US-04 tasks; not in this PR.

---

## T-04-02 — completion record

**Issue:** #51 · **Parent:** US-04 · **Branch:** `feature/T-04-01-sqlalchemy-models`
**Status:** 🟡 Done (pending review/merge) · Builds directly on T-04-01

### Acceptance criteria
| AC | Result |
|----|--------|
| `alembic upgrade head` creates all 6 tables on empty DB | ✅ Verified on PostgreSQL 16 (compose + throwaway) |
| `alembic downgrade -1` rolls back cleanly on empty DB | ✅ `downgrade base` removes all tables; re-upgrade succeeds |
| Migration committed under `api/alembic/versions/` | ✅ `0001_initial_core_tables.py` |
| Documented in README: `make migrate` | ✅ `api/README.md` + `docs/runbooks/migrations.md`; `make migrate`/`migrate-down` wired |

### Delivered
- `api/alembic.ini` — URL via `DATABASE_URL`; ruff post-write hook
- `api/alembic/env.py` — `target_metadata = Base.metadata`; online/offline; `compare_type`/`compare_server_default`
- `api/alembic/script.py.mako` — typed template matching repo style
- `api/alembic/versions/0001_initial_core_tables.py` — autogenerated from models, reviewed; 6 tables, FKs, indexes, unique + enum CHECK constraints, JSONB variant, named per D-19
- `Makefile` — `migrate` (`upgrade head`) + `migrate-down` (`downgrade -1`) via one-off container on `aimpos-spark` network
- `api/README.md`, `docs/runbooks/migrations.md` — migration docs
- `DECISIONS.md` — D-20

### Verification
Autogenerate **NO_DRIFT** vs models; `upgrade head` → 6 tables (+ `alembic_version`) confirmed in the live compose DB via `psql \dt`; `downgrade base` clean; `make migrate` recipe run against the real Sprint-0 stack (exit 0). `ruff check` + `format --check` clean.

### Self-review notes
- Migration is generated from the T-04-01 models (single source of truth) — no hand-drift.
- Resolves TD-05's sibling: `make migrate` is no longer a stub. (`logs-api` stub remains, TD-05.)
- Remaining US-04 task: **T-04-03** (repository interfaces) — not in scope here.

---

## T-04-03 — completion record (closes US-04)

**Issue:** #52 · **Parent:** US-04 · **Branch:** `feature/T-04-01-sqlalchemy-models`
**Status:** 🟡 Done (pending review/merge) · Completes US-04 (T-04-01/02/03)

### Acceptance criteria
| AC | Result |
|----|--------|
| Repository interfaces in `api/app/infrastructure/db/repositories/` | ✅ `Repository` Protocol + `SQLAlchemyRepository` base + 5 concrete repos |
| CRUD / query methods per aggregate root | ✅ add/get/list + `list_active`, `list_for_project`, `next_version`, `list_for_run`, `append` |
| Async SQLAlchemy session pattern | ✅ `AsyncSession`; `session.py` async engine/sessionmaker builders |
| ≥1 smoke test instantiates each repository against a test DB | ✅ 5 async round-trip tests on `aiosqlite` (all repos) |

### Delivered
- `api/app/infrastructure/db/session.py` — pure async engine/sessionmaker builders (no globals, no env reads)
- `api/app/infrastructure/db/repositories/` — `base.py` (Protocol + generic), `project.py`, `pipeline_run.py`, `asset_version.py`, `approval.py`, `audit_event.py`, `__init__.py`
- `api/tests/conftest.py` — hermetic in-memory async DB fixture
- `api/tests/integration/test_repositories.py` — per-repository round-trip tests
- `api/pyproject.toml` — `aiosqlite` dev dep
- `packages/aimpos-core/aimpos_core/py.typed` — PEP 561 marker (types now flow to api/worker)
- `DECISIONS.md` — D-21

### Verification
`pytest` → **10 passed** (5 model + 5 repository). `ruff check` + `format --check` clean (35 files). `mypy` strict clean on `aimpos-core`; clean on `api/app`.

### Self-review notes
- Repositories `flush`, not `commit` — caller owns the transaction (enables US-05 atomic `store_asset`).
- `Repository` Protocol keeps domain free to depend on the port, not SQLAlchemy (domain purity).
- No `LineageEdgeRepository` yet — `lineage_edges` is a relation, not an aggregate root; added when US-14+ writes edges (TD-13).
- **US-04 is complete** (all three tasks). Unblocks US-01 (seed/repo), US-03 (`/health` DB probe), US-05 (asset storage).

---

## T-03-01 — completion record (opens US-03)

**Issue:** #53 · **Parent:** US-03 · **Branch:** `feature/T-04-01-sqlalchemy-models`
**Status:** 🟡 Done (pending review/merge) · First running API service + `aimpos-config`

### Acceptance criteria
| AC | Result |
|----|--------|
| `GET /health` reports postgresql, minio, redis status | ✅ Three concurrent probes; per-dependency `{status, detail}` block |
| Returns 200 when all dependencies reachable | ✅ Live stack → `{"status":"healthy", ...}` HTTP 200 |
| Failed dependency returns 503 | ✅ Stopped PostgreSQL → `postgresql: error`, HTTP 503; recovers to 200 on restart |
| Endpoint registered in OpenAPI schema | ✅ `test_health_is_registered_in_openapi` (200 + 503 shapes) |

*Note: US-03 AC also lists structured JSON logs + `temporal`. Logs are **T-03-02/03**; `temporal`/`ollama` join `/health` in Sprint 1 (Sprint 0 plan §4.6). The response shape already supports adding probes.*

### Delivered
- `packages/aimpos-config/` — new shared package: Pydantic `Settings` (env/`.env`, no `os.getenv` in app code) + minimal JSON `configure_logging`; `py.typed`
- `api/app/main.py` — `create_app()` factory + lifespan owning DB engine / Redis / HTTP client on `app.state`
- `api/app/dependencies.py` — DI providers + `get_health_checks` (overridable in tests)
- `api/app/routes/health.py` — `GET /health` (200/503 + OpenAPI)
- `api/app/infrastructure/health/probes.py` — `check_postgres` / `check_redis` / `check_minio` (timeout-bounded, never raise)
- `api/app/infrastructure/cache/redis_client.py` — pure async Redis builder
- `api/Dockerfile` — repo-root build context; installs local `packages/*` + api; non-root
- `deploy/compose/docker-compose.yml` — `redis` + `api` services (internal, health-gated); dev overlay publishes `6379` + `API_PORT`
- `api/pyproject.toml` — `aimpos-config`, `redis`, `httpx`; `flake8-bugbear` immutable-calls for FastAPI DI
- `Makefile` — `logs-api` (resolves TD-05), `health` targets
- `api/tests/unit/test_health.py` — 6 tests (route 200/503/OpenAPI + offline probe tests)
- `DECISIONS.md` — D-22

### Verification
`pytest` → **16 passed** (10 prior + 6 health). `ruff check` + `format --check` clean (37 files); `mypy` strict clean on `aimpos-config`, clean on `api/app` (27 files). **Live:** `make up-dev` (build) → all 4 services healthy; `GET /health` = **200** (postgres/redis/minio ok) and the `api` container's own healthcheck passes; `stop postgresql` → **503** (`postgresql: error`); `start postgresql` → back to **200**.

### Self-review notes
- Resolves **TD-05** (`logs-api` is real). `make migrate` still uses the one-off container (D-20) — not switched to the api image yet because the wheel excludes `alembic/` (TD-17).
- Probes are reachability-only by design; full MinIO client is US-05, logging middleware is T-03-02.
- Corrects the stale **#53 → T-02-01** dependency edge (see D-22 / Planning notes below).

---

## Technical debt register

Identified during the T-02-02 PR review. Items with a follow-up issue are tracked in the backlog; minor items are noted here for awareness.

| ID | Item | Severity | Disposition |
|----|------|----------|-------------|
| TD-01 | `env_file` injects all repo secrets into the PostgreSQL container (not least-privilege) | Low | Follow-up #69 |
| TD-02 | Smoke test is non-hermetic — operates on the dev stack/volume and bounces containers | Low | Follow-up #70 |
| TD-03 | Smoke test writes a real `.env` into the working tree when absent | Low | Follow-up #70 |
| TD-04 | `pgcrypto` is speculative for Sprint 0 (`gen_random_uuid()` is built-in on PG13+; lineage/audit is Future Release) | Low | Accepted for now; revisit if unused by US-04 |
| TD-05 | `Makefile` `logs-api` is a stub until the API service joins the compose | Trivial | ✅ Resolved in T-03-01 (`logs-api` tails the api service) |
| TD-06 | Root `README.md` lacks the Sprint-0 service port map required by the Phase A DoD | Low | Follow-up #71 |
| TD-07 | `minio` uses blanket `env_file` (same least-privilege smell as TD-01) | Low | Broaden #69 to all compose services |
| TD-08 | `test_minio.py` shares the dev stack/volume (same non-hermetic gap as TD-02) | Low | Broaden #70 to all smoke tests |
| TD-09 | `#46` carries a stale `sprint:s1` label and the tasks markdown still says "Sprint 1" (live milestone is Sprint 0) | Trivial | Doc/label drift; same as T-02-02 |
| TD-10 | `pipeline_runs.temporal_workflow_id` is a nullable forward-looking column with no writer until US-07 (Sprint 2) | Low | Intentional; keeps the run table stable per Sprint 0 plan §4.3 ("tables must be correct before data exists"). Populated by US-07 |
| TD-11 | Enum columns are app-validated `VARCHAR + CHECK`; no DB-native enum type and no DB-level append-only guard on `audit_events`/`approvals` (immutability is by domain rule only, per Sprint 0 plan §4.3) | Low | Accepted for MVP; revisit if a DB trigger is wanted post-MVP |
| TD-12 | `#50` / T-04-01 task card says `sprint:s1` + location `api/app/...` while milestone is Sprint 0 — same label/milestone drift as TD-09 | Trivial | Doc/label drift |
| TD-13 | No `LineageEdgeRepository` yet (lineage_edges has a model + migration but no repo) | Low | Intentional — not an aggregate root; add when US-14+/US-20 write/read lineage |
| TD-14 | Repository tests run on SQLite (`aiosqlite`), not PostgreSQL — JSONB/edge SQL not exercised at unit level | Low | Hermetic by design; covered by compose integration tests later (relates to TD-02/08) |
| TD-15 | `api` dev overlay publishes the port but does **not** mount source for hot-reload (image installs the package non-editable) | Low | DX-only; add an editable/`--reload` dev image when iteration speed warrants |
| TD-16 | A down-PostgreSQL `/health` probe reports `detail: ""` (psycopg `OperationalError` str is sometimes empty) — status is correctly `error` but the message is unhelpful | Trivial | Cosmetic; improve probe error formatting (use `repr`/type name fallback) in T-03-02 |
| TD-17 | `make migrate` still runs in a one-off container; not switched to `docker compose run --rm api alembic` because the api wheel excludes `alembic/` | Low | Switch when the image ships migrations (copy `alembic/` into the image or add a console entrypoint); supersedes the D-20 follow-up |
| TD-18 | `api` service uses blanket `env_file: .env` (same least-privilege smell as TD-01/07) | Low | Broaden #69 to the api service |

---

## Follow-up backlog items (recorded, not implemented)

| # | Title | Milestone | Labels |
|---|-------|-----------|--------|
| [#69](https://github.com/smcshahid/ai-media-production-os/issues/69) | Harden PostgreSQL service env (least-privilege, drop blanket `env_file`) | Sprint 1 | tech-debt, devops |
| [#70](https://github.com/smcshahid/ai-media-production-os/issues/70) | Isolate PostgreSQL smoke test from the dev stack (ephemeral project/volume) | Sprint 1 | tech-debt, devops, test |
| [#71](https://github.com/smcshahid/ai-media-production-os/issues/71) | Add Sprint-0 service port map to README | Sprint 1 | tech-debt, docs |

## Planning inconsistencies discovered (T-04-01)

- **`projects.name` vs `title`:** Sprint 0 plan §4.6 (`GET /projects` → `name`) and the exit gate conflict with T-01-01/T-01-03 task cards (`title`). Resolved to **`name`** (higher doc authority) in D-18. **Action for US-01:** align T-01-03 API field to `name` (no model change needed).
- **`asset_versions.minio_key` vs `storage_key`:** MVP Definition §6.5 and T-04-01 AC say `minio_key`; Sprint 0 plan §4.3 DoD says `storage_key`. Resolved to **`minio_key`** in D-18. **Action for US-05:** `store_asset()` must populate `minio_key`.
- Neither requires an SCR — both are field-name reconciliations inside the frozen 6-table model.

## Planning notes (for when the owning issue begins)

- **Sprint-0 compose service ownership — ✅ DONE in T-03-01:** the **API** and **Redis** service entries were added to the Sprint-0 compose by T-03-01 (D-22), as planned. No new task was needed.
- **T-03-01 dependency inconsistency — ✅ RESOLVED in T-03-01 (D-22):** the stale `#53 → T-02-01` (full 9-service compose, Sprint 1) edge is corrected. The effective Sprint-0 prerequisite is "Sprint-0 compose exists"; T-03-01 added the `redis`/`api` services it needs, and `/health` requires **no** migration (probe is `SELECT 1`).

---

## Document control

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-09 | Initial Sprint 0 status; T-02-02 complete; tech-debt register; follow-ups #69–#71 |
| 1.1 | 2026-06-09 | T-04-01 (SQLAlchemy models) done pending review; first `api/` + `aimpos-core` code; D-18/D-19; TD-10–12; name/minio_key inconsistencies recorded |
| 1.2 | 2026-06-09 | T-04-02 (initial Alembic migration) done pending review; `make migrate`/`migrate-down` wired; migrations runbook; D-20; verified on PostgreSQL 16 (no drift) |
| 1.3 | 2026-06-09 | T-04-03 (repositories) done pending review — **closes US-04**; async repos + Protocol port; `py.typed`; D-21; TD-13/14; 10 tests + ruff + mypy clean |
| 1.4 | 2026-06-09 | US-04 committed (`791a94b`); **T-03-01 (`/health`) done** — opens US-03; `aimpos-config` + app factory + probes + api/redis compose services + Dockerfile; D-22; TD-05 resolved, TD-15–18; 16 tests + ruff + mypy clean; live 200/503 verified |
