# Sprint 3E — US-14 Implementation Plan

**Status:** DRAFT — for governance review. **No code authorized** by this document.  
**Parent brief:** `docs/sprints/sprint-3e-us14-brief.md` (**ACCEPTED**)  
**Story:** US-14 Generate one-scene script · FEAT-06 · P0 · 5 SP  
**Baseline:** `v0.3.2-us09` (`main` @ US-09 closure)  
**Decision record:** `D-39` (script asset semantics — to be appended to `DECISIONS.md` at implementation start)

---

## 0. Implementation summary

US-14 replaces the **SCRIPT-stage stub** with a real Ollama Screenwriter agent. Net-new work is **worker-only** (LangGraph agent, Temporal activity, asset store, lineage insert, Fountain validator) plus a **minimal workflow dispatch change**. **No API routes, no web UI, no Alembic migration.**

| Layer | Net-new | Reuse |
|---|---|---|
| API | — | `POST /pipeline/approve` advances STORY→SCRIPT; `GET /pipeline/status` |
| Temporal workflow | `SCRIPT` → `run_script_agent` branch in `_run_stage_generation` | Stage loop, signals, post-reject regenerate loop (US-09) |
| Worker | Screenwriter graph, `run_script_agent`, `store_script_fountain`, `fetch_approved_story`, lineage insert, Fountain validator | `sync_pipeline_status`, Ollama client, audit helpers |
| Web | — | — |
| DB schema | — | `asset_versions`, `lineage_edges`, `audit_events`, `approvals` |
| Config | `configs/prompts/screenwriter/v1.yaml` | `configs/ollama/models.json` → `stages.script` |

**Estimated effort:** 5 SP · ~3–4 days (worker/agent track → workflow wiring → unit tests → Olares verification).

---

## 1. Acceptance criteria traceability

### AC-1 — Exactly 1 scene Fountain script

| Track | Task IDs | Deliverable |
|---|---|---|
| **Backend** | — (no API change) | — |
| **Workflow** | W-01 | `SCRIPT` stage invokes `run_script_agent` instead of `run_stub_stage` |
| **Worker** | A-01..A-06, A-09 | LangGraph Screenwriter + `finalize` validator (§3) |
| **Tests** | T-01..T-06, T-10 | Validator unit tests; graph integration with mocked Ollama |
| **Verification** | V-01, V-04, V-07 | MinIO Fountain sample; worker log `script_agent_completed`; validator pass in unit log |

### AC-2 — `script` asset stored (`stage=SCRIPT`)

| Track | Task IDs | Deliverable |
|---|---|---|
| **Backend** | — | — |
| **Workflow** | W-01 | Activity return value consumed; no workflow state mutation |
| **Worker** | A-07, A-08 | `store_script_fountain` → `asset_versions` row + MinIO put |
| **Tests** | T-07, T-08 | Mocked store asserts `stage=SCRIPT`, `version=1` on first gen |
| **Verification** | V-02, V-03 | SQL `asset_versions` row; `mc stat` on `minio_key` |

### AC-3 — Fountain format, `is_ai_generated=true`

| Track | Task IDs | Deliverable |
|---|---|---|
| **Backend** | — | — |
| **Workflow** | W-01 | — |
| **Worker** | A-07, A-08 | `is_ai_generated=true`, `branch=ai-draft`, `content_type=text/plain` |
| **Tests** | T-07 | Assert flags on stored row |
| **Verification** | V-02, V-04 | SQL columns; content-type + Fountain syntax sample |

### AC-4 — Lineage edge story → script

| Track | Task IDs | Deliverable |
|---|---|---|
| **Backend** | — | — |
| **Workflow** | — | Lineage written inside activity (worker-side, mirrors US-12 pattern) |
| **Worker** | A-10, A-11 | `fetch_approved_story` returns parent id; `insert_lineage_edge(parent, child)` |
| **Tests** | T-09 | Mock DB asserts `lineage_edges` insert with correct parent/child |
| **Verification** | V-05 | SQL join: parent `stage=STORY`, child `stage=SCRIPT` |

### AC-5 — Workflow to SCRIPT review

