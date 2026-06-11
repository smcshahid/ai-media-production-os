# Sprint 3H — US-17 Review Storyboard Gallery (governance brief)

**Status:** **CLOSED** — formally accepted 2026-06-11 (`v0.3.6-us17`, Olares verification PASS).  
**Story:** US-17 "Review storyboard gallery" · FEAT-09 Storyboard Review & Approval · EPIC-04 · P0 · 3 SP · Sprint S5.  
**Prerequisites (all closed):** US-08 ✅ (approve/reject) · US-09 ✅ (regenerate pattern) · US-16 ✅ (STORYBOARD frames, `D-43`/`D-44`/`D-45`, `run_storyboard_agent`) · US-26 ✅ (Review route shell).  
**Blocks:** US-V01 (Visual MVP E2E sign-off). **Does not block** US-20 (lineage viewer) or US-22 (asset history) — those are parallel P1 stories.

**Canonical source:** `GitHub Issues - Visual MVP.md` → Issue 39 `[US-17]` (5 ACs, tasks T-17-01..04).  
**Superseded detail:** `MVP Backlog.md` → FEAT-09 / US-17 — used only to disambiguate; Visual MVP issue is authoritative.

**Baseline:** `v0.3.5-us16` (`4f52bb5` @ US-16 closure)

---

## 1A. Batch-Level Review Semantics (governance acceptance conditions)

US-17 review operates on the **storyboard batch as a single unit**, not individual frames. These semantics are **mandatory** for Visual MVP:

| Rule | Semantics |
|---|---|
| **Regeneration** | `POST /pipeline/regenerate` with `stage=STORYBOARD` creates a **new storyboard batch version** — all 4 frames at `version = MAX(version)+1` (`D-43`/`D-38`). |
| **Immutability** | **Existing storyboard assets remain immutable** — prior batch rows and MinIO PNG objects are never updated, deleted, or overwritten. |
| **Approval** | **Approval applies to the entire batch** — one `APPROVED` `approvals` row for `stage=STORYBOARD`; no per-frame approval records. |
| **Rejection** | **Rejection applies to the entire batch** — one `REJECTED` `approvals` row with rationale; enables batch-level regenerate. |
| **Per-frame approval** | **Not part of Visual MVP** — no checkboxes, no partial approve, no frame subset selection. |

**Proposed contracts (unchanged from review):** **`D-46`** (approved batch resolution) and **`D-47`** (regeneration input contract).

**Explicitly forbidden in US-17:** asset history UI, lineage UI, gallery framework abstraction, video workflow extension, schema migrations.

---

Complete the **Visual MVP pipeline terminal review gate** by letting the creator **inspect all storyboard frames in a gallery**, **approve the batch as a whole**, or **reject with a note and regenerate** a fresh 4-frame set.

US-16 delivers PNG assets at `AWAITING_APPROVAL` / `STORYBOARD`. US-17 adds the **human curation surface** and wires **approve-all → `COMPLETED`**, closing the Idea → Story → Script → Storyboard path defined in MVP Scope Freeze.

| Dimension | Intent |
|---|---|
| **User value** | Creative control over visual output before sign-off |
| **System value** | Deterministic approved-frame batch contract for downstream consumers (`D-46`, proposed) |
| **MVP boundary** | Last human gate in Visual MVP; **no video stage** (US-18 deferred) |

---

## 2. Source Review

### 2.1 Approved acceptance criteria (Visual MVP Issue 39 — authoritative)

1. **Grid of 4–6 images** — responsive gallery of the current storyboard batch.
2. **Lightbox preview** — enlarged single-frame view.
3. **Approve-all sets pipeline COMPLETED** — single approve action finishes the run.
4. **Reject triggers regenerate** — rejection note + regenerate produces a new frame batch.
5. **AI badge on frames** — visible indicator that frames are AI-generated.

### 2.2 Approved tasks (Visual MVP Issue 39)

| Task | Description |
|---|---|
| T-17-01 | Build Review screen — storyboard gallery mode |
| T-17-02 | Implement image preview lightbox |
| T-17-03 | Wire approve-all / reject for storyboard stage |
| T-17-04 | Display AI badge and model on frames |

