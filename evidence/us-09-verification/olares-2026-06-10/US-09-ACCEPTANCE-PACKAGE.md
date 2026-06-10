# US-09 Acceptance Package — Olares Verification

**Environment:** Olares (`olares@10.0.0.34`, namespace `aimpos-mwayolares`)  
**Date:** 2026-06-10  
**API image:** `docker.io/library/aimpos-api:us09`  
**Worker image:** `docker.io/library/aimpos-worker:us09`  
**Project:** `ba0c4636-817c-423b-9771-20100e080b76`  
**Run:** `8c35926c-0a4e-44ed-ac5a-ea3c178902cd`  
**Verify log:** `logs/us09-verify.log`

---

## Verification summary

| Check | Result |
|---|---|
| V1 — Reject story, pipeline stays STORY | **PASS** |
| V2 — Regenerate #1 (agent + new ai-draft version) | **PASS** |
| V3 — Regenerate #2 and #3 (version chain v→v+1) | **FAIL** |
| V4 — 4th regenerate returns 429, no side effects | **PASS** |
| V5 — Approve final draft → SCRIPT | **PASS** |
| V6 — D-38 append-only version chain | **PARTIAL** |

---

## Deployment (verification prerequisite)

US-09 was not present on Olares (`POST /pipeline/regenerate` returned 404 against `aimpos-api:us13`). Images were built on-node via `nerdctl` and rolled out:

| Component | Image | Action |
|---|---|---|
| API | `docker.io/library/aimpos-api:us09` | `kubectl set image` + rollout |
| Worker | `docker.io/library/aimpos-worker:us09` | `kubectl set image` + rollout |

Scripts: `deploy/k8s/us09-verify/deploy_api.sh`, `deploy_worker.sh`, `verify_us09.sh`

---

## V1 — Reject story

**Precondition:** `AWAITING_APPROVAL` / `current_stage=STORY`

### API response

```
POST /pipeline/approve
{"project_id":"ba0c4636-817c-423b-9771-20100e080b76","stage":"STORY","decision":"REJECT","note":"US-09 Olares verify: deepen Act III."}
```

```json
{
  "approval_id": "44969fec-0fbf-4747-9a42-7fa0bc007e03",
  "decision": "REJECTED",
  "stage": "STORY",
  "status": "AWAITING_APPROVAL",
  "current_stage": "STORY"
}
```

### Approval row

| id | stage | decision | rationale |
|---|---|---|---|
| `44969fec-0fbf-4747-9a42-7fa0bc007e03` | STORY | REJECTED | US-09 Olares verify: deepen Act III. |

### Audit

```
APPROVAL_RECORDED | decision=REJECTED | note="US-09 Olares verify: deepen Act III." | 2026-06-10 22:32:16
```

### Pipeline status (unchanged stage)

| Field | Value |
|---|---|
| status | `AWAITING_APPROVAL` |
| current_stage | `STORY` |

| Assertion | Expected | Observed |
|---|---|---|
| Rejection recorded | yes | **PASS** |
| Rationale stored | yes | **PASS** |
| Pipeline remains STORY | yes | **PASS** |

---

## V2 — Regenerate #1

### API response

```
POST /pipeline/regenerate
HTTP 200
```

```json
{
  "stage": "STORY",
  "status": "AWAITING_APPROVAL",
  "current_stage": "STORY",
  "regenerations_used": 1
}
```

### `asset_versions` — before

| id | version | branch | is_ai_generated |
|---|---|---|---|
| `b87c4c5b-…` | 1 | ai-draft | true |
| `d02b1e64-…` | 2 | human-edit | false |
| `c6a43261-…` | 3 | ai-draft | true |

### `asset_versions` — after

