# AIMPOS-Spark Visual — Coding Standards

**Document Type:** Engineering Governance  
**Version:** 1.0  
**Status:** FROZEN — Effective June 9, 2026  
**Date:** June 9, 2026  
**Product:** AIMPOS-Spark Visual

---

## Purpose

Minimum coding standards for consistent, reviewable implementation. **Architecture and folder placement** are defined in frozen planning documents — this document adds tooling, naming, and non-negotiable implementation rules.

**Authority chain (highest wins on structure):**

1. [Repository Structure.md](../../Repository%20Structure.md) — folders and service boundaries
2. [Domain Driven Design.md](../../Domain%20Driven%20Design.md) §10 — domain layer rules
3. This document — style, tooling, and conventions

---

## Service Boundary Rules (Non-Negotiable)

These rules come from approved architecture. Violations block PR merge.

| Rule | Detail |
|------|--------|
| **API isolation** | `api/` never calls Ollama, ComfyUI, or LangGraph directly — starts workflows and sends signals only |
| **Worker isolation** | `worker/` never exposes HTTP — polls Temporal task queue |
| **Web isolation** | `web/` communicates with `api/` REST only — never Temporal, Ollama, or ComfyUI |
| **Domain purity** | `api/domain/` has no FastAPI, SQLAlchemy, or HTTP client imports |
| **Persistence location** | SQLAlchemy models live in `api/infrastructure/db/` only |
| **Shared types** | Enums, stage constants, and shared DTOs live in `packages/aimpos-core` |
| **Agent location** | LangGraph graphs live in `worker/agents/` only |
| **Workflow location** | Temporal workflows and activities live in `worker/temporal/` |
| **Config vs code** | Ollama model manifests and ComfyUI workflow JSON live under `configs/` — not hardcoded in Python |
| **Cross-domain imports** | Domain modules do not import other domain modules except via `packages/` shared types or explicit application services |

---

## Repository Layout

Place new code in the folder defined by [Repository Structure.md](../../Repository%20Structure.md):

| Code type | Location |
|-----------|----------|
| HTTP routes | `api/routes/` |
| Domain logic | `api/domain/<context>/` |
| DB adapters | `api/infrastructure/` |
| Temporal workflows | `worker/temporal/workflows/` |
| Temporal activities | `worker/temporal/activities/` |
| LangGraph agents | `worker/agents/` |
| Ollama/ComfyUI tools | `worker/tools/` |
| React pages | `web/src/routes/` |
| React components | `web/src/components/` |
| Shared Python types | `packages/aimpos-core/` |
| Settings / logging | `packages/aimpos-config/` |
| Smoke scripts | `scripts/smoke/` |
| Compose / Docker | `deploy/` |

Do not create parallel folder structures outside this layout.

---

## Tooling

| Stack | Tool | Config |
|-------|------|--------|
| Python (`api/`, `worker/`, `packages/`) | **Ruff** — lint + format | `pyproject.toml` |
| Python types | **mypy** — strict on `packages/`, pragmatic elsewhere | `pyproject.toml` |
| TypeScript (`web/`) | **ESLint** + **Prettier** | `web/eslint.config.*`, `web/.prettierrc` |
| Pre-commit (optional) | Ruff + ESLint on staged files | `.pre-commit-config.yaml` when added |

Run before PR:

```bash
# Python — from repo root once pyproject.toml exists
ruff check api worker packages
ruff format --check api worker packages

# Web
cd web && npm run lint && npm run format:check
```

CI enforces lint when `.github/workflows/ci-*.yml` is added (required before US-03 merges).

---

## Python Standards

### Style

- **Line length:** 100 characters
- **Quotes:** double quotes (Ruff default)
- **Imports:** absolute imports from package root; group stdlib → third-party → local
- **Type hints:** required on all public functions and methods
- **Async:** use `async def` in FastAPI routes and async adapters; keep domain logic sync unless I/O-bound

### Naming

| Element | Convention | Example |
|---------|------------|---------|
| Modules | snake_case | `pipeline_run.py` |
| Classes | PascalCase, ubiquitous language | `PipelineRun`, `AssetVersion` |
| Functions | snake_case | `start_pipeline()` |
| Constants | UPPER_SNAKE | `PIPELINE_STAGE_STORY` |
| Private | leading underscore | `_validate_stage()` |

