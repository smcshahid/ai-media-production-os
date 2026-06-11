# Sprint 3G — US-16 Generate Storyboard Frames (governance brief)

**Status:** **CLOSED** — formally accepted 2026-06-11 (`v0.3.5-us16`, Olares verification PASS).  
**Story:** US-16 "Generate storyboard frames" · FEAT-08 AI Storyboard Generation · EPIC-04 · P0 · 8 SP · Sprint S4.  
**Prerequisites (all closed):** US-05 ✅ (MinIO/assets) · US-06 ✅ (ComfyUI smoke, `D-03`) · US-07 ✅ (workflow) · US-14 ✅ (`script.fountain`, `D-39`/`D-40`) · US-15 ✅ (SCRIPT gate, `D-41`/`D-42`, `fetch_approved_script`).  
**Blocks:** US-17 (storyboard gallery review), US-20 (lineage viewer), US-V01 (Visual MVP E2E).

**Canonical source:** `GitHub Issues - Visual MVP.md` → Issue 38 `[US-16]` (5 ACs, tasks T-16-01..07).  
**Superseded detail:** `MVP Backlog.md` → FEAT-08 / US-16 — used only to disambiguate; Visual MVP issue is authoritative.

---

## 1. Source Review

### 1.1 Approved acceptance criteria (Visual MVP Issue 38 — authoritative)

1. **4–6 PNG frames via ComfyUI** — Cinematography agent produces storyboard images locally.
2. **Ollama unloaded before GPU** — single-GPU hosts must not run LLM and ComfyUI concurrently (`D-08`).
3. **Lineage script → frames** — each frame linked to the approved script asset.
4. **STORYBOARD_REVIEW on success** — workflow reaches review gate (`AWAITING_APPROVAL` / `STORYBOARD`).
5. **Retry 2× then FAILED** — ComfyUI failures retry up to two attempts, then pipeline marks `FAILED`.

### 1.2 Approved tasks (Visual MVP Issue 38)

| Task | Description |
|---|---|
| T-16-01 | Implement Cinematography agent (planning via Ollama) |
| T-16-02 | Implement ComfyUI tool — SDXL/Flux workflow |
| T-16-03 | Implement `run_storyboard_agent` Temporal activity |
| T-16-04 | GPU sequencing: unload Ollama before ComfyUI |
| T-16-05 | Store multiple frame assets per run |
| T-16-06 | Record lineage edges script → frames |
| T-16-07 | ComfyUI error handling and retry |

### 1.3 Backlog (FEAT-08) corroborating detail

- "Given **approved script**, when storyboard activity runs, then agent produces 4–6 PNG frames via ComfyUI."
- Each frame stored as `frame_{n}.png` with `is_ai_generated=true`.
- Ollama unloaded before ComfyUI GPU job (`D-08` / `docs/runbooks/gpu-sequencing.md`).
- Lineage edges `script.fountain → frame_n.png` in `lineage_edges`.
- Workflow status → `STORYBOARD_REVIEW` (maps to `AWAITING_APPROVAL` / `STORYBOARD` — **no new status enum**).
- ComfyUI failure → activity retries up to 2 times, then `PIPELINE_FAILED` audit + `status=FAILED`.

### 1.4 Dependencies

| Dependency | Status | Contract |
|---|---|---|
| US-05 MinIO + `asset_versions` | ✅ Closed | Content-addressed store; append-only versions |
| US-06 ComfyUI smoke | ✅ Closed | `sdxl_storyboard.json` pin (`D-03`); M1-DV PNG verified |
| US-07 `SparkPipelineWorkflow` | ✅ Closed | STORYBOARD currently `run_stub_stage` |
| US-08 approve/reject | ✅ Closed | STORYBOARD gate uses same signal contract |
| US-15 + `D-41` | ✅ Closed | `fetch_approved_script()` → Fountain bytes + `APPROVED` gate |
| US-12/US-14 agent pattern | ✅ Closed | LangGraph inside activity; Temporal owns retries |

**Hard dependency chain:** US-15 → **US-16** → US-17 → US-V01.

### 1.5 Presentation vs API status mapping

