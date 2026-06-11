# Sprint 3G — US-16 Implementation Plan

**Status:** **CLOSED** — Olares verification PASS; release `v0.3.5-us16`. Implementation report: `docs/sprints/sprint-3g-us16-implementation-report.md`. Closure report: `docs/sprints/sprint-3g-us16-closure-report.md`.  
**Parent brief:** `docs/sprints/sprint-3g-us16-brief.md` (**ACCEPTED**)  
**Story:** US-16 Generate storyboard frames · FEAT-08 · P0 · 8 SP  
**Baseline:** `v0.3.4-us15` (`main` @ US-15 closure)  
**Decision records:** `D-43` (storyboard frame asset contract), `D-44` (batch completeness) — appended to `DECISIONS.md` at plan authorization

---

## 0. Implementation summary

US-16 replaces the **STORYBOARD stub** with a real **Cinematography agent** (Ollama planning) + **ComfyUI inference** (SDXL), storing **4 PNG frames** per generation (`D-45`) with **script lineage** and **GPU sequencing** (`D-08`). Net-new work is **worker-only** plus a **production ComfyUI workflow JSON**, **Olares verify scripts**, and **Alembic `0003`** (D-43 multi-frame batch versioning). **No API routes. No web changes.**

| Layer | Net-new | Reuse |
|---|---|---|
| API | — | `GET /assets`, `GET /pipeline/status`, `POST /pipeline/approve` (unchanged) |
| Temporal workflow | STORYBOARD → `run_storyboard_agent` (replace `run_stub_stage`) | Stage loop, approve/reject signals, STORY/SCRIPT agents |
| Worker | Cinematography graph, ComfyUI tool, GPU sequencer, `run_storyboard_agent`, `store_storyboard_batch` | `fetch_approved_script` (D-41), `insert_lineage_edge`, audit helpers |
| Web | — | No changes (US-17 gallery) |
| DB schema | — | `asset_versions.metadata_json`, `lineage_edges`, `audit_events` |
| Config | `sdxl_storyboard_production.json`, `prompts/cinematography/v1.yaml` | `D-03` smoke workflow (read-only) |

**Estimated effort:** 8 SP · ~4–5 days (agent + ComfyUI tool → activity + workflow → GPU sequencing → tests → Olares verification).

---

## 1. D-43 — Storyboard frame asset contract

**Recorded in `DECISIONS.md` as D-43.** Parallels `D-39` (script asset semantics).

### 1.1 Filename convention

| Field | Value |
|---|---|
| Logical artifact name | `frame_{n}.png` where `n` is 1-based index within the batch |
| `n` range | `1 .. frame_count` where `4 <= frame_count <= 6` |
| Purpose | Human-readable label in docs/evidence and US-17 gallery copy |
| Bytes identity | Content-addressed SHA-256 hash (same as all assets) |

The filename is **not** a separate MinIO path segment; storage uses `{project_id}/STORYBOARD/{content_hash}` per existing `build_object_key()`.

### 1.2 Storage convention

| Field | Value |
|---|---|
| `asset_versions.stage` | `STORYBOARD` (`AssetStage.STORYBOARD`) |
| `asset_versions.branch` | `ai-draft` |
| `asset_versions.is_ai_generated` | `true` |
| `asset_versions.pipeline_run_id` | Active run id (same as STORY/SCRIPT pattern) |
| MinIO key | `{project_id}/STORYBOARD/{content_hash}` |
| MinIO `content_type` | `image/png` |
| Input gate | `fetch_approved_script()` per **D-41** before planning |

### 1.3 Frame indexing

| Field | Location | Rule |
|---|---|---|
| `frame_index` | `metadata_json` (required) | Integer `1..N`; unique within batch |
| `frame_count` | `metadata_json` (required) | Total N in batch; same value on every row in the batch |
| `prompt` | `metadata_json` (required) | Shot prompt string used for ComfyUI positive encode |
| `workflow` | `metadata_json` (optional) | e.g. `"sdxl_storyboard_production_v1"` |
| `seed` | `metadata_json` (optional) | Per-frame seed (`base_seed + frame_index`) |
| `model_id` | `metadata_json` (optional) | Checkpoint name if not captured in audit only |

