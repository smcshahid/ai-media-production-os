# Sprint 0 — Platform Skeleton: Briefing & Handoff

**Status:** ✅ Complete (delivered via PR #74) · **Date:** 2026-06-09
**Purpose:** A single reference to resume work in a later session. For the authoritative, blow-by-blow record see [`Sprint0_Status.md`](../../Sprint0_Status.md) (tracker) and [`DECISIONS.md`](../../DECISIONS.md) (decision log). Scope/AC are frozen in [`Sprint 0 — Platform Skeleton.md`](../../Sprint%200%20%E2%80%94%20Platform%20Skeleton.md).

---

## 1. What Sprint 0 delivered

A runnable **platform skeleton**: a 5-container local stack and a browser app that exercises the four Sprint-0 success criteria end to end.

| Capability | How it's met | Key issues |
|------------|--------------|------------|
| **Login** | Static Bearer token (`AIMPOS_API_TOKEN`); `AuthMiddleware` on all routes except `/health`; SPA `/login` stores the token in `localStorage` | US-25 |
| **Create Project** | Idempotent startup seed of "AIMPOS Spark Demo"; `GET /projects` | US-01 |
| **Upload Asset** | `store_asset` (ports & adapters) → MinIO content-addressed blob + version row; `POST /assets` + `GET /assets`; SPA Assets screen | US-05 |
| **View Dashboard** | `GET /pipeline/status` (read-only, `IDLE` + 4-stage order); SPA Dashboard with idle stepper | US-03, US-10 |
| **App shell** | React SPA: routes `/login` `/` `/assets` `/audit`, nav, route guard, single `api/client.ts` gateway | US-26, T-25-03 |
| **Foundation** | DB schema (6 tables) + Alembic migration + async repositories; `/health` probes; structured JSON logs + request-id | US-04, US-03 |

**Exit gate:** the 7-step browser walkthrough (login → dashboard → assets → audit → logout) + `/health` all-healthy **passes** (recorded in `Sprint0_Status.md` → "Sprint 0 Exit Gate — verification record").

---

## 2. Architecture at a glance

- **Monorepo:** `api/` (FastAPI monolith), `web/` (React SPA), `worker/` (Temporal/agents — stub only, Sprint 1+), `packages/` (shared `aimpos-core` enums/events, `aimpos-config` settings/logging), `deploy/compose/` (local stack).
- **DDD module boundaries:** business rules in `api/app/domain/` import **no** framework/SQLAlchemy/SDK; adapters live in `api/app/infrastructure/`; HTTP controllers in `api/app/routes/` are thin and own the transaction (repositories `flush`, routes `commit`).
- **Ports & adapters:** e.g. `store_asset` depends on `BlobStore`/`AssetVersionStore` Protocols; `MinioClient` + `AssetVersionRepository` are the injected adapters.
- **Config:** `pydantic-settings` via `aimpos-config` — **no `os.getenv` in app code**.
- **Persistence:** SQLAlchemy 2.0 (async), Alembic migrations are the single source of truth; app-side UUID PKs and `VARCHAR + CHECK` enums for portability.
- **Frontend:** all backend calls go through `web/src/api/client.ts` (Bearer interceptor; 401 → `/login`); components never call `fetch` directly.

### Key decisions (see `DECISIONS.md` for full text)
- **D-09** API auth = single static Bearer token; Keycloak/OIDC deferred to Phase 1; only `/health` is exempt (so `/docs` is protected too).
- **D-18/D-19** field reconciliations (`name`, `minio_key`); enum/UUID/migration strategy.
- **D-21** repositories `flush` not `commit` (caller owns the unit of work).
- **D-23** pure-ASGI middleware for request-id + access logging (contextvar propagation).
- **D-25/D-26** asset storage service + HTTP routes; SHA-256 content hash (ETag/MD5 verified post-upload); dedup = same blob, new version row.
- **D-27** `GET /pipeline/status` read-only; `IDLE` is a presentation sentinel.
- **D-28** `web/` SPA foundation + outermost `CORSMiddleware` (resolves the cross-origin preflight problem).

---

## 3. How to run (local dev)

Prerequisites: Docker Desktop, Node 24+, Python 3.12+ (only for host-side tooling/tests).

```bash
cp .env.example .env          # first time; review values
make up-dev                   # build + start postgresql, minio(+init), redis, api, web (host ports published)
```

- **SPA:** http://localhost:5173 — sign in with the `AIMPOS_API_TOKEN` from `.env` (default `change-me-local-dev-token`).
- **API:** http://localhost:8000 — `/health`, and `/docs` (needs the Bearer token).
- **Stop / reset:** `make down` (keep data) · `docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml --env-file .env down -v` (wipe volumes for a pristine stack).

### Tests / quality gates
- **API:** create a venv, `pip install -e packages/aimpos-core -e packages/aimpos-config -e api[dev]`, then `pytest` (47 unit; integration needs `AIMPOS_RUN_INTEGRATION=1` + the live stack), `ruff check`, `ruff format --check`, `mypy app`.
- **Web:** `cd web && npm install`, then `npm run build` (strict `tsc` + Vite), `npm run lint`, `npm test` (Vitest).

---

## 4. Repo map (where things live)

```
api/app/
  routes/         health, projects, assets, pipeline   (thin HTTP controllers + auth/CORS wiring in main.py)
  domain/         studio/project, assets/{content,service}  (framework-free business rules + ports)
  infrastructure/ db/{models,repositories,session}, storage/minio_client, cache/redis_client, health/probes
  middleware/     auth, request_id, logging            (pure ASGI)
  seed/           default_project
  alembic/        env.py + versions/0001_initial_core_tables.py
web/src/
  api/            client.ts (single gateway) + types.ts
  components/      RequireAuth, layout/AppShell, Stepper
  routes/          LoginPage, DashboardPage, AssetsPage, AuditPage
  hooks/           usePipelineStatus
  tests/           Vitest (Stepper, RequireAuth, client)
packages/         aimpos-core (enums/events, py.typed), aimpos-config (settings, logging)
deploy/compose/   docker-compose.yml (base) + docker-compose.dev.yml (host ports) + init/{postgres,minio}
docs/             governance/, runbooks/{postgres,minio,migrations}, adr/, sprints/ (this doc)
```

---

## 5. Deferred to Sprint 1 (do NOT start without the prerequisites)

- **US-02** — full 9-container Olares deployment.
- **US-06** — GPU "kill check": Ollama + ComfyUI smoke + sequential GPU test (D-02/D-03/D-08). **Requires GPU + Olares hardware.** Phase B; explicitly does not block Sprint 0.
- **US-07+** — Temporal workflow (`SparkPipelineWorkflow`), agents, the Review screen, live polling dashboard.

When resuming: confirm GPU/Olares availability first; Sprint 1 is "Infrastructure Validation."

---

## 6. Known tech debt & gotchas (carry into Sprint 1)

- **TD-21** — no CI workflow yet; tests run locally only. First Sprint-1 chore: add `ci-api.yml` (+ a web job) running ruff/mypy/pytest and npm build/lint/test.
- **TD-23 / #69** — services use MinIO **root** creds + blanket `env_file`; mint least-privilege keys.
- **TD-25** — `store_asset` writes the blob before the DB row; benign (content-addressed, self-dedup) but no delete-on-failure compensation yet.
- **TD-11** — enum/immutability is app-enforced (no DB triggers) for `audit_events`/`approvals`.
- **Windows dev:** `psycopg` async rejects the default `ProactorEventLoop`; integration tests select `WindowsSelectorEventLoopPolicy` (no-op on Linux/CI).
- **IPv6 `localhost`:** inside containers `localhost` may resolve to `::1` while servers bind IPv4 — use `127.0.0.1` for in-container healthchecks/host curl (bit us on the web healthcheck and PowerShell `Invoke-WebRequest`).
- **Auth covers `/docs`:** explore the schema with `curl -H "Authorization: Bearer <token>" http://localhost:8000/openapi.json`.

---

## 7. Resuming in a future session — quick start

1. `make up-dev`; open the SPA, sign in, sanity-check `/health`.
2. Read this briefing + the tail of `Sprint0_Status.md` (document-control table) + recent `DECISIONS.md` entries.
3. Pick up Sprint 1 from the frozen plan (`Sprint Reclassification.md` → S1: US-02, US-06, EPIC-01). Confirm GPU/Olares before US-06.
4. Add CI (TD-21) early so Sprint-1 PRs are gated.
