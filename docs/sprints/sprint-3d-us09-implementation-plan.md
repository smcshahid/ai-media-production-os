# Sprint 3D — US-09 Implementation Plan

**Status:** **IMPLEMENTED** — pending formal closure review (`docs/sprints/sprint-3d-us09-implementation-report.md`).  
**Parent brief:** `docs/sprints/sprint-3d-us09-brief.md`  
**Governance review:** `docs/sprints/sprint-3d-us09-governance-review.md` (**ACCEPTED**)  
**Story:** US-09 Regenerate after rejection · FEAT-03 · P0 · 3 SP  
**Baseline:** `v0.3.1-us13` (`main` @ US-13 closure)  
**Decision record:** `D-38` (regeneration asset semantics)

---

## 0. Implementation summary

US-09 wires **regenerate execution** on top of closed US-08 (reject) and US-13 (affordance). Net-new work spans API, Temporal workflow, worker activity, agent prompt, web button, and audit enum — **no Alembic migration**.

| Layer | Net-new | Reuse |
|---|---|---|
| API | `POST /pipeline/regenerate`, audit counter, post-reject guards | `POST /pipeline/approve` contract unchanged |
| Temporal | `regenerate` signal + post-reject inner loop | `approve` / `reject` signals |
| Worker | `run_story_agent(rejection_note)`, prompt injection | `store_story_markdown`, Story Architect graph |
| Web | Enable Regenerate button + API client | Review story mode, polling, content reload |
| DB schema | — | `approvals`, `audit_events`, `asset_versions` |
| `aimpos-core` | `AuditEventType.REGENERATION_REQUESTED` | Existing audit types |

**Estimated effort:** 3 SP · ~2–3 days (backend + workflow track, then worker/agent, then frontend, then Olares verification).

---

## 1. Story breakdown

### 1.1 Backend tasks

| ID | Task | Files (expected) | Depends on |
|---|---|---|---|
| B-01 | Add `AuditEventType.REGENERATION_REQUESTED` | `packages/aimpos-core/aimpos_core/events/audit.py` | — |
| B-02 | Add `ApprovalRepository.latest_rejected_for_stage(run_id, stage)` | `api/app/infrastructure/db/repositories/approval.py` | — |
| B-03 | Add `AuditEventRepository.count_regenerations(run_id, stage)` | `api/app/infrastructure/db/repositories/audit_event.py` | B-01 |
| B-04 | Add `TemporalService.signal_regenerate(workflow_id, stage)` | `api/app/infrastructure/temporal/client.py` | — |
| B-05 | Implement `POST /pipeline/regenerate` route | `api/app/routes/pipeline.py` | B-02, B-03, B-04 |
| B-06 | Request/response models + OpenAPI registration | `api/app/routes/pipeline.py` | B-05 |
| B-07 | API unit tests for regenerate route | `api/tests/unit/test_pipeline_regenerate.py` | B-05 |

**B-05 validation order (fail-fast):**

1. Project exists  
2. Active run (`AWAITING_APPROVAL`)  
3. `body.stage == run.current_stage`  
4. **Stage allowlist:** `STORY` only → else **501**  
5. **Post-reject gate:** latest approval for `(run_id, stage)` is `REJECTED` → else **409**  
6. **Regeneration budget:** `count_regenerations >= 3` → **429** (no signal, no audit append)  
7. Load rejection note from B-02  
8. `signal_regenerate` → append `REGENERATION_REQUESTED` audit → commit  
9. Return 200

### 1.2 Workflow tasks

| ID | Task | Files (expected) | Depends on |
|---|---|---|---|
| W-01 | Add `_regenerate_requested` flag + `regenerate` signal handler | `worker/app/temporal/workflows/spark_pipeline.py` | — |
| W-02 | Replace post-reject `wait(approve)` with `wait(approve \| regenerate)` | same | W-01 |
| W-03 | On regenerate: re-run stage activity block (STORY → `run_story_agent`) | same | W-02 |
| W-04 | Pass `rejection_note` from `_state.last_rejection_note` to activity args | same | W-03 |
| W-05 | Workflow unit tests for signal handling | `worker/tests/unit/test_spark_pipeline_regenerate.py` | W-01..W-04 |

