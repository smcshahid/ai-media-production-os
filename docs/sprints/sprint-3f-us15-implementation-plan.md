# Sprint 3F — US-15 Implementation Plan

**Status:** **IMPLEMENTED** — Olares verification PASS (`evidence/us-15-verification/olares-2026-06-11/`).  
**Parent brief:** `docs/sprints/sprint-3f-us15-brief.md` (**ACCEPTED**)  
**Story:** US-15 Review and approve script · FEAT-07 · P0 · 3 SP  
**Baseline:** `v0.3.3-us14` (`main` @ US-14 closure)  
**Decision records:** `D-41` (approved script contract — appended to `DECISIONS.md` at plan authorization)

---

## 0. Implementation summary

US-15 completes the **SCRIPT review gate** opened by US-14. Net-new work spans **API extensions** (SCRIPT content-read, SCRIPT regenerate), **worker extensions** (rejection note → Screenwriter), **minimal workflow arg change**, and **web script mode** (Fountain preview + approve/reject/regenerate). **No Alembic migration. No new pipeline status values. STORYBOARD remains stub until US-16.**

| Layer | Net-new | Reuse |
|---|---|---|
| API | Extend `GET /assets/{id}/content` (SCRIPT); extend `POST /pipeline/regenerate` (SCRIPT) | `POST /pipeline/approve`, `GET /assets`, `GET /pipeline/status` |
| Temporal workflow | Pass `rejection_note` to `run_script_agent` | Stage loop, US-09 post-reject regenerate loop (stage-agnostic) |
| Worker | `run_script_agent(rejection_note)`, Screenwriter prompt injection | `run_script_agent`, `store_script_fountain`, `fetch_approved_story`, D-40 validator |
| Web | Script review mode, Fountain→HTML formatter, script asset selection | `ReviewPage` approve/reject/regenerate chrome, `usePipelineStatus` |
| DB schema | — | `asset_versions`, `approvals`, `audit_events`, `lineage_edges` |

**Estimated effort:** 3 SP · ~2–3 days (API + worker track → web formatter/mode → tests → Olares verification).

---

## 1. D-41 — Approved script contract

**Recorded in `DECISIONS.md` as D-41.** Parallels `D-37` (approved story).

### 1.1 Authoritative script source

| Question | Answer |
|---|---|
| What is the approved script bytes? | The **latest** `asset_versions` row where `project_id = :project_id` and `stage = 'SCRIPT'`, ordered by `version DESC LIMIT 1`. |
| Which branch? | Whatever row is latest — at SCRIPT gate this is normally `branch=ai-draft`, `is_ai_generated=true`. Human-edit SCRIPT rows are **out of US-15 scope**; if added later, latest version wins (same as `D-37`). |
| MinIO location | `minio_key` on that row (`{project_id}/SCRIPT/{content_hash}` per `D-39`). |
| Format | UTF-8 Fountain plain text (`text/plain`). |

**Worker helper (US-16 prep, implement in US-15):** `fetch_approved_script(settings, project_id, pipeline_run_id)` in `worker/app/tools/assets.py` — mirror `fetch_approved_story`:

```sql
-- Gate: APPROVED approval must exist for this run + SCRIPT
SELECT 1 FROM approvals
WHERE pipeline_run_id = :run_id AND stage = 'SCRIPT' AND decision = 'APPROVED';

-- Latest SCRIPT version for project (at activity start)
SELECT av.id, av.minio_key, av.version, av.content_hash
FROM asset_versions av
WHERE av.project_id = :project_id AND av.stage = 'SCRIPT'
ORDER BY av.version DESC LIMIT 1;
```

If approval row missing → raise `ApprovedScriptNotFoundError` (new, symmetric with `ApprovedStoryNotFoundError`).

### 1.2 Approval requirements

| Requirement | Detail |
|---|---|
| Immutable approval row | `approvals` insert on `POST /pipeline/approve` GRANT with `stage=SCRIPT`, `decision=APPROVED` (US-08 path — unchanged). |
| No asset write on approve | Approve **must not** create a new `asset_versions` row, mutate MinIO, or promote branch. |
| Audit | `APPROVAL_RECORDED` audit row (existing enum). |
| Temporal | `approve` signal → workflow exits SCRIPT wait → STORYBOARD generation. |
| Regenerate before approve | Each regen appends new ai-draft SCRIPT version (`D-38`/`D-39`). Approve binds to **latest** version at signal time. |