**US-17 query pattern (document in implementation report):**

```sql
-- Latest storyboard batch: all frames at max version
WITH latest AS (
  SELECT MAX(version) AS v
  FROM asset_versions
  WHERE project_id = :project_id AND stage = 'STORYBOARD'
)
SELECT av.id, av.version, av.content_hash, av.metadata_json->>'frame_index' AS frame_index
FROM asset_versions av
JOIN latest ON av.version = latest.v
WHERE av.project_id = :project_id AND av.stage = 'STORYBOARD'
ORDER BY (av.metadata_json->>'frame_index')::int;
```

### 1.4 Versioning behavior

| Behavior | Rule |
|---|---|
| Batch version | One `version` integer shared by **all N frames** in a successful generation |
| Version assignment | `next_version = COALESCE(MAX(version), 0) + 1` for `(project_id, STORYBOARD)` — computed **once** at batch start |
| Append-only | Each generation appends N new rows; prior batches immutable |
| In-place update | **Forbidden** — no UPDATE of STORYBOARD rows or MinIO objects |
| Regeneration (US-17) | Future regen appends batch `version+1` with a fresh N-frame set (`D-38` parity) |
| Approve | **No asset write** — `approvals` row only (mirror D-37/D-41) |

---

## 2. D-44 — Storyboard batch completeness contract

**Recorded in `DECISIONS.md` as D-44.**

### 2.1 Successful batch definition

A storyboard generation attempt is **successful** only when **all** conditions are met in a **single atomic unit of work**:

| # | Condition |
|---|---|
| 1 | Planner output: `4 <= frame_count <= 6` with unique `frame_index` values 1..N |
| 2 | Each shot rendered to PNG bytes via ComfyUI (production workflow) |
| 3 | Each PNG passes `validate_storyboard_frame()` (PNG magic bytes, non-zero size, decodable) |
| 4 | GPU sequencing: Ollama unloaded per **D-08** before **any** ComfyUI call |
| 5 | All N MinIO `put_object` calls succeed |
| 6 | All N `asset_versions` INSERTs succeed in **one DB transaction** at shared batch `version` |
| 7 | All N `lineage_edges` INSERTs succeed in the **same transaction** (`parent_id` = approved script) |
| 8 | Post-commit: N `ASSET_STORED` audit events + `AGENT_TASK_COMPLETED` with `frame_count=N` |

### 2.2 Behavior when one or more frames fail

| Failure point | Required behavior |
|---|---|
| Planning (Ollama) — invalid frame count | Raise before ComfyUI; **zero** assets stored |
| Planning — duplicate/missing `frame_index` | Raise before ComfyUI; **zero** assets stored |
| GPU sequencing — unload fails | Raise before ComfyUI; **zero** assets stored |
| ComfyUI — queue/poll/timeout on shot *k* | **Abort entire batch**; discard in-memory PNGs from shots 1..k-1; **zero** DB/MinIO/lineage writes from this attempt |
| Validation — shot *k* invalid PNG | Same as ComfyUI failure — abort batch, zero persistence |
| DB transaction — any INSERT fails | Transaction rolls back; **zero** rows from this attempt (including any MinIO objects written in same attempt — roll back MinIO writes or defer MinIO until after DB commit; **preferred: write MinIO inside transaction callback only after validation, commit DB first, or use two-phase: collect all PNGs in memory → single transactional store function**) |

**Implementation pin:** `store_storyboard_batch()` collects all N PNG byte buffers in memory during ComfyUI phase, then performs MinIO puts + DB inserts + lineage inserts inside one function with explicit rollback semantics. If any step fails, function raises without committing.