| Track | Task IDs | Deliverable |
|---|---|---|
| **Backend** | — | Regression: `test_pipeline_approve.py` STORY approve still advances |
| **Workflow** | W-01 | Existing post-generation `sync_pipeline_status(AWAITING_APPROVAL, SCRIPT)` unchanged |
| **Worker** | A-12 | Activity completes before sync; failures call `_mark_script_failed` |
| **Tests** | T-11 | Approve STORY → status poll shows `AWAITING_APPROVAL`/`SCRIPT` (smoke) |
| **Verification** | V-06, V-08 | `GET /pipeline/status` JSON; Temporal history snippet |

### Visual MVP task mapping (T-14-01..05)

| Backlog task | Implementation tasks |
|---|---|
| T-14-01 LangGraph Screenwriter | A-01..A-06 |
| T-14-02 `run_script_agent` | A-12, A-13, W-01 |
| T-14-03 Fountain validation | A-09, T-01..T-06 |
| T-14-04 Lineage edge | A-10, A-11, T-09 |
| T-14-05 Store script asset | A-07, A-08, T-07, T-08 |

---

## 2. Fountain validation specification

Implementation location: `worker/app/agents/screenwriter/validate.py` (pure functions, no I/O).

### 2.1 Scene heading regex

**Canonical pattern (line-anchored, multiline):**

```python
SCENE_HEADING_RE = re.compile(
    r"^(?P<prefix>INT\.|EXT\.|INT/EXT\.|I/E\.)\s+(?P<location>.+?)(?:\s+-\s+(?P<time>.+))?$",
    re.MULTILINE,
)
```

| Component | Rule |
|---|---|
| Prefix | `INT.`, `EXT.`, `INT/EXT.`, or `I/E.` (Fountain abbreviations) |
| Location | Non-empty after prefix + space |
| Time of day | Optional; if present, preceded by ` - ` (space-hyphen-space) |
| Line anchor | `^` … `$` with `re.MULTILINE` — heading must be a full line |

### 2.2 Accepted forms (examples)

```
INT. MARS HABITAT - NIGHT
EXT. VALLES MARINERIS - DAY
INT/EXT. ROVER - CONTINUOUS
I/E. LAB - MORNING
INT. CORRIDOR
```

Title-page lines (`Title:`, `Credit:`, `Author:`, `Draft date:`) above the scene heading are **ignored** by scene-heading detection.

### 2.3 Rejected forms (non-exhaustive)

| Input | Reason |
|---|---|
| `int. room - night` | Lowercase prefix (Fountain requires uppercase `INT.`/`EXT.`) |
| `INTERIOR. ROOM` | Non-standard prefix |
| `INT ROOM - NIGHT` | Missing dot after `INT` |
| `INT. ROOM\nEXT. STREET` | Two scene headings → **V-05 fail** |
| *(empty file)* | **V-01 fail** |
| Scene heading only, no action/dialogue | **V-04 or V-03 fail** |
| Markdown code fences wrapping entire script | Strip before validate; if still invalid → fail |

### 2.4 Dialogue detection rules

**Character cue line:**

```python
CHARACTER_CUE_RE = re.compile(r"^[A-Z0-9][A-Z0-9 \.'\-()]{0,30}$")
```

| Rule | Detail |
|---|---|
| Case | All uppercase letters/digits (Fountain convention) |
| Length | 1–31 characters |
| Allowed chars | `A-Z`, `0-9`, space, `.`, `'`, `-`, `(`, `)` |
| Exclusions | Lines matching `SCENE_HEADING_RE`; title-page keys (`Title:` etc.); blank lines |
| Parenthetical | Line `(whispering)` immediately after cue — skip, not dialogue |
| Dialogue | First non-empty line after cue (or after parenthetical) that is **not** a new cue and **not** a scene heading |

**Minimum dialogue block (V-03):** At least one character cue with ≥1 following dialogue line (non-empty, not a cue, not a heading).

### 2.5 Action detection rules (V-04)

After the **first** scene heading line, before the **first** character cue:

- At least one non-empty line that is **not** a scene heading, **not** a character cue, **not** a title-page key, **not** parenthetical-only.
- Action may span multiple paragraphs (blank lines allowed within action).