**W-03 loop structure (STORY stage only in workflow; API pins execution):**

```
after initial generate + sync AWAITING_APPROVAL:
  wait(approve | reject)
  if reject:
    while not approved:
      wait(approve | regenerate)
      if regenerate:
        sync RUNNING
        run_story_agent(project_id, run_id, rejection_note)
        sync AWAITING_APPROVAL
        wait(approve | reject)   # user may reject again with new note
      else:  # approve
        break
  append completed_stages; advance to next stage
```

### 1.3 Worker / agent tasks

| ID | Task | Files (expected) | Depends on |
|---|---|---|---|
| A-01 | Extend `run_story_agent(project_id, run_id, rejection_note=None)` | `worker/app/temporal/activities/story.py` | — |
| A-02 | Extend `run_story_architect_graph(..., rejection_note=None)` | `worker/app/agents/story_architect/graph.py` | — |
| A-03 | Add `rejection_note` to `StoryArchitectState` | `worker/app/agents/story_architect/state.py` | — |
| A-04 | Inject note into `draft_story_node` prompt (T-09-02) | `worker/app/agents/story_architect/nodes.py` | A-03 |
| A-05 | Optional: extend `configs/prompts/story_architect/v1.yaml` with `{revision_note_block}` | `configs/prompts/story_architect/v1.yaml` | A-04 |
| A-06 | Unit tests: prompt contains rejection note | `worker/tests/unit/test_story_architect_regenerate.py` | A-04 |

**Asset write:** reuse `store_story_markdown` — always `branch=ai-draft`, `is_ai_generated=true`, `version = MAX+1` (`D-38`). No update-in-place.

### 1.4 Frontend tasks

| ID | Task | Files (expected) | Depends on |
|---|---|---|---|
| F-01 | Add `regeneratePipeline({ project_id, stage })` client helper | `web/src/api/client.ts`, `web/src/api/types.ts` | B-05 |
| F-02 | Enable **Regenerate** button post-reject; disable during `RUNNING` | `web/src/routes/ReviewPage.tsx` | F-01 |
| F-03 | On success: `refresh()` pipeline + `loadStory()`; clear stale dirty state | `web/src/routes/ReviewPage.tsx` | F-02 |
| F-04 | Handle 429 with user-visible limit message | `web/src/routes/ReviewPage.tsx` | F-02 |
| F-05 | Update post-reject hint copy (remove "future update" wording) | `web/src/routes/ReviewPage.tsx` | F-02 |
| F-06 | Add `selectLatestAiDraftStoryAsset` or post-regenerate reload policy | `web/src/lib/storyReview.ts` | F-03 |
| F-07 | Web unit tests: button enablement + asset selection after regenerate | `web/src/tests/storyReview.test.ts` | F-06 |

**F-06 reload policy (`D-38`):** After regenerate, editor loads **latest `ai-draft`** by version (not human-edit) so the user sees the new model output. Human-edit rows remain in DB unchanged.

### 1.5 Tests