| Retry | Behavior |
|---|---|
| Temporal activity retry | **Full activity restart** — re-plan (or reuse cached plan only if idempotent; **pin: re-plan on each attempt** for simplicity) |
| Workflow `RetryPolicy` | `maximum_attempts=2` (Issue 38 AC-5) |
| After exhausted retries | `_mark_storyboard_failed` → `status=FAILED`, `PIPELINE_FAILED` audit |
| Partial rows from failed attempt | **Must be zero** — verified by unit test and Olares SQL |

**No compensating DELETE** of prior successful batches. Failed attempts leave no footprint.

---

## 3. Acceptance criteria traceability

### AC-1 — 4–6 PNG frames via ComfyUI

| Track | Task IDs | Deliverable |
|---|---|---|
| **Workflow** | W-01 | `run_storyboard_agent` replaces stub for `STORYBOARD` |
| **Worker** | G-01..G-03, A-01..A-05, C-01..C-03 | Cinematography graph, `run_storyboard_agent`, `store_storyboard_batch` |
| **ComfyUI** | C-01, C-02 | `sdxl_storyboard_production.json`; `comfyui.py` queue/poll/fetch |
| **Tests** | T-01, T-02, T-03, T-10 | Planner count; mock ComfyUI; batch store count |
| **Verification** | V-01, V-02 | SQL 4–6 STORYBOARD rows; MinIO PNG stat |

### AC-2 — Ollama unloaded before GPU

| Track | Task IDs | Deliverable |
|---|---|---|
| **Workflow** | — | Activity ordering inside `run_storyboard_agent` |
| **Worker** | A-04, S-01 | `gpu/sequencer.py` — `unload_ollama_before_comfyui()` |
| **ComfyUI** | — | ComfyUI calls only after sequencer |
| **Tests** | T-04 | Mock: unload invoked before `comfyui_generate` |
| **Verification** | V-05 | Olares worker log: unload → comfyui_queued ordering |

### AC-3 — Lineage script → frames

| Track | Task IDs | Deliverable |
|---|---|---|
| **Workflow** | — | — |
| **Worker** | A-05 | `insert_lineage_edge(script_id, frame_id)` × N in batch transaction |
| **ComfyUI** | — | — |
| **Tests** | T-05 | N frames → N edges, same `parent_id` |
| **Verification** | V-03, V-06 | SQL join SCRIPT → STORYBOARD children; parent = D-41 script id |

### AC-4 — STORYBOARD_REVIEW on success

| Track | Task IDs | Deliverable |
|---|---|---|
| **Workflow** | W-01 | Existing stage loop → `sync_pipeline_status(AWAITING_APPROVAL, STORYBOARD)` after activity |
| **Worker** | A-01 | Activity success path (mirror `run_script_agent`) |
| **ComfyUI** | — | — |
| **Tests** | T-06 | Activity completion returns frame ids; status sync called |
| **Verification** | V-04 | `GET /pipeline/status` → `AWAITING_APPROVAL` / `STORYBOARD` |

### AC-5 — Retry 2× then FAILED

| Track | Task IDs | Deliverable |
|---|---|---|
| **Workflow** | W-02 | `RetryPolicy(maximum_attempts=2)` on `run_storyboard_agent`; `timedelta(minutes=15)` timeout |
| **Worker** | A-06 | `_mark_storyboard_failed`; re-raise after audit |
| **ComfyUI** | C-03 | ComfyUI errors mapped to retryable exceptions |
| **Tests** | T-07, T-08 | Mid-batch failure → zero rows; exhausted retry → failed sync |
| **Verification** | V-08 (optional) | Negative path on Olares or unit-only attestation |

### Visual MVP task mapping (T-16-01..07)

