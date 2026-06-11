# Sprint 3F — US-15 Review and Approve Script (governance brief)

**Status:** RATIFIED for planning — **not authorized for implementation** until this brief is accepted.  
**Story:** US-15 "Review and approve script" · FEAT-07 Script Review & Approval · EPIC-03 · P0 · 3 SP · Sprint S3.  
**Prerequisites (all closed):** US-08 ✅ (approve/reject) · US-14 ✅ (`script.fountain`, SCRIPT gate, `D-39`/`D-40`) · US-09 ✅ (regenerate pattern at STORY) · US-26 ✅ (Review route shell).  
**Blocks:** US-16 (storyboard consumes approved script per `D-37`-style resolution).

**Canonical source:** `GitHub Issues - Visual MVP.md` → Issue 31 `[US-15]` (4 ACs, tasks T-15-01..04).  
**Superseded detail:** `MVP Backlog.md` → FEAT-07 / US-15 — used only to disambiguate; Visual MVP issue is authoritative.

---

## 1. Source Review

### 1.1 Approved acceptance criteria (Visual MVP Issue 31 — authoritative)

1. **Fountain rendered with formatting** — readable preview of the generated script.
2. **Approve advances to STORYBOARD_GENERATING** — pipeline leaves SCRIPT review and proceeds to storyboard stage.
3. **Reject/regenerate works** — rejection note + regenerate produces a new SCRIPT ai-draft version.
4. **Approved version marked in DB** — the accepted script is deterministically identifiable for downstream stages.

### 1.2 Approved tasks (Visual MVP Issue 31)

| Task | Description |
|---|---|
| T-15-01 | Build Review screen — script mode with Fountain preview |
| T-15-02 | Add basic Fountain-to-HTML formatter |
| T-15-03 | Wire approve/reject for script stage |
| T-15-04 | Mark approved script version in DB |

### 1.3 Backlog (FEAT-07) corroborating detail

- Review screen loads when script is ready; Fountain shows **scene heading** and **dialogue** with formatting.
- Approve → pipeline advances to **`STORYBOARD_GENERATING`** (presentation label; API remains `RUNNING`/`STORYBOARD` then review gate).
- Reject + regenerate → **new SCRIPT version** with **rejection note in agent context** (extends US-09 pattern to SCRIPT).
- Approved script → **marked as current approved version for stage SCRIPT** (see §5 — mirrors `D-37` Option A).

### 1.4 Dependencies

| Dependency | Status | Contract |
|---|---|---|
| US-14 SCRIPT asset + gate | ✅ Closed | `stage=SCRIPT`, `branch=ai-draft`, `AWAITING_APPROVAL`/`SCRIPT` |
| US-08 `POST /pipeline/approve` | ✅ Closed | GRANT/REJECT signals; immutable `approvals` rows |
| US-09 regenerate machinery | ✅ Closed at STORY | API 501 for SCRIPT today; **US-15 extends to SCRIPT** |
| US-13 content-read pattern | ✅ Closed | `GET /assets/{id}/content` — STORY only today |
| US-26 Review route | ✅ Closed | `ReviewPage.tsx` — STORY mode only |

**Hard dependency chain:** US-14 → **US-15** → US-16.

### 1.5 Presentation vs API status mapping

Issue AC-2 uses **`STORYBOARD_GENERATING`**. Per US-10 (`D-34`), dashboard maps `RUNNING` → **GENERATING**. After SCRIPT approve the API sequence is:

1. `RUNNING` / `STORYBOARD` (stub or future agent)
2. `AWAITING_APPROVAL` / `STORYBOARD` (when generation completes)

US-15 does **not** add new `PipelineRunStatus` or stage enum values.

---

## 2. Approved Scope

### 2.1 In scope (US-15)

| ID | Item | Rationale |
|---|---|---|
| S-01 | Review page **script mode** when `current_stage=SCRIPT` | T-15-01 |
| S-02 | Client-side **Fountain → HTML** formatter (basic) | T-15-02, AC-1 |
| S-03 | Load latest SCRIPT ai-draft via `GET /assets` + content read | AC-1 |
| S-04 | Approve/Reject wired to `POST /pipeline/approve` with `stage=SCRIPT` | T-15-03 |
| S-05 | Reject note UI (reuse STORY pattern) | AC-3 prerequisite |
| S-06 | **SCRIPT regenerate execution** — extend US-09 to SCRIPT stage | AC-3 |
| S-07 | `run_script_agent(rejection_note)` + Screenwriter prompt injection | AC-3 backlog detail |
| S-08 | Approved-script contract in DB per **`D-41` (proposed)** | T-15-04, AC-4 |
| S-09 | Extend `GET /assets/{id}/content` to SCRIPT bytes | Required enabler (mirror US-13) |
| S-10 | Worker/API/web unit tests + Olares verify package | Closure gates |
| S-11 | Append **`D-41`** to `DECISIONS.md` at implementation start | Approved-script semantics |

