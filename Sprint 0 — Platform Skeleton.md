# AIMPOS-Spark Visual — Sprint 0: Platform Skeleton

**Document Type:** Sprint Planning  
**Version:** 1.1  
**Status:** FROZEN — Effective June 9, 2026  
**Date:** June 9, 2026  
**Sprint:** 0 — Platform Skeleton  
**Codename:** `AIMPOS-Spark-Visual`  
**Audience:** Solo founder working evenings and weekends  
**Tooling:** Claude Code + Cursor + Docker Desktop → Olares One  
**Parent Documents:**

- [MVP Scope Freeze.md](./MVP%20Scope%20Freeze.md)
- [GitHub Issues - Visual MVP.md](./GitHub%20Issues%20-%20Visual%20MVP.md)
- [Repository Structure.md](./Repository%20Structure.md)
- [Sprint Reclassification.md](./Sprint%20Reclassification.md)
- [Architecture Freeze Review.md](./Architecture%20Freeze%20Review.md)
- [docs/governance/definition-of-done.md](./docs/governance/definition-of-done.md)
- [docs/governance/development-workflow.md](./docs/governance/development-workflow.md)

---

## Table of Contents

1. [Sprint Objective](#1-sprint-objective)
2. [Success Criteria](#2-success-criteria)
3. [Issue Assignment](#3-issue-assignment)
4. [Deliverables](#4-deliverables)
5. [Sprint 0 Timeline](#5-sprint-0-timeline)
6. [Decisions Log](#6-decisions-log)
7. [Hard Gates](#7-hard-gates)
8. [Risk Register](#8-risk-register)
9. [Sprint 0 Exit Gate](#9-sprint-0-exit-gate)
10. [Impact on Sprint 1](#10-impact-on-sprint-1)
11. [Document Control](#11-document-control)

---

## 1. Sprint Objective

> Prove that the platform exists. By the end of Sprint 0, a human evaluator can open a browser, authenticate, navigate to the default project, upload a file, and see the dashboard — without touching a CLI, without any AI pipeline running, and without any workflow started.

The AI pipeline (Idea → Story → Script → Storyboard) does **not** start in Sprint 0. Sprint 0 delivers the ground it will run on.

**Sprint 0 is not:**

- A planning-only sprint with no code
- An infrastructure-only sprint with no user-facing deliverable
- A sprint that includes Temporal workflow or AI agent integration

**Sprint 0 is:**

- A risk-elimination and platform-validation sprint
- The first independently demo-able milestone
- The prerequisite for Sprint 1 (Pipeline Orchestration)

---

## 2. Success Criteria

Sprint 0 is complete when all four of the following are true simultaneously — end-to-end, in sequence, in a browser:

| # | Capability | Verified when |
|---|------------|---------------|
| 1 | **Login** | User enters a token on the login screen; API validates it; dashboard loads |
| 2 | **Create Project** | Dashboard displays the seeded "AIMPOS Spark Demo" project with status `ACTIVE` |
| 3 | **Upload Asset** | User uploads a file via the Assets screen; file appears in the version list with a content hash |
| 4 | **View Dashboard** | Dashboard renders the 4-stage pipeline stepper in idle state with the project name visible |

These four capabilities must work together in one session. Testing them in isolation is insufficient for Sprint 0 sign-off.

---

## 3. Issue Assignment

Per [Sprint Reclassification.md](./Sprint%20Reclassification.md) (conservative). GitHub milestones were relabeled to Sprint 0–5 + Future Release on 2026-06-09 and all 68 issues reassigned (see `backlog/reassign_milestones.py`).

### 3.1 Issues assigned to Sprint 0 (26 total)

| Issue | Was | Sprint 0 deliverable |
|-------|-----|----------------------|
| US-01 | Sprint 1 | Create Project |
| US-03 | Sprint 1 | Basic Backend |
| US-04 | Sprint 1 | Database Setup |
| US-05 | Sprint 1 | Asset Storage |
| US-25 | Sprint 2 | Authentication (Login) |
| US-26 | Sprint 2 | Basic Frontend (nav shell) |
| FEAT-01 | Sprint 1 | Project Bootstrap |
| EPIC-06 | Sprint 1–5 | Governance umbrella (opens) |
| T-01-01 – T-01-04 | Sprint 1 | Project tasks |
| T-02-02, T-02-03 | Sprint 1 | Core Docker (PostgreSQL, MinIO) |
| T-03-01 – T-03-03 | Sprint 1 | Health and logging |
| T-04-01 – T-04-03 | Sprint 1 | Schema and repositories |
| T-05-01 – T-05-04 | Sprint 1 | Asset storage tasks |
| T-26-01, T-26-02 | Sprint 2 | App shell and nav |

### 3.2 Issues explicitly not in Sprint 0 (moved later)

| Issue | Recommended sprint | Reason |
|-------|-------------------|--------|
| US-02 | Sprint 1 (B) | Full 9-container Olares deploy |
| US-06 | Sprint 1 (B) | GPU kill check — not needed for browser skeleton |
| US-10 | Sprint 2 (C) | Full AC requires running workflow (US-07) |
| FEAT-16 | Sprint 2 (C) | Live polling dashboard |

Sprint 1 (Infrastructure Validation) begins after Sprint 0 exit gate passes. Sprint 2 (Workflow Foundation) begins after Sprint 1 GPU gate passes.

---

## 4. Deliverables

### 4.1 Repository Setup

#### Why it belongs in Sprint 0

There is no Sprint 0 without a repository. Every other deliverable — Docker files, database models, API code, frontend — lives here. The folder structure also enforces the service boundary rules that prevent architectural drift for the remaining 34 issues. Establishing it in one deliberate act on Day 1 costs 2–3 hours and saves recurring re-work throughout the entire product.

Repository setup also includes the governance artifacts that Sprint 0 depends on: branch protection, milestone labels, the PR template, and `DECISIONS.md`. These are not administrative overhead — they are the guardrails that keep Claude Code and Cursor output within bounds.

#### Dependencies

None. This is the first action of the sprint, with no predecessors.

#### Estimated effort

**2–3 hours** (Day 1, Monday of Week 1)

The monorepo structure is fully designed in [Repository Structure.md](./Repository%20Structure.md). Claude Code can generate the skeleton in minutes. The founder's time goes into: verifying folder names against the approved structure, configuring branch protection on GitHub, importing labels and milestones, and creating `DECISIONS.md` with its first entry (D-01: local Docker first).

#### Definition of Done

- [ ] Repository `aimpos-spark-visual` exists on GitHub with `main` as the default branch
- [ ] Branch protection on `main`: no direct push; PRs required
- [ ] Folder structure matches Repository Structure.md §3 (all top-level folders present: `api/`, `worker/`, `web/`, `packages/`, `configs/`, `deploy/`, `scripts/`, `tests/`, `docs/`)
- [ ] `.gitignore` covers Python bytecode, `node_modules`, `.env`, and `__pycache__`
- [ ] `.env.example` exists at repo root with placeholder values for all Sprint 0 services
- [ ] `Makefile` exists with `up`, `down`, `migrate`, and `logs-api` targets
- [ ] `README.md` at repo root describes prerequisites and `make up` quick start
- [ ] GitHub milestones created: Sprint 0, Sprint 1, Sprint 2, Sprint 3, Sprint 4
- [ ] GitHub labels imported: all labels from GitHub Issues - Visual MVP.md plus `sprint:s0`
- [ ] Sprint 0 issues (US-02, US-04, US-03, US-01, US-05, US-06, US-25, US-26, US-10) opened and assigned to Sprint 0 milestone
- [ ] `DECISIONS.md` created at repo root; D-01 recorded (local Docker Desktop for Week 1 development)
- [ ] PR template created at `.github/PULL_REQUEST_TEMPLATE.md` per development-workflow governance

---

### 4.2 Docker Setup

#### Why it belongs in Sprint 0

Docker Compose is the runtime for everything in Sprint 0. The database, API, MinIO, and frontend all run inside it. A developer cannot verify a single line of application code without containers running. Docker Setup is therefore not a feature — it is the execution environment, and it must be complete and verified before any other verification can happen.

Docker Setup in Sprint 0 has two distinct phases that must not be conflated:

**Phase A — Core infrastructure** (Week 1): PostgreSQL, MinIO, Redis, and the API container. These are needed to close US-02, US-04, US-03, US-01, US-05.

**Phase B — GPU and AI validation** (Week 2): Ollama, ComfyUI, Temporal, and the Worker stub. This is the US-06 kill check. It does not block any Sprint 0 success criteria (Login, Create Project, Upload Asset, View Dashboard), but it must be resolved before Sprint 1 begins, because Sprint 1 depends on Temporal and the AI path.

Separating these two phases within Sprint 0 prevents the GPU risk from blocking the Platform Skeleton delivery.

#### Dependencies

- Repository Setup (Dockerfile paths, `.env.example`, folder structure must exist)

#### Estimated effort

| Phase | Hours | Notes |
|-------|-------|-------|
| Phase A (core infra) | 4–6 h | AI generates compose file; founder configures Olares volume paths and port mappings |
| Phase B (GPU validation) | 4–8 h | Highest-variance item; Saturday deep-work block required |
| **Total** | **8–14 h** | Across Weeks 1 and 2 |

#### Definition of Done

**Phase A — Core infrastructure (required before Week 2 begins):**

- [ ] `deploy/compose/docker-compose.yml` defines services: `postgresql`, `minio`, `redis`, `api`
- [ ] `deploy/compose/docker-compose.dev.yml` adds bind-mounts for `api/app/` hot reload
- [ ] `deploy/init/postgres/01-extensions.sql` applies `uuid-ossp` extension on first start
- [ ] `deploy/init/minio/create-buckets.sh` creates the `aimpos-spark` bucket on first start
- [ ] `make up` starts all four Phase A services; all reach healthy state within 3 minutes
- [ ] No service requires manual intervention after `make up`
- [ ] Port map documented in `README.md`: API (8000), PostgreSQL (5432), MinIO (9000/9001), Redis (6379)

**Phase B — GPU and AI validation (Sprint 1 — not Sprint 0 exit gate):**

- [ ] `deploy/compose/docker-compose.yml` extended with: `ollama`, `comfyui`, `temporal`, `worker` (stub)
- [ ] `scripts/smoke/test_ollama.py` runs and produces a text response in < 30 seconds; zero network egress to public internet during test
- [ ] `scripts/smoke/test_comfyui.py` runs and writes a PNG file to the MinIO `aimpos-spark` bucket
- [ ] Sequential GPU test: Ollama invoked, then unloaded, then ComfyUI invoked — no OOM error observed
- [ ] D-02 (Ollama model selection) recorded in `DECISIONS.md` with chosen model and VRAM justification
- [ ] D-03 (ComfyUI workflow JSON) recorded; workflow file pinned under `configs/comfyui/workflows/`
- [ ] D-08 (GPU sequencing rule) recorded: never run Ollama and ComfyUI concurrently; documented in `worker/README.md`
- [ ] If Phase B fails after 2 remediation attempts: stub protocol invoked, documented in US-06 GitHub issue, and Sprint 0 proceeds with placeholder PNG path acknowledged as known limitation

**Failure protocol for Phase B:** Phase B is **Sprint 1** work (US-02, US-06, T-06-*). It does not block Sprint 0 sign-off. Sprint 0 uses a 4-service compose (PostgreSQL, MinIO, Redis, API) only.

---

### 4.3 Database Setup

#### Why it belongs in Sprint 0

Every Sprint 0 success criterion touches the database. Login reads the auth configuration. Create Project reads the `projects` table. Upload Asset writes to `asset_versions`. View Dashboard reads project and pipeline state. Without a schema, none of these can be implemented or verified.

Database Setup also establishes the migration discipline. The Alembic migration applied in Sprint 0 is the first entry in the audit trail of all schema changes. Getting this right once — with a clean initial migration and a passing rollback test — means every future migration follows a proven pattern.

The schema designed in Sprint 0 must be stable for the Platform Skeleton. It does not need to be the complete final schema, but any table used by Sprint 0 features must be correct, because future migrations cannot alter tables that already have production data in them once deployment begins.

#### Dependencies

- Docker Setup — Phase A (PostgreSQL must be running before `alembic upgrade head` can execute)
- Repository Setup (Alembic configuration files must exist at correct paths)

#### Estimated effort

**2–4 hours** (Wednesday of Week 1)

Claude Code generates SQLAlchemy models and the Alembic migration. The founder's time goes into verifying the 6-table schema against MVP Definition.md §6.5 and confirming column names match the domain model — because AI-generated schema names are a frequent source of drift.

#### Definition of Done

- [ ] `api/alembic.ini` and `api/alembic/env.py` configured against the `DATABASE_URL` environment variable
- [ ] Initial migration creates all 6 tables: `projects`, `pipeline_runs`, `asset_versions`, `approvals`, `audit_events`, `lineage_edges`
- [ ] `alembic upgrade head` runs without error on a blank PostgreSQL database
- [ ] `alembic downgrade -1` runs without error (rollback verified)
- [ ] Table names and primary key conventions match Repository Structure.md §4.4 SQLAlchemy model paths
- [ ] `projects` table includes at minimum: `id` (UUID), `name`, `status` (ACTIVE/ARCHIVED), `created_at`
- [ ] `asset_versions` table includes at minimum: `id`, `project_id` (FK), `stage`, `content_hash`, `storage_key`, `is_ai_generated`, `created_at`
- [ ] `audit_events` table is append-only by convention (no UPDATE or DELETE on this table — enforced by domain rule, not DB constraint in MVP)
- [ ] Migration file is the only source of truth for schema — no `CREATE TABLE` statements in application code
- [ ] `packages/aimpos-core/aimpos_core/enums/` contains `PipelineStage` and `AssetStage` enums matching the table constraints
- [ ] US-04 acceptance criteria verified and issue closable

---

### 4.4 Asset Storage

#### Why it belongs in Sprint 0

"Upload Asset" is one of the four Sprint 0 success criteria. Asset storage is the infrastructure behind it. Without MinIO configured, without a versioned asset record written to the database, and without a content-hash object key strategy in place, the Upload Asset capability cannot be demonstrated end-to-end.

Asset storage also establishes the versioning contract that the entire MVP depends on. Every AI output in Sprint 1–4 (story, script, storyboard frames) will be written through this same `store_asset()` path. The storage key scheme, the content-hash strategy, and the `asset_versions` record format must be correct before the first production upload, because changing them later means migrating both the database and the MinIO bucket.

#### Dependencies

- Docker Setup — Phase A (MinIO must be running; `aimpos-spark` bucket must exist)
- Database Setup (`asset_versions` table must exist)
- Repository Setup (folder `api/infrastructure/storage/` must exist)

#### Estimated effort

**3–5 hours** (Monday of Week 2)

Claude Code generates the MinIO client wrapper. The founder's time goes into: choosing the object key scheme (content-hash vs project/stage/timestamp), configuring bucket policy (private, no public access), and writing the round-trip integration test (upload → download → SHA-256 match).

#### Definition of Done

- [ ] `api/infrastructure/storage/minio_client.py` implements `store_asset(content: bytes, stage: str, project_id: UUID) → AssetVersion`
- [ ] Object key uses content-addressable scheme: `{project_id}/{stage}/{sha256_hash}` — deterministic, deduplicated
- [ ] `store_asset()` creates an `asset_versions` record in PostgreSQL atomically with the MinIO write (or compensates on failure)
- [ ] `store_asset()` sets `is_ai_generated = False` for human uploads; `True` is reserved for agent outputs
- [ ] `GET /assets` API endpoint returns the list of `asset_versions` for the current project, ordered by `created_at` descending
- [ ] Round-trip integration test passes: upload 1KB test file → download → SHA-256 hash matches original
- [ ] MinIO bucket policy is private; no public access configured
- [ ] US-05 acceptance criteria verified and issue closable

---

### 4.5 Authentication

#### Why it belongs in Sprint 0

"Login" is the first of the four Sprint 0 success criteria and the gateway to all others. Without authentication, none of the subsequent user flows (project view, asset upload, dashboard) can be validated as protected. Including authentication in Sprint 0 also establishes the API contract that all future Sprint 1+ endpoints will inherit — every route built in Sprint 1 through 4 will depend on the auth middleware being in place and trusted.

Keycloak is deferred. The MVP Scope Freeze is explicit: auth in the MVP is a Bearer API token. Sprint 0 implements exactly this — not a simulated stub, not a TODO, but a working token validation that the frontend sends and the API enforces. The scope creep risk to avoid is treating "Login = Keycloak" which would introduce weeks of work not in scope.

The login screen in the frontend is a lightweight form: enter token → validate against API → store in browser → redirect to dashboard. This is the complete Login flow for Sprint 0.

#### Dependencies

- Repository Setup (`api/middleware/auth.py` path must exist; `packages/aimpos-config/` must be scaffolded)
- Basic Backend (FastAPI app must be running; middleware must register before routes)

#### Estimated effort

**2–4 hours** (Week 2 backend + Week 3 frontend login page)

| Component | Hours |
|-----------|-------|
| Backend middleware | 1–2 h |
| Frontend login page | 1–2 h |

#### Definition of Done

**Backend (auth middleware):**

- [ ] `api/middleware/auth.py` implements Bearer token validation against `AIMPOS_API_TOKEN` environment variable
- [ ] All API routes except `/health` return `401 Unauthorized` when the token is absent or invalid
- [ ] `/health` endpoint is explicitly exempt from auth (required for Docker health checks and monitoring)
- [ ] `401` response body is consistent: `{ "detail": "Unauthorized" }`
- [ ] Token is read from `Authorization: Bearer <token>` header only — no query parameter fallback
- [ ] `AIMPOS_API_TOKEN` documented in `.env.example` with a placeholder value
- [ ] D-09 recorded in `DECISIONS.md`: token strategy confirmed as env var for Sprint 0; Keycloak migration path noted for Phase 1

**Frontend (login page):**

- [ ] Login page renders at `/login` route; accessible when no token is stored
- [ ] Token input field accepts the value; submit sends `GET /health` with the token to validate
- [ ] On valid token: stored in `localStorage`; user redirected to `/` (Dashboard)
- [ ] On invalid token (401): error message shown; token not stored
- [ ] `api/client.ts` attaches `Authorization: Bearer <token>` header to all requests automatically
- [ ] Authenticated routes redirect to `/login` if no token is present in `localStorage`
- [ ] US-25 acceptance criteria verified and issue closable

---

### 4.6 Basic Backend

#### Why it belongs in Sprint 0

The backend is the contract surface between the database and the frontend. Three of the four Sprint 0 success criteria depend on API responses: Create Project (`GET /projects`), Upload Asset (`POST /assets`), and View Dashboard (`GET /pipeline/status`). Without the backend, the frontend has nothing to call and the success criteria cannot be verified.

The backend in Sprint 0 is intentionally minimal. It provides health, project listing, asset upload, and the dashboard status endpoint — nothing more. It must not include pipeline start, approve, or Temporal workflow logic. Those belong to Sprint 1. The risk to manage is Claude Code or Cursor scaffolding too much — generating the full route set including pipeline endpoints. Every route not needed for Sprint 0 success criteria should be stubbed with `501 Not Implemented` or deferred.

The health endpoint is both a user-facing diagnostic and a Docker health check. It must report the status of every downstream dependency so that infrastructure failures are immediately visible.

#### Dependencies

- Repository Setup (FastAPI app structure, `packages/aimpos-core`, `packages/aimpos-config` must exist)
- Docker Setup — Phase A (all four infra containers must be running when the API starts)
- Database Setup (schema must exist before seed runs on startup)

#### Estimated effort

**4–7 hours** (distributed across Week 1: Saturday main block + Tuesday/Wednesday partial sessions)

Claude Code generates the FastAPI app factory, middleware registration, dependency injection, and route scaffolding. Founder's time: reviewing route shape against OpenAPI expectations, validating the health check dependency list, verifying the project seed runs idempotently (no duplicate rows on restart), and confirming domain module boundaries (no SQLAlchemy imports inside `api/domain/`).

#### Definition of Done

- [ ] `api/app/main.py` is a FastAPI app factory; does not contain inline route definitions
- [ ] `GET /health` returns `200 OK` with JSON body listing status of: `postgresql`, `minio`, `redis` (and `temporal` + `ollama` once Phase B completes)
- [ ] `GET /health` returns `503 Service Unavailable` if any critical dependency is unreachable — allows Docker health check to fail correctly
- [ ] `packages/aimpos-config/aimpos_config/settings.py` loads all environment variables via Pydantic Settings; no `os.getenv()` calls in application code
- [ ] `packages/aimpos-config/aimpos_config/logging.py` emits structured JSON logs with `request_id` per request
- [ ] `GET /projects` returns the seeded project: `{ "id": "...", "name": "AIMPOS Spark Demo", "status": "ACTIVE" }`
- [ ] Default project is seeded on startup from `api/seed/default_project.py` — idempotent (no duplicate on restart)
- [ ] `api/domain/studio/` contains project domain logic with no FastAPI or SQLAlchemy imports
- [ ] `api/infrastructure/db/repositories/` contains the SQLAlchemy repository implementations
- [ ] API service boundary rule enforced: `api/` never calls Ollama, ComfyUI, or Temporal activities directly
- [ ] OpenAPI schema accessible at `/docs` and `/openapi.json`
- [ ] US-03 and US-01 acceptance criteria verified and issues closable

---

### 4.7 Basic Frontend

#### Why it belongs in Sprint 0

The frontend is the surface where Sprint 0 success criteria are verified by a human. Login, Create Project, Upload Asset, and View Dashboard are user-visible actions — they cannot be confirmed by `curl` or a script. A human evaluator must open a browser, navigate the application, and complete each flow. Without the frontend, Sprint 0 cannot be signed off.

The frontend in Sprint 0 is a navigation shell with four real screens. It is not a mock or a prototype. It makes real API calls, handles auth headers, and reflects real data from the database. The scope boundary is: no review screens, no pipeline start button wired up, no Temporal interaction. The dashboard shows the idle 4-stage stepper. The assets screen shows the upload form and the version list. These are enough to satisfy all four success criteria.

Sprint 0 is also the correct time to establish the frontend architecture: route structure, API client with token injection, and component folder layout. These decisions made in Sprint 0 will be inherited by the 6 screens built in Sprints 1–4.

#### Dependencies

- Repository Setup (`web/` folder structure, `vite.config.ts` paths)
- Authentication (backend middleware must be live; login page depends on `/health` for token validation)
- Basic Backend (`GET /projects`, `GET /health`, `GET /pipeline/status` must respond)
- Asset Storage (`POST /assets` and `GET /assets` must work for the upload screen)

#### Estimated effort

**4–7 hours** (Week 3: Monday for nav shell + routes, Wednesday/Saturday for login page + assets screen + dashboard + integration walkthrough)

Claude Code generates the Vite + React + TypeScript scaffold, React Router setup, nav bar, and empty-state pages. Founder's time: wiring the API client token interceptor, implementing the login redirect guard, connecting the assets upload form to `POST /assets`, and validating the dashboard stepper displays correct project data.

#### Definition of Done

**Application shell:**

- [ ] React + TypeScript SPA bootstrapped with Vite; runs with `npm run dev` on `localhost:5173`
- [ ] React Router defines four routes: `/login`, `/` (Dashboard), `/assets`, `/audit`
- [ ] `AppShell.tsx` renders a nav bar on all authenticated routes with links to Dashboard and Assets
- [ ] `api/client.ts` attaches `Authorization: Bearer <token>` on every request; reads token from `localStorage`
- [ ] Unauthenticated requests (no token or 401 response) redirect to `/login`
- [ ] All frontend-to-backend communication goes through `api/client.ts` only — never direct `fetch()` calls in components
- [ ] Desktop layout ≥ 768px; mobile layout explicitly out of scope

**Login screen (`/login`):**

- [ ] Renders a token input form with a submit button
- [ ] On valid token: stored in `localStorage`; redirect to `/`
- [ ] On invalid token: error message displayed; no redirect

**Dashboard screen (`/`):**

- [ ] Displays project name: "AIMPOS Spark Demo"
- [ ] Renders 4-stage stepper (Idea, Story, Script, Storyboard) in idle / no-pipeline state
- [ ] "Start Pipeline" button present but visually disabled or shows "Coming in Sprint 1" state — not wired to any API call
- [ ] US-26 and US-10 acceptance criteria verified and issues closable

**Assets screen (`/assets`):**

- [ ] File upload input accepts any file type; submits to `POST /assets` with Bearer token
- [ ] After successful upload: version appears in list below the upload form with content hash visible
- [ ] Upload failure (4xx/5xx): error message shown; form remains active
- [ ] US-05 frontend upload flow verified end-to-end

---

## 5. Sprint 0 Timeline

**Duration:** 3 weeks  
**Hours per week:** 12–15 (solo founder, evenings and weekends)  
**Total estimated effort:** 30–49 hours

| Week | Days | Focus | Issues targeted | Gate |
|------|------|-------|-----------------|------|
| **Week 1** | Mon–Sun | Repository + Docker Phase A + Database + Backend skeleton | US-02 (partial), US-04, US-03, US-01 | `GET /health` → 200; `GET /projects` → seeded project |
| **Week 2** | Mon–Sun | Asset Storage + Authentication + frontend start | US-05, US-25, US-26 (partial) | Authenticated upload round-trip works |
| **Week 3** | Mon–Sun | Frontend: login + assets + idle dashboard + integration walkthrough | US-26, T-26-* | End-to-end: Login → Project → Upload → Dashboard in one browser session |

### 5.1 Week 1 — Day-by-day

| Day | Hours | Task |
|-----|-------|------|
| Monday | 2 h | Repository Setup: scaffold, GitHub config, labels, milestones, `DECISIONS.md` |
| Tuesday | 2 h | US-02 (partial): Docker Compose Phase A — PostgreSQL, MinIO, Redis start |
| Wednesday | 2 h | US-04: Database models + Alembic migration applied |
| Saturday | 5–6 h | US-03 + US-01: FastAPI health endpoint, project seed, `GET /projects` |
| Sunday | 2 h | Week 1 gate check; close US-04, US-03, US-01; prep Week 2 GPU notes |

**Week 1 — do not start:**

- Ollama / ComfyUI (US-06) — scheduled Week 2
- React UI beyond stub — Week 3
- Temporal (US-07) — Sprint 1

### 5.2 Week 2 — Day-by-day

| Day | Hours | Task |
|-----|-------|------|
| Monday | 2 h | US-05: MinIO client wrapper + `store_asset()` + round-trip test |
| Tuesday | 2 h | US-02 (complete): Add Ollama, ComfyUI, Temporal stub, Worker stub to compose; deploy to Olares |
| Wednesday | 2 h | Olares GPU configuration: VRAM check, model pull, D-02 decision recorded |
| Saturday | 6 h | US-06: Ollama smoke → ComfyUI smoke → sequential GPU test; D-03, D-08 recorded. Auth middleware (US-25 backend half) |
| Sunday | 2 h | Week 2 gate check; close US-05, US-06, US-25 backend; prep frontend week |

### 5.3 Week 3 — Day-by-day

| Day | Hours | Task |
|-----|-------|------|
| Monday | 2 h | US-26: React app scaffold, Vite + TypeScript, React Router, AppShell, NavBar |
| Tuesday | 2 h | US-25 frontend: login page + token interceptor in `api/client.ts` |
| Wednesday | 2 h | US-10: Dashboard page — project name, 4-stage stepper, idle state |
| Saturday | 5 h | Assets screen: upload form + version list; full integration walkthrough |
| Sunday | 2 h | Sprint 0 exit gate check; close US-25, US-26, US-10; open Sprint 1 issues |

### 5.4 Effort summary by deliverable

| Deliverable | Estimated hours |
|-------------|-----------------|
| Repository Setup | 2–3 |
| Docker Setup | 8–14 |
| Database Setup | 2–4 |
| Asset Storage | 3–5 |
| Authentication | 2–4 |
| Basic Backend | 4–7 |
| Basic Frontend | 4–7 |
| **Total** | **30–49** |

---

## 6. Decisions Log

All decisions must be recorded in `DECISIONS.md` at repo root as they are made. These decisions are irreversible without migration cost.

| # | Decision | Decide by | Default if unclear |
|---|----------|-----------|-------------------|
| D-01 | Local Docker vs Olares for Week 1 | Week 1 Monday | Local Docker Desktop |
| D-02 | Ollama model: `llama3.1:13b` vs `mistral:7b` | Week 2 Wednesday | `mistral:7b` if VRAM < 16 GB |
| D-03 | ComfyUI workflow JSON: pin specific SDXL workflow | Week 2 Saturday | SDXL-base from community workflow, committed to `configs/comfyui/workflows/` |
| D-04 | Temporal deployment: compose with PostgreSQL persistence | Week 2 Tuesday | Full Temporal in compose, PostgreSQL backend |
| D-08 | GPU rule: never run Ollama and ComfyUI concurrently | Week 2 Saturday | Unload Ollama before ComfyUI; documented in `worker/README.md` |
| D-09 | Auth token: env var vs config file | Week 2 Saturday | `AIMPOS_API_TOKEN` in `.env`; rotate by changing env var and restarting API |
| D-10 | Login screen token UX: plain input vs masked password | Week 3 Monday | Masked password input; stored in `localStorage` with key `aimpos_token` |

---

## 7. Hard Gates

These gates are non-negotiable. The next activity cannot begin until the gate passes.

| Gate | Condition | Blocks |
|------|-----------|--------|
| **Week 1 gate** | `GET /health` returns 200; `GET /projects` returns seeded project | Week 2 GPU work |
| **Sprint 1 GPU gate** | Ollama + ComfyUI smoke pass on Olares (US-06) | Sprint 2 (Temporal workflow) |
| **Sprint 0 exit gate** | All 26 Sprint 0 issues closed; end-to-end browser walkthrough passes | Sprint 1 (Infrastructure Validation) |

The Week 2 GPU gate deliberately does not block the Platform Skeleton verification. If GPU smoke fails, invoke the failure protocol (stub PNGs, document as known limitation, proceed). The Platform Skeleton can be signed off regardless. Sprint 1 then carries the GPU resolution as an open risk item.

---

## 8. Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|------------|--------|------------|
| R-01 | Ollama/ComfyUI fails to start on Olares GPU | Medium | High (Sprint 1 AI agents blocked) | Failure protocol: stub PNG outputs; Sprint 0 signs off without GPU; resolve in Sprint 1 Week 1 |
| R-02 | Claude Code generates route code that violates service boundaries | Medium | Medium (architectural drift) | Review every PR: API must not import from `worker/`; domain layer must not import SQLAlchemy |
| R-03 | Database schema wrong on first migration | Low | High (all data from that point onward is wrong) | Verify 6 tables against MVP Definition.md §6.5 before applying; run downgrade test |
| R-04 | Sprint 0 expands to include Temporal workflow | Medium | High (Sprint boundary collapses) | Hard rule: no `POST /pipeline/start` implementation in Sprint 0; dashboard "Start Pipeline" button is disabled |
| R-05 | Login scope creeps to Keycloak | Low | High (weeks of unplanned work) | Auth = Bearer env var token only; Keycloak is deferred per Scope Freeze; US-25 acceptance criteria are sufficient |
| R-06 | GPU work overruns Week 2 and blocks frontend | Medium | Medium | GPU is Phase B — isolated failure; frontend work in Week 3 does not depend on GPU passing |
| R-07 | `DECISIONS.md` not maintained | Medium | Medium (context lost; future contributor makes conflicting decisions) | DoD for Docker Setup and Auth explicitly require `DECISIONS.md` entries before issue can close |

---

## 9. Sprint 0 Exit Gate

Sprint 0 is signed off when a human evaluator — sitting at a browser, not a terminal — completes the following sequence without assistance and without errors:

| Step | Action | Expected result |
|------|--------|-----------------|
| 1 | Open `http://localhost:5173` (or Olares IP) | Login page renders |
| 2 | Enter the API token from `.env` | Redirect to Dashboard |
| 3 | View Dashboard | "AIMPOS Spark Demo" project name visible; 4-stage stepper in idle state |
| 4 | Navigate to Assets | Empty asset list; upload form visible |
| 5 | Upload any test file (e.g. `idea.txt`) | File appears in version list with content hash and stage label |
| 6 | Navigate back to Dashboard | Project and stepper still correct; no errors |
| 7 | Open `http://localhost:8000/health` | JSON response with all infrastructure dependencies listed as healthy |

All 26 Sprint 0 issues (§3.1) must be closed before the exit gate walkthrough is attempted. US-02, US-06, and US-10 are Sprint 1+ and do not block Sprint 0.

---

## 10. Impact on subsequent sprints

After Sprint 0, the platform guarantees:

- 4-service compose runs (PostgreSQL, MinIO, Redis, API)
- Database schema is stable and migrated
- Asset storage works end-to-end
- Auth middleware is live on all routes
- Frontend connects to API with token injection
- Idle dashboard renders project and 4-stage stepper

### 10.1 Full sprint map (per Sprint Reclassification)

| Sprint | Class | Deliverable | Key issues |
|--------|-------|-------------|------------|
| **S0** | A | Platform Skeleton | US-01, US-03–05, US-25–26, FEAT-01 |
| **S1** | B | Infrastructure Validation | US-02, US-06, EPIC-01, FEAT-INFRA |
| **S2** | C | Workflow Foundation | US-07, US-08, US-10, FEAT-03, FEAT-16 |
| **S3** | D | Idea → Story | US-11–13, US-09, FEAT-02, FEAT-04–05 |
| **S4** | E | Story → Script | US-14–15, US-23, FEAT-06–07, FEAT-13 |
| **S5** | F | Script → Storyboard + sign-off | US-16–17, US-22, US-24, US-V01, FEAT-08–09, FEAT-12 |
| **Future** | G | Deferred | FEAT-14, US-20 |

Sprint 1 cannot begin until Sprint 0 exit gate passes. Sprint 2 cannot begin until Sprint 1 GPU gate passes.

---

## 11. Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-06-09 | Product / Architecture | Initial Sprint 0 planning document — Platform Skeleton |
| 1.1 | 2026-06-09 | Product / Architecture | Aligned with Sprint Reclassification; US-02/US-06/US-10 moved to Sprint 1+; 26 issues in S0 |
| 1.2 | 2026-06-09 | Lead Engineer | GitHub milestones relabeled + 68 issues reassigned; S0 count corrected 24→26 (T-02-02/03 included) |

**Related documents (frozen):**

| Document | Status |
|----------|--------|
| [Sprint Reclassification.md](./Sprint%20Reclassification.md) | FROZEN — issue → sprint map |
| [Architecture Freeze Review.md](./Architecture%20Freeze%20Review.md) | FROZEN — freeze boundary |
| GitHub milestones | Relabel per Sprint Reclassification before Sprint 0 Day 1 |

---

*This document is the execution contract for Sprint 0. When in conflict with informal discussion, this document and [MVP Scope Freeze.md](./MVP%20Scope%20Freeze.md) win.*

*End of document*