Issue AC-4 uses **`STORYBOARD_REVIEW`**. Per US-10 (`D-34`), dashboard maps `AWAITING_APPROVAL` → **REVIEW**. After STORYBOARD generation completes the API sequence is:

1. `RUNNING` / `STORYBOARD` (agent active)
2. `AWAITING_APPROVAL` / `STORYBOARD` (frames ready for US-17 gallery)

US-16 does **not** add new `PipelineRunStatus` or stage enum values.

---

## 2. Approved Scope

### 2.1 In scope (US-16)

| ID | Item | Rationale |
|---|---|---|
| S-01 | **Cinematography LangGraph** — Ollama plans 4–6 shot prompts from approved Fountain script | T-16-01 |
| S-02 | **ComfyUI client tool** — queue workflow, poll completion, fetch PNG bytes | T-16-02 |
| S-03 | **`run_storyboard_agent` Temporal activity** — orchestrate plan → GPU sequence → store | T-16-03 |
| S-04 | **Workflow swap** — replace `run_stub_stage` for `STORYBOARD` with `run_storyboard_agent` | AC-4 |
| S-05 | **GPU sequencing** — unload Ollama / confirm VRAM before ComfyUI (`D-08`) | T-16-04, AC-2 |
| S-06 | **Multi-frame asset store** — 4–6 `asset_versions` rows per generation | T-16-05, AC-1 |
| S-07 | **Lineage edges** — `parent_id` = approved script → each frame `child_id` | T-16-06, AC-3 |
| S-08 | **ComfyUI error handling** — Temporal retry (max 2 attempts per activity policy) + `FAILED` path | T-16-07, AC-5 |
| S-09 | **Storyboard asset contract** — propose **`D-43`** in `DECISIONS.md` at implementation start | Frame semantics |
| S-10 | **Production ComfyUI workflow** — fork from `D-03` pin (new file, do not mutate smoke graph) | T-16-02 |
| S-11 | Worker/API unit tests + Olares verify package | Closure gates |

### 2.2 Optional (may defer without blocking AC)

| Item | Defer to |
|---|---|
| Flux checkpoint / higher resolution than 512×512 | Amendment if Olares VRAM allows; SDXL 512×512 satisfies AC |
| Per-frame negative-prompt tuning from agent | Single workflow template with injected positive prompt sufficient |
| `metadata_json.model_id` on each frame | Recommended; not strictly required if audit events capture model |
| STORYBOARD regenerate execution (`POST /pipeline/regenerate`) | **US-17** (reject/regenerate at review gate) |
| Image content-read API (`GET /assets/{id}/content` for PNG) | **US-17** gallery enabler |

### 2.3 Out of scope (do not implement in US-16)

| Item | Owner |
|---|---|
| Storyboard gallery review UI | **US-17** |
| Approve-all → `COMPLETED` | **US-17** |
| STORYBOARD reject/regenerate API wiring | **US-17** |
| Video generation / export | **EPIC-05** (post-Visual MVP) |
| Human-edit frames / inpainting | Deferred |
| Asset history browser / diff | **US-22** |
| `GET /lineage` API | **US-20** |
| Alembic schema migration | Not needed — reuse `asset_versions` + `metadata_json` |
| New pipeline status family | Forbidden |
| PDF export | Deferred |
| Neo4j / knowledge graph | Scope Freeze §5 |

---

## 3. Storyboard Asset Contract

**Recorded as `D-43` in `DECISIONS.md`** (plan authorization). Batch completeness: **`D-44`**.

### 3.1 Frame filename convention

| Field | Value |
|---|---|
| Logical artifact name | `frame_{n}.png` where `n ∈ {1..6}` |
| Purpose | Human-readable label in docs/evidence; bytes identified by content hash |
| Count per generation | **4–6 frames** (agent decides within band; validator rejects &lt;4 or &gt;6) |

### 3.2 Asset row convention