| id | version | branch | is_ai_generated | content_hash (prefix) |
|---|---|---|---|---|
| `b87c4c5b-…` | 1 | ai-draft | true | `52f69b19…` |
| `d02b1e64-…` | 2 | human-edit | false | `a469cbdb…` |
| `c6a43261-…` | 3 | ai-draft | true | `aa917060…` |
| `b736740b-137e-4942-9151-1f44fbf500e6` | **4** | **ai-draft** | **true** | `104891e5…` |

| Assertion | Expected | Observed |
|---|---|---|
| Regeneration accepted | HTTP 200 | **PASS** |
| Story Architect executed | `STAGE_STARTED` + `AGENT_TASK_COMPLETED` | **PASS** |
| Rejection note supplied | audit ties to `44969fec…` reject | **PASS** |
| Version increment 3→4 | new row | **PASS** |
| branch=ai-draft | true | **PASS** |
| Pipeline AWAITING_APPROVAL/STORY | unchanged gate | **PASS** |

### Worker evidence

```
STAGE_STARTED | agent.story_architect | 22:32:16
AGENT_TASK_COMPLETED | qwen3:14b | asset_version_id=b736740b… | duration_ms=19146 | 22:32:36
```

### Audit

```
REGENERATION_REQUESTED | rejection_approval_id=44969fec… | 22:32:16
ASSET_STORED | version=4 | branch=ai-draft | 22:32:36
```

---

## V3 — Regenerate #2 and #3

### API responses (both accepted)

| Request | HTTP | regenerations_used |
|---|---|---|
| Regenerate #2 | 200 | 2 |
| Regenerate #3 | 200 | 3 |

### Expected vs observed version chain

| Step | Expected version | Observed |
|---|---|---|
| After regen #1 | v4 | v4 ✅ |
| After regen #2 | v5 | **v4 — no new row** ❌ |
| After regen #3 | v6 | **v4 — no new row** ❌ |

### Audit events for regens 2–3

```
REGENERATION_REQUESTED | 22:32:47  (regen #2 — API + audit only)
REGENERATION_REQUESTED | 22:42:53  (regen #3 — API + audit only)
```

**No** matching `STAGE_STARTED` / `AGENT_TASK_COMPLETED` / `ASSET_STORED` after the first regeneration.

### Worker evidence

Worker log shows exactly **one** post-reject `run_story_agent` completion (`activity_id=5`, asset `b736740b…`). No additional story-agent activity after regen #2/#3 signals.