| ID | Task | Type | Covers |
|---|---|---|---|
| T-01 | Regenerate happy path → 200, audit row, signal called (mock Temporal) | API unit | AC-1 |
| T-02 | Regenerate creates no row when 429 | API unit | AC-3 |
| T-03 | 4th regenerate → 429, message contains limit | API unit | AC-3 |
| T-04 | Regenerate without prior reject → 409 | API unit | guard |
| T-05 | Regenerate SCRIPT stage → 501 | API unit | stage pin |
| T-06 | Regenerate when not `AWAITING_APPROVAL` → 409 | API unit | guard |
| T-07 | `run_story_agent` passes note to graph when provided | Worker unit | AC-4 |
| T-08 | `draft_story_node` includes note in prompt | Worker unit | AC-4 |
| T-09 | Workflow: regenerate signal sets flag; re-enters activity | Worker unit | AC-1 |
| T-10 | `store_story_markdown` increments version (regression) | Worker unit | AC-2, D-38 |
| T-11 | Approve/reject regression — `test_pipeline_approve.py` green | API unit | US-08 |
| T-12 | US-13 asset routes regression — `test_assets_us13.py` green | API unit | US-13 |
| T-13 | Web build + unit tests pass | CI | regression |
| T-14 | Smoke: `scripts/smoke/test_us09_regenerate.py` (new) | Smoke (Olares gate) | E2E AC-1..4 |

### 1.6 Verification tasks

| ID | Task | Deliverable |
|---|---|---|
| V-01 | Olares E2E: reject → regenerate → new ai-draft | `evidence/us-09-verification/<env>-<date>/` |
| V-02 | Write `US-09-ACCEPTANCE-PACKAGE.md` | evidence package |
| V-03 | SQL: `asset_versions` version chain, `REGENERATION_REQUESTED` count | `logs/` |
| V-04 | 4th regenerate → 429 capture | `logs/` |
| V-05 | Rejection note in worker log / prompt test reference | `logs/` |
| V-06 | UI screenshot: enabled Regenerate + post-regenerate editor | `screenshots/` |
| V-07 | US-13 + US-12 regression smoke | CI / Olares log |
| V-08 | Temporal history snippet: regenerate signal + `run_story_agent` | `logs/` |

---

## 2. Acceptance criteria traceability

| AC | Backend | Frontend | Tests | Verification |
|---|---|---|---|---|
| **AC-1** POST /pipeline/regenerate triggers agent for current stage | B-04, B-05, W-01..W-04, A-01 | F-01, F-02, F-03 | T-01, T-09, T-14 | V-01, V-08 |
| **AC-2** New `asset_version` with incremented version | A-01 (`store_story_markdown` reuse) | F-03, F-06 (reload new ai-draft) | T-10, T-14 | V-01, V-03 |
| **AC-3** Max 3 regenerations → 429 | B-01, B-03, B-05 | F-04 | T-02, T-03, T-14 | V-04 |
| **AC-4** Rejection note passed to agent | B-02, B-05, A-01..A-05, W-04 | — (note entered on reject, US-13) | T-07, T-08, T-14 | V-05 |

### Visual MVP task mapping (T-09-01..04)

| Backlog task | Implementation tasks |
|---|---|
| T-09-01 Implement regenerate endpoint | B-05, B-06, B-07 (T-01..T-06) |
| T-09-02 Pass rejection note to activity input | B-02, A-01..A-05, W-04 (T-07, T-08) |
| T-09-03 Enforce max 3 regenerations per stage | B-01, B-03, B-05 (T-02, T-03) |
| T-09-04 Increment version on regenerate | A-01 + `store_story_markdown` (T-10) — `D-38` |

---

## 3. Complete regenerate sequence

### 3.1 Preconditions

| Gate | Required |
|---|---|
| Run status | `AWAITING_APPROVAL` |
| Current stage | `STORY` |
| Latest stage decision | `REJECTED` (US-08) |
| Regeneration count | `< 3` `REGENERATION_REQUESTED` audit rows |
| Stage execution | `STORY` only (501 otherwise) |

Initial pipeline-start `run_story_agent` **does not** increment regeneration count.

