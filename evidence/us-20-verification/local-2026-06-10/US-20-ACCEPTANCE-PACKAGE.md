# US-20 Acceptance Package — Local Verification

**Status:** **PASS**  
**Date:** 2026-06-10  
**Baseline:** `v0.7.0-usv02`  
**Olares E2E:** **PENDING** — required before closure (see `../olares-*/US-20-ACCEPTANCE-PACKAGE.md`)

---

## Local test summary

| Suite | Result | Log |
|---|---|---|
| API unit | **94 passed** | `logs/pytest-api.txt` |
| Web vitest | **26 passed** | `logs/vitest-web.txt` |

New tests: `api/tests/unit/test_lineage.py` (6 cases), `web/src/tests/lineageDisplay.test.ts` (3 cases).

---

## Governance constraints verified locally

| Constraint | Local evidence |
|---|---|
| **D-55** GET-only read API | Route accepts GET only; 404/401 tests |
| **D-55** API/SQL edge parity | `test_lineage_edge_parity_with_repository` |
| **D-56** list/tree UI helpers | `lineageDisplay.test.ts` ordering + synthetic label |
| **C-01** synthetic IDEA | `synthetic: true`; no IDEA in `edges[]` |
| **C-01** no lineage writes | Read-only repository; no INSERT in API layer |
| Export regression | Existing `test_export.py` — PASS in full suite |

---

## Next gate

Deploy `aimpos-api:us20` to Olares; run `deploy/k8s/us20-verify/verify_us20.sh` against US-V02 COMPLETED run (`RUN_ID=042983f7-0f55-48c3-9d65-fce89a684625`).