### 2.3 Backlog (FEAT-09) corroborating detail

- Responsive grid of 4–6 images; lightbox; approve-all advances pipeline; reject triggers regenerate; AI badge on frames.
- Backlog wording "advances to video" is **superseded** by Scope Freeze — Visual MVP terminates at **approved storyboard** (`COMPLETED`), not US-18 video.

### 2.4 Dependencies

| Dependency | Status | Contract |
|---|---|---|
| US-16 frame generation | ✅ Closed | 4 PNG frames per batch (`D-45`); `D-43` batch `version` + `frame_index` |
| US-08 `POST /pipeline/approve` | ✅ Closed | GRANT/REJECT signals; immutable `approvals` rows |
| US-09 regenerate machinery | ✅ Closed at STORY/SCRIPT | STORYBOARD returns **501** today — **US-17 extends to STORYBOARD** |
| US-26 Review route | ✅ Closed | `ReviewPage.tsx` — STORY + SCRIPT modes |
| US-05 `GET /assets` | ✅ Closed | Metadata includes `metadata_json`; bytes require content-read |

**Hard dependency chain:** US-16 → **US-17** → US-V01.

### 2.5 Presentation vs API status mapping

| Phase | API | Dashboard (D-34) |
|---|---|---|
| Frames ready | `AWAITING_APPROVAL` / `STORYBOARD` | **REVIEW** |
| After approve-all | `COMPLETED` / `current_stage=null` | **COMPLETED** |
| During regen | `RUNNING` / `STORYBOARD` | **GENERATING** |
| After regen | `AWAITING_APPROVAL` / `STORYBOARD` | **REVIEW** |

US-17 does **not** add new `PipelineRunStatus` or stage enum values.

### 2.6 D-45 frame count pin

Issue AC-1 allows **4–6** images. US-16 **`D-45`** pins **exactly 4** frames per batch for a **2×2 grid**. US-17 gallery **MUST** render 4 tiles for the current batch without assuming dynamic N until a future SCR widens `D-45`.

---

## 3. Acceptance Criteria Mapping

### AC-1 — Grid of 4–6 images

| Dimension | Detail |
|---|---|
| **User action** | Navigate to Review while `AWAITING_APPROVAL` / `STORYBOARD`. |
| **System behavior** | Load **latest storyboard batch** (§6.1): 4 `STORYBOARD` rows sharing `MAX(version)`; order by `metadata_json.frame_index` ascending; display 2×2 responsive grid with shot label / frame index. |
| **Data changes** | None (read-only). |
| **Evidence** | Screenshot of 4-tile grid; network trace `GET /assets` + per-frame content fetch; unit test for batch selection helper. |

### AC-2 — Lightbox preview

| Dimension | Detail |
|---|---|
| **User action** | Click a grid thumbnail. |
| **System behavior** | Modal/overlay shows full-size PNG; keyboard dismiss (Esc); optional prev/next within batch. |
| **Data changes** | None. |
| **Evidence** | UI test or manual screenshot; lightbox opens correct `asset_version_id` / hash. |

### AC-3 — Approve-all sets pipeline COMPLETED

| Dimension | Detail |
|---|---|
| **User action** | Click **Approve** at STORYBOARD gate (single action — no per-frame approve). |
| **System behavior** | `POST /pipeline/approve` `{stage:STORYBOARD, decision:APPROVED}` → Temporal `approve` signal → workflow exits stage loop → `sync_pipeline_status(COMPLETED)` (existing `SparkPipelineWorkflow` tail). Dashboard shows **COMPLETED**. |
| **Data changes** | `approvals` row (`stage=STORYBOARD`, `decision=APPROVED`); `APPROVAL_RECORDED` audit; **no new STORYBOARD asset rows** (`D-43` / `D-37`/`D-41` parity). |
| **Evidence** | SQL `approvals` STORYBOARD/APPROVED; status JSON `COMPLETED`; frame row count unchanged post-approve; Olares E2E. |

### AC-4 — Reject triggers regenerate

