# US-09 Acceptance Package — Olares Re-Verification (post defect fix)

**Environment:** Olares (`olares@10.0.0.34`, namespace `aimpos-mwayolares`)  
**Date:** 2026-06-10  
**API image:** `docker.io/library/aimpos-api:us09` (unchanged)  
**Worker image:** `docker.io/library/aimpos-worker:us09-fix1` (defect fix)  
**Project:** `ba0c4636-817c-423b-9771-20100e080b76`  
**Run:** `980617a8-1f3d-46e9-9165-59ea72af742a` (fresh run, post-fix)  
**Verify log:** `logs/us09-fix1-verify.log` · **Temporal history:** `logs/temporal-history.txt`  
**Defect-fix report:** `docs/sprints/sprint-3d-us09-defect-fix-report.md`  
**Supersedes:** `evidence/us-09-verification/olares-2026-06-10/US-09-ACCEPTANCE-PACKAGE.md` (REJECT)

---

## Verification summary

| Check | Result |
|---|---|
| V1 — Reject story, pipeline stays STORY | **PASS** |
| V2 — Regenerate #1 → new ai-draft v6 | **PASS** |
| V3 — Regenerate #2 → new ai-draft v7 | **PASS** |
| V4 — Regenerate #3 → new ai-draft v8 | **PASS** |
| V5 — 4th regenerate returns 429, no side effects | **PASS** |
| V6 — Approve final draft → SCRIPT | **PASS** |
| V7 — D-38 append-only version chain complete | **PASS** |

---

## Defect fix under verification

One wait-condition lambda extended in `worker/app/temporal/workflows/spark_pipeline.py` — the
post-regeneration wait now also accepts `_regenerate_requested` (previously only
approve/reject), so regenerations #2 and #3 are no longer dropped. No other code changed.
Full root cause: `docs/sprints/sprint-3d-us09-defect-fix-report.md`.

**Test gates before deployment:** API unit 76 passed · worker unit 5 passed · web unit 14 passed.

**Stale-run cleanup (documented deviation):** the pre-fix run `8c35926c-…` had dropped regenerate
signals in its Temporal history and is non-deterministic under the fixed code (`TMPRL1100`). It was
terminated via Temporal CLI and its `pipeline_runs` row set to existing status `CANCELLED`. A fresh
run was started for re-verification.

---

## Setup — fresh STORY review gate

```
POST /ideas      → IDEA v4 (US-09 Fix1 Verify)
POST /pipeline/start → run 980617a8-1f3d-46e9-9165-59ea72af742a, RUNNING/STORY
poll             → AWAITING_APPROVAL / STORY
```

Initial Story Architect run produced STORY **v5** (`0a739db6-…`, ai-draft). Baseline chain at gate: v1–v5.

---

## V1 — Reject story

```
POST /pipeline/approve {"stage":"STORY","decision":"REJECT","note":"US-09 fix1 verify: raise the stakes in Act II."}
HTTP 200
```

| Field | Value |
|---|---|
| approval_id | `44243eeb-bcf3-4aaf-b2af-1f3b2e6065bf` |
| decision | REJECTED |
| rationale (DB `approvals.rationale`) | US-09 fix1 verify: raise the stakes in Act II. |
| status after | `AWAITING_APPROVAL` |
| current_stage after | `STORY` |

Audit: `APPROVAL_RECORDED | REJECTED | note="US-09 fix1 verify: raise the stakes in Act II."` @ 23:10:18

---

## V2 / V3 / V4 — Regenerate #1, #2, #3

All three accepted (HTTP 200) while the run remained `AWAITING_APPROVAL` / `STORY`, each producing a
**new ai-draft version** via a distinct Story Architect execution:

| Regen | HTTP | regenerations_used | New version | asset_version_id | content_hash (prefix) | run_story_agent activity_id |
|---|---|---|---|---|---|---|
| #1 | 200 | 1 | v5 → **v6** | `034ad36b-…` | `bf956036…` | 5 |
| #2 | 200 | 2 | v6 → **v7** | `1e06e977-…` | `28b87f9a…` | 8 |
| #3 | 200 | 3 | v7 → **v8** | `9facea33-…` | `21dc6323…` | 11 |

All new rows: `branch=ai-draft`, `is_ai_generated=true`.

### Audit chain (per regeneration)

```
REGENERATION_REQUESTED @23:10:19 → STAGE_STARTED → AGENT_TASK_COMPLETED (qwen3:14b, v6) → ASSET_STORED v6
REGENERATION_REQUESTED @23:10:34 → STAGE_STARTED → AGENT_TASK_COMPLETED (qwen3:14b, v7) → ASSET_STORED v7
REGENERATION_REQUESTED @23:10:50 → STAGE_STARTED → AGENT_TASK_COMPLETED (qwen3:14b, v8) → ASSET_STORED v8
```