### 2.2 Optional (may defer without blocking AC)

| Item | Defer to |
|---|---|
| Human-edit save for Fountain (`PUT /assets/{id}`, `branch=human-edit` on SCRIPT) | Post-US-15 / US-22 if creator editing needed before approve |
| Inline Fountain text editor (raw `.fountain` textarea) | Optional enhancement; formatted preview satisfies AC-1 |
| `AGENT_TASK_FAILED` audit on validation errors | Implementation discretion |
| Stage filter on `GET /assets?stage=SCRIPT` | Client-side filter sufficient for MVP |

### 2.3 Out of scope (do not implement in US-15)

| Item | Owner |
|---|---|
| Storyboard / ComfyUI generation (`run_storyboard_agent`) | **US-16** |
| Multi-scene scripts | Scope Freeze |
| PDF / Fountain export download | Deferred |
| Asset history browser / diff view | **US-22** |
| `GET /lineage` API | **US-20** |
| Alembic schema migration | Not needed |
| New pipeline status family (`SCRIPT_REVIEW`, etc.) | Forbidden |
| Branch promotion / copy-to-`main` on approve | Forbidden (`D-37` parity) |

---

## 3. Acceptance Criteria Mapping

### AC-1 — Fountain rendered with formatting

| Dimension | Detail |
|---|---|
| **User action** | Navigate to Review while `AWAITING_APPROVAL` / `SCRIPT`. |
| **System behavior** | Load latest SCRIPT `asset_versions` row (`branch=ai-draft` at gate); fetch Fountain bytes; render HTML preview with distinguished scene heading, action paragraphs, character cues, and dialogue blocks. |
| **Data changes** | None (read-only). |
| **Evidence** | Screenshot/DOM of formatted preview; network trace `GET /assets/{id}/content`; sample matches MinIO object; formatter unit tests for scene heading + dialogue. |

### AC-2 — Approve advances to STORYBOARD generating

| Dimension | Detail |
|---|---|
| **User action** | Click **Approve** at SCRIPT gate. |
| **System behavior** | `POST /pipeline/approve` `{stage:SCRIPT, decision:GRANT}` → Temporal `approve` signal → workflow advances SCRIPT → STORYBOARD; worker runs STORYBOARD generation (stub until US-16); status becomes `RUNNING`/`STORYBOARD` then `AWAITING_APPROVAL`/`STORYBOARD` when stub completes. Dashboard shows **GENERATING** then **REVIEW** at storyboard gate. |
| **Data changes** | `approvals` row (`stage=SCRIPT`, `decision=APPROVED`); `APPROVAL_RECORDED` audit; `sync_pipeline_status` updates. |
| **Evidence** | `approvals` SQL row; status JSON pre/post approve; Temporal history shows STORYBOARD activity scheduled; dashboard stepper advances past SCRIPT. |

### AC-3 — Reject/regenerate works

| Dimension | Detail |
|---|---|
| **User action** | Enter note → **Reject** → **Regenerate** (up to 3× per US-09 cap). |
| **System behavior** | Reject: `POST /pipeline/approve` REJECT + note → stays `AWAITING_APPROVAL`/`SCRIPT`. Regenerate: `POST /pipeline/regenerate` `{stage:SCRIPT}` → `REGENERATION_REQUESTED` audit → workflow re-invokes `run_script_agent` with `rejection_note` → new ai-draft SCRIPT version (`D-38`/`D-39` append-only) → UI reloads latest ai-draft preview. 4th regenerate → **429**, no side effects. |
| **Data changes** | Reject: `approvals` REJECTED + audit. Regenerate: new `asset_versions` SCRIPT row, incremented version, new MinIO object, new lineage edge (parent story unchanged), audit chain. |
| **Evidence** | Olares/SQL version chain; `REGENERATION_REQUESTED` audit; worker log `script_agent_completed` with rejection note in prompt; 429 test; UI shows new preview after regen. |