| Assertion | Expected | Observed |
|---|---|---|
| v4 → v5 (regen #2) | new ai-draft row | **FAIL** |
| v5 → v6 (regen #3) | new ai-draft row | **FAIL** |
| Agent execution per regen | 3× total | **1× only** |

### Root cause (verification blocker)

In `worker/app/temporal/workflows/spark_pipeline.py`, after a regeneration completes the workflow waits only for `_approval_granted` or `_approval_rejected` (lines 156–159). It does **not** listen for `_regenerate_requested` in that wait. Subsequent `regenerate` Temporal signals are therefore **silently ignored** while the workflow sits at the post-regen approval gate.

The API layer correctly accepts regens #2–#3 (audit appended, Temporal signal sent), but the worker never executes additional Story Architect runs.

---

## V4 — Regenerate #4 (429 governance gate)

### API response

```
POST /pipeline/regenerate (4th request)
HTTP 429
{"detail":"regeneration limit reached for stage STORY (max 3 per run)"}
```

### Side-effect proof

| Check | Before | After | Unchanged? |
|---|---|---|---|
| `REGENERATION_REQUESTED` count | 3 | 3 | **YES** |
| Total audit rows (run) | 12 | 12 | **YES** |
| `asset_versions` STORY rows | 4 versions | 4 versions | **YES** |
| Worker story-agent activity | none new | none new | **YES** |

```
VERSIONS_UNCHANGED=YES
AUDIT_UNCHANGED=YES
```

### API log

```json
{"path": "/pipeline/regenerate", "status_code": 429, "duration_ms": 8.09}
```

| Assertion | Expected | Observed |
|---|---|---|
| HTTP 429 | yes | **PASS** |
| No new asset_versions row | yes | **PASS** |
| No new audit row | yes | **PASS** |
| No Temporal-driven agent run | yes | **PASS** |

---

## V5 — Approval continuity

Executed separately with correct enum `APPROVED` (initial verify script used invalid `APPROVE`).

### API response

```
POST /pipeline/approve {"decision":"APPROVED"}
HTTP 200
```

```json
{
  "approval_id": "9170c103-0b8b-4fed-96e5-ac70436520a3",
  "decision": "APPROVED",
  "stage": "STORY",
  "status": "AWAITING_APPROVAL",
  "current_stage": "STORY"
}
```

### Pipeline after approve

```json
{
  "status": "AWAITING_APPROVAL",
  "current_stage": "SCRIPT",
  "updated_at": "2026-06-10T22:57:45.268374"
}
```

### Approval history (run)

| id | stage | decision | rationale |
|---|---|---|---|
| `0f415d6d-…` | STORY | REJECTED | US-13 Olares UI verify: … |
| `44969fec-…` | STORY | REJECTED | US-09 Olares verify: deepen Act III. |
| `9170c103-…` | STORY | APPROVED | (empty) |

### Workflow transition

| Gate | status | current_stage |
|---|---|---|
| Pre-approve | AWAITING_APPROVAL | STORY |
| Post-approve | AWAITING_APPROVAL | **SCRIPT** |

| Assertion | Expected | Observed |
|---|---|---|
| STORY → APPROVED recorded | yes | **PASS** |
| Advance to SCRIPT stage | yes | **PASS** |

Log: `logs/collect-post-v5.txt`

---

## V6 — D-38 compliance

### Full STORY version chain (post-verification)

| version | id | branch | is_ai_generated | content_hash (prefix) | created_at |
|---|---|---|---|---|---|
| 1 | `b87c4c5b-…` | ai-draft | true | `52f69b19…` | 18:14:09 |
| 2 | `d02b1e64-…` | human-edit | false | `a469cbdb…` | 20:14:23 |
| 3 | `c6a43261-…` | ai-draft | true | `aa917060…` | 20:15:32 |
| 4 | `b736740b-…` | ai-draft | true | `104891e5…` | 22:32:36 |

| Assertion | Expected | Observed |
|---|---|---|
| Append-only (no in-place updates) | prior rows unchanged | **PASS** |
| Regenerated drafts are new rows | v4 appended | **PASS** (partial — v5/v6 absent due to V3 blocker) |
| No asset row updates in place | hashes stable for v1–v3 | **PASS** |

---

## Temporal evidence

| Field | Value |
|---|---|
| workflow_id | `spark-pipeline-8c35926c-0a4e-44ed-ac5a-ea3c178902cd` |
| workflow_run_id | `06896552-e211-49f3-9856-de46862e614e` |

Activity sequence observed in worker logs for STORY regeneration:

1. `sync_pipeline_status` → RUNNING/STORY  
2. `run_story_agent` → `b736740b…` (v4)  
3. `sync_pipeline_status` → AWAITING_APPROVAL/STORY  

No further `run_story_agent` invocations after regen #2/#3 API signals.

---

## US-09 Closure Recommendation

**REJECT**

**Rationale:** V3 fails on Olares. The API and 429 governance gate (V4) behave correctly, and single-regeneration (V2), reject handling (V1), approval continuity (V5), and D-38 append-only semantics (V6) are evidenced. However, regenerations #2 and #3 are accepted at the API layer without worker execution or new `asset_versions` rows — a workflow signal-handling defect in `SparkPipelineWorkflow` blocks the required multi-regenerate chain.

**Required fix before re-verification:** After each regeneration completes, the post-regen wait must also accept `_regenerate_requested` (same as the initial post-reject loop), or loop back to the regenerate-capable wait without requiring a new reject between regenerations.

**No code changes were made during this verification run** per governance instructions; the blocker is reported for implementation fix and re-run.
