# US-09 Defect Fix Report — Regenerate Signal Dropped After First Regeneration

**Date:** 2026-06-10  
**Classification:** Implementation defect (governance-authorized targeted fix)  
**Story:** US-09 Regenerate after rejection · FEAT-03 · EPIC-02  
**Trigger:** US-09 Olares closure review **REJECT** (`evidence/us-09-verification/olares-2026-06-10/US-09-ACCEPTANCE-PACKAGE.md`)

---

## 1. Root-cause summary

`SparkPipelineWorkflow` (worker) implements the post-reject regeneration loop. After a regeneration
completed, the workflow waited at:

```python
await workflow.wait_condition(
    lambda: self._approval_granted or self._approval_rejected,
    timeout=timedelta(days=30),
)
```

A subsequent `regenerate` Temporal signal set `self._regenerate_requested = True` (the signal
handler accepts it — the run is `awaiting_approval` at the current stage), but the wait condition
never evaluated that flag, so the workflow never woke. Regenerations #2 and #3 were therefore
accepted by the API (HTTP 200, `REGENERATION_REQUESTED` audit appended, signal delivered) but the
worker never executed Story Architect again and no new `asset_versions` rows were created.

The defect was observable only on the second and later regenerations — the first regeneration is
reached through the initial post-reject wait, which already included `_regenerate_requested`.

## 2. The fix (minimal diff)

One condition extended in `worker/app/temporal/workflows/spark_pipeline.py` — the post-regeneration
wait now also accepts `_regenerate_requested`:

```python
await workflow.wait_condition(
    lambda: self._approval_granted
    or self._approval_rejected
    or self._regenerate_requested,
    timeout=timedelta(days=30),
)
```

When a regenerate signal wakes this wait, control returns to the existing
`while not self._approval_granted:` loop. Its head wait condition
(`approval_granted or regenerate_requested`) is already satisfied, so the loop proceeds directly to
the existing regeneration branch: clear flag → `sync_pipeline_status RUNNING` →
`_run_stage_generation` (Story Architect for STORY) → `sync_pipeline_status AWAITING_APPROVAL` →
wait again. Approve and reject behaviour at this wait is unchanged.

## 3. Scope confirmation

| Constraint | Status |
|---|---|
| Same pipeline run reused | ✅ regenerations stay within one `pipeline_runs` row |
| Same workflow reused | ✅ no new workflow, signal, or activity definitions |
| Same Story Architect reused | ✅ `_run_stage_generation` path untouched |
| No new status values | ✅ only existing RUNNING / AWAITING_APPROVAL transitions |
| No schema changes | ✅ no migration; no model edits |
| D-37 untouched | ✅ no branch-promotion changes |
| D-38 untouched | ✅ append-only `store_story_markdown` path unchanged |
| No workflow redesign | ✅ one wait-condition lambda extended |

## 4. Tests

| Suite | Result |
|---|---|
| API unit (`api/tests/unit`) | **76 passed** |
| Worker unit (`worker/tests/unit`) | **5 passed** |
| Web unit (vitest) | **14 passed** |

No existing test covered the workflow wait loop (no Temporal `WorkflowEnvironment` harness exists in
the worker test suite); the multi-regenerate behaviour is verified end-to-end on Olares
(see verification package).

## 5. Deployment note — stale in-flight run

The pre-fix run `8c35926c-0a4e-44ed-ac5a-ea3c178902cd` had the dropped regenerate signals **baked
into its Temporal history**. Replaying that history under the fixed code is inherently
non-deterministic (`TMPRL1100: Activity type of scheduled event 'run_stub_stage' does not match
activity command 'run_story_agent'`) — the fixed code would now act on signals the old code ignored.

Resolution (verification environment only):

1. `temporal workflow terminate spark-pipeline-8c35926c-…` (reason recorded).
2. `pipeline_runs` row set to existing enum status `CANCELLED`.

This is an unavoidable consequence of fixing a signal-dropping defect for runs already past the
defective wait; no production data exists. New runs are unaffected.

## 6. Verification

Full re-verification (V1–V7) executed on Olares with `aimpos-worker:us09-fix1`:
`evidence/us-09-verification/olares-2026-06-10-fix1/US-09-ACCEPTANCE-PACKAGE.md`