**T-15-04 "Mark approved script version in DB"** is satisfied by **`approvals` + latest SCRIPT version identity** — not a separate `approved_asset_id` column.

### 1.3 Relationship to US-16

| US-16 need | D-41 contract |
|---|---|
| Input script bytes for storyboard agent | `fetch_approved_script()` → Fountain text from latest SCRIPT version |
| Proof script was human-approved | `APPROVED` `approvals` row for `stage=SCRIPT` on the run |
| Lineage (optional context) | Existing `lineage_edges` story→script from US-14; US-16 does not require new edges on approve |
| Gate timing | US-16 `run_storyboard_agent` runs only after SCRIPT approve advanced workflow to STORYBOARD stage |

**US-15 deliverable for US-16:** Document the D-41 resolution query in the implementation report and Olares acceptance package. Implement `fetch_approved_script` in US-15 (used by tests; consumed by US-16 activity).

**US-15 does not implement** `run_storyboard_agent`, ComfyUI calls, or frame assets.

---

## 2. Acceptance criteria traceability

### AC-1 — Fountain rendered with formatting

| Track | Task IDs | Deliverable |
|---|---|---|
| **API** | B-01, B-02 | Extend `GET /assets/{id}/content` for `stage=SCRIPT`; `text/plain` response |
| **Workflow** | — | — |
| **Worker** | — | — |
| **Web** | F-01, F-02, F-03, F-04 | `fountainFormat.ts`, script mode preview pane, `selectLatestAiDraftScriptAsset` |
| **Tests** | T-01, T-02, T-03, T-09 | API content-read SCRIPT; formatter unit tests; script asset selection |
| **Verification** | V-01 | Formatted preview DOM/screenshot; `GET /assets/{id}/content` network trace; Fountain sample |

### AC-2 — Approve advances to STORYBOARD generating

| Track | Task IDs | Deliverable |
|---|---|---|
| **API** | — (reuse `POST /pipeline/approve`) | GRANT at `stage=SCRIPT` |
| **Workflow** | — (reuse existing stage advance) | STORYBOARD stub runs after SCRIPT approve |
| **Worker** | — | `run_stub_stage` for STORYBOARD unchanged |
| **Web** | F-05 | Approve button active in script mode (no dirty-state gate) |
| **Tests** | T-10 | `test_pipeline_approve.py` SCRIPT approve advances stage |
| **Verification** | V-04, V-05 | Status `RUNNING`/`STORYBOARD` → `AWAITING_APPROVAL`/`STORYBOARD`; `approvals` SCRIPT/APPROVED |

### AC-3 — Reject/regenerate works

| Track | Task IDs | Deliverable |
|---|---|---|
| **API** | B-03 | Add `PipelineStage.SCRIPT` to `_SUPPORTED_REGENERATE_STAGES` |
| **Workflow** | W-01 | Pass `rejection_note` to `run_script_agent` args |
| **Worker** | A-01..A-05 | `run_script_agent(rejection_note)`, graph state, `draft_script` injection |
| **Web** | F-06, F-07 | Script reject hint; Regenerate enabled after reject; reload preview |
| **Tests** | T-04, T-05, T-06, T-11 | SCRIPT regen happy path; 429; rejection note in prompt; 501 removed |
| **Verification** | V-02, V-03 | SQL version chain v→v+1; `REGENERATION_REQUESTED` audit; worker `script_agent_completed`; 429 on 4th |

### AC-4 — Approved version marked in DB

| Track | Task IDs | Deliverable |
|---|---|---|
| **API** | — | `approvals` row via existing approve route |
| **Workflow** | — | No extra persistence |
| **Worker** | A-06 | `fetch_approved_script()` helper + unit test |
| **Web** | — | — |
| **Tests** | T-07, T-08 | Assert no new SCRIPT row on approve; D-41 resolution query |
| **Verification** | V-05 | SQL: `approvals` + latest SCRIPT id/hash unchanged post-approve |

### Visual MVP task mapping (T-15-01..04)

| Backlog task | Implementation tasks |
|---|---|
| T-15-01 Review screen — script mode | F-02, F-03, F-05, F-06 |
| T-15-02 Fountain-to-HTML formatter | F-01, F-04, T-01 |
| T-15-03 Wire approve/reject for script | F-05, F-06 (reuse handlers); T-10 regression |
| T-15-04 Mark approved script in DB | D-41 + `approvals` row; A-06; T-07, T-08; V-05 |