### AC-4 — Approved version marked in DB

| Dimension | Detail |
|---|---|
| **User action** | Approve script (AC-2). |
| **System behavior** | Per **`D-41` (proposed)**: "approved script" = **latest SCRIPT `asset_versions` row at approve time** + **`APPROVED` `approvals` row for `stage=SCRIPT`**. No branch promotion, no extra asset write on approve. US-16 resolves input via this contract. |
| **Data changes** | `approvals` row only (no new SCRIPT asset on approve). |
| **Evidence** | SQL: `approvals` SCRIPT/APPROVED + latest SCRIPT version id/hash unchanged after approve; documented query for US-16 consumer. |

---

## 4. Script Review UX Requirements

### 4.1 Mode detection

| Condition | Review mode |
|---|---|
| `AWAITING_APPROVAL` + `current_stage=SCRIPT` | **Script mode** (US-15) |
| `AWAITING_APPROVAL` + `current_stage=STORY` | Story mode (US-13 — unchanged) |
| Other stages | Existing redirect-to-dashboard behavior |

### 4.2 Script mode layout

| Element | Requirement |
|---|---|
| Header | `Review — Script` + REVIEW badge (reuse STORY chrome) |
| Lead copy | Explain: preview AI-generated Fountain script; approve to advance to storyboard, or reject with note to regenerate |
| Metadata strip | Version, branch (`ai-draft`), AI-generated badge |
| **Fountain preview pane** | Rendered HTML (T-15-02); scrollable; monospace/action styling acceptable |
| Reject note | Reuse `reject-note` textarea; required on reject |
| Actions | **Approve**, **Reject**, **Regenerate** (enabled after reject, same affordance rules as STORY/US-09) |
| Regenerate 429 | Surface API error message; disable or explain limit |

### 4.3 Fountain formatter minimum (T-15-02)

Client-side parser — **not** a full Fountain spec implementation:

| Element | Detection | HTML output |
|---|---|---|
| Scene heading | Line matching `INT.` / `EXT.` / `INT/EXT.` / `I/E.` | `<h2 class="fountain-scene">` |
| Action | Non-empty lines not matching heading/cue/parenthetical/title-page | `<p class="fountain-action">` |
| Character cue | ALL-CAPS line per US-14 validator convention | `<p class="fountain-character">` |
| Dialogue | Lines following character cue | `<p class="fountain-dialogue">` |
| Parenthetical | `(…)` under character | `<p class="fountain-parenthetical">` |
| Title page | `Title:`, `Author:`, etc. (optional) | `<p class="fountain-title-page">` |

Invalid or empty Fountain → show error state with link to raw content (optional fallback `<pre>`).

### 4.4 Accessibility / MVP constraints

- Plain preview (no PDF viewer, no Final Draft integration).
- Single-column layout matching existing Review page card pattern.
- No autosave, no collaborative editing.

---

## 5. Asset Versioning Behavior

### 5.1 Review target selection

At SCRIPT gate, UI loads **latest SCRIPT version** where `branch=ai-draft` and `is_ai_generated=true` (mirror `selectLatestAiDraftStoryAsset` for STORY).

After regenerate, reload **latest ai-draft** SCRIPT (version monotonic per `D-38`/`D-39`).

### 5.2 Regenerate semantics (SCRIPT)

| Field | Value |
|---|---|
| New row | Append-only `asset_versions` |
| `stage` | `SCRIPT` |
| `branch` | `ai-draft` |
| `is_ai_generated` | `true` |
| `version` | `COALESCE(MAX(version),0)+1` per `(project_id, SCRIPT)` |
| MinIO | New content-addressed object; prior objects immutable |
| Lineage | New edge story parent → new script child (same story parent id from `fetch_approved_story`) |

### 5.3 Proposed decision — D-41 (approved script resolution)

**To be appended at US-15 implementation start** (mirrors `D-37`):

> An "approved script" is represented by (a) the **latest SCRIPT asset version** at the time of approval and (b) an **`APPROVED` `approvals` record for `stage=SCRIPT`**. There is **NO branch promotion, NO copy-to-`main`, and NO additional asset write during approval**. US-16 **MUST** resolve the approved script by reading the latest SCRIPT version, gated by the `APPROVED` `approvals` row.