| Field | Value |
|---|---|
| `asset_versions.stage` | `STORYBOARD` (`AssetStage.STORYBOARD`) |
| `asset_versions.branch` | `ai-draft` |
| `asset_versions.is_ai_generated` | `true` |
| `asset_versions.version` | **Shared generation set** — all frames from one activity invocation share the same monotonic `version` integer per `(project_id, STORYBOARD)` generation batch; distinguish frames via `metadata_json.frame_index` |
| MinIO key | `{project_id}/STORYBOARD/{content_hash}` via existing `build_object_key()` |
| MinIO `content_type` | `image/png` |
| `metadata_json` | **Required:** `{"frame_index": n, "frame_count": total, "prompt": "<shot prompt>"}`; **Optional:** `{"workflow": "sdxl_storyboard_v1", "seed": <int>}` |

### 3.3 Storage behavior

| Behavior | Rule |
|---|---|
| Write path | **Append-only** — each generation creates **new** rows for all frames (aligns with `D-38`) |
| In-place update | **Forbidden** — no UPDATE of existing STORYBOARD rows or MinIO objects |
| Input gate | Activity reads **approved script** per **`D-41`** (`fetch_approved_script`) before planning |
| Lineage | On each frame store, insert `lineage_edges(parent_id=script_asset_id, child_id=frame_asset_id)` |
| Failure | Planning, GPU, ComfyUI, or validation failure → no partial frame set stored (all-or-nothing per attempt) |
| Approve | **No asset write on approve** — US-17 approve writes `approvals` only (mirror `D-37`/`D-41`) |

### 3.4 Frame-set validation gate (proposed)

Before persisting any frame, validate:

- `4 <= frame_count <= 6`
- Each PNG decodes as valid image (magic bytes / PIL verify)
- Each `frame_index` unique within the set
- Each lineage edge references the same approved `script_asset_id`

On failure: raise validation error → Temporal retry → after max attempts mark pipeline `FAILED`.

---

## 4. Approved Script Input Contract (D-41)

US-16 **MUST** consume the approved script exclusively via **`D-41`** — already implemented in US-15.

### 4.1 Resolution rule

An approved script is:

1. The **latest** `asset_versions` row for `stage=SCRIPT` (highest `version`).
2. Gated by an **`APPROVED`** `approvals` row for `stage=SCRIPT` on the active `pipeline_run_id`.

No branch promotion. No copy-to-`main`. No additional asset write at SCRIPT approve time.

### 4.2 Worker API (closed)

```python
fetch_approved_script(settings, project_id=..., pipeline_run_id=...) -> ApprovedScriptAsset
```

Returns: `asset_version_id`, `script_fountain` (UTF-8 text), `minio_key`, `version`.

Raises `ApprovedScriptNotFoundError` if approval gate or SCRIPT row missing.

### 4.3 Cinematography agent inputs

| Input | Source | Forbidden |
|---|---|---|
| Fountain screenplay text | `ApprovedScriptAsset.script_fountain` | Prior rejected SCRIPT drafts |
| Style context (optional) | IDEA `metadata_json.style_note` via existing fetch | Raw STORY bytes (script is canonical for shots) |
| Rejection note | **Not in US-16** — first generation only; US-17 regen contract deferred | N/A |

### 4.4 Timing gate

`run_storyboard_agent` executes only when:

- Workflow stage loop reaches `PipelineStage.STORYBOARD` **after** SCRIPT approve advanced the run.
- `fetch_approved_script` succeeds (proves SCRIPT was approved on this run).

---

## 5. Acceptance Criteria Mapping

### AC-1 — 4–6 PNG frames via ComfyUI

| Track | Deliverable |
|---|---|
| **Worker** | Cinematography graph outputs 4–6 shot prompts; ComfyUI tool renders each to PNG |
| **Storage** | `store_storyboard_frames()` — 4–6 `asset_versions` rows, `stage=STORYBOARD` |
| **Tests** | Unit: mock ComfyUI returns PNG bytes; count validator |
| **Verification** | Olares: SQL 4–6 STORYBOARD rows; MinIO PNG objects; magic-byte check |

### AC-2 — Ollama unloaded before GPU

| Track | Deliverable |
|---|---|
| **Worker** | `gpu_sequencer.unload_ollama()` (or equivalent) before ComfyUI queue |
| **Runbook** | Follow `docs/runbooks/gpu-sequencing.md` |
| **Tests** | Unit: assert unload called before ComfyUI client |
| **Verification** | Olares worker log: unload event before `comfyui_queued`; no concurrent Ollama+ComfyUI |