---

## 3. Script review UX

### 3.1 Mode detection

| Condition | UI mode |
|---|---|
| `AWAITING_APPROVAL` + `current_stage=SCRIPT` | **Script mode** (US-15) |
| `AWAITING_APPROVAL` + `current_stage=STORY` | Story mode (US-13 — unchanged) |
| Other | Redirect to dashboard (existing) |

Replace generic stub copy in `ReviewPage.tsx` (lines ~263–266) with script-mode branch.

### 3.2 Fountain rendering approach (T-15-02)

**Location:** `web/src/lib/fountainFormat.ts` (pure functions, no API calls).

**Algorithm:** Line-scanner state machine (not a Fountain library):

```text
for each line (preserve blank lines as block separators):
  if matches SCENE_HEADING_RE → emit <h2 class="fountain-scene">
  else if matches TITLE_PAGE_PREFIX → emit <p class="fountain-title-page">
  else if matches CHARACTER_CUE_RE and next non-blank is not heading → emit <p class="fountain-character">
  else if previous state was character/parenthetical and line is dialogue → emit <p class="fountain-dialogue">
  else if line is parenthetical → emit <p class="fountain-parenthetical">
  else if non-empty → emit <p class="fountain-action">
```

**Regex alignment:** Reuse the same heading/cue patterns as `worker/app/agents/screenwriter/validate.py` (D-40) for consistency — copy constants into shared doc comment, not a cross-package import.

**Output:** Sanitized HTML string rendered via `dangerouslySetInnerHTML` inside a scrollable `<div class="fountain-preview">` or built DOM via React elements (preferred if trivial).

**CSS:** Add minimal classes in existing stylesheet (`web/src/index.css` or component-scoped): scene heading bold/uppercase; character centered/small-caps; dialogue indented; action full-width.

**Fallback:** On empty input or parse error → `<pre class="fountain-raw">` with escaped raw Fountain bytes.

### 3.3 Preview behavior

| Event | Behavior |
|---|---|
| Enter script mode | `listAssets(projectId)` → `selectLatestAiDraftScriptAsset(assets)` → `getAssetContent(asset.id)` → `formatFountainHtml(text)` |
| Loading | Show "Loading script…" |
| Missing asset | Error: "No SCRIPT asset found" |
| Metadata | Version, branch, AI-generated badge (mirror story mode) |
| After regenerate | Reload latest ai-draft SCRIPT + re-render preview |
| `RUNNING`/generating | Disable Regenerate; show poll refresh via `usePipelineStatus` |

### 3.4 Approve flow

```
User clicks "Approve stage"
  → POST /pipeline/approve { project_id, stage: "SCRIPT", decision: "GRANT" }
  → refresh pipeline status
  → user redirected to dashboard (Navigate when status ≠ REVIEW) or sees STORYBOARD gate later
```

No save/dirty gate in script mode (no human-edit in scope).

### 3.5 Reject flow

```
User enters note → clicks "Reject"
  → validate note non-empty
  → POST /pipeline/approve { stage: "SCRIPT", decision: "REJECT", note }
  → setRejectedHint(true)
  → refresh status (stays AWAITING_APPROVAL / SCRIPT)
  → show hint: "Script rejected. Regenerate to request a new AI draft…"
```

### 3.6 Regenerate flow

```
Precondition: rejectedHint && stage === "SCRIPT" && status !== "RUNNING"
User clicks "Regenerate"
  → POST /pipeline/regenerate { project_id, stage: "SCRIPT" }
  → on 200: refresh status; loadScript(projectId, { preferAiDraft: true })
  → on 429: surface API detail; keep preview on last version
Worker (async):
  → REGENERATION_REQUESTED audit
  → workflow regen loop → run_script_agent(project_id, run_id, rejection_note)
  → new SCRIPT ai-draft version + lineage edge
```

Max 3 regenerations per run (US-09 unchanged). 4th → HTTP 429, no signal.

---

## 4. Architecture impact

### 4.1 API impact