### 2.6 Single-scene validation logic

```text
validate_fountain(text) -> ValidationResult(ok, errors[])

1. V-01: text.strip() non-empty
2. V-06: text encodable UTF-8 (input already str; reject surrogate pairs if any)
3. Find all SCENE_HEADING_RE matches → list headings
4. V-02: len(headings) == 1  (else error "expected exactly 1 scene heading, found N")
5. V-05: redundant if V-02 exact; same check
6. Locate first_heading_line_index
7. Scan lines after heading for first CHARACTER_CUE_RE match → cue_index
8. V-04: if cue_index is None → error "no character cue found"
           else lines between heading and cue must include ≥1 action line (§2.5)
9. V-03: at cue_index, verify dialogue line exists per §2.4
10. Return ok=True iff errors empty
```

**On failure:** `finalize` node raises `FountainValidationError`; activity does **not** call `store_script_fountain` or insert lineage. Temporal retry policy: `maximum_attempts=3` (match `run_story_agent`).

---

## 3. D-39 — Script asset definition

**To be recorded in `DECISIONS.md` at implementation start** (governance pin for US-14, US-15, US-16).

### 3.1 Script filename

| Field | Value |
|---|---|
| Logical artifact name | `script.fountain` |
| Purpose | Human-readable label in docs/evidence; **not** a separate filesystem path on MinIO |
| Bytes identity | Content-addressed by SHA-256 hash (same as all assets) |

### 3.2 Asset naming convention

| Field | Value |
|---|---|
| `asset_versions.stage` | `SCRIPT` (`AssetStage.SCRIPT`) |
| `asset_versions.branch` | `ai-draft` (first AI generation; US-15 may add `human-edit` later) |
| `asset_versions.is_ai_generated` | `true` |
| `asset_versions.version` | Monotonic per `(project_id, stage)` — `COALESCE(MAX(version),0)+1` |
| MinIO key | `{project_id}/SCRIPT/{content_hash}` via `build_object_key()` |
| MinIO `content_type` | `text/plain; charset=utf-8` |
| `metadata_json` | `null` on first generation (optional `{"format":"fountain","scenes":1}` — **optional**, not required for AC) |

### 3.3 Storage behavior

| Behavior | Rule |
|---|---|
| Write path | **Append-only** — each generation creates a **new** `asset_versions` row (aligns with `D-38` semantics for AI drafts) |
| In-place update | **Forbidden** — no UPDATE of existing SCRIPT rows or MinIO objects |
| Dedup | If `content_hash` collides, MinIO put is idempotent; DB still appends new version row with new UUID |
| Input gate | Activity reads **approved story** per `D-37` before generation |
| Lineage | On successful store, insert `lineage_edges(parent_id=story_asset_id, child_id=script_asset_id)` |
| Failure | Validation or Ollama failure → no asset row, no lineage edge, no MinIO write |

**Approved story resolution (`D-37` + US-14):**

```sql
-- Latest STORY version for project (at activity start)
SELECT av.id, av.minio_key, av.version
FROM asset_versions av
WHERE av.project_id = :project_id AND av.stage = 'STORY'
ORDER BY av.version DESC LIMIT 1;

-- Gate: APPROVED approval must exist for this run + STORY
SELECT 1 FROM approvals
WHERE pipeline_run_id = :run_id AND stage = 'STORY' AND decision = 'APPROVED';
```

If approval row missing → raise `ApprovedStoryNotFoundError` → activity fails → `PIPELINE_FAILED` audit (mirror `_mark_story_failed`).

---

## 4. Architecture impact

### 4.1 API impact

| Area | Change |
|---|---|
| New routes | **None** |
| Modified routes | **None** |
| `POST /pipeline/regenerate` | **Unchanged** — SCRIPT returns **501** (pre-US-15 extension) |
| `GET /assets`, content read | **Unchanged** — US-15 adds SCRIPT preview |
| Auth / middleware | **Unchanged** |
| Regression | All existing API unit tests must pass (76+) |

### 4.2 Workflow impact

**File:** `worker/app/temporal/workflows/spark_pipeline.py`

