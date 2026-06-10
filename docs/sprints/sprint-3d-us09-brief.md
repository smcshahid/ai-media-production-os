# Sprint 3D — US-09 Regenerate After Rejection (governance brief)

**Status:** **CLOSED** — formally accepted 2026-06-10 (`v0.3.2-us09`).  
**Story:** US-09 "Regenerate after rejection" · FEAT-03 Pipeline Orchestration · EPIC-02 · P0 · 3 SP · Sprint S2 (deferred to post-US-13).  
**Prerequisites (closed):** US-07 ✅ · US-08 ✅ · US-12 ✅ (`run_story_agent`) · US-13 ✅ (reject affordance + human-edit path).  
**Unblocks:** Full reject→regenerate→approve loop at STORY gate; later stages inherit the same contract when real agents land (US-14, US-16).

**Canonical source:** `GitHub Issues - Visual MVP.md` → Issue 15 `[US-09]` (4 ACs, tasks T-09-01..04).  
**Superseded detail:** `MVP Backlog.md` FEAT-03 / US-09 — used only to disambiguate; Visual MVP issue is authoritative.

---

## 1. Source review — approved scope for US-09

### 1.1 Approved acceptance criteria (Visual MVP Issue 15)

1. `POST /pipeline/regenerate` triggers agent for **current stage**.
2. New `asset_version` with **incremented version**.
3. **Max 3 regenerations per stage** → `429` after limit.
4. **Rejection note passed to agent**.

### 1.2 Approved tasks

| Task | Description |
|---|---|
| T-09-01 | Implement regenerate endpoint |
| T-09-02 | Pass rejection note to activity input |
| T-09-03 | Enforce max 3 regenerations per stage |
| T-09-04 | Increment version on regenerate |

### 1.3 US-13 boundary (closed — do not re-open)

US-13 delivered **reject + regenerate affordance only** (disabled button, post-reject hint).  
US-09 owns **execution**: API route, workflow signal/loop, worker re-invocation, version increment, note→agent, rate limit.

---

## 2. Acceptance criteria mapping

### AC-1 — `POST /pipeline/regenerate` triggers agent for current stage

| Dimension | Specification |
|---|---|
| **User action** | After rejecting a stage (pipeline `AWAITING_APPROVAL`, same `current_stage`), click **Regenerate** or call API directly. |
| **Expected behavior** | API validates active run + stage match + prior reject at this stage; sends Temporal **regenerate** signal; workflow re-executes the stage's generation activity (`run_story_agent` when `current_stage=STORY`); status transitions `AWAITING_APPROVAL` → `RUNNING` → `AWAITING_APPROVAL` at same stage. |
| **Data changes** | `sync_pipeline_status` rows; `STAGE_STARTED` / `AGENT_TASK_COMPLETED` audit (existing US-12 pattern). |
| **Evidence** | Network trace `POST /pipeline/regenerate` → 200; Temporal history shows regenerate signal + second `run_story_agent` schedule; `GET /pipeline/status` returns same `current_stage`, `status=AWAITING_APPROVAL`. |

### AC-2 — New `asset_version` with incremented version

| Dimension | Specification |
|---|---|
| **User action** | Complete regenerate (agent finishes). |
| **Expected behavior** | New STORY row on `branch=ai-draft`, `is_ai_generated=true`, `version = max(STORY versions)+1`. Prior versions (ai-draft + human-edit) **retained** — no deletion, no branch promotion (`D-37`). |
| **Data changes** | New `asset_versions` row + MinIO object; `ASSET_STORED` audit. |
| **Evidence** | SQL: version N+1 ai-draft row; content_hash differs from prior ai-draft unless model returns identical text (still new row). |

### AC-3 — Max 3 regenerations per stage → 429

| Dimension | Specification |
|---|---|
| **User action** | Regenerate 4th time at same stage in same run. |
| **Expected behavior** | API returns **429** with limit message; **no** workflow signal; **no** agent invocation. |
| **Data changes** | None on 429. |
| **Evidence** | Four sequential regenerate calls: first three 200, fourth 429; counter source documented (see §4.3). |

### AC-4 — Rejection note passed to agent

| Dimension | Specification |
|---|---|
| **User action** | Reject with note, then regenerate. |
| **Expected behavior** | Latest `REJECTED` approval `rationale` for `(run_id, stage)` is passed into `run_story_agent` / Story Architect graph as revision context (prompt augmentation). |
| **Data changes** | None beyond agent inputs (note not duplicated if already in `approvals`). |
| **Evidence** | Audit payload or structured log showing note hash/length in activity input; generated treatment visibly addresses note (Olares spot-check) OR unit test asserts prompt contains note. |

---

## 3. Architecture impact (MVP-minimal)

### 3.1 Required changes

| Layer | Item | Notes |
|---|---|---|
| **API** | `POST /pipeline/regenerate` | Body: `{ project_id, stage }`. Auth + active-run guards mirror `POST /pipeline/approve`. |
| **API** | Regeneration counter | Count regenerations per `(pipeline_run_id, stage)` — recommend dedicated counter in workflow query state **or** count `REGENERATION_REQUESTED` audit events (decision at implementation plan). |
| **Temporal** | `regenerate` signal on `SparkPipelineWorkflow` | **Minimal workflow change required.** Today reject path waits only for `approve` (lines 113–116 `spark_pipeline.py`). Regenerate must re-enter stage activity loop without advancing stage. |
| **Worker** | Extend `run_story_agent` | Add optional `rejection_note: str | None` arg; pass to `run_story_architect_graph`. |
| **Agent** | Story Architect prompt | Inject latest rejection note into draft prompt (T-09-02). |
| **Web** | Enable Regenerate button | Wire existing disabled control in `ReviewPage.tsx` after reject; call regenerate endpoint; refresh status + reload treatment. |