| Dimension | Detail |
|---|---|
| **User action** | Enter note → **Reject** → **Regenerate** (up to 3× per US-09 cap). |
| **System behavior** | Reject: `POST /pipeline/approve` REJECT + note → stays `AWAITING_APPROVAL`/`STORYBOARD`. Regenerate: `POST /pipeline/regenerate` `{stage:STORYBOARD}` → `REGENERATION_REQUESTED` audit → workflow re-invokes `run_storyboard_agent` with **`D-47`** inputs → new batch at **`version+1`** (4 frames, `D-44` atomic) → UI reloads latest batch. 4th regenerate → **429**. |
| **Data changes** | Reject: `approvals` REJECTED + audit. Regenerate: 4 new `asset_versions` rows (shared new batch version), 4 new MinIO objects, 4 new lineage edges (script parent → each frame), audit chain. Prior batch rows **immutable**. |
| **Evidence** | SQL batch version increment; Olares regen log `storyboard_agent_completed`; 429 test; UI shows new grid after regen. |

### AC-5 — AI badge on frames

| Dimension | Detail |
|---|---|
| **User action** | View gallery. |
| **System behavior** | Each tile shows AI-generated badge when `is_ai_generated=true` (always true for US-16 output). Optionally surface `metadata_json.workflow` or model id from metadata/audit if present. |
| **Data changes** | None. |
| **Evidence** | DOM/badge visible on all 4 tiles; metadata strip matches `asset_versions` flags. |

---

## 4. Workflow Impact

### 4.1 Current workflow (post-US-16)

```
STORY → approve → SCRIPT → approve → STORYBOARD (run_storyboard_agent) → AWAITING_APPROVAL
```

After STORYBOARD approve today, workflow already sets **`COMPLETED`** — no further stages in `_STAGE_ORDER`.

### 4.2 US-17 changes

| Component | Change |
|---|---|
| **Web** | Gallery mode on Review page; approve/reject/regenerate for `STORYBOARD` |
| **API** | Extend `GET /assets/{id}/content` for PNG; extend `POST /pipeline/regenerate` for `STORYBOARD` |
| **Worker** | `run_storyboard_agent(rejection_note)` + **`D-47`** input resolution |
| **Workflow** | Pass `rejection_note` to STORYBOARD activity in regenerate loop (mirror SCRIPT) |
| **Temporal** | **No new signals**; reuse approve/reject/regenerate |

### 4.3 Regenerate loop (reuse US-09 pattern)

The existing reject → wait → regenerate → re-run generation → `AWAITING_APPROVAL` loop in `SparkPipelineWorkflow` is **stage-agnostic**. US-17 only requires:

1. API allows `stage=STORYBOARD` on `/pipeline/regenerate`.
2. `_run_stage_generation(STORYBOARD)` passes `rejection_note` to `run_storyboard_agent`.
3. Worker Cinematography planner consumes **`D-47`** inputs.

### 4.4 Terminal completion

**Approve-all** at STORYBOARD is the **Visual MVP terminal gate**. `COMPLETED` is the correct API status — not `RUNNING`/video. US-18 remains deferred per Scope Freeze.

---

## 5. Asset Contracts Affected

### 5.1 Inherited (read-only semantics — do not mutate)

| Decision | Relevance to US-17 |
|---|---|
| **D-37** | Approved story resolution — unchanged; regen does not alter STORY |
| **D-38** | Append-only ai-draft chains — STORYBOARD regen appends batch `version+1`, never UPDATE |
| **D-39** / **D-40** | Script asset — unchanged |
| **D-41** | Approved script — regen input per **`D-47`** |
| **D-42** | SCRIPT regen input pattern — **template for `D-47`** |
| **D-43** | Frame rows, batch `version`, `frame_index`, MinIO keys — gallery read + regen append |
| **D-44** | Atomic 4-frame batch — regen must satisfy same all-or-nothing contract |
| **D-45** | Exactly 4 frames — 2×2 grid |

### 5.2 Proposed at implementation start

#### D-46 — Approved storyboard batch resolution (proposed)

