# Sprint 3E — US-14 Generate One-Scene Script (governance brief)

**Status:** RATIFIED for planning — **not authorized for implementation** until this brief is accepted.  
**Story:** US-14 "Generate one-scene script" · FEAT-06 AI Script Generation · EPIC-03 · P0 · 5 SP · Sprint S3.  
**Prerequisites (all closed):** US-05 ✅ (MinIO/assets) · US-07 ✅ (workflow) · US-12 ✅ (`run_story_agent`) · US-13 ✅ (`D-37` approved-story contract) · US-09 ✅ (regenerate contract at STORY; SCRIPT regenerate deferred to post-US-14).  
**Blocks:** US-15 (script review UI), US-16 (storyboard consumes approved script).

**Canonical source:** `GitHub Issues - Visual MVP.md` → Issue 30 `[US-14]` (5 ACs, tasks T-14-01..05).  
**Superseded detail:** `MVP Backlog.md` → FEAT-06 / US-14 — used only to disambiguate; Visual MVP issue is authoritative.

---

## 1. Source Review

### 1.1 Approved acceptance criteria (Visual MVP Issue 30 — authoritative)

1. Exactly **1 scene** Fountain script.
2. `script` stored as an asset (`stage=SCRIPT`).
3. `fountain` format with `is_ai_generated=true`.
4. **Lineage edge** story → script recorded.
5. Workflow advances to **SCRIPT review** (`AWAITING_APPROVAL` / `current_stage=SCRIPT`).

### 1.2 Approved tasks (Visual MVP Issue 30)

| Task | Description |
|---|---|
| T-14-01 | Implement LangGraph Screenwriter graph |
| T-14-02 | Implement `run_script_agent` Temporal activity |
| T-14-03 | Add Fountain format validation |
| T-14-04 | Record lineage edge story → script |
| T-14-05 | Store script asset version |

### 1.3 Backlog (FEAT-06) corroborating detail

- "Given **approved story**, when script activity runs, then Screenwriter produces Fountain-format script for exactly **1 scene**."
- Output contains **scene heading**, **action**, and **at least one dialogue block**.
- `script.fountain` stored with `is_ai_generated=true`.
- Lineage edge `story.md → script.fountain` in `lineage_edges`.
- Workflow status → `SCRIPT_REVIEW` (maps to `AWAITING_APPROVAL` / `SCRIPT` in current schema — **no new status enum**).

### 1.4 Dependencies

| Dependency | Status | Contract |
|---|---|---|
| US-05 MinIO + `asset_versions` | ✅ Closed | `store_asset` / worker `store_story_markdown` pattern |
| US-07 `SparkPipelineWorkflow` | ✅ Closed | Stage loop; SCRIPT currently `run_stub_stage` |
| US-08 approve/reject | ✅ Closed | Signals unchanged; SCRIPT gate uses same contract |
| US-12 Story Architect | ✅ Closed | Agent + activity pattern to mirror |
| US-13 + `D-37` | ✅ Closed | Approved story = latest STORY version + `APPROVED` approvals row |
| US-09 regenerate | ✅ Closed at STORY | SCRIPT regenerate returns 501 until US-14 lands; extend in US-15/US-09 follow-up if needed |

**Hard dependency chain:** US-13 → **US-14** → US-15 → US-16.

---

## 2. Script Format Definition

### 2.1 Output file type

| Field | Value |
|---|---|
| Logical filename | `script.fountain` |
| `asset_versions.stage` | `SCRIPT` (`AssetStage.SCRIPT`) |
| MinIO `content_type` | `text/plain; charset=utf-8` (Fountain is plain text) |
| `branch` | `ai-draft` (first generation; mirrors US-12 STORY semantics) |
| `is_ai_generated` | `true` |
| Encoding | UTF-8 |

### 2.2 Fountain requirements (MVP minimum)

Fountain is a plain-text screenplay format. US-14 output **must** be valid enough for US-15 preview and US-16 storyboard consumption.

**Required elements (1 scene only):**

| Element | Fountain syntax | Example |
|---|---|---|
| Title page (optional but recommended) | `Title:` / `Credit:` / `Author:` lines at top | `Title: Mars Garden` |
| Scene heading | Line starting with `INT.` or `EXT.` | `INT. MARS HABITAT - NIGHT` |
| Action | Plain paragraph(s) between blocks | `Elara studies the bioluminescent sample.` |
| Character + Dialogue | `CHARACTER` on its own line; dialogue follows | `ELARA` / `We need more light.` |
| Parenthetical (optional) | `(whispering)` indented under character | — |

**Explicitly not required for US-14:**

- Multiple scenes (must be **exactly one** scene heading block).
- Transitions (`CUT TO:`, `FADE OUT.`).
- Dual dialogue, lyrics, centered text, or title-page pagination.
- PDF or Final Draft export.

