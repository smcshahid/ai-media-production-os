# Sprint 3D — US-09 Implementation Report

**Date:** 2026-06-10  
**Status:** **ACCEPTED** — Olares re-verification complete (`evidence/us-09-verification/olares-2026-06-10-fix1/`)  
**Baseline:** `v0.3.1-us13`  
**Tag:** `v0.3.2-us09`  
**Governance:** `D-38`, `docs/sprints/sprint-3d-us09-governance-review.md`, `docs/sprints/sprint-3d-us09-implementation-plan.md`

---

## 1. Summary

US-09 delivers STORY-stage regenerate execution after rejection: `POST /pipeline/regenerate`, Temporal `regenerate` signal, `run_story_agent` with rejection-note feedback, max-3 enforcement (429), and new append-only `ai-draft` versions (`D-38`).

| Deliverable | Status |
|---|---|
| `POST /pipeline/regenerate` (STORY only) | ✅ |
| `REGENERATION_REQUESTED` audit counter | ✅ |
| 429 on 4th request (no signal/audit) | ✅ |
| Temporal `regenerate` + inner loop | ✅ |
| Rejection note → Story Architect prompt | ✅ |
| Review Regenerate button | ✅ |
| SCRIPT/STORYBOARD → 501 | ✅ |
| Alembic migration | ❌ Not added |
| Branch promotion | ❌ Not added (`D-37`) |

---

## 2. Files changed

### aimpos-core
- `packages/aimpos-core/aimpos_core/events/audit.py` — `REGENERATION_REQUESTED`

### API
- `api/app/routes/pipeline.py` — regenerate route
- `api/app/infrastructure/temporal/client.py` — `signal_regenerate`
- `api/app/infrastructure/db/repositories/approval.py` — `latest_for_stage`
- `api/app/infrastructure/db/repositories/audit_event.py` — `count_regenerations`
- `api/tests/unit/test_pipeline_regenerate.py` — 4 tests
- `api/tests/unit/test_pipeline_start.py` — `FakeTemporal.regenerates`

### Worker
- `worker/app/temporal/workflows/spark_pipeline.py` — regenerate signal + loop
- `worker/app/temporal/activities/story.py` — `rejection_note` arg
- `worker/app/agents/story_architect/{state,graph,nodes}.py` — note injection
- `worker/tests/unit/test_story_architect.py` — rejection note test

### Web
- `web/src/api/{client,types}.ts` — `regeneratePipeline`
- `web/src/lib/storyReview.ts` — `selectLatestAiDraftStoryAsset`
- `web/src/routes/ReviewPage.tsx` — enabled Regenerate + 429 handling
- `web/src/tests/storyReview.test.ts` — ai-draft selection test

---

## 3. Test results

| Suite | Result |
|---|---|
| API unit | **76 passed** (+4 US-09) |
| Worker unit | **5 passed** (+1 US-09) |
| Web unit | **14 passed** (+1 US-09) |
| Web build | **PASS** |

Key US-09 tests:
- `test_regenerate_happy_path_signal_and_audit`
- `test_fourth_regenerate_returns_429_without_side_effects` — proves 429, no Temporal signal, no new audit row
- `test_regenerate_script_stage_returns_501`
- `test_draft_story_node_includes_rejection_note`

---

## 4. AC implementation mapping

| AC | Implementation | Evidence |
|---|---|---|
| AC-1 Regenerate triggers agent | API route + workflow loop + `run_story_agent` | Unit + Olares E2E (pending) |
| AC-2 New asset version | `store_story_markdown` reuse (`D-38`) | Worker path + Olares SQL |
| AC-3 Max 3 → 429 | Audit count at API | `test_fourth_regenerate_*` |
| AC-4 Note to agent | `approvals.rationale` → activity → prompt | `test_draft_story_node_includes_rejection_note` |

### 429 side-effect proof (unit)

`test_fourth_regenerate_returns_429_without_side_effects` verifies:
- HTTP **429**
- `len(fake.regenerates) == 0` (no Temporal signal)
- Audit `REGENERATION_REQUESTED` count unchanged at **3**

---

## 5. Constraints compliance

| Constraint | Compliant |
|---|---|
| D-37 no branch promotion | ✅ |
| D-38 append-only ai-draft | ✅ |
| No schema migration | ✅ |
| STORY only (501 elsewhere) | ✅ |
| No auto-regenerate | ✅ |
| No new pipeline status family | ✅ |
| Minimal workflow change (signal + loop) | ✅ |

---

## 6. Formal closure

| Item | Result |
|---|---|
| Initial Olares verification | REJECT — workflow defect (regen #2/#3 dropped) |
| Defect fix | `spark_pipeline.py` post-regen wait accepts `_regenerate_requested` |
| Re-verification | **ACCEPT** — `evidence/us-09-verification/olares-2026-06-10-fix1/` |
| Release tag | `v0.3.2-us09` |