### 3.2 Explicitly not required (scope control)

| Item | Rationale |
|---|---|
| `PUT /assets` / human-edit changes | US-13 closed (`D-37`) |
| Branch promotion / copy-to-main | `D-37` |
| `GET /assets` browser, history, diff | US-22 territory |
| Regenerate for SCRIPT / STORYBOARD **execution** | No real agents yet — return **501** or clear error until US-14/US-16; **do not** add stub regenerate that creates fake assets |
| New Alembic migration | Counter can use audit/workflow state for MVP unless implementation plan proves otherwise |
| `POST /pipeline/regenerate` on non-rejected stage | Reject — require latest decision REJECTED at stage (or workflow `last_rejection_note` set) |
| Auto-regenerate on reject | Reject path stays explicit two-step (US-08 + US-09) |
| Regenerate after approve | Out of scope — only post-reject |
| LakeFS / branch merge | Deferred |

### 3.3 Visual MVP stage scope (critical scope pin)

| Stage | Regenerate behavior in US-09 |
|---|---|
| **STORY** | **In scope** — re-invoke `run_story_agent` |
| **SCRIPT** | **Out of scope for execution** — no `run_script_agent` yet; endpoint may return 501 |
| **STORYBOARD** | **Out of scope for execution** — stub only |

Pin in implementation plan: US-09 closure verification runs on **STORY only**, matching US-12/US-13 Olares evidence pattern.

---

## 4. Workflow contract (proposed — ratify at implementation plan)

### 4.1 Current state (post-US-13)

```
generate → AWAITING_APPROVAL → wait(approve|reject)
  reject → wait(approve only) → approve → advance stage
```

No agent re-run on reject. `last_rejection_note` stored on workflow state.

### 4.2 Target state (US-09)

```
generate → AWAITING_APPROVAL → wait(approve|reject)
  reject → wait(approve|regenerate)
    regenerate → re-run stage activity → AWAITING_APPROVAL → wait(approve|reject)  [loop]
    approve → advance stage
```

**Constraints:**
- Regenerate does **not** clear human-edit versions; editor should reload **latest** STORY asset (may be human-edit if user saved — product decision: **regenerate always produces new ai-draft**, human-edit preserved in chain).
- Approve after human-edit still valid (`D-37`).

### 4.3 Regeneration counter (governance default)

**Default:** count `REGENERATION_REQUESTED` audit events per `(pipeline_run_id, stage)`; fourth request returns 429.  
Alternative (implementation plan): workflow state field `regeneration_count[stage]`. Either is acceptable if evidenced in tests.

---

## 5. Scope-control review

### 5.1 Primary creep risks

| Risk | Severity | Mitigation |
|---|---|---|
| **Implementing SCRIPT/STORYBOARD regenerate** before agents exist | High | STORY-only execution; 501 for other stages |
| **Collapsing US-09 into US-13** (auto-regenerate on reject) | Medium | Separate endpoint + explicit UI action |
| **Branch promotion on regenerate/approve** | Medium | `D-37` — ai-draft chain only |
| **Asset browser / diff UI** | Medium | Reload latest content in existing textarea only |
| **Rewriting approve/reject contract** | High | Reuse US-08 signals; add `regenerate` only |
| **Unbounded Ollama spend** | Medium | Max-3 enforced at API before signal |

### 5.2 Dependency regression surface

| Dependency | Regression check |
|---|---|
| US-08 approve/reject | Unchanged request/response; existing tests green |
| US-12 story generation | `run_story_agent` backward-compatible when `rejection_note=None` |
| US-13 review UI | Save / approve / reject still work; Regenerate enables only post-reject |
| US-10 dashboard | Status polling unchanged (`AWAITING_APPROVAL` / `RUNNING`) |

### 5.3 Out-of-scope backlog hooks (do not implement in US-09)

- US-14 Screenwriter agent
- US-16 Storyboard ComfyUI agent
- US-22 asset history UI
- Cross-stage regenerate
- Pipeline restart from IDEA

---

## 6. Verification strategy (exit gate)

| Check | Evidence |
|---|---|
| Reject → Regenerate → new ai-draft version | Olares API + SQL + MinIO |
| Note in agent context | Audit/log + prompt unit test |
| 4th regenerate → 429 | API test sequence |
| Approve still advances to SCRIPT | Reuse US-13 V3 pattern |
| Human-edit preserved after regenerate | SQL shows both human-edit and new ai-draft rows |
| No `/pipeline/regenerate` on IDLE/COMPLETED | Negative test |

**Recommended environment:** Olares (`aimpos-mwayolares`), same pattern as US-12/US-13.

---

## 7. Authorization gate

| Gate | Status |
|---|---|
| US-13 formally accepted | ✅ |
| This brief accepted | ⏳ Pending |
| Implementation plan | ⏳ Not started |
| Implementation | **Blocked** until brief + plan ratified |

**Estimated effort:** 3 SP (Visual MVP) — holds if STORY-only execution and minimal workflow loop.

---

## 8. Recommendation

US-09 is a **focused orchestration story**: one new API route, one new workflow signal, a small `run_story_agent` extension, and enabling the existing Review UI button. Keep verification **STORY-only**; defer SCRIPT/STORYBOARD execution to their agent stories. **Request governance acceptance of this brief before implementation authorization.**