| Backlog task | Plan task IDs |
|---|---|
| T-16-01 Cinematography agent | G-01, G-02, G-03, `prompts/cinematography/v1.yaml` |
| T-16-02 ComfyUI tool | C-01, C-02, C-03 |
| T-16-03 `run_storyboard_agent` | A-01..A-06 |
| T-16-04 GPU sequencing | S-01, A-04 |
| T-16-05 Store multiple frames | A-05, `store_storyboard_batch()` |
| T-16-06 Lineage script → frames | A-05 |
| T-16-07 ComfyUI error handling | A-06, C-03, W-02, T-07, T-08 |

---

## 4. ComfyUI architecture

### 4.1 Planning step (Ollama / LangGraph)

**Module:** `worker/app/agents/cinematography/`

| Step | Node | Input | Output |
|---|---|---|---|
| 1 | `load_script_context` | `fetch_approved_script()` → Fountain text; optional IDEA `style_note` | `script_fountain`, `script_asset_id` |
| 2 | `plan_shots` | Fountain scene + style; Ollama `/api/generate` | JSON list of 4–6 `{frame_index, prompt, shot_label}` |
| 3 | `validate_plan` | Planner output | Fail if count ∉ [4,6] or indexes not 1..N unique |

**Graph:** Linear `StateGraph` — mirror Screenwriter (US-14). Ephemeral state; no DB writes in graph.

**Prompt:** `configs/prompts/cinematography/v1.yaml` — instruct: derive shots from **one scene** Fountain script; output structured JSON only; 4–6 shots covering establishing, character, detail angles.

### 4.2 Image generation step (ComfyUI / GPU)

**Module:** `worker/app/tools/comfyui.py`

**Precondition (D-08 / D-44):** `gpu_sequencer.unload_ollama_before_comfyui(settings)` completes successfully.

| Step | Function | Detail |
|---|---|---|
| 1 | `load_production_workflow()` | Read `configs/comfyui/workflows/sdxl_storyboard_production.json` (fork of `D-03`, **do not mutate** smoke file) |
| 2 | `patch_workflow_prompt(workflow, positive_text, seed)` | Replace node `2` CLIP positive text; set KSampler seed |
| 3 | `queue_prompt(host, workflow)` | `POST {COMFYUI_HOST}/prompt` |
| 4 | `wait_for_image(host, prompt_id)` | Poll `/history/{id}` until SaveImage output |
| 5 | `fetch_image_bytes(host, filename, subfolder)` | `GET /view?...` → PNG bytes |

**Loop:** For each shot in plan (ordered by `frame_index`): call steps 1–5. Any failure → abort batch (D-44).

**Settings addition:** `comfyui_host: str = Field(default="http://comfyui:8188", validation_alias="COMFYUI_HOST")` in `aimpos_config`.

### 4.3 Persistence step

**Module:** `worker/app/tools/assets.py` — `store_storyboard_batch()`

| Step | Action |
|---|---|
| 1 | Compute `batch_version` = `MAX(version)+1` for STORYBOARD |
| 2 | For each frame: `content_hash` = SHA-256(PNG bytes) |
| 3 | MinIO `put_object` for each hash key |
| 4 | Single DB transaction: INSERT N `asset_versions` rows (shared `version`, distinct `metadata_json`) |
| 5 | Same transaction: INSERT N `lineage_edges` |
| 6 | Commit |
| 7 | Append N `ASSET_STORED` + one `AGENT_TASK_COMPLETED` audit events |

Returns `list[StoredStoryboardFrame]` with `asset_version_id`, `frame_index`, `content_hash`, `version`.

### 4.4 Lineage step

| Aspect | Detail |
|---|---|
| Table | `lineage_edges` (existing) |
| `parent_id` | `ApprovedScriptAsset.asset_version_id` from D-41 |
| `child_id` | Each frame `asset_versions.id` |
| Count | Exactly N edges per successful batch |
| Timing | Same transaction as frame INSERTs (D-44) |
| API exposure | **None** in US-16 (`GET /lineage` is US-20) |

### 4.5 End-to-end activity sequence (`run_storyboard_agent`)

