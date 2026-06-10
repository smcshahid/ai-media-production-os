# US-09 Acceptance Package — Local Verification

**Environment:** Local dev (unit tests + web build)  
**Date:** 2026-06-10  
**Baseline:** Post-implementation (pre-Olares E2E)  
**Recommendation:** **CONDITIONAL ACCEPT** — AC-3 429 side effects fully evidenced via unit tests; AC-1/2/4 Olares E2E recommended for formal ACCEPT.

---

## Acceptance criteria status

| AC | Description | Status | Evidence |
|---|---|---|---|
| AC-1 | `POST /pipeline/regenerate` triggers agent | **PARTIAL** | Route + workflow implemented; unit test mocks Temporal signal; Olares E2E pending |
| AC-2 | New `asset_version` incremented | **PARTIAL** | `store_story_markdown` unchanged (`D-38`); Olares SQL pending |
| AC-3 | Max 3 → 429 | **PASS** | `test_fourth_regenerate_returns_429_without_side_effects` |
| AC-4 | Rejection note to agent | **PASS** | `test_draft_story_node_includes_rejection_note` |

---

## AC-3 evidence — 429 with no side effects

**Test:** `api/tests/unit/test_pipeline_regenerate.py::test_fourth_regenerate_returns_429_without_side_effects`

| Check | Expected | Observed |
|---|---|---|
| HTTP status | 429 | ✅ |
| Temporal signal | None | ✅ `len(fake.regenerates) == 0` |
| Audit row | None added | ✅ count stays at 3 |
| Asset version | N/A at API layer | Worker not invoked (no signal) |

Log: `logs/pytest-us09.txt`

---

## AC-4 evidence — rejection note in prompt

**Test:** `worker/tests/unit/test_story_architect.py::test_draft_story_node_includes_rejection_note`

Note `"Strengthen the third act climax."` present in Ollama prompt passed to `generate_text`.

---

## AC-1 partial evidence — API route

**Test:** `test_regenerate_happy_path_signal_and_audit`

- `POST /pipeline/regenerate` → 200
- `regenerations_used: 1`
- `REGENERATION_REQUESTED` audit appended
- Temporal `signal_regenerate` called

---

## Constraint verification

| Check | Result |
|---|---|
| STORY only (501 SCRIPT) | PASS — `test_regenerate_script_stage_returns_501` |
| No schema migration | PASS |
| D-37 no branch promotion | PASS (no approve-path changes) |
| D-38 append-only ai-draft | PASS (design + `selectLatestAiDraftStoryAsset`) |
| US-13 regression | PASS — `test_assets_us13.py` 8 passed |
| US-08 regression | PASS — `test_pipeline_approve.py` green |

---

## CI-equivalent gates

| Gate | Result |
|---|---|
| API unit (76 tests) | PASS |
| Worker unit (5 tests) | PASS |
| Web unit (14 tests) | PASS |
| Web build | PASS |

---

## Olares verification (recommended for ACCEPT)

Run `deploy/k8s/us09-verify/verify_us09.sh` on `aimpos-mwayolares`:

1. Reject STORY with note  
2. Regenerate ×3 — version increment + audit count  
3. 4th regenerate → 429, versions unchanged  
4. Optional: approve → SCRIPT

Deliver: `evidence/us-09-verification/olares-2026-06-10/US-09-ACCEPTANCE-PACKAGE.md`

---

## Recommendation

**CONDITIONAL ACCEPT** pending Olares E2E for AC-1/AC-2 asset evidence.

**Requesting formal US-09 closure review.**