### 3.2 End-to-end sequence (authoritative)

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as ReviewPage
    participant API as POST /pipeline/regenerate
    participant DB as Postgres
    participant T as SparkPipelineWorkflow
    participant W as Worker
    participant O as Ollama
    participant M as MinIO

    Note over User,M: Setup: STORY at AWAITING_APPROVAL; user rejected with note (US-08)

    User->>UI: Click Regenerate
    UI->>API: { project_id, stage: STORY }

    API->>DB: active run + stage match + AWAITING_APPROVAL
    API->>DB: stage in { STORY } else 501
    API->>DB: latest approval for stage == REJECTED else 409
    API->>DB: COUNT(REGENERATION_REQUESTED) for run+stage

    alt count >= 3
        API-->>UI: 429 regeneration limit reached
    else count < 3
        API->>DB: SELECT latest REJECTED.rationale AS rejection_note
        API->>T: signal regenerate(STORY)
        API->>DB: INSERT audit REGENERATION_REQUESTED
        API-->>UI: 200

        T->>W: sync_pipeline_status(RUNNING, STORY)
        T->>W: run_story_agent(project_id, run_id, rejection_note)
        W->>DB: fetch latest IDEA
        W->>O: generate with note-augmented prompt
        W->>M: PUT new story bytes
        W->>DB: INSERT asset_versions (STORY, ai-draft, version+1) per D-38
        W->>DB: audit STAGE_STARTED, AGENT_TASK_COMPLETED, ASSET_STORED

        T->>W: sync_pipeline_status(AWAITING_APPROVAL, STORY)
        T->>T: wait(approve | reject)

        UI->>API: poll status + reload latest ai-draft content
        UI-->>User: New treatment in editor
    end
```

### 3.3 Post-regenerate user options

| Action | Endpoint | Result |
|---|---|---|
| Approve | `POST /pipeline/approve` GRANT | Advance to SCRIPT (`D-37` — latest STORY version) |
| Reject again | `POST /pipeline/approve` REJECT + note | New REJECTED row; new note for next regenerate |
| Regenerate again | `POST /pipeline/regenerate` | Loop if count < 3 |
| Save edits | `PUT /assets/{id}` (US-13) | New human-edit version; independent of ai-draft chain |
| 4th regenerate | `POST /pipeline/regenerate` | **429** — no agent run |

---

## 4. Max-3 regeneration enforcement

### 4.1 Counter definition

| Property | Value |
|---|---|
| **What is counted** | `audit_events` where `event_type = REGENERATION_REQUESTED` and `payload.stage = <stage>` |
| **Scope** | Per `(pipeline_run_id, stage)` |
| **Excluded** | Initial `run_story_agent` on pipeline start |
| **Enforcement layer** | **API only** (before Temporal signal) |
| **Storage** | Append-only audit — **no new DB table** |

### 4.2 429 behavior (normative)

| Condition | HTTP | Body (example) | Side effects |
|---|---|---|---|
| `count >= 3` | **429** | `{ "detail": "regeneration limit reached for stage STORY (max 3 per run)" }` | No Temporal signal · no `REGENERATION_REQUESTED` row · no worker activity · no new asset version |
| `count == 2` → request | **200** | Standard regenerate response | Signal sent · audit appended · count becomes 3 |
| 4th request | **429** | Same as above | Pipeline remains `AWAITING_APPROVAL` / `STORY` |

### 4.3 Transaction order (accepted request)

```
1. BEGIN
2. SELECT count REGENERATION_REQUESTED (lock not required for MVP)
3. IF count >= 3 → ROLLBACK path → 429
4. signal_regenerate (external)
5. INSERT REGENERATION_REQUESTED audit
6. COMMIT
7. Return 200
```

If Temporal signal fails after count check: return **502**; do **not** append audit (mirror approve route failure handling).

### 4.4 Implementation tasks for limit

| Task | Responsibility |
|---|---|
| B-01 | Enum value |
| B-03 | `count_regenerations(run_id, stage)` |
| B-05 | Pre-check + 429 response |
| T-02, T-03 | Unit proof |
| V-04 | Olares 4-request sequence log |

---

## 5. Authoritative rejection-note source

### 5.1 Source of truth (ratified)

| Priority | Source | Field | When set |
|---|---|---|---|
| **1 (authoritative for API)** | `approvals` table | `rationale` | `POST /pipeline/approve` REJECT (US-08) |
| **2 (workflow transport)** | `SparkPipelineWorkflowState.last_rejection_note` | signal payload | `reject` signal handler |

**Rule:** API regenerate handler reads note via **B-02**:

```sql
SELECT rationale FROM approvals
 WHERE pipeline_run_id = :run_id
   AND stage = :stage
   AND decision = 'REJECTED'
 ORDER BY created_at DESC
 LIMIT 1;