### 2.3 Minimum one-scene structure

```
Title: <derived from story or project>
Author: AIMPOS Screenwriter

INT. OR EXT. LOCATION - TIME

Action description paragraph(s).

CHARACTER NAME
Dialogue line(s).
```

**Scene count rule:** exactly **one** line matching `^(INT\.|EXT\.|INT/EXT\.)` (case-sensitive per Fountain convention). A second scene heading is a **validation failure**.

### 2.4 Validation rules (T-14-03)

Implement lightweight **post-generation validation** in the Screenwriter `finalize` node (not a full Fountain parser library unless already present):

| Rule | Check | On failure |
|---|---|---|
| V-01 Non-empty | `len(script.strip()) > 0` | Retry activity (Temporal policy) or mark run FAILED |
| V-02 Scene heading | Exactly 1 match of `^(INT\.|EXT\.|INT/EXT\.)\s+.+` | Reject output; log validation error |
| V-03 Dialogue block | At least one line that is ALL CAPS (character cue) followed by non-empty dialogue | Reject output |
| V-04 Action present | At least one non-heading, non-dialogue paragraph between scene heading and first character | Reject output |
| V-05 No second scene | Zero additional scene headings after the first | Reject output |
| V-06 UTF-8 | Encodable as UTF-8 | Reject output |

Validation failures surface as activity errors (worker logs + optional `AGENT_TASK_FAILED` audit if pattern exists); do **not** store invalid bytes to MinIO.

---

## 3. Architecture Impact

### 3.1 API

| Area | Change | Notes |
|---|---|---|
| New routes | **None required** | SCRIPT generation is workflow-driven after STORY approval (existing `POST /pipeline/approve` advances to SCRIPT; worker runs agent on stage entry) |
| `POST /pipeline/regenerate` | **No change in US-14** | SCRIPT stage continues to return **501** until a follow-up extends the allowlist (document in implementation plan; not US-14 AC) |
| `GET /assets`, content read | **No change in US-14** | US-15 adds script review + Fountain preview; US-14 may add `GET /assets/{id}/content` for SCRIPT if US-15 needs it (optional enabler — decide in US-15 brief) |
| Lineage API | **None** | Edge written by worker activity (T-14-04); `GET /lineage` is US-20 |

### 3.2 Workflow (`SparkPipelineWorkflow`)

| Today | US-14 change |
|---|---|
| `SCRIPT` stage calls `run_stub_stage` | `SCRIPT` stage calls **`run_script_agent`** (mirror STORY branch) |
| Post-reject regenerate loop | **Unchanged** — already supports multi-regenerate after US-09 fix; SCRIPT regenerate execution still 501 at API until extended |
| Stage order | Unchanged: STORY → SCRIPT → STORYBOARD |
| Signals / statuses | Unchanged: `approve`, `reject`, `regenerate`; `RUNNING` / `AWAITING_APPROVAL` only |

**Conceptual diff (same pattern as US-12):**

```python
if stage == PipelineStage.STORY:
    await workflow.execute_activity(run_story_agent, ...)
elif stage == PipelineStage.SCRIPT:
    await workflow.execute_activity(run_script_agent, ...)
else:
    await workflow.execute_activity(run_stub_stage, ...)
```

### 3.3 Worker

**New files (mirror Story Architect layout):**

```
worker/app/
├── agents/
│   └── screenwriter/
│       ├── graph.py       # LangGraph StateGraph (T-14-01)
│       ├── state.py       # ScreenwriterState
│       ├── nodes.py       # load_story, draft_script, finalize + validate
│       └── constants.py   # agent.screenwriter, PROMPT_VERSION, SCRIPT_BRANCH
├── temporal/activities/
│   └── script.py          # run_script_agent (T-14-02)
└── tools/
    └── assets.py          # + fetch_approved_story (D-37), store_script_fountain (T-14-05)
```

**Activity contract (`run_script_agent`):**

1. `STAGE_STARTED` audit (`agent.screenwriter`).
2. Resolve **approved story** per `D-37`: latest `asset_versions` row for `stage=STORY` where run has `approvals` row `decision=APPROVED` for STORY; download story bytes from MinIO.
3. Run LangGraph Screenwriter (`qwen3:14b` per `configs/ollama/models.json` → `stages.script`).
4. Validate Fountain (§2.4).
5. `store_script_fountain` → new `asset_versions` row (`stage=SCRIPT`, `branch=ai-draft`, `version=1` for first script in run).
6. Insert `lineage_edges` row: `parent_id` = approved story asset id, `child_id` = new script asset id (T-14-04).
7. `AGENT_TASK_COMPLETED` + `ASSET_STORED` audits (mirror US-12).
8. Return `asset_version_id`.