| Change | Detail |
|---|---|
| Import | `from app.temporal.activities.script import run_script_agent` |
| `_run_stage_generation` | Add `elif stage == PipelineStage.SCRIPT:` branch calling `run_script_agent` with `[project_id, run_id]` |
| Timeouts | `start_to_close_timeout=timedelta(minutes=5)` (match STORY) |
| Retry policy | `RetryPolicy(maximum_attempts=3)` |
| Unchanged | STORY branch (`run_story_agent` + `rejection_note`); STORYBOARD stub; approve/reject/regenerate signals; post-reject inner loop |

**Risk pin (US-09 lesson):** Do **not** modify post-regeneration `wait_condition` lambdas in this story.

### 4.3 Worker impact

**New modules:**

| Path | Purpose |
|---|---|
| `worker/app/agents/screenwriter/constants.py` | `AGENT_ID`, `PROMPT_VERSION`, `SCRIPT_BRANCH`, `MIN_SCRIPT_CHARS` |
| `worker/app/agents/screenwriter/state.py` | `ScreenwriterState` TypedDict/dataclass |
| `worker/app/agents/screenwriter/nodes.py` | `load_story_context`, `draft_script`, `finalize_script` |
| `worker/app/agents/screenwriter/validate.py` | `validate_fountain()` per §2 |
| `worker/app/agents/screenwriter/graph.py` | `run_screenwriter_graph()` — linear graph |
| `worker/app/temporal/activities/script.py` | `run_script_agent` activity |
| `configs/prompts/screenwriter/v1.yaml` | System/user templates; **ONE SCENE ONLY** guardrails |

**Modified modules:**

| Path | Change |
|---|---|
| `worker/app/tools/assets.py` | `fetch_approved_story()`, `store_script_fountain()`, `insert_lineage_edge()` |
| `worker/app/main.py` | Register `run_script_agent` in `activities=[...]` |
| `worker/app/temporal/activities/__init__.py` | Export `run_script_agent` |

**Activity sequence (`run_script_agent`):**

1. `STAGE_STARTED` (`agent.screenwriter`)
2. `fetch_approved_story` → story bytes + `story_asset_id`
3. `run_screenwriter_graph` → Fountain text + `model_id` + `duration_ms`
4. `validate_fountain` (in finalize node)
5. `store_script_fountain` → `StoredScriptAsset`
6. `insert_lineage_edge(story_asset_id, script_asset_id)`
7. `AGENT_TASK_COMPLETED` + `ASSET_STORED`
8. Return `asset_version_id`

### 4.4 Audit impact

| Event | New/changed | Payload |
|---|---|---|
| `STAGE_STARTED` | Existing enum | `stage=SCRIPT`, `agent=agent.screenwriter` |
| `AGENT_TASK_COMPLETED` | Existing enum | `asset_version_id`, `model_id`, `duration_ms`, `prompt_version`, `branch=ai-draft` |
| `ASSET_STORED` | Existing enum | `stage=SCRIPT`, `version`, `content_hash`, `branch=ai-draft` |
| `PIPELINE_FAILED` | Existing enum | On activity failure: `stage=SCRIPT`, `error`, `agent=agent.screenwriter` |

**No new `AuditEventType` values required.**

### 4.5 Lineage impact

| Aspect | Detail |
|---|---|
| Table | `lineage_edges` (existing, `0001_initial_core_tables`) |
| Insert | One row per successful script generation |
| `parent_id` | Approved story `asset_versions.id` (`stage=STORY`) |
| `child_id` | New script `asset_versions.id` (`stage=SCRIPT`) |
| Constraint | `UNIQUE(parent_id, child_id)` — duplicate insert is a bug; activity should not retry insert on same ids |
| API exposure | **None** in US-14 (`GET /lineage` is US-20) |

---

## 5. Scope control

### IN SCOPE