**Decision:** An "approved storyboard" is represented by (a) the **latest STORYBOARD batch** — all `asset_versions` rows for `stage=STORYBOARD` at **`MAX(version)`** for the project, ordered by `metadata_json.frame_index` — and (b) an **`APPROVED` `approvals` record for `stage=STORYBOARD`** on the active pipeline run. There is **NO branch promotion, NO copy-to-`main`, and NO additional asset write during approval**. Approve writes **`approvals` only** (mirror `D-37`/`D-41`/`D-43`).

**Rationale:** Visual MVP AC-3 requires batch approve → `COMPLETED` with a deterministic approved-frame set for US-V01 and any post-MVP consumer without mutating immutable PNG assets.

#### D-47 — Storyboard regeneration input contract (proposed)

**Decision:** STORYBOARD-stage regeneration (`POST /pipeline/regenerate` with `stage=STORYBOARD`) **MUST** supply the Cinematography agent with exactly two inputs: (1) the **approved script** per **`D-41`** (`fetch_approved_script`), and (2) the **latest rejected STORYBOARD rationale** — the `rationale` from the most recent `approvals` row where `stage=STORYBOARD` and `decision=REJECTED` for the run. **Prior STORYBOARD `asset_versions` rows, MinIO PNG objects, or frame bytes MUST NOT** be read, concatenated, or passed into the planning prompt. Each regeneration produces a **fresh 4-frame batch** at **`version+1`** (`D-38`/`D-43` append-only).

**Rationale:** Mirrors **`D-42`** — rejection note guides revision without contaminating the prompt with superseded frames. Preserves lineage script→frames on each new batch.

### 5.3 Latest batch resolution query (from US-16 — authoritative)

```sql
WITH latest AS (
  SELECT COALESCE(MAX(version), 0) AS v
  FROM asset_versions
  WHERE project_id = :project_id AND stage = 'STORYBOARD'
)
SELECT av.id, av.version, av.content_hash, av.minio_key,
       av.metadata_json->>'frame_index' AS frame_index,
       av.metadata_json->>'frame_count' AS frame_count,
       av.metadata_json->>'prompt' AS prompt,
       av.metadata_json->>'shot_label' AS shot_label,
       av.is_ai_generated, av.branch
FROM asset_versions av, latest
WHERE av.project_id = :project_id
  AND av.stage = 'STORYBOARD'
  AND av.version = latest.v
ORDER BY (av.metadata_json->>'frame_index')::int;
```

**Integrity check:** UI **MUST** verify `COUNT(*) = 4` and contiguous `frame_index` 1..4 before rendering ( **`D-44`/`D-45`** ). If count ≠ 4, show error state — do not render partial gallery.

### 5.4 Content-read extension (proposed enabler)

| Field | Value |
|---|---|
| Endpoint | `GET /assets/{id}/content` |
| New stage | `STORYBOARD` |
| Response | `image/png` bytes |
| Scope | Single asset by id — **no** gallery API, **no** batch zip download |

Mirrors US-13/US-15 content-read minimalism (`D-37`/`D-41`).

---

## 6. Approval / Rejection Behavior

### 6.1 Approve-all (batch)

| Field | Behavior |
|---|---|
| Trigger | Single **Approve** button — not per-frame checkboxes |
| API | `POST /pipeline/approve` `{project_id, stage:"STORYBOARD", decision:"APPROVED"}` |
| Asset writes | **None** — latest batch rows unchanged |
| Approval record | One `approvals` row for `stage=STORYBOARD` |
| Workflow | `approve` signal → stage completes → **`COMPLETED`** |
| Audit | `APPROVAL_RECORDED` |

### 6.2 Reject

| Field | Behavior |
|---|---|
| Trigger | **Reject** with required note (reuse STORY/SCRIPT pattern) |
| API | `POST /pipeline/approve` `{decision:"REJECTED", note:"..."}` |
| Asset writes | **None** |
| Workflow | Stays `AWAITING_APPROVAL`/`STORYBOARD`; enables **Regenerate** |
| Audit | `APPROVAL_RECORDED` with rationale |

### 6.3 Regenerate

| Field | Behavior |
|---|---|
| Preconditions | Latest STORYBOARD approval = **REJECTED**; regen count `< 3` per run |
| API | `POST /pipeline/regenerate` `{stage:"STORYBOARD"}` |
| Worker | Full `run_storyboard_agent` — Ollama plan + ComfyUI × 4 + atomic store |
| Output | New batch `version = MAX+1`; prior batch preserved |
| Cap | 4th request → **429** (US-09 parity) |