### AC-3 — Lineage script → frames

| Track | Deliverable |
|---|---|
| **Worker** | `lineage_edges` insert per frame with `parent_id = script_asset_id` |
| **Tests** | Unit: N frames → N edges with same parent |
| **Verification** | Olares SQL join: SCRIPT id → STORYBOARD children count = frame count |

### AC-4 — STORYBOARD_REVIEW on success

| Track | Deliverable |
|---|---|
| **Workflow** | After activity success → `sync_pipeline_status(AWAITING_APPROVAL, STORYBOARD)` |
| **API** | `GET /pipeline/status` reflects gate (unchanged route) |
| **Tests** | Workflow unit / integration: status after STORYBOARD activity |
| **Verification** | Olares: status `AWAITING_APPROVAL` / `current_stage=STORYBOARD` |

### AC-5 — Retry 2× then FAILED

| Track | Deliverable |
|---|---|
| **Workflow** | `RetryPolicy(maximum_attempts=2)` on `run_storyboard_agent` (match issue text; note US-14 uses 3 for Ollama-only — ComfyUI is heavier) |
| **Worker** | `_mark_storyboard_failed` → `PIPELINE_FAILED` audit + `status=FAILED` |
| **Tests** | Unit: ComfyUI error propagates; mock retry exhaustion |
| **Verification** | Olares negative path optional; unit tests mandatory |

### Visual MVP task mapping (T-16-01..07)

| Backlog task | Implementation focus |
|---|---|
| T-16-01 Cinematography agent | `worker/app/agents/cinematography/{graph,state,nodes}.py` |
| T-16-02 ComfyUI tool | `worker/app/tools/comfyui.py` + production workflow JSON |
| T-16-03 `run_storyboard_agent` | `worker/app/temporal/activities/storyboard.py` |
| T-16-04 GPU sequencing | `worker/app/infrastructure/gpu/sequencer.py` (or inline per US-06 plan) |
| T-16-05 Multi-frame store | `worker/app/tools/assets.py` — `store_storyboard_frame(s)` |
| T-16-06 Lineage | Reuse lineage insert pattern from US-14 |
| T-16-07 Error handling | Activity try/except + Temporal retry + failed sync |

---

## 6. ComfyUI Architecture Impact

### 6.1 Workflow pin strategy

| Item | Decision |
|---|---|
| Smoke workflow | **`configs/comfyui/workflows/sdxl_storyboard.json`** — **do not mutate** (`D-03`) |
| Production workflow | **New file** e.g. `configs/comfyui/workflows/sdxl_storyboard_production.json` — fork from smoke pin |
| Checkpoint | `sdxl_base_1.0.safetensors` (matches `yanwk/comfyui-boot:cu124-sdxl-20240919`) |
| Resolution | 512×512 MVP (smoke default); amendment for 768+ if VRAM proof on Olares |
| Prompt injection | Replace static positive prompt node input with per-shot prompt from Cinematography agent |
| Seed | Deterministic per frame (`base_seed + frame_index`) for reproducibility in evidence |

### 6.2 ComfyUI client tool (T-16-02)

| Step | Behavior |
|---|---|
| 1 | Load production workflow JSON template |
| 2 | Patch positive-prompt node text |
| 3 | `POST /prompt` to ComfyUI API |
| 4 | Poll `/history/{prompt_id}` until complete |
| 5 | Fetch output image via `/view` |
| 6 | Return PNG bytes to activity |

**Config:** `COMFYUI_HOST` from settings (compose service name `comfyui:8188` on Olares).

### 6.3 Agent architecture (two-phase)

```text
Phase A — Ollama (CPU/GPU shared, LLM):
  fetch_approved_script → parse Fountain scene → plan 4-6 shot descriptions

Phase B — GPU handoff (D-08):
  unload_ollama() → comfyui_generate(shot_i) for i in 1..N

Phase C — Persist:
  store frames + lineage + audit ASSET_STORED × N
```

LangGraph runs **inside** `run_storyboard_agent` only (mirror US-12/US-14). Temporal owns durability, approval gates, and retry boundaries.

