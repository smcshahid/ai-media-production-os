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

### D-12 — Tooling pinned for the monorepo
**Date:** 2026-06-09  
**Decision:** Python uses Ruff (lint + format) and mypy; TypeScript uses ESLint + Prettier. Versions pinned in each service's `pyproject.toml` / `package.json` when introduced (US-04, US-03, US-26).  
**Rationale:** Single source of truth per coding-standards §66–73. Repository Setup declares intent; manifests land with the first code in each service.

### D-13 — Repository Setup committed as bootstrap to `main`
**Date:** 2026-06-09  
**Decision:** The monorepo skeleton (folders, `.gitkeep`, governance files, templates) is committed directly to `main` as a bootstrap commit.  
**Rationale:** Permitted by branching-strategy §73–81 for "empty repo skeleton with no application logic." All subsequent application code merges via `feature/*` PRs.

---

<!-- New decisions appended below. Do not edit prior entries; supersede with a new D-NN. -->