### 6.4 What approve does **not** do

- No branch promotion to `main`
- No per-frame approval subset
- No in-place PNG replacement
- No deletion of rejected batches

---

## 7. Lineage Implications

| Event | Lineage impact |
|---|---|
| **US-16 initial generation** | 4 edges: approved SCRIPT parent → each frame child (existing) |
| **US-17 approve** | **No new edges** |
| **US-17 reject** | **No new edges** |
| **US-17 regenerate** | 4 **new** edges: same approved SCRIPT parent → each new frame child (`D-47` does not create script→script edges) |
| **Prior batch after regen** | Old script→frame edges **preserved** (append-only graph) |

US-20 lineage viewer will show branched frame sets across batch versions; US-17 does **not** implement lineage UI or `GET /lineage`.

**US-V01 traceability:** Ordered chain Idea → Story → Script → **approved frame batch** is satisfied by existing edges + **`D-46`** approval gate.

---

## 8. Approved Scope

### 8.1 In scope (US-17)

| ID | Item | Rationale |
|---|---|---|
| S-01 | Review page **storyboard gallery mode** when `current_stage=STORYBOARD` | T-17-01 |
| S-02 | **2×2 grid** + responsive layout for 4 frames | AC-1, `D-45` |
| S-03 | **Lightbox** component for enlarged preview | T-17-02, AC-2 |
| S-04 | Load latest batch via `GET /assets` + batch selector helper | AC-1 |
| S-05 | **PNG content-read** — extend `GET /assets/{id}/content` to STORYBOARD | Gallery enabler |
| S-06 | Approve / Reject / Regenerate wired for `STORYBOARD` | T-17-03, AC-3/4 |
| S-07 | **STORYBOARD regenerate execution** — extend API + workflow + worker | AC-4 |
| S-08 | `run_storyboard_agent(rejection_note)` + **`D-47`** | AC-4 |
| S-09 | AI badge + optional metadata strip (workflow, frame index, shot label) | T-17-04, AC-5 |
| S-10 | **`D-46`**, **`D-47`** appended to `DECISIONS.md` at implementation start | Governance |
| S-11 | Unit tests + Olares verify package | Closure gates |

### 8.2 Optional (may defer without blocking AC)

| Item | Defer to |
|---|---|
| Per-frame reject / selective regen | Post-MVP — AC specifies approve-**all** |
| Download all frames as ZIP | Export / US-22 |
| Shot prompt overlay in lightbox | Nice-to-have; metadata available in DB |
| `metadata_json.model_id` on every frame | Optional; badge satisfies AC-5 |

### 8.3 Out of scope (do not implement in US-17)

| Item | Owner |
|---|---|
| ComfyUI / Cinematography agent changes beyond regen input | Minimal worker touch only |
| Video generation (US-18) | Deferred — Scope Freeze |
| `GET /lineage` API + lineage UI | **US-20** |
| Asset version browser / diff | **US-22** |
| Human-edit frame upload / inpainting | Deferred |
| Per-frame approval checkboxes | Forbidden — AC is approve-all |
| Alembic schema migration | Not expected — reuse `D-43` metadata + `approvals` |
| New pipeline status values (`STORYBOARD_REVIEW`, etc.) | Forbidden (`D-34`) |
| Neo4j / knowledge graph | Scope Freeze §5 |
| PDF / export | Deferred |

---

## 9. Gallery UX Requirements

### 9.1 Mode detection

| Condition | Review mode |
|---|---|
| `AWAITING_APPROVAL` + `current_stage=STORYBOARD` | **Storyboard gallery mode** (US-17) |
| `AWAITING_APPROVAL` + `current_stage=SCRIPT` | Script mode (US-15 — unchanged) |
| `AWAITING_APPROVAL` + `current_stage=STORY` | Story mode (US-13 — unchanged) |
| `COMPLETED` | Redirect or completion summary (implementation discretion) |

### 9.2 Gallery layout