### 6.4 Workflow diff (conceptual)

**File:** `worker/app/temporal/workflows/spark_pipeline.py`

```python
elif stage == PipelineStage.STORYBOARD:
    rejection_note = self._state.last_rejection_note or ""
    await workflow.execute_activity(
        run_storyboard_agent,
        args=[project_id, run_id, rejection_note],
        start_to_close_timeout=timedelta(minutes=15),
        retry_policy=RetryPolicy(maximum_attempts=2),
    )
```

**Unchanged:** STORY/SCRIPT branches; approve/reject signals; stage loop order; 30-day approval timeout.

### 6.5 API impact

| Area | Change |
|---|---|
| New routes | **None expected** |
| Modified routes | **None expected** |
| `POST /pipeline/regenerate` | **Unchanged** — STORYBOARD returns 501 until US-17 |
| `GET /assets` | **Unchanged** — US-17 adds client filter for `stage=STORYBOARD` |
| Regression | All existing API unit tests must pass (78+) |

### 6.6 Infrastructure

| Service | Role |
|---|---|
| ComfyUI | Image inference (GPU) |
| Ollama | Shot planning (evicted before ComfyUI) |
| MinIO | PNG storage |
| Temporal | Activity orchestration |

Olares single-GPU constraint is **mandatory** — failure to unload Ollama is a closure blocker.

---

## 7. Asset Versioning and Lineage

### 7.1 Version semantics

| Stage | Version model |
|---|---|
| STORY | Monotonic per `(project_id, STORY)` — one row per generation |
| SCRIPT | Monotonic per `(project_id, SCRIPT)` — one row per generation |
| STORYBOARD | Monotonic **generation batch** per `(project_id, STORYBOARD)`; **multiple rows per batch** distinguished by `metadata_json.frame_index` |

Example after first storyboard generation:

| version | stage | frame_index | content_hash |
|---|---|---|---|
| 1 | STORYBOARD | 1 | `abc…` |
| 1 | STORYBOARD | 2 | `def…` |
| 1 | STORYBOARD | 3 | `ghi…` |
| 1 | STORYBOARD | 4 | `jkl…` |

Second generation (US-17 regen, future): all frames get `version=2`.

### 7.2 Lineage graph

```text
IDEA → STORY → SCRIPT → frame_1.png
                      → frame_2.png
                      → …
                      → frame_N.png
```

- US-14 already records `STORY → SCRIPT`.
- US-16 adds `SCRIPT → each STORYBOARD frame` (N edges per generation).
- US-20 lineage viewer will consume these edges later; US-16 does not add lineage API.

### 7.3 Audit events

| Event | Payload |
|---|---|
| `STAGE_STARTED` | `{"stage":"STORYBOARD","agent":"agent.cinematography"}` |
| `AGENT_TASK_COMPLETED` | model id, duration, frame_count |
| `ASSET_STORED` | per frame: `stage=STORYBOARD`, `frame_index`, `content_hash` |
| `PIPELINE_FAILED` | on exhausted retries: ComfyUI error summary |

---

## 8. Scope Control

### 8.1 Boundary register

| Capability | Owner |
|---|---|
| Cinematography agent + ComfyUI inference | **US-16** |
| Multi-frame asset store + lineage | **US-16** |
| `run_storyboard_agent` workflow swap | **US-16** |
| GPU sequencing enforcement | **US-16** |
| Storyboard gallery + lightbox | **US-17** |
| STORYBOARD approve/reject/regenerate UI | **US-17** |
| PNG content-read for gallery | **US-17** (proposed extension) |
| Pipeline `COMPLETED` on frame approve | **US-17** |

### 8.2 Primary creep risks

| Risk | Guard |
|---|---|
| Building gallery UI in US-16 | Generation only; stop at `AWAITING_APPROVAL`/`STORYBOARD` |
| STORYBOARD regenerate in US-16 | Defer to US-17; keep API 501 for STORYBOARD regen |
| Schema migration for frame grouping table | Use `metadata_json.frame_index` + shared `version` |
| Mutating `D-03` smoke workflow | Fork new production JSON |
| Video/export work | EPIC-05; forbidden in US-16 |
| Running Ollama + ComfyUI concurrently | `D-08` mandatory sequencing |

