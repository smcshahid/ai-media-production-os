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

---

<!-- New decisions appended below. Do not edit prior entries; supersede with a new D-NN. -->