| ID | Item |
|---|---|
| S-01 | LangGraph Screenwriter agent (`agent.screenwriter`) |
| S-02 | `configs/prompts/screenwriter/v1.yaml` |
| S-03 | `run_script_agent` Temporal activity |
| S-04 | Workflow: SCRIPT → `run_script_agent` (replace stub) |
| S-05 | Fountain validator (§2) in `validate.py` |
| S-06 | `store_script_fountain` + MinIO write |
| S-07 | `fetch_approved_story` per `D-37` |
| S-08 | `lineage_edges` insert story → script |
| S-09 | Audit events (STAGE_STARTED, AGENT_TASK_COMPLETED, ASSET_STORED) |
| S-10 | `D-39` decision record in `DECISIONS.md` |
| S-11 | Worker unit tests (validator + activity mocks) |
| S-12 | Smoke script outline (`scripts/smoke/test_us14_script.py` or equivalent) |
| S-13 | Olares verify scripts (`deploy/k8s/us14-verify/`) + acceptance package |
| S-14 | API/worker/web regression (no new failures) |

### OUT OF SCOPE

| ID | Item | Owner |
|---|---|---|
| X-01 | Script review UI / Fountain HTML preview | US-15 |
| X-02 | `GET /assets/{id}/content` for SCRIPT | US-15 (if needed) |
| X-03 | `PUT /assets/{id}` human-edit for SCRIPT | US-15 |
| X-04 | `POST /pipeline/regenerate` for SCRIPT execution | US-15 / US-09 extension |
| X-05 | Storyboard / ComfyUI (`run_storyboard_agent`) | US-16 |
| X-06 | Multi-scene Fountain output | Scope Freeze |
| X-07 | PDF / export download | Deferred |
| X-08 | Video assembly | Deferred |
| X-09 | `GET /lineage/{run_id}` API | US-20 |
| X-10 | Alembic migration | N/A |
| X-11 | Web UI changes | US-15 |
| X-12 | New `PipelineRunStatus` or stage enum values | Forbidden |
| X-13 | Full Fountain parser library dependency | Avoid unless necessary |

---

## 6. Verification plan

### 6.1 Unit tests

| ID | File | Assertion |
|---|---|---|
| T-01 | `worker/tests/unit/test_fountain_validate.py` | Valid 1-scene sample → `ok=True` |
| T-02 | same | Two scene headings → `ok=False` |
| T-03 | same | No scene heading → `ok=False` |
| T-04 | same | Scene + action, no dialogue → `ok=False` |
| T-05 | same | Lowercase `int.` heading → `ok=False` |
| T-06 | same | Accepted `INT/EXT.` and `I/E.` forms → `ok=True` |
| T-07 | `worker/tests/unit/test_script_agent.py` | Mocked graph+store: SCRIPT row flags correct |
| T-08 | same | First script version = 1 for project |
| T-09 | same | Lineage insert called with story parent id |
| T-10 | `worker/tests/unit/test_screenwriter_graph.py` | Mocked Ollama: graph returns fountain text |
| T-11 | API regression | `pytest api/tests/unit` — 76+ pass, zero changes required |
| T-12 | Web regression | Vitest 14 pass — zero changes |

### 6.2 Smoke tests

**Script:** `scripts/smoke/test_us14_script.py` (new, gated on live stack env vars — same pattern as US-12).

| Step | Action | Expected |
|---|---|---|
| 1 | `POST /ideas` | IDEA asset |
| 2 | `POST /pipeline/start` | RUNNING/STORY |
| 3 | Poll status | `AWAITING_APPROVAL` / `STORY` |
| 4 | `POST /pipeline/approve` STORY | 200 |
| 5 | Poll status (≤10 min) | `AWAITING_APPROVAL` / `SCRIPT` |
| 6 | SQL: SCRIPT `asset_versions` | 1 row, `is_ai_generated=true`, `branch=ai-draft` |
| 7 | SQL: `lineage_edges` | parent STORY → child SCRIPT |
| 8 | SQL: `audit_events` | `STAGE_STARTED` → `AGENT_TASK_COMPLETED` → `ASSET_STORED` for SCRIPT |

### 6.3 Olares verification

**Prerequisites:** `aimpos-worker` image with US-14 code; shared Ollama `qwen3:14b`; existing Temporal/Postgres/MinIO.

**Script:** `deploy/k8s/us14-verify/verify_us14.sh` (to be authored at implementation).