```

If no row → **409** `"no rejection note found for stage"` (cannot regenerate without reject).

### 5.2 Note freshness

| Event | Note used on next regenerate |
|---|---|
| First reject with note A | A |
| Regenerate (no new reject) | A (same latest REJECTED row) |
| Second reject with note B | B (new latest REJECTED row) |
| Regenerate after second reject | B |

**No new persistence for US-09.** Multi-note history stays in immutable `approvals` rows.

### 5.3 Agent consumption path

```
approvals.rationale (API read)
  → run_story_agent(..., rejection_note=note)
  → StoryArchitectState.rejection_note
  → draft_story_node revision block in Ollama prompt
```

---

## 6. D-38 — Regeneration asset semantics

Recorded in `DECISIONS.md` as **D-38**:

> **Regeneration creates a new `ai-draft` asset version. Existing `ai-draft` versions remain immutable.**

### 6.1 Implications

| Behavior | Required |
|---|---|
| On regenerate | `INSERT` new `asset_versions` row: `branch=ai-draft`, `is_ai_generated=true`, `version = MAX(version)+1` |
| Prior ai-draft rows | **Never UPDATE or DELETE** |
| Prior human-edit rows | **Untouched** by regenerate |
| MinIO | New object at content-hash key; prior objects retained |
| Approve (`D-37`) | Approved story = latest STORY version by `version DESC` + APPROVED approval |

### 6.2 Version chain example

```
v1  ai-draft   (US-12 initial)
v2  human-edit (US-13 save — optional)
v3  ai-draft   (US-09 regenerate #1)  ← new row, v1 unchanged
v4  ai-draft   (US-09 regenerate #2)
```

### 6.3 UI reload rule

After regenerate, Review editor displays **latest `ai-draft`** (highest version where `branch=ai-draft`), not latest human-edit, so the user sees the new model output (`F-06`).

---

## 7. Impact analysis

### 7.1 API impact

| Change | Type |
|---|---|
| `POST /pipeline/regenerate` | **New route** |
| `PipelineRegenerateRequest/Response` models | **New** |
| `TemporalService.signal_regenerate` | **New method** |
| `ApprovalRepository.latest_rejected_for_stage` | **New query** |
| `AuditEventRepository.count_regenerations` | **New query** |
| `POST /pipeline/approve` | **No change** |
| `POST /pipeline/start` | **No change** |
| Asset routes (US-13) | **No change** |

### 7.2 Workflow impact

| Change | Type |
|---|---|
| `regenerate` signal | **New** |
| Post-reject wait: `approve \| regenerate` | **Modified** |
| Re-execute `run_story_agent` on regenerate | **New loop path** |
| `approve` / `reject` signal handlers | **Unchanged** |
| Workflow id / task queue | **Unchanged** (D-32) |
| SCRIPT / STORYBOARD stub path | **Unchanged** (API blocks regenerate) |

### 7.3 Audit impact

| Event | When | New? |
|---|---|---|
| `REGENERATION_REQUESTED` | API accepts regenerate | **Yes** — B-01 |
| `STAGE_STARTED` | Worker activity begins | Existing |
| `AGENT_TASK_COMPLETED` | Agent finishes | Existing |
| `ASSET_STORED` | New ai-draft persisted | Existing |
| `APPROVAL_RECORDED` | Reject / approve | Unchanged (US-08) |

**No Alembic migration** — `event_type` stored as `VARCHAR(32)`.

### 7.4 Asset-version impact

| Operation | `asset_versions` effect |
|---|---|
| Regenerate | **INSERT** new row (`ai-draft`, version+1) per **D-38** |
| Human edit (US-13) | Unchanged — separate `human-edit` INSERT |
| Approve | **No asset write** per **D-37** |
| Reject | **No asset write** |

---

## 8. Scope

### 8.1 IN SCOPE

| ID | Item |
|---|---|
| S-01 | `POST /pipeline/regenerate` with `{ project_id, stage }` |
| S-02 | STORY-stage execution via `run_story_agent` |
| S-03 | Temporal `regenerate` signal + workflow inner loop |
| S-04 | `REGENERATION_REQUESTED` audit counter + 429 at max 3 |
| S-05 | Rejection note from latest `approvals.rationale` → agent prompt |
| S-06 | New `ai-draft` version on each successful regenerate (`D-38`) |
| S-07 | Enable Review Regenerate button post-reject |
| S-08 | Olares closure verification (STORY only) |
| S-09 | `aimpos-core` audit enum extension |
| S-10 | Smoke script `test_us09_regenerate.py` |

### 8.2 OUT OF SCOPE

| ID | Item | Owner |
|---|---|---|
| X-01 | SCRIPT / STORYBOARD regenerate execution | US-14 / US-16 |
| X-02 | `run_stub_stage` on regenerate | — |
| X-03 | Auto-regenerate on reject | US-13 closed |
| X-04 | Regenerate after approve | — |
| X-05 | Branch promotion / copy-to-main | D-37 |
| X-06 | UPDATE/DELETE prior ai-draft versions | D-38 forbids |
| X-07 | Asset browser / history / diff UI | US-22 |
| X-08 | Alembic migration | — |
| X-09 | Changes to approve/reject API contract | US-08 |
| X-10 | Aggregate all historical reject notes to agent | MVP: latest only |
| X-11 | `POST /pipeline/regenerate` without prior reject | — |
| X-12 | Pipeline restart as regenerate substitute | US-07 |

---

## 9. API contract (draft)

### 9.1 `POST /pipeline/regenerate`

| Field | Value |
|---|---|
| Method / path | `POST /pipeline/regenerate` |
| Auth | Bearer token required |
| Body | `{ "project_id": "<uuid>", "stage": "STORY" }` |

**Responses:**

| Status | Condition |
|---|---|
| **200** | Regenerate accepted; signal sent; audit appended |
| **404** | Project not found / no active run |
| **409** | Not `AWAITING_APPROVAL` / stage mismatch / not post-reject |
| **422** | Invalid body |
| **429** | Regeneration limit reached (≥ 3) |
| **501** | `stage` is SCRIPT or STORYBOARD |
| **502** | Temporal signal failure |

**200 body (draft):**

```json
{
  "project_id": "<uuid>",
  "run_id": "<uuid>",
  "stage": "STORY",
  "status": "AWAITING_APPROVAL",
  "current_stage": "STORY",
  "regenerations_used": 1
}
```

---

## 10. Closure verification plan

### 10.1 Environments

| Environment | Role |
|---|---|
| **Olares** (`aimpos-mwayolares`) | Primary closure evidence (required) |
| **Local compose + CI** | Unit tests + smoke dev iteration |

### 10.2 Verification script outline

New: `deploy/k8s/us09-verify/verify_us09.sh` (mirror US-13 pattern)

```
SETUP: ensure STORY review gate (idea + start + poll)
V1: Reject with note
V2: Regenerate #1 — asset version increment, ai-draft, note in evidence
V3: Regenerate #2 — version increment again
V4: Regenerate #3 — version increment; count = 3
V5: Regenerate #4 — expect 429, no new asset row
V6: Approve — advance to SCRIPT (regression)
```

### 10.3 Per-AC evidence checklist

| AC | Evidence artifacts |
|---|---|
| AC-1 | `POST /pipeline/regenerate` 200 log; Temporal history; status `AWAITING_APPROVAL`/`STORY`; `STAGE_STARTED` audit |
| AC-2 | SQL `asset_versions`: monotonic versions, new `ai-draft` rows; prior rows unchanged (`D-38`); MinIO keys |
| AC-3 | Logs: 3× 200 then 4th 429; SQL count `REGENERATION_REQUESTED` = 3; no 4th asset row |
| AC-4 | Distinctive reject note in request; worker/prompt test ref; regenerated content spot-check |

### 10.4 Evidence package structure

```
evidence/us-09-verification/<env>-<date>/
├── US-09-ACCEPTANCE-PACKAGE.md
├── screenshots/
│   ├── v1-regenerate-button-enabled.png
│   └── v2-post-regenerate-editor.png
└── logs/
    ├── us09-verify.log
    ├── 01-reject.txt
    ├── 02-regenerate-1.txt
    ├── 03-regenerate-4th-429.txt
    ├── asset-versions.sql
    └── audit-regenerations.sql
```

### 10.5 Exit gate

- AC-1..AC-4 each **PASS** with mapped evidence on Olares.
- CI green: API unit (incl. T-11, T-12), worker unit, web build/test.
- US-12 + US-13 regression smokes pass.
- `D-38` documented in PR description.
- No Alembic migration in PR.
- SCRIPT/STORYBOARD regenerate returns 501 (negative test in package).

### 10.6 Recommended commit plan (post-implementation authorization)

| # | Scope | Message (draft) |
|---|---|---|
| C1 | aimpos-core enum + API regenerate route + tests | `feat(us09): POST /pipeline/regenerate with audit counter` |
| C2 | Workflow signal + run_story_agent note + agent prompt | `feat(us09): workflow regenerate loop and rejection note to agent` |
| C3 | Web Regenerate button + client | `feat(us09): enable Review regenerate control` |
| C4 | Smoke + Olares evidence | `test(us09): regenerate verification package` |

---

## 11. Implementation sequence (recommended)

```
Day 1:  B-01 → B-02 → B-03 → B-04 → B-05 → B-07 (T-01..T-06)
        W-01 → W-02 → W-05 (T-09)

Day 2:  W-03 → W-04
        A-01 → A-05 → A-06 (T-07, T-08, T-10)

Day 3:  F-01 → F-06 → F-07 (T-13)
        T-11, T-12, T-14
        V-01..V-08 → evidence package → closure request
```

**Dependency order:** API + workflow land before Olares E2E; worker/agent before full E2E; frontend can parallel after B-05 contract is stable.

---

## 12. Risk review

| # | Risk | Mitigation |
|---|---|---|
| R1 | Workflow deadlock after regenerate | W-05 unit tests; Olares V-08 Temporal history |
| R2 | 429 bypass via direct Temporal signal | API-only counter; no regenerate signal path outside API |
| R3 | Note stale after re-reject | B-02 always reads latest REJECTED |
| R4 | Editor shows human-edit after regenerate | F-06 explicit ai-draft selection |
| R5 | Ollama cost on 429 race | Count check before signal |
| R6 | SCRIPT 501 not tested | T-05 + verification negative case |

---

## 13. Pre-implementation checklist

- [ ] Governance review package accepted ✅
- [ ] This implementation plan accepted ⏳
- [ ] `D-38` recorded in `DECISIONS.md` ✅
- [ ] Baseline `v0.3.1-us13` checked out
- [ ] Olares access confirmed for closure
- [ ] US-13 Regenerate affordance present in baseline

---

## 14. Authorization gate

| Gate | Status |
|---|---|
| US-09 governance review | ✅ Accepted |
| US-09 implementation plan | ⏳ **Pending acceptance** |
| Code implementation | **Blocked** until plan accepted |

---

*Implementation plan for governance review. No code written. Awaiting implementation authorization.*