| Element | Requirement |
|---|---|
| Header | `Review — Storyboard` + REVIEW badge |
| Lead copy | Explain: review 4 AI storyboard frames; approve to complete pipeline, or reject with note to regenerate |
| Grid | 2×2 on desktop; stacked pairs on narrow viewports |
| Thumbnail | PNG from content-read; `object-fit: contain`; frame index label |
| Metadata strip | Batch version, AI badge, optional shot label from `metadata_json` |
| Lightbox | Full-size image; close control; optional arrow navigation |
| Reject note | Reuse existing textarea; required on reject |
| Actions | **Approve**, **Reject**, **Regenerate** (same affordance rules as STORY/SCRIPT) |

### 9.3 Batch selector (client helper)

Mirror `selectLatestAiDraftScriptAsset`:

- Filter `stage=STORYBOARD`, `branch=ai-draft`
- Group by `version`; take **`MAX(version)`**
- Sort by `metadata_json.frame_index`
- Assert `length === 4` (`D-45`)

After regenerate, reload latest batch (new `version`).

---

## 10. Architecture Impact

### 10.1 API

| Item | Change |
|---|---|
| `GET /assets/{id}/content` | **Extend** — allow `stage=STORYBOARD`; `image/png` response |
| `POST /pipeline/regenerate` | **Extend** — add `STORYBOARD` to `_SUPPORTED_REGENERATE_STAGES` |
| `POST /pipeline/approve` | **Reuse** — no contract change |
| Alembic migration | **None expected** |

### 10.2 Web

| Item | Change |
|---|---|
| `ReviewPage.tsx` | Storyboard gallery branch |
| `lib/storyboardReview.ts` (or similar) | Latest batch frame selection |
| `components/StoryboardGrid.tsx` / lightbox | T-17-01/02 |
| `api/client.ts` | Handle PNG blob responses for content-read |
| Dashboard / stepper | **Regression** — COMPLETED state after STORYBOARD approve |

### 10.3 Worker

| Item | Change |
|---|---|
| `run_storyboard_agent` | Add `rejection_note` arg; inject into Cinematography planner |
| `fetch_latest_storyboard_rejection_rationale` | Mirror `fetch_latest_script_rejection_rationale` |
| ComfyUI / store path | **Reuse** US-16 — regen is full activity re-run |

### 10.4 Workflow

| Item | Change |
|---|---|
| `_run_stage_generation(STORYBOARD)` | Pass `rejection_note` (mirror SCRIPT) |
| Wait-condition lambdas | **Do not modify** (US-09 lesson) |
| Post-STORYBOARD | Existing `COMPLETED` sync — **no change** |

---

## 11. Risks

| ID | Risk | L | I | Mitigation |
|---|---|---|---|---|
| R1 | Partial batch displayed after regen failure | M | H | Client integrity check (`COUNT=4`); rely on **`D-44`** worker contract |
| R2 | Regen wall-clock (4× ComfyUI) blocks UI | M | M | GENERATING state during `RUNNING`; disable actions; reuse pipeline poll |
| R3 | Large PNG payloads over content-read | L | M | Thumbnails in grid; lazy-load; 512×512 SDXL sizes bounded |
| R4 | Scope creep into US-20 lineage UI | M | M | PR checklist — zero lineage API |
| R5 | Per-frame approve scope creep | M | H | Single Approve button; AC mapping §3 AC-3 |
| R6 | Mutating prior frame rows on regen | L | H | **`D-38`/`D-43`** append-only; SQL regression |
| R7 | STORYBOARD regen without GPU / ComfyUI | M | H | Olares verify mandatory; same infra as US-16 |
| R8 | Confusion with video "next stage" | L | M | Brief + UI copy: approve → **COMPLETED** (Visual MVP terminal) |
| R9 | Wrong batch after regen (stale version) | M | M | Selector uses `MAX(version)`; reload after regen completes |
| R10 | Breaking STORY/SCRIPT review modes | L | H | Regression suite; mode detection guards |

---

## 12. Verification Approach

### 12.1 Unit tests