### 5.4 Human-edit (explicitly out of AC)

Visual MVP Issue 31 does **not** require Save/human-edit for script. Defer `PUT /assets/{id}` SCRIPT support unless governance amends AC during implementation plan review.

---

## 6. Approval/Rejection Behavior

### 6.1 Approve (SCRIPT)

```
POST /pipeline/approve
{ project_id, stage: "SCRIPT", decision: "GRANT" }
```

- Validates active run `AWAITING_APPROVAL` + stage match.
- Temporal `approve` signal → workflow exits SCRIPT wait loop → STORYBOARD generation.
- Immutable `approvals` row + `APPROVAL_RECORDED` audit (US-08 path, unchanged).

### 6.2 Reject (SCRIPT)

```
POST /pipeline/approve
{ project_id, stage: "SCRIPT", decision: "REJECT", note: "<required>" }
```

- Workflow stays at SCRIPT; `last_rejection_note` set (existing signal handler).
- UI shows regenerate affordance (enabled after reject, same as STORY).

### 6.3 Regenerate (SCRIPT) — US-09 extension

```
POST /pipeline/regenerate
{ project_id, stage: "SCRIPT" }
```

**Required changes (in scope):**

| Layer | Change |
|---|---|
| API | Add `PipelineStage.SCRIPT` to `_SUPPORTED_REGENERATE_STAGES` |
| Workflow | Pass `rejection_note` to `run_script_agent` in `_run_stage_generation` (mirror STORY) |
| Worker | `run_script_agent(project_id, run_id, rejection_note="")` |
| Screenwriter | `ScreenwriterState.rejection_note` + prompt injection in `draft_script` node |
| Web | `handleRegenerate` loads script preview when `stage=SCRIPT` |

Preconditions unchanged from US-09: latest stage approval must be REJECTED; max 3 regenerations per run; 429 on 4th.

---

## 7. Architecture Impact

### 7.1 API

| Item | Change |
|---|---|
| `GET /assets/{id}/content` | **Extend** — allow `stage=SCRIPT` in addition to STORY; `text/plain` response |
| `POST /pipeline/regenerate` | **Extend** — SCRIPT stage execution (remove 501 for SCRIPT) |
| `POST /pipeline/approve` | **Reuse** — no contract change |
| `PUT /assets/{id}` for SCRIPT | **Not required** (human-edit out of AC) |
| Alembic migration | **None** |

### 7.2 Web

| Item | Change |
|---|---|
| `ReviewPage.tsx` | Script mode branch; Fountain preview component |
| `lib/fountainFormat.ts` (or similar) | T-15-02 formatter + unit tests |
| `lib/scriptReview.ts` (or similar) | `selectLatestAiDraftScriptAsset` |
| `api/client.ts` | No new endpoints if content-read extension suffices |
| Dashboard / stepper | **Regression only** — SCRIPT review CTA already routes to `/review` |

### 7.3 Worker

| Item | Change |
|---|---|
| `run_script_agent` | Add `rejection_note` arg; pass to graph |
| `screenwriter/nodes.py` | Inject revision block when note present |
| `screenwriter/state.py` | Add `rejection_note` field |
| Workflow | One-line arg extension for SCRIPT branch |
| Storyboard stub | **Unchanged** — US-16 replaces later |

### 7.4 Workflow

| Item | Change |
|---|---|
| Post-reject regenerate loop | **Reuse** US-09 loop (already stage-agnostic) |
| Wait-condition lambdas | **Do not modify** except SCRIPT activity args (US-09 lesson) |
| New signals / statuses | **Forbidden** |

### 7.5 Audit

| Event | Change |
|---|---|
| `APPROVAL_RECORDED` | Reuse on SCRIPT approve/reject |
| `REGENERATION_REQUESTED` | New rows with `payload.stage=SCRIPT` |
| `STAGE_STARTED` / `AGENT_TASK_COMPLETED` / `ASSET_STORED` | Reuse on SCRIPT regen (US-14 path) |

---

## 8. Scope Control

### 8.1 Boundary register

| Capability | Owner |
|---|---|
| Fountain HTML preview + SCRIPT approve/reject UI | **US-15** |
| SCRIPT regenerate execution + rejection note → agent | **US-15** (extends US-09) |
| Approved script resolution (`D-41`) | **US-15** |
| ComfyUI storyboard frames | **US-16** |
| Script human-edit save | **Deferred** (not in Visual MVP AC) |
| Asset history / diff | **US-22** |
| Audit trail viewer | **US-23** |