| Route | Change |
|---|---|
| `GET /assets/{asset_id}/content` | **Modify** — allow `stage=SCRIPT` in addition to STORY; return `text/plain; charset=utf-8`; 422 for IDEA/other stages |
| `POST /pipeline/regenerate` | **Modify** — add `SCRIPT` to `_SUPPORTED_REGENERATE_STAGES` (remove 501 for SCRIPT) |
| `POST /pipeline/approve` | **Unchanged** |
| `PUT /assets/{id}` | **Unchanged** (STORY human-edit only) |
| `GET /assets`, `GET /pipeline/status` | **Unchanged** |
| New routes | **None** |

**File:** `api/app/routes/assets.py` — rename `_require_story_asset` → `_require_readable_asset` accepting STORY | SCRIPT.

**Regression:** All 76+ API unit tests must pass; extend `test_assets_us13.py` or add `test_assets_us15.py`.

### 4.2 Workflow impact

**File:** `worker/app/temporal/workflows/spark_pipeline.py`

| Change | Detail |
|---|---|
| W-01 | In `_run_stage_generation` SCRIPT branch, pass `rejection_note` like STORY: `args=[project_id, run_id, rejection_note]` |
| Unchanged | Post-reject `wait_condition` lambdas (US-09 fix preserved) |
| Unchanged | STORYBOARD `run_stub_stage` branch |
| Unchanged | Signal handlers, stage order, approval timeouts |

**Risk pin:** Diff limited to SCRIPT activity `args` list — do **not** edit regenerate wait lambdas.

### 4.3 Worker impact

| Path | Change |
|---|---|
| `worker/app/temporal/activities/script.py` | `run_script_agent(project_id, run_id, rejection_note="")`; pass to graph |
| `worker/app/agents/screenwriter/state.py` | Add `rejection_note: str \| None` |
| `worker/app/agents/screenwriter/graph.py` | Accept `rejection_note` in `run_screenwriter_graph()` |
| `worker/app/agents/screenwriter/nodes.py` | Inject revision block in `draft_script_node` (mirror `story_architect/nodes.py`) |
| `worker/app/tools/assets.py` | Add `ApprovedScriptNotFoundError`, `fetch_approved_script()` |
| `configs/prompts/screenwriter/v1.yaml` | Optional: add `{rejection_note}` placeholder in user template |

### 4.4 Audit impact

| Event | New/changed | When |
|---|---|---|
| `APPROVAL_RECORDED` | Reuse | SCRIPT approve/reject |
| `REGENERATION_REQUESTED` | Reuse | `payload.stage=SCRIPT` |
| `STAGE_STARTED` | Reuse | SCRIPT regen → `agent.screenwriter` |
| `AGENT_TASK_COMPLETED` | Reuse | SCRIPT regen complete |
| `ASSET_STORED` | Reuse | New SCRIPT version after regen |
| `PIPELINE_FAILED` | Reuse | Validation/Ollama failure on regen |

**No new `AuditEventType` values.**

### 4.5 Asset / versioning impact

| Behavior | Rule |
|---|---|
| Review load target | Latest SCRIPT `ai-draft` (`is_ai_generated=true`) |
| Regenerate | Append-only new SCRIPT row (`D-38`/`D-39`) |
| Approve | **No** new SCRIPT row; `approvals` APPROVED marks intent (`D-41`) |
| Human-edit SCRIPT | **Out of scope** — no `PUT /assets/{id}` extension |
| Lineage on regen | New `lineage_edges` row story parent → new script child (same story parent per `fetch_approved_story`) |
| Schema migration | **None** |

---

## 5. Scope control

### 5.1 IN SCOPE

| ID | Item |
|---|---|
| S-01 | `ReviewPage` script mode with Fountain HTML preview |
| S-02 | `web/src/lib/fountainFormat.ts` + styles |
| S-03 | `web/src/lib/scriptReview.ts` — `selectLatestAiDraftScriptAsset` |
| S-04 | Extend `GET /assets/{id}/content` for SCRIPT (`D-41`) |
| S-05 | Extend `POST /pipeline/regenerate` for SCRIPT |
| S-06 | `run_script_agent(rejection_note)` + Screenwriter injection |
| S-07 | Workflow SCRIPT args include `rejection_note` |
| S-08 | `fetch_approved_script()` worker helper (`D-41`) |
| S-09 | `D-41` in `DECISIONS.md` |
| S-10 | API/worker/web unit tests per §6 |
| S-11 | Olares verify scripts `deploy/k8s/us15-verify/` + acceptance package |
| S-12 | Full regression (API 76+, worker 16+, web 14+) |

### 5.2 OUT OF SCOPE