Register `run_script_agent` in `worker/app/main.py`.

### 3.4 Assets (MinIO + `asset_versions`)

| Field | Value |
|---|---|
| `stage` | `SCRIPT` |
| `version` | `1` on first generation for `(project_id, SCRIPT)` chain; monotonic on regenerate (future) |
| `branch` | `ai-draft` |
| `is_ai_generated` | `true` |
| `minio_key` | `{project_id}/SCRIPT/{content_hash}` (existing `build_object_key` convention) |
| `pipeline_run_id` | Current run |

**Input resolution (`D-37`):** Screenwriter reads the **latest STORY version at the time SCRIPT stage starts** (typically the approved human-edit or ai-draft the user approved). Do not re-fetch after approval signal delay; use version present when activity begins.

### 3.5 Audit

| Event | When | Payload highlights |
|---|---|---|
| `STAGE_STARTED` | Activity start | `stage=SCRIPT`, `agent=agent.screenwriter` |
| `AGENT_TASK_COMPLETED` | Ollama success | `model_id=qwen3:14b`, `asset_version_id`, `duration_ms` |
| `ASSET_STORED` | After MinIO write | `stage=SCRIPT`, `branch=ai-draft`, `version`, `content_hash` |

No new audit enum values required unless implementation chooses `AGENT_TASK_FAILED` for validation errors (optional).

### 3.6 Database

| Area | Change |
|---|---|
| Alembic migration | **None** — `asset_versions`, `lineage_edges`, `audit_events`, `approvals` tables already exist (`0001_initial_core_tables`) |
| New repositories | Optional thin helper for `lineage_edges` insert in worker (raw SQL acceptable, matching US-12 worker style) |
| `lineage_edges` | One row per script generation: `parent_id` = story asset, `child_id` = script asset; `UNIQUE(parent_id, child_id)` |

---

## 4. Acceptance Criteria Mapping

### AC-1 — Exactly 1 scene Fountain script

- **Trigger:** Pipeline reaches SCRIPT stage (`RUNNING` / `SCRIPT`) after STORY approval; workflow invokes `run_script_agent`.
- **Behavior:** Screenwriter produces Fountain text with exactly one scene heading; validation §2.4 passes.
- **Evidence:** Stored MinIO object; validator unit test; Olares worker log showing `story_agent_completed` equivalent for script; manual Fountain inspect showing single `INT./EXT.` block.

### AC-2 — `script` asset stored (`stage=SCRIPT`)

- **Behavior:** New `asset_versions` row with `stage=SCRIPT`, `version>=1`, `branch=ai-draft`.
- **Evidence:** SQL `SELECT * FROM asset_versions WHERE stage='SCRIPT'`; MinIO `mc stat` on `minio_key`.

### AC-3 — Fountain, `is_ai_generated=true`

- **Behavior:** Bytes are plain-text Fountain; row flag `is_ai_generated=true`.
- **Evidence:** SQL column check; content sample with scene heading + dialogue.

### AC-4 — Lineage edge story → script

- **Behavior:** `lineage_edges` row linking approved story `asset_versions.id` → new script `asset_versions.id`.
- **Evidence:** SQL `SELECT parent_id, child_id FROM lineage_edges WHERE child_id=<script_id>`; parent row `stage=STORY`.

### AC-5 — Workflow to SCRIPT review

- **Behavior:** After activity + `sync_pipeline_status`, run is `AWAITING_APPROVAL` / `current_stage=SCRIPT` (dashboard displays **REVIEW** per US-10 mapping).
- **Evidence:** `GET /pipeline/status` JSON; `pipeline_runs` row; Temporal history showing SCRIPT generation then approval wait.

**Note:** Visual MVP AC wording "SCRIPT_REVIEW" maps to existing `AWAITING_APPROVAL` + `current_stage=SCRIPT` — **no new `PipelineRunStatus` value**.

---

## 5. Scope Control

### 5.1 Required (in US-14)

| Item | Rationale |
|---|---|
| LangGraph Screenwriter agent (Ollama `qwen3:14b`) | AC-1, T-14-01 |
| `run_script_agent` Temporal activity | AC-1/2, T-14-02 |
| Replace SCRIPT `run_stub_stage` in workflow | AC-5 |
| Fountain validation (§2.4) | AC-1, T-14-03 |
| `store_script_fountain` + MinIO write | AC-2/3, T-14-05 |
| `lineage_edges` insert story → script | AC-4, T-14-04 |
| Approved-story fetch per `D-37` | Backlog prerequisite |
| Audit events (`STAGE_STARTED`, `AGENT_TASK_COMPLETED`, `ASSET_STORED`) | Parity with US-12 |
| Prompt template `configs/prompts/screenwriter/v1.yaml` | D-36 config pattern |