| Check | Evidence capture |
|---|---|
| V-01 | Fountain content sample (first 40 lines, redacted) |
| V-02 | `asset_versions` SCRIPT row (id, version, branch, hash) |
| V-03 | MinIO `mc stat` on script key |
| V-04 | Validator pass implied by successful store (unit log reference) |
| V-05 | `lineage_edges` SQL join |
| V-06 | `GET /pipeline/status` → `AWAITING_APPROVAL`/`SCRIPT` |
| V-07 | Worker log: `script_agent_completed` with `model_id=qwen3:14b` |
| V-08 | Temporal `workflow show` — SCRIPT activity scheduled after STORY approve |
| V-09 | US-09 STORY regenerate regression (quick smoke on separate run or pre-check) |
| V-10 | US-12/US-13 regression (story path still works on fresh run) |

**Package:** `evidence/us-14-verification/olares-<date>/US-14-ACCEPTANCE-PACKAGE.md`

### 6.4 Acceptance evidence checklist

| AC | Required evidence |
|---|---|
| AC-1 | Fountain file sample + validator unit test log + single `INT./EXT.` block |
| AC-2 | SQL `asset_versions` + MinIO stat |
| AC-3 | SQL `is_ai_generated=true` + plain-text content |
| AC-4 | SQL `lineage_edges` parent=STORY, child=SCRIPT |
| AC-5 | API status JSON + `pipeline_runs.current_stage=SCRIPT` |

**Closure recommendation criteria:** All five ACs evidenced on Olares → **ACCEPT**; partial local-only → **CONDITIONAL ACCEPT**.

---

## 7. Risk review

| ID | Risk | L | I | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | Model outputs markdown/prose not Fountain | M | H | `v1.yaml` strict output contract; §2 validator; 3-attempt retry | Agent |
| R2 | Model emits 2+ scenes | M | H | Prompt "EXACTLY ONE SCENE HEADING"; V-02/V-05 | Agent |
| R3 | Wrong story version (not approved / not latest) | L | H | `D-37` fetch + approval gate query; unit test | Worker |
| R4 | Lineage edge omitted on partial failure | L | M | Insert only after successful store; T-09 | Worker |
| R5 | Workflow nondeterminism (US-09 regression) | L | H | Diff limited to `_run_stage_generation` elif branch; no wait-loop edits | Workflow |
| R6 | Scope creep into US-15 Review UI | M | M | PR checklist X-11; zero `web/` changes | Governance |
| R7 | Ollama timeout / 14B latency | L | M | 5-min activity timeout; Olares already proven for STORY | Ops |
| R8 | Fountain validator false negatives (valid script rejected) | M | M | Fixture suite T-01..T-06; tune CHARACTER_CUE_RE if needed | Agent |
| R9 | Fountain validator false positives (invalid stored) | L | H | Conservative rules; Olares manual inspect in V-01 | QA |
| R10 | `lineage_edges` unique violation on retry | L | M | Idempotent activity design: store creates new child id each attempt; lineage only on success | Worker |

---

## 8. Implementation task checklist (execution order)

| Phase | Tasks | Gate |
|---|---|---|
| **P0 — Decision** | Append `D-39` to `DECISIONS.md` | Governance pin |
| **P1 — Validator** | A-09, T-01..T-06 | Validator green |
| **P2 — Agent** | A-01..A-06, `v1.yaml`, T-10 | Graph unit test green |
| **P3 — Assets** | A-07, A-08, A-10, A-11, T-07..T-09 | Store + lineage mocked |
| **P4 — Activity** | A-12, A-13, register in `main.py` | Activity unit test green |
| **P5 — Workflow** | W-01 | Worker starts; no import errors |
| **P6 — Regression** | T-11, T-12 | CI-equivalent pass |
| **P7 — Smoke** | T-11 smoke script | Local/compose optional |
| **P8 — Olares** | V-01..V-10, acceptance package | Formal closure review |

---

## 9. Governance attestation

This plan implements **only** Visual MVP Issue 30 (US-14). It follows the US-12 agent pattern, preserves US-09 workflow semantics, honors `D-37` story input and `D-38`-aligned append-only AI draft storage (`D-39` for SCRIPT), and opens **M4 — Script pipeline** without UI or schema changes.

**Request: governance acceptance of this implementation plan before code authorization.**