| ID | Item | Owner |
|---|---|---|
| X-01 | `run_storyboard_agent` / ComfyUI inference | US-16 |
| X-02 | Storyboard gallery review UI | US-17 |
| X-03 | SCRIPT human-edit save (`PUT /assets/{id}`) | Deferred |
| X-04 | Raw Fountain textarea editor | Optional; not in AC |
| X-05 | PDF / export download | Deferred |
| X-06 | Asset history browser / diff | US-22 |
| X-07 | `GET /lineage` API | US-20 |
| X-08 | Alembic migration | N/A |
| X-09 | New `PipelineRunStatus` or stage enum | Forbidden |
| X-10 | Branch promotion on approve | Forbidden (`D-41`) |
| X-11 | Full Fountain spec parser library | Avoid unless necessary |

---

## 6. Verification plan

### 6.1 Unit tests

| ID | File | Assertion |
|---|---|---|
| T-01 | `web/src/tests/fountainFormat.test.ts` | Scene heading, action, character, dialogue HTML |
| T-02 | `web/src/tests/fountainFormat.test.ts` | Olares US-14 sample parses without error |
| T-03 | `web/src/tests/scriptReview.test.ts` | `selectLatestAiDraftScriptAsset` picks highest ai-draft version |
| T-04 | `api/tests/unit/test_assets_us15.py` | `GET /assets/{id}/content` returns SCRIPT bytes; 422 for IDEA |
| T-05 | `api/tests/unit/test_pipeline_regenerate.py` | SCRIPT happy path: signal + audit (extend existing fixtures) |
| T-06 | `api/tests/unit/test_pipeline_regenerate.py` | SCRIPT 4th regen → 429; SCRIPT without reject → 409 |
| T-07 | `api/tests/unit/test_pipeline_regenerate.py` | `test_regenerate_script_stage_no_longer_501` |
| T-08 | `worker/tests/unit/test_screenwriter.py` | `draft_script_node` includes rejection note in prompt |
| T-09 | `worker/tests/unit/test_script_approved.py` (new) | `fetch_approved_script` gates on APPROVED approval |
| T-10 | `api/tests/unit/test_pipeline_approve.py` | SCRIPT approve advances to STORYBOARD (regression) |
| T-11 | `web/src/tests/reviewPage.test.ts` (optional) | Script mode renders preview container |

### 6.2 Regression tests

| Suite | Gate |
|---|---|
| API unit | **76+** pass (zero regressions) |
| Worker unit | **16+** pass |
| Web unit | **14+** pass (new formatter tests add to count) |
| Web build | `npm run build` PASS |
| US-14 smoke path | Fresh run still reaches SCRIPT gate with `script_agent_completed` |
| US-09 STORY regen | Existing tests unchanged |

### 6.3 Olares verification

**Prerequisites:** `aimpos-worker:us15` (US-14 + rejection note); `aimpos-api:us15` (content-read + regenerate); fresh pipeline run (cancel stale SCRIPT-gate runs if worker changed).

**Scripts:** `deploy/k8s/us15-verify/verify_us15.sh`, `collect_us15.sh`, `run_remote.sh` (mirror `us14-verify/`).

| Check | Steps | Evidence |
|---|---|---|
| V-01 | Reach SCRIPT gate; open Review; capture formatted preview | Screenshot / HTML excerpt in package |
| V-02 | Reject with note → Regenerate #1 → poll new SCRIPT version | SQL `asset_versions` v→v+1; audit chain |
| V-03 | Regenerate #2, #3 → 4th returns 429 | HTTP 429 body; version chain unchanged after 429 |
| V-04 | Approve final SCRIPT → poll STORYBOARD gate | `GET /pipeline/status` → `AWAITING_APPROVAL`/`STORYBOARD` |
| V-05 | D-41 resolution query post-approve | `approvals` SCRIPT/APPROVED + latest SCRIPT id/hash |
| V-06 | US-14 regression on same deploy | `script_agent_completed` on fresh run |
| V-07 | Worker log rejection note on SCRIPT regen | Pod log excerpt |

**Package:** `evidence/us-15-verification/olares-<date>/US-15-ACCEPTANCE-PACKAGE.md`

### 6.4 Acceptance evidence checklist