---

## 9. Verification Plan

### 9.1 Unit tests

| ID | File | Assertion |
|---|---|---|
| T-01 | `worker/tests/unit/test_cinematography.py` | 4–6 shot prompts from Fountain fixture |
| T-02 | `worker/tests/unit/test_comfyui_tool.py` | Mock ComfyUI client returns PNG |
| T-03 | `worker/tests/unit/test_storyboard_activity.py` | D-41 input gate; frame store count |
| T-04 | `worker/tests/unit/test_storyboard_lineage.py` | N lineage edges from script parent |
| T-05 | `worker/tests/unit/test_gpu_sequencer.py` | Unload before ComfyUI call order |
| T-06 | Regression | API 78+, worker 21+, web 20+ green |

### 9.2 Smoke / E2E (local or compose)

1. Reach STORYBOARD gate (idea → start → approve STORY → approve SCRIPT).
2. Worker generates 4–6 PNG frames (or mocked ComfyUI in CI).
3. `GET /pipeline/status` → `AWAITING_APPROVAL` / `STORYBOARD`.
4. SQL: STORYBOARD rows + lineage edges + SCRIPT parent unchanged.

### 9.3 Olares verification

**Script:** `deploy/k8s/us16-verify/verify_us16.sh` (to be authored at implementation).

| Check | Evidence |
|---|---|
| V-01 | 4–6 STORYBOARD `asset_versions` rows with PNG hashes |
| V-02 | MinIO objects under `{project_id}/STORYBOARD/` |
| V-03 | Lineage: SCRIPT parent → N frame children |
| V-04 | Status `AWAITING_APPROVAL`/`STORYBOARD` |
| V-05 | Worker log: Ollama unload before ComfyUI |
| V-06 | D-41 script asset id matches lineage parent |
| V-07 | US-15 regression — SCRIPT gate still passes |
| V-08 | ComfyUI failure path (optional negative test) |

**Package:** `evidence/us-16-verification/olares-<date>/US-16-ACCEPTANCE-PACKAGE.md`

### 9.4 Closure criteria

All five Visual MVP ACs evidenced on Olares with GPU sequencing proven → **ACCEPT**.  
Local-only ComfyUI mock without Olares GPU proof → **CONDITIONAL ACCEPT** (not sufficient for Visual MVP M5 gate).

---

## 10. Risk Assessment

| ID | Risk | L | I | Mitigation |
|---|---|---|---|---|
| R1 | VRAM OOM if Ollama not unloaded | H | H | Mandatory `D-08` sequencing; Olares log evidence V-05 |
| R2 | ComfyUI API drift / timeout | M | H | Pin production workflow; 15-min activity timeout; retry 2× |
| R3 | Partial frame store on mid-batch failure | M | H | All-or-nothing transaction per attempt; no orphan frames |
| R4 | Approved script not found at STORYBOARD | L | H | `fetch_approved_script` gate; only runs post-SCRIPT approve |
| R5 | Frame count outside 4–6 | M | M | Post-plan validator; fail before ComfyUI if out of band |
| R6 | Scope creep into US-17 gallery | M | M | No web changes in US-16; PR checklist |
| R7 | `D-03` smoke workflow mutated | L | M | Fork production JSON; code review gate |
| R8 | In-flight runs nondeterministic after worker swap | L | M | Fresh runs after deploy; cancel stale STORYBOARD stubs |
| R9 | 512×512 quality insufficient for review | M | L | Accept for MVP; amendment path documented |
| R10 | Multi-frame version query ambiguity | M | M | `D-43` `frame_index` in `metadata_json`; document SQL for US-17 |

---

## 11. Governance attestation

US-16 is a **high-scope worker story (8 SP)** that replaces the STORYBOARD stub with real **Ollama planning + ComfyUI inference**, stores **4–6 PNG frames** with **script lineage**, and enforces **GPU sequencing** on Olares. It consumes the **closed `D-41` approved-script contract** and does not require schema migrations, API routes, or review UI.

**Request: governance acceptance of this brief before implementation authorization.**