Each `REGENERATION_REQUESTED` carries `rejection_approval_id=44243eeb-…` — the V1 rejection note is
the note supplied to the agent (`last_rejection_note` → `run_story_agent` arg → prompt).

### Worker evidence

Three distinct `story_agent_completed` log lines (activity_ids 5, 8, 11) for workflow
`spark-pipeline-980617a8-…`, asset ids matching v6/v7/v8. This is the behaviour that failed in the
pre-fix run (only activity 5 ever ran).

### Temporal history evidence (`logs/temporal-history.txt`)

Pattern repeats three times: `WorkflowExecutionSignaled` → `WorkflowTaskCompleted` → `TimerCanceled`
→ `ActivityTaskScheduled` (sync RUNNING) → `ActivityTaskScheduled` (run_story_agent) →
`ActivityTaskCompleted` — proving the second and third regenerate signals now wake the workflow.

---

## V5 — 4th regenerate (429 governance gate)

```
POST /pipeline/regenerate (4th)
HTTP 429
{"detail":"regeneration limit reached for stage STORY (max 3 per run)"}
```

| Check | Before | After | Unchanged? |
|---|---|---|---|
| `REGENERATION_REQUESTED` count | 3 | 3 | **YES** |
| Total audit rows (run) | 17 | 17 | **YES** |
| STORY `asset_versions` | v1–v8 | v1–v8 | **YES** (`VERSIONS_UNCHANGED=YES`) |
| Story Architect executions | 4 (initial + 3 regens) | 4 | **YES** — no new `run_story_agent` after 429 |

---

## V6 — Approve final regenerated draft → SCRIPT

```
POST /pipeline/approve {"stage":"STORY","decision":"APPROVED"}
HTTP 200 → approval_id 9460fc72-254d-4a8c-a80e-5210e465d717
```

| Gate | status | current_stage |
|---|---|---|
| Pre-approve | AWAITING_APPROVAL | STORY |
| Post-approve | AWAITING_APPROVAL | **SCRIPT** |

Approval rows for run `980617a8-…`:

| id | stage | decision | rationale |
|---|---|---|---|
| `44243eeb-…` | STORY | REJECTED | US-09 fix1 verify: raise the stakes in Act II. |
| `9460fc72-…` | STORY | APPROVED | — |

---

## V7 — D-38 proof (append-only version chain)

Full STORY chain for the project after verification — every row preserved, hashes of pre-existing
versions (v1–v5, including all prior-run drafts) byte-identical to earlier captures; no in-place
updates:

| version | id | branch | is_ai | content_hash (prefix) | created_at |
|---|---|---|---|---|---|
| 1 | `b87c4c5b-…` | ai-draft | true | `52f69b19…` | 18:14:09 |
| 2 | `d02b1e64-…` | human-edit | false | `a469cbdb…` | 20:14:23 |
| 3 | `c6a43261-…` | ai-draft | true | `aa917060…` | 20:15:32 |
| 4 | `b736740b-…` | ai-draft | true | `104891e5…` | 22:32:36 |
| 5 | `0a739db6-…` | ai-draft | true | `e64d4eaa…` | 23:10:17 |
| 6 | `034ad36b-…` | ai-draft | true | `bf956036…` | 23:10:33 |
| 7 | `1e06e977-…` | ai-draft | true | `28b87f9a…` | 23:10:48 |
| 8 | `9facea33-…` | ai-draft | true | `21dc6323…` | 23:11:06 |

| Assertion | Observed |
|---|---|
| All regenerated drafts append-only | **PASS** — v6, v7, v8 are new rows |
| Previous ai-draft versions unchanged | **PASS** — v1–v5 ids/hashes identical to pre-fix captures |
| No asset rows updated in place | **PASS** — monotonic version chain, distinct ids |

---

## Scope confirmation

| Constraint | Status |
|---|---|
| Same pipeline run reused across regens | ✅ all three regens on run `980617a8-…` |
| Same workflow reused | ✅ single `spark-pipeline-980617a8-…` execution |
| Same Story Architect reused | ✅ `run_story_agent` / `qwen3:14b` each time |
| No new status values | ✅ only RUNNING / AWAITING_APPROVAL observed |
| No schema changes | ✅ none |
| D-37 / D-38 unmodified | ✅ |

---

## US-09 Closure Recommendation

**ACCEPT**

All seven verification gates pass on Olares against the deployed fix (`aimpos-worker:us09-fix1`).
The reject → regenerate ×3 → 429 → approve loop is fully evidenced end-to-end with API, database,
audit, worker, and Temporal history proof, and D-38 append-only semantics hold across the complete
version chain. The single documented deviation (termination of the stale pre-fix run, required by
Temporal determinism) affects no acceptance criterion.