| AC | Required evidence |
|---|---|
| AC-1 | Preview screenshot + formatter unit log + content-read network trace |
| AC-2 | Status JSON STORYBOARD + `approvals` SCRIPT/APPROVED + Temporal history |
| AC-3 | Regen version chain + `REGENERATION_REQUESTED` + 429 + worker log |
| AC-4 | D-41 SQL query result; no new SCRIPT row on approve |

**Closure recommendation:** All four ACs on Olares → **ACCEPT**; local-only → **CONDITIONAL ACCEPT**.

---

## 7. Risk review

| ID | Risk | L | I | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | Fountain formatter misclassifies US-14 output | M | M | T-02 fixture from Olares US-14 sample; raw `<pre>` fallback | Web |
| R2 | SCRIPT regen breaks US-09 STORY path | L | H | Extend allowlist only; full regression; no wait-loop edits | API/Workflow |
| R3 | Content-read opened too wide | L | M | Stage guard STORY\|SCRIPT only; T-04 rejects IDEA | API |
| R4 | Rejection note not in Screenwriter prompt | L | H | T-08 mirrors US-09 story test; Olares log check | Worker |
| R5 | US-16 ambiguous approved script | M | H | D-41 + `fetch_approved_script` + V-05 SQL | Worker/Governance |
| R6 | Scope creep into US-16 ComfyUI | M | M | Approve stops at STORYBOARD stub gate; PR checklist X-01 | Governance |
| R7 | Nondeterminism on in-flight runs after worker deploy | L | M | Fresh runs only; `cancel_stale_run.sh` pattern from US-14 | Ops |
| R8 | Regenerate 429 UX confusion | L | L | Reuse STORY hint copy; same error contract | Web |
| R9 | `dangerouslySetInnerHTML` XSS from model output | L | M | Escape HTML entities in formatter; trusted local AI output only | Web |
| R10 | Lineage duplicate on regen retry | L | M | Insert only after successful store (US-14 pattern) | Worker |

---

## 8. Implementation task checklist (execution order)

| Phase | Tasks | Gate |
|---|---|---|
| **P0 — Decision** | Append `D-41` to `DECISIONS.md` | Governance pin ✅ (this plan) |
| **P1 — API** | B-01..B-03, T-04..T-07, T-10 | Content-read + SCRIPT regen tests green |
| **P2 — Worker** | A-01..A-06, W-01, T-08, T-09 | Rejection note + `fetch_approved_script` green |
| **P3 — Web formatter** | F-01, F-04, T-01, T-02 | Formatter unit tests green |
| **P4 — Web review mode** | F-02, F-03, F-05, F-06, F-07, T-03 | Script mode manual smoke |
| **P5 — Regression** | T-10, full suites | CI-equivalent pass |
| **P6 — Olares** | V-01..V-07, acceptance package | Formal closure review |

### Task ID reference

**API (B-*)**

| ID | Task |
|---|---|
| B-01 | Generalize content-read guard for STORY \| SCRIPT |
| B-02 | Return `text/plain` for SCRIPT Fountain bytes |
| B-03 | Add SCRIPT to `_SUPPORTED_REGENERATE_STAGES` |

**Workflow (W-*)**

| ID | Task |
|---|---|
| W-01 | Pass `rejection_note` to `run_script_agent` |

**Worker (A-*)**

| ID | Task |
|---|---|
| A-01 | `run_script_agent(rejection_note)` signature |
| A-02 | `ScreenwriterState.rejection_note` |
| A-03 | `run_screenwriter_graph(..., rejection_note)` |
| A-04 | `draft_script_node` revision block injection |
| A-05 | Optional `v1.yaml` template placeholder |
| A-06 | `fetch_approved_script()` + `ApprovedScriptNotFoundError` |

**Web (F-*)**

| ID | Task |
|---|---|
| F-01 | `fountainFormat.ts` |
| F-02 | Script mode in `ReviewPage.tsx` |
| F-03 | `loadScript` callback + preview pane |
| F-04 | Fountain preview CSS |
| F-05 | Approve in script mode (no dirty gate) |
| F-06 | Script reject hint + regenerate button visibility |
| F-07 | `handleRegenerate` reloads script preview |

---

## 9. Governance attestation

This plan implements **only** Visual MVP Issue 31 (US-15). It extends US-13 content-read and US-09 regenerate patterns to SCRIPT, establishes **`D-41`** approved-script semantics for US-16, and completes the script review gate without schema changes, human-edit, or storyboard agent work.

**Request: governance authorization of this plan before implementation begins.**
