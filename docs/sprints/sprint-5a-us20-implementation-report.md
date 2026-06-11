# Sprint 5A — US-20 Implementation Report

**Date:** 2026-06-10  
**Status:** **IMPLEMENTED** — local PASS · Olares **PASS** · **CLOSED** (`v0.8.0-us20`)  
**Parent brief:** `docs/sprints/sprint-5a-us20-brief.md` (**ACCEPT WITH CONDITION C-01**)  
**Implementation plan:** `docs/sprints/sprint-5a-us20-implementation-plan.md` (**ACCEPT**)  
**Baseline:** `v0.7.0-usv02` (`905f1f1`)

---

## 1. Summary

US-20 adds **`GET /lineage/{pipeline_run_id}`** — a read-only provenance API over existing `lineage_edges` and `asset_versions` — plus a minimal **list/tree lineage viewer** on the Export page and `/lineage` route. Synthetic IDEA root is presentation-only (C-01). No schema, worker, or workflow changes.

| Deliverable | Status |
|---|---|
| D-55, D-56 in `DECISIONS.md` | ✅ |
| `LineageEdgeRepository` (SELECT only) | ✅ |
| Lineage domain service + resolver | ✅ |
| `GET /lineage/{pipeline_run_id}` route | ✅ |
| `LineageViewer` + Export / Lineage pages | ✅ |
| Unit tests | ✅ 94 API / 26 web |
| Olares verify scripts | ✅ `deploy/k8s/us20-verify/` |
| Olares E2E evidence | ✅ **PASS** — `RUN_ID=042983f7-0f55-48c3-9d65-fce89a684625` |

---

## 2. Contract implementation

| Contract | Implementation |
|---|---|
| **D-55** | `get_lineage_for_run()` — JSON with `nodes[]`, `edges[]`; edges mirror SQL join query |
| **D-55 GET only** | Single GET route; no mutation endpoints |
| **D-55 synthetic IDEA** | `synthetic: true`, `parent_asset_ids: []`; excluded from `edges[]` |
| **D-56** | `LineageViewer` — CSS list/tree, metadata panel, COMPLETED gate on UI |
| **C-01** | No lineage INSERT/UPDATE; no migrations; no backfill |
| **Export alignment** | Display chain via `resolve_export_files()` |

---

## 3. Local test results

| Suite | Result | Log |
|---|---|---|
| API unit | **94 passed** | `evidence/us-20-verification/local-2026-06-10/logs/pytest-api.txt` |
| Web vitest | **26 passed** | `evidence/us-20-verification/local-2026-06-10/logs/vitest-web.txt` |

New tests: `test_lineage.py` (6), `lineageDisplay.test.ts` (3).

---

## 4. Olares verification

**Scripts:** `deploy/k8s/us20-verify/verify_us20.sh`, `run_remote.sh`, `deploy_us20.sh`

**Reference run:** `042983f7-0f55-48c3-9d65-fce89a684625` (US-V02 COMPLETED)

**Result (2026-06-11):** **PASS** — `FAIL=0`, `VERIFY_RC=0`. Full report: `docs/sprints/sprint-5a-us20-verification-report.md`. Evidence: `evidence/us-20-verification/olares-2026-06-10/`.

---

## 5. Files changed

| Area | Key files |
|---|---|
| Decisions | `DECISIONS.md` (D-55, D-56) |
| API domain | `api/app/domain/lineage/{types,resolver,service}.py` |
| API infra | `api/app/infrastructure/db/repositories/lineage_edge.py` |
| API route | `api/app/routes/lineage.py`, `api/app/main.py` |
| Web | `web/src/components/LineageViewer.tsx`, `web/src/lib/lineageDisplay.ts`, `web/src/routes/{ExportPage,LineagePage}.tsx`, `web/src/api/{client,types}.ts`, `web/src/styles.css` |
| Tests | `api/tests/unit/test_lineage.py`, `web/src/tests/lineageDisplay.test.ts` |
| Verify | `deploy/k8s/us20-verify/*` |
| Docs | `docs/sprints/sprint-5a-us20-implementation-plan.md`, this report |

---

## 6. Repository status

| Item | Value |
|---|---|
| Baseline tag | `v0.7.0-usv02` |
| Story | US-20 |
| Phase | Spark Full Phase 2 |
| Closure | **CLOSED** — `v0.8.0-us20` |

---

## 7. Explicit exclusions (verified)

No graph database · no graph visualization framework · no lineage editing/repair · no asset history (US-22/23) · no workflow/Temporal changes · no export contract changes.