### 5.2 Optional (may defer without blocking AC)

| Item | Defer to |
|---|---|
| `GET /assets/{id}/content` for SCRIPT bytes | US-15 (if preview needs it) |
| `POST /pipeline/regenerate` for SCRIPT stage | Post-US-14 / US-15 (API currently 501) |
| `AGENT_TASK_FAILED` audit on validation errors | Implementation discretion |
| Title-page polish beyond minimum | US-15 review UX |
| Shared `fetch_latest_approved_asset(stage)` helper in aimpos-core | Refactor optional |

### 5.3 Out of scope (do not implement in US-14)

| Item | Owner story |
|---|---|
| Script review UI / Fountain preview | **US-15** |
| Approve/reject/regenerate at SCRIPT gate (UI) | **US-15** / US-09 extension |
| Storyboard / ComfyUI frame generation | **US-16** |
| Human-edit save for script (`branch=human-edit`) | **US-15** if in AC |
| Multi-scene scripts | Scope Freeze — 1 scene only |
| PDF/Fountain export download | Deferred (Scope Freeze) |
| Video assembly | Deferred |
| `GET /lineage` API | **US-20** |
| Alembic schema migration | Not needed |
| Neo4j / graph projector | ADR-0003 — PostgreSQL edges only |

---

## 6. Verification Plan

### 6.1 Unit tests

| Suite | Tests |
|---|---|
| Worker | Screenwriter graph: validation accepts valid 1-scene Fountain; rejects 0-scene, 2-scene, no-dialogue |
| Worker | `run_script_agent` mocked: stores SCRIPT row, writes lineage edge |
| API | Regression only — no new routes; existing pipeline tests green |

### 6.2 Integration / smoke (local)

Ephemeral compose or pytest harness:

1. `POST /ideas` → `POST /pipeline/start` → poll to STORY `AWAITING_APPROVAL`.
2. `POST /pipeline/approve` STORY → poll to SCRIPT `AWAITING_APPROVAL`.
3. Assert `asset_versions` SCRIPT row exists; `is_ai_generated=true`; `branch=ai-draft`.
4. Assert `lineage_edges` story→script.
5. Assert audit chain: `STAGE_STARTED` → `AGENT_TASK_COMPLETED` → `ASSET_STORED`.

### 6.3 Olares E2E (preferred for ACCEPT)

Mirror US-12/US-09 evidence pattern:

| Check | Evidence |
|---|---|
| SCRIPT asset row + MinIO object | SQL + `mc stat` |
| Lineage edge | SQL |
| Audit trail | `audit_events` for run |
| Pipeline status `AWAITING_APPROVAL`/`SCRIPT` | API JSON |
| Worker log `script_agent_completed` | Pod logs |
| Fountain content sample | First 40 lines redacted in package |

Scripts: `deploy/k8s/us14-verify/` (to be authored at implementation time).

### 6.4 Regression gates

| Gate | Requirement |
|---|---|
| US-12 story generation | Still passes |
| US-13 story review / human-edit | Still passes |
| US-09 STORY regenerate | Still passes |
| CI | API 76+, worker 5+, web 14+ tests green |

---

## 7. Risk Assessment

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Ollama outputs markdown/prose instead of Fountain | Medium | High | Strong system prompt; §2.4 validator; retry policy (max 3) |
| R2 | Model emits 2+ scenes despite prompt | Medium | High | V-05 validator; explicit "ONE SCENE ONLY" in `v1.yaml` |
| R3 | Wrong story version fed to Screenwriter | Low | High | `D-37` contract: fetch latest STORY + verify APPROVED approval exists for run |
| R4 | Lineage edge omitted | Low | Medium | Activity unit test asserts insert; Olares SQL check in acceptance package |
| R5 | Workflow nondeterminism (US-09 lesson) | Low | High | Do not change post-regen wait semantics; only swap stub→agent for SCRIPT |
| R6 | Scope creep into US-15 (review UI) | Medium | Medium | US-14 stops at asset + gate; no ReviewPage script mode |
| R7 | SCRIPT regenerate 501 confuses testers | Low | Low | Document in implementation report; US-15 may extend |
| R8 | GPU/Ollama timeout on 14B model | Low | Medium | 5-minute activity timeout (match `run_story_agent`); Olares `qwen3:14b` already proven |

---

## 8. Governance attestation

US-14 is a **medium-scope agent story (5 SP)** that replaces the SCRIPT-stage stub with a real Ollama Screenwriter, following the proven US-12 pattern. It opens **M4 — Script pipeline** without UI changes, schema migrations, or new pipeline status values.

**Request: governance acceptance of this brief before implementation authorization.**