Use terms from [Domain Driven Design.md](../../Domain%20Driven%20Design.md) §4 — do not invent synonyms (`PipelineRun`, not `WorkflowJob`).

### FastAPI routes

- Routes are thin — delegate to domain services or application layer
- Request/response models as Pydantic schemas in route module or `packages/aimpos-core`
- Return appropriate HTTP status codes; use structured error responses

### Domain layer

- Business rules and invariants live in domain services and aggregate roots
- No framework imports in `api/domain/`
- Test invariants in domain tests, not only via HTTP

### Worker / Temporal

- Workflow code must be deterministic — no direct I/O in workflow functions
- Side effects belong in activities
- Activity names stable and prefixed: `run_story_agent`, `store_asset_version`

### Logging

Use structured logging via `aimpos-config`. Include when available:

```python
logger.info(
    "stage_completed",
    pipeline_run_id=run_id,
    stage=stage,
    model_id=model_id,  # required for AI activities — SC-05
)
```

Never log secrets, tokens, or full prompt text containing PII.

---

## TypeScript / React Standards

### Style

- **Strict mode** enabled in `tsconfig.json`
- **Components:** PascalCase filenames matching export (`ReviewStory.tsx`)
- **Hooks:** `use` prefix (`usePipelineStatus.ts`)
- **API client:** all backend calls through `web/src/api/client.ts`

### Patterns

- Functional components with hooks — no class components
- Colocate component tests in `web/src/tests/` or adjacent `*.test.tsx`
- Poll pipeline status via HTTP (WebSocket deferred)
- Attach Bearer token in API client when US-25 is implemented

---

## Testing Standards

| Layer | Location | Expectation |
|-------|----------|-------------|
| API unit | `api/tests/` | Domain and route tests; mock infrastructure |
| Worker unit | `worker/tests/` | Activity and agent tests; mock Ollama/ComfyUI |
| Web unit | `web/src/tests/` | Component and hook tests |
| Integration | `tests/integration/` | Compose-based; not required for every issue |
| E2E / GPU | `tests/e2e/` | Manual or nightly; not PR-blocking initially |

**Naming:** `test_<behavior>.py` or `<Component>.test.tsx`

**Minimum for DoD:** new domain logic or non-trivial routes include at least one test covering the happy path or core invariant.

---

## Database Migrations

- All schema changes via Alembic in `api/alembic/versions/`
- One migration per logical change; descriptive slug: `001_initial_core_tables.py`
- Migrations must be reversible — `downgrade()` implemented
- Never edit a migration already merged to `main` — create a new migration instead

---

## Configuration and Secrets

| Rule | Detail |
|------|--------|
| **Secrets** | Only in `.env` (gitignored) — never in code, configs, or GitHub |
| **Env template** | Every new env var added to `.env.example` with comment |
| **Model pins** | Ollama models in `configs/ollama/`; ComfyUI graphs in `configs/comfyui/workflows/` |
| **Defaults** | Sensible defaults in `aimpos-config`; secrets never defaulted |

---

## Git Conventions

| Element | Format | Example |
|---------|--------|---------|
| **Commit message** | `(<task-id>) <imperative summary>` | `(T-02-01) Add docker-compose for nine services` |
| **PR title** | `[<issue-id>] <summary>` | `[US-02] Deploy MVP stack on Olares` |
| **Branch** | per [branching-strategy.md](./branching-strategy.md) | `feature/T-02-01-docker-compose` |

Keep commits small and focused. Squash merge on PR is preferred.

---

## Dependencies

| Rule | Detail |
|------|--------|
| **Pin versions** | Pin major dependencies in `pyproject.toml` / `package.json` |
| **Add minimally** | New dependency requires justification in PR description |
| **No secrets in lockfiles** | Lockfiles committed; no credentials embedded |

---

## Prohibited Patterns

| Pattern | Reason |
|---------|--------|
| Business logic in route handlers beyond orchestration | Belongs in domain layer |
| Direct MinIO/PostgreSQL access from `web/` | Must go through API |
| Calling Temporal from LangGraph without activity boundary | Breaks durability model |
| Hardcoded model names in agent code | Use `configs/ollama/` manifest |
| Cross-import between `api/domain/*` contexts | Use shared packages or application services |
| `print()` for operational logging | Use structured logger |
| Committing `.env`, API keys, or tokens | Security |

---

## Document Control

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-09 | Initial coding standards for Visual MVP |

*End of document*