```text
1. STAGE_STARTED {stage: STORYBOARD, agent: agent.cinematography}
2. fetch_approved_script() → script bytes + script_asset_id
3. run_cinematography_graph() → shot plan [4..6]
4. unload_ollama_before_comfyui()
5. FOR each shot: comfyui_generate_png(prompt, seed) → bytes[]  (all in memory)
6. validate_storyboard_batch(bytes[], plan)
7. store_storyboard_batch(frames, script_asset_id, plan)  # atomic
8. AGENT_TASK_COMPLETED {frame_count, model_id, duration_ms}
9. Return comma-separated frame asset_version_ids (or JSON string — pin: first frame id for workflow return, full list in audit)
```

### 4.6 Workflow diff

**File:** `worker/app/temporal/workflows/spark_pipeline.py`

```python
elif stage == PipelineStage.STORYBOARD:
    await workflow.execute_activity(
        run_storyboard_agent,
        args=[pipeline_input.project_id, pipeline_input.run_id],
        start_to_close_timeout=timedelta(minutes=15),
        retry_policy=RetryPolicy(maximum_attempts=2),
    )
```

**Note:** `rejection_note` arg deferred to US-17 STORYBOARD regen; US-16 first generation only.

**Risk pin (US-09 lesson):** Do **not** modify post-regeneration `wait_condition` lambdas.

---

## 5. Asset versioning

### 5.1 Batch version semantics

| Generation | STORYBOARD rows | `version` | `frame_index` |
|---|---|---|---|
| First success | 4 rows (example) | 1 | 1, 2, 3, 4 |
| US-17 regen (future) | 5 rows (example) | 2 | 1, 2, 3, 4, 5 |
| Failed attempt | 0 rows | — | — |

All frames in a batch share `version`. US-17 "latest frame set" = `MAX(version)` + filter by `metadata_json.frame_index`.

### 5.2 Append-only behavior

| Operation | Allowed? |
|---|---|
| INSERT new batch (N rows) | ✅ Each successful generation |
| UPDATE existing STORYBOARD row | ❌ Forbidden |
| DELETE STORYBOARD row | ❌ Forbidden |
| Overwrite MinIO object at same key | ❌ Content-addressed keys make this unlikely; new hash → new key |
| Partial batch INSERT | ❌ Forbidden (D-44) |

Aligns with **D-38** (regeneration append-only ai-draft chain). STORYBOARD regen in US-17 will append `version+1` batch without mutating prior frames.

### 5.3 Comparison to prior stages

| Stage | Rows per generation | Version model |
|---|---|---|
| STORY | 1 | Monotonic per `(project_id, STORY)` |
| SCRIPT | 1 | Monotonic per `(project_id, SCRIPT)` |
| STORYBOARD | **N (4–6)** | Monotonic batch version; N rows share version |

---

## 6. Scope control

### IN SCOPE

| ID | Item |
|---|---|
| S-01 | `worker/app/infrastructure/gpu/sequencer.py` — Ollama unload before ComfyUI (`D-08`) |
| S-02 | `worker/app/agents/cinematography/` — LangGraph + `v1.yaml` prompt |
| S-03 | `worker/app/tools/comfyui.py` — ComfyUI HTTP client |
| S-04 | `configs/comfyui/workflows/sdxl_storyboard_production.json` — fork from `D-03` |
| S-05 | `worker/app/temporal/activities/storyboard.py` — `run_storyboard_agent` |
| S-06 | `worker/app/tools/assets.py` — `store_storyboard_batch()`, `validate_storyboard_frame()` |
| S-07 | Workflow swap STORYBOARD stub → agent |
| S-08 | `aimpos_config` — `COMFYUI_HOST` setting |
| S-09 | `D-43`, `D-44` in `DECISIONS.md` |
| S-10 | Worker unit tests (§7.1) |
| S-11 | `deploy/k8s/us16-verify/` + acceptance package |
| S-12 | API/worker/web regression (no new failures) |

### OUT OF SCOPE