| ID | Area | Assertion |
|---|---|---|
| T-01 | `lib/storyboardReview.test.ts` | Latest batch = max version; 4 frames ordered by `frame_index` |
| T-02 | `api/tests/unit/test_assets_us17.py` | Content-read returns PNG for STORYBOARD; rejects IDEA |
| T-03 | `api/tests/unit/test_pipeline_regenerate.py` | STORYBOARD regenerate happy path; 501 removed |
| T-04 | `worker/tests/unit/test_storyboard_regen.py` | **`D-47`**: prompt has script + rationale; no prior frame bytes |
| T-05 | Web component tests | AI badge rendered; grid count = 4 |

### 12.2 Regression

| Suite | Gate |
|---|---|
| API unit | 78+ pass; STORY/SCRIPT paths unchanged |
| Worker unit | 33+ pass; US-16 storyboard tests unchanged |
| Web unit | STORY + SCRIPT review tests pass |

### 12.3 Olares verification (mandatory)

**Script:** `deploy/k8s/us17-verify/` (author at implementation).

| Check | Evidence |
|---|---|
| V-01 | Gallery loads 4 PNGs at latest batch version |
| V-02 | Approve → `COMPLETED`; `approvals` STORYBOARD/APPROVED |
| V-03 | Reject + regen → batch `version+1`; 4 new hashes |
| V-04 | 4th regen → 429 |
| V-05 | **`D-46`**: no new STORYBOARD rows on approve |
| V-06 | **`D-47`**: worker log shows rejection note; no partial batch |
| V-07 | US-15/US-16 regression — SCRIPT gate + frame generation |

**Package:** `evidence/us-17-verification/olares-<date>/US-17-ACCEPTANCE-PACKAGE.md`

### 12.4 Closure criteria

| Outcome | Condition |
|---|---|
| **ACCEPT** | All 5 ACs evidenced; **`D-46`/`D-47`** recorded; Olares E2E pass; regressions green |
| **CONDITIONAL ACCEPT** | Not sufficient — Visual MVP requires Olares proof of approve → `COMPLETED` |

---

## 13. Scope Control

### 13.1 Boundary register

| Capability | Owner |
|---|---|
| Storyboard gallery + lightbox UI | **US-17** |
| STORYBOARD approve/reject/regenerate | **US-17** |
| PNG content-read | **US-17** |
| Approved storyboard batch contract (`D-46`) | **US-17** |
| Frame generation (ComfyUI) | **US-16** (closed) |
| Lineage viewer | **US-20** |
| Asset history browser | **US-22** |
| Visual MVP sign-off E2E | **US-V01** |

### 13.2 Primary creep risks

| Risk | Guard |
|---|---|
| Building video stage after approve | Workflow already `COMPLETED`; no US-18 work |
| Full asset management UI | Content-read by id only |
| Schema migration for "approved frames" table | Use `approvals` + latest batch query (`D-46`) |
| Editing individual frames | Out of scope |

---

## 14. Governance Attestation

This brief implements **only** Visual MVP Issue 39 (US-17). It completes the **terminal human review gate** for the frozen Visual MVP pipeline (Idea → Story → Script → Storyboard), consumes **`D-43`/`D-44`/`D-45`** frame assets from US-16, extends approve/regenerate patterns established in **`D-37`–`D-42`**, and preserves **append-only asset immutability** per MVP Scope Freeze.

| Constraint | Compliance |
|---|---|
| Append-only history | **`D-38`** — regen appends batch version; no UPDATE/DELETE |
| Asset immutability | Approve writes `approvals` only; PNG bytes never mutated |
| MVP scope freeze | Terminal at storyboard `COMPLETED`; no video/export |
| No schema migration | **`D-46`/`D-47`** use existing tables |
| Protected story US-17 | Scope Freeze §11.2 — may not cut without SCR |

**Request: governance acceptance of this brief before implementation plan authorization.**

---

## 15. Document Control

| Field | Value |
|---|---|
| Sprint | 3H |
| Baseline tag | `v0.3.5-us16` |
| Author | Engineering (governance draft) |
| Reviewers | Product Owner, Lead Architect |
| Next artifact | `docs/sprints/sprint-3h-us17-implementation-plan.md` (after brief ACCEPT) |
