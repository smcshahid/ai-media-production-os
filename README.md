# AIMPOS-Spark

Privacy-first, local-AI media production platform.

## Status

| Program | Status | Frontier |
|---------|--------|----------|
| **Visual MVP** | **CLOSED** (M5 · `v0.4.0-usv01`) | — |
| **Spark Full** | **CLOSED** (M6 · `v0.7.0-usv02`) | — |

| State | Detail |
|-------|--------|
| Visual MVP release | `v0.4.0-usv01` — US-V01 acceptance (`93214fc`) |
| Spark Full release | `v0.7.0-usv02` — US-V02 Spark Full acceptance |
| Visual MVP summary | `docs/sprints/visual-mvp-completion-summary.md` |
| Spark Full summary | `docs/sprints/spark-full-completion-summary.md` |
| Spark Full governance | `docs/sprints/spark-full-governance-brief.md` (**ACCEPT — Phase 1 closed**) |
| US-18 | **CLOSED** — `v0.5.0-us18` · `docs/sprints/sprint-4a-us18-closure-report.md` |
| US-19 | **CLOSED** — `v0.6.0-us19` · `docs/sprints/sprint-4b-us19-closure-report.md` |
| US-V02 | **CLOSED** — `v0.7.0-usv02` · `docs/sprints/sprint-4c-usv02-closure-report.md` |
| M6 Spark Full | **COMPLETE** |
| Stack | 9-service compose; Olares GPU path verified through VIDEO + export |
| CI | `.github/workflows/ci-api.yml` — ruff/mypy/pytest + web build/lint/vitest on PRs |

## Document authority (frozen)

| Priority | Document | Role |
|----------|----------|------|
| 1 | [MVP Scope Freeze.md](./MVP%20Scope%20Freeze.md) | Scope contract |
| 2 | [Architecture Freeze Review.md](./Architecture%20Freeze%20Review.md) | Freeze boundary |
| 3 | [Sprint Reclassification.md](./Sprint%20Reclassification.md) | Issue → sprint map |
| 4 | [Sprint 0 — Platform Skeleton.md](./Sprint%200%20%E2%80%94%20Platform%20Skeleton.md) | Sprint 0 execution |
| 5 | [GitHub Issues - Visual MVP.md](./GitHub%20Issues%20-%20Visual%20MVP.md) | 43 epics / features / stories |
| 6 | [docs/governance/](./docs/governance/) | Engineering workflow |

**Read-only references** (do not edit during Visual MVP): Blueprint, Business Capabilities, DDD, System Architecture, Workflow Architecture, Multi-Agent Architecture, Technology Recommendations, Enterprise Knowledge Graph.

**Archived** (do not use for execution): MVP Definition, MVP Backlog, GitHub Issues - Full MVP (Superseded), Solo Founder Development Plan.

## Sprint plan

| Sprint | Deliverable | Issues |
|--------|-------------|--------|
| **Sprint 0** | Platform Skeleton — Login, Project, Upload, Dashboard | 24 |
| **Sprint 1** | Infrastructure Validation — Olares, GPU smoke | 11 |
| **Sprint 2** | Workflow Foundation — Temporal skeleton | 6 |
| **Sprint 3** | Idea → Story | 7 |
| **Sprint 4** | Story → Script | 7 |
| **Sprint 5** | Script → Storyboard + Visual MVP sign-off | 9 |
| **Spark Full** | Phase 1 complete (M6 signed) | — |

See [Sprint Reclassification.md](./Sprint%20Reclassification.md) for full issue mapping.

## GitHub

- **Repository:** https://github.com/smcshahid/ai-media-production-os
- **Project board:** AI Media Production OS (AIMPOS)
- **Codename:** `AIMPOS-Spark` (Visual MVP: `AIMPOS-Spark-Visual` · closed)
- **First implementation issue:** T-02-02 (PostgreSQL init) or US-04 (database schema) — Sprint 0

### Backlog maintenance

```powershell
# One-time setup after gh auth login (no manual tokens)
.\scripts\setup-github.ps1

# Or verify anytime (uses gh keyring automatically)
python backlog/verify_github_token.py
python backlog/protect_and_audit.py
```

Do **not** re-run `import_to_github.py --all` unless resetting the repo — it creates duplicate issues.

Do **not** create new architecture documents in this planning repository. Changes require SCR per MVP Scope Freeze §11.

## Quick start (local dev)

Prerequisites: Docker Desktop, Node 24+, Python 3.12+ (host venv for migrations/tests).

```powershell
# from repo root
cp .env.example .env
docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml --env-file .env up -d
```

- **SPA:** http://localhost:5173 — sign in with `AIMPOS_API_TOKEN` from `.env`
- **API:** http://localhost:8000/health (no auth) · protected routes need `Authorization: Bearer <token>`
- **Stop:** `docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.dev.yml --env-file .env down`
- **Reset data:** add `-v` to `down`

### Service port map (dev overlay)

| Service | Host port | Purpose |
|---------|-----------|---------|
| `api` | 8000 | FastAPI REST + `/health` |
| `web` | 5173 | React SPA (nginx) |
| `postgresql` | 5432 | System of record |
| `minio` | 9000 / 9001 | S3 API / console |
| `redis` | 6379 | Cache |
| `temporal` | 7233 | Workflow gRPC (Sprint 1) |
| `temporal-ui` | 8080 | Temporal Web UI (Sprint 1) |
| `ollama` | 11434 | Local LLM API (Sprint 1, GPU) |
| `comfyui` | 8188 | Image diffusion API (Sprint 1, GPU) |
| `worker` | — | Temporal worker stub (internal only) |

Compose env template: [`deploy/compose/.env.compose.example`](./deploy/compose/.env.compose.example).

### Smoke tests

| Script | Gate | Exit codes |
|--------|------|------------|
| `scripts/smoke/test_postgres.py` | S1-SW (hermetic) | 0 = PASS |
| `scripts/smoke/test_minio.py` | S1-SW (hermetic) | 0 = PASS |
| `scripts/smoke/test_ollama.py` | M1-DV (live GPU) | 0 = PASS · **2 = SKIP** (unavailable) · 1 = FAIL |
| `scripts/smoke/test_comfyui.py` | M1-DV (live GPU) | 0 = PASS · **2 = SKIP** · 1 = FAIL |

**SKIP is not PASS.** On CPU-only dev hosts, AI smokes exit 2 by design. On Olares, use `--require-live` for M1-DV.

Runbooks: [`docs/runbooks/local-development.md`](./docs/runbooks/local-development.md) · [`olares-deployment.md`](./docs/runbooks/olares-deployment.md) · [`gpu-sequencing.md`](./docs/runbooks/gpu-sequencing.md)

### Quality gates (run before every PR)

```powershell
# API
cd api; .\.venv\Scripts\python.exe -m pytest tests/unit -q; .\.venv\Scripts\python.exe -m ruff check app tests; .\.venv\Scripts\python.exe -m ruff format --check app tests; .\.venv\Scripts\python.exe -m mypy app
# Web
cd web; npm run build; npm run lint; npm test
```

## Repository layout

See [Repository Structure.md](./Repository%20Structure.md) for the monorepo folder plan.