| ID | Item | Owner |
|---|---|---|
| X-01 | Storyboard gallery review UI | US-17 |
| X-02 | Lightbox / grid layout | US-17 |
| X-03 | Approve-all → `COMPLETED` | US-17 |
| X-04 | STORYBOARD reject/regenerate API + UI | US-17 |
| X-05 | `GET /assets/{id}/content` for PNG bytes | US-17 |
| X-06 | Video generation / export | EPIC-05 |
| X-07 | Human-edit / inpainting frames | Deferred |
| X-08 | Asset history browser / diff | US-22 |
| X-09 | `GET /lineage` API | US-20 |
| X-10 | Alembic schema migration | N/A |
| X-11 | Web UI changes | US-17 |
| X-12 | New `PipelineRunStatus` or stage enum values | Forbidden |
| X-13 | Mutating `configs/comfyui/workflows/sdxl_storyboard.json` (`D-03`) | Forbidden |
| X-14 | Flux / SD3 models (unless amendment) | Deferred |
| X-15 | Neo4j / knowledge graph | Scope Freeze §5 |

---

## 7. Verification plan

### 7.1 Unit tests

| ID | File | Assertion |
|---|---|---|
| T-01 | `worker/tests/unit/test_cinematography.py` | Fountain fixture → 4–6 shots with unique indexes |
| T-02 | `worker/tests/unit/test_cinematography.py` | Planner returning 3 or 7 shots → validation fail |
| T-03 | `worker/tests/unit/test_comfyui_tool.py` | Mock HTTP: queue → poll → PNG bytes |
| T-04 | `worker/tests/unit/test_gpu_sequencer.py` | `unload_ollama` called before ComfyUI client |
| T-05 | `worker/tests/unit/test_storyboard_batch.py` | N frames → N lineage edges, shared parent script id |
| T-06 | `worker/tests/unit/test_storyboard_activity.py` | Happy path: status sync, audit events, return value |
| T-07 | `worker/tests/unit/test_storyboard_batch.py` | ComfyUI fail on shot 3 → **zero** STORYBOARD rows (D-44) |
| T-08 | `worker/tests/unit/test_storyboard_activity.py` | Exhausted retries → `_mark_storyboard_failed` |
| T-09 | `worker/tests/unit/test_storyboard_validate.py` | Invalid PNG magic → fail |
| T-10 | `worker/tests/unit/test_storyboard_batch.py` | Batch version monotonic; all frames share version |
| T-11 | API regression | `pytest api/tests/unit` — 78+ pass, zero API changes |
| T-12 | Web regression | Vitest 20 pass — zero web changes |

### 7.2 Smoke / E2E (local or compose)

| Step | Action | Expected |
|---|---|---|
| 1 | Fresh pipeline to STORYBOARD gate | Approve STORY + SCRIPT |
| 2 | Worker runs `run_storyboard_agent` | 4–6 frames (live ComfyUI on GPU host; mock in CI) |
| 3 | `GET /pipeline/status` | `AWAITING_APPROVAL` / `STORYBOARD` |
| 4 | SQL: STORYBOARD rows | N rows, same `version`, `frame_index` 1..N |
| 5 | SQL: lineage | N edges from SCRIPT parent |
| 6 | Worker logs | Ollama unload before ComfyUI |

### 7.3 Olares verification

**Prerequisites:** `aimpos-worker:us16` image; ComfyUI + Ollama on Olares; `COMFYUI_HOST` wired in worker deployment.

**Script:** `deploy/k8s/us16-verify/verify_us16.sh` (author at implementation).

| Check | Evidence |
|---|---|
| V-01 | SQL: 4–6 STORYBOARD rows at latest batch `version` |
| V-02 | MinIO `mc stat` on `{project_id}/STORYBOARD/{hash}` (sample frame) |
| V-03 | SQL: lineage count = frame count; parent = approved SCRIPT id |
| V-04 | `GET /pipeline/status` → `AWAITING_APPROVAL`/`STORYBOARD` |
| V-05 | Worker log: `ollama_unloaded` (or equivalent) before `comfyui_queued` |
| V-06 | D-41 script `asset_version_id` matches lineage `parent_id` |
| V-07 | US-15 regression — SCRIPT gate + content-read still pass |
| V-08 | D-44 attestation — no orphan frames at non-max version after success |