### 8.2 Primary creep risks

| Risk | Guard |
|---|---|
| Implementing `run_storyboard_agent` in US-15 | Stop at STORYBOARD stub gate; US-16 only |
| Full Fountain spec parser dependency | Lightweight formatter only |
| Schema migration for "approved version" column | Use `approvals` + latest version (`D-41`) |
| Duplicating STORY editor UX for raw Fountain editing | Preview-first; no textarea requirement in AC |

---

## 9. Verification Plan

### 9.1 Unit tests

| ID | File | Assertion |
|---|---|---|
| T-01 | `web/src/tests/fountainFormat.test.ts` | Scene heading, dialogue, action rendered |
| T-02 | `web/src/tests/scriptReview.test.ts` | Latest ai-draft SCRIPT selection |
| T-03 | `api/tests/unit/test_assets_us15.py` | Content read returns SCRIPT bytes |
| T-04 | `api/tests/unit/test_pipeline_regenerate.py` | SCRIPT regenerate happy path + 501 removed |
| T-05 | `worker/tests/unit/test_screenwriter.py` | Rejection note in prompt |
| T-06 | Regression | API 76+, worker 16+, web 14+ green |

### 9.2 Smoke / E2E (local or compose)

1. Reach SCRIPT gate (idea → start → approve STORY).
2. Open Review — formatted Fountain visible.
3. Reject with note → Regenerate → new SCRIPT version in SQL.
4. Approve SCRIPT → status advances to STORYBOARD stage.
5. Assert `approvals` SCRIPT/APPROVED + latest SCRIPT version id stable.

### 9.3 Olares verification

**Script:** `deploy/k8s/us15-verify/verify_us15.sh` (to be authored at implementation).

| Check | Evidence |
|---|---|
| V-01 | Fountain preview screenshot / HTML sample |
| V-02 | SCRIPT reject → regen → v2 ai-draft |
| V-03 | 4th SCRIPT regen → 429 |
| V-04 | SCRIPT approve → `AWAITING_APPROVAL`/`STORYBOARD` |
| V-05 | `approvals` SCRIPT/APPROVED + D-41 resolution query |
| V-06 | US-14 regression — fresh run still produces SCRIPT v1 |
| V-07 | US-09 STORY regen regression |

**Package:** `evidence/us-15-verification/olares-<date>/US-15-ACCEPTANCE-PACKAGE.md`

### 9.4 Closure criteria

All four Visual MVP ACs evidenced on Olares → **ACCEPT**; partial local-only → **CONDITIONAL ACCEPT**.

---

## 10. Risk Assessment

| ID | Risk | L | I | Mitigation |
|---|---|---|---|---|
| R1 | Fountain formatter misclassifies valid US-14 output | M | M | Fixture tests from Olares US-14 sample; optional raw `<pre>` fallback |
| R2 | SCRIPT regenerate breaks US-09 STORY path | L | H | Extend allowlist only; regression suite; no wait-loop edits |
| R3 | `GET /assets/content` opened too wide (non STORY/SCRIPT) | L | M | Stage guard in route; unit tests for 422 on IDEA |
| R4 | Rejection note not reaching Screenwriter | L | H | Mirror US-09 story test pattern; Olares audit/log check |
| R5 | Approved script ambiguity for US-16 | M | H | **`D-41`** decision + SQL evidence at approve time |
| R6 | Scope creep into US-16 storyboard agent | M | M | Approve advances to **stub** STORYBOARD only |
| R7 | In-flight SCRIPT runs nondeterministic after worker change | L | M | Document: fresh runs after deploy; cancel stale runs |
| R8 | 429/regen limit confusion at SCRIPT | L | L | Reuse STORY UX copy; same API error contract |
| R9 | Human-edit demand mid-sprint | M | L | Explicitly out of AC; defer to amendment if needed |

---

## 11. Governance attestation

US-15 is a **low-scope UI + API-extension story (3 SP)** that completes the **script review gate** opened by US-14. It reuses US-08 approval, US-09 regenerate machinery, and US-13 content-read patterns without schema migrations or new pipeline statuses. It unblocks **US-16** by establishing the approved-script contract (`D-41`).

**Request: governance acceptance of this brief before implementation authorization.**