**Package:** `evidence/us-16-verification/olares-<date>/US-16-ACCEPTANCE-PACKAGE.md`

**Operational pin:** Pin `RUN_ID` in verify script when `pipeline/start` returns 409 (lesson from US-15 verify).

### 7.4 Closure criteria

| Outcome | Condition |
|---|---|
| **ACCEPT** | All 5 ACs evidenced on Olares; GPU sequencing log proven; unit suites green |
| **CONDITIONAL ACCEPT** | Not sufficient for Visual MVP M5 — Olares GPU proof required |

---

## 8. Risk review

| ID | Risk | L | I | Mitigation |
|---|---|---|---|---|
| R1 | VRAM OOM if Ollama not unloaded | H | H | Mandatory `S-01` sequencer; V-05 log evidence; fail activity before ComfyUI if unload fails |
| R2 | ComfyUI timeout (15 min insufficient for 6 frames) | M | H | 15-min `start_to_close_timeout`; monitor Olares first run; amend timeout via SCR if needed |
| R3 | Partial frame store (D-44 violation) | M | H | `store_storyboard_batch()` single transaction; T-07 negative test |
| R4 | ComfyUI API drift | M | M | Pin production workflow JSON; fork from `D-03`; C-03 error mapping |
| R5 | Planner returns non-JSON / wrong count | M | M | `validate_plan` node; T-02; Temporal retry |
| R6 | `fetch_approved_script` missing at STORYBOARD | L | H | Only runs post-SCRIPT approve; unit test with missing approval |
| R7 | Scope creep into US-17 gallery | M | M | PR checklist X-01..X-05; zero web files in diff |
| R8 | Mutating `D-03` smoke workflow | L | M | Code review; production JSON in separate file |
| R9 | In-flight stub runs after worker deploy | L | M | Document: fresh runs only; cancel stale STORYBOARD stubs |
| R10 | Multi-frame version query ambiguity for US-17 | M | M | D-43 `frame_index` + documented SQL in implementation report |
| R11 | MinIO write before DB commit leaves orphans | M | H | Collect PNGs in memory; transactional store function; T-07 |

---

## 9. Implementation task checklist (execution order)

| Order | ID | Task | Owner track |
|---|---|---|---|
| 1 | — | Append D-43, D-44 to `DECISIONS.md` | Governance ✅ (this plan) |
| 2 | S-08 | Add `COMFYUI_HOST` to settings | Config |
| 3 | C-01 | Author `sdxl_storyboard_production.json` | ComfyUI |
| 4 | G-01 | Cinematography state + nodes + graph | Agent |
| 5 | C-02 | `comfyui.py` client | Tool |
| 6 | S-01 | GPU sequencer module | Infra |
| 7 | A-05 | `store_storyboard_batch()` + validators | Assets |
| 8 | A-01 | `run_storyboard_agent` activity | Activity |
| 9 | W-01 | Workflow swap | Temporal |
| 10 | T-01..T-10 | Unit tests | QA |
| 11 | T-11, T-12 | Regression | QA |
| 12 | V-01..V-08 | Olares verify + acceptance package | Evidence |

---

## 10. Governance attestation

This plan implements **only** Visual MVP Issue 38 (US-16). It replaces the STORYBOARD stub with Ollama planning + ComfyUI SDXL inference, establishes **`D-43`** frame asset semantics and **`D-44`** batch completeness for US-17 gallery consumption, and enforces **`D-08`** GPU sequencing — without schema changes, API routes, or review UI.

**Request: governance acceptance of this plan before implementation authorization.**
