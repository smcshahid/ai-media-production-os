# Sprint 3C — US-13 Review and Edit Story (governance brief)

**Status:** **CLOSED** — formally accepted 2026-06-10 (`v0.3.1-us13`).
**Governance decisions ratified (2026-06-10, `D-37`):** §4.2 → **Option A adopted** (no branch promotion; "approved story" = latest STORY version + `APPROVED` `approvals` row). §3.1 → **`GET /assets/{id}/content` is an in-scope required enabler** for US-13 (story text only).
**Story:** US-13 "Review and edit story" · FEAT-05 Story Review & Approval · EPIC-03 · P0 · 3 SP · Sprint S3.
**Prerequisites (all closed):** US-12 ✅ (`story.md` on `stage=STORY`, `branch=ai-draft`, `AWAITING_APPROVAL`), US-08 ✅ (`POST /pipeline/approve`), US-26 ✅ (nav shell / Review route).
**Blocks:** US-14 (Screenwriter consumes the approved story).

This brief is traceable to two approved sources:
- **Canonical execution source:** `GitHub Issues - Visual MVP.md` → Issue 29 `[US-13]` (4 acceptance criteria, tasks T-13-01..04).
- **Detailed backlog (archived, superseded):** `MVP Backlog.md` → FEAT-05 / US-13 (expanded AC + tasks).
Where the two differ, the **Visual MVP issue is authoritative**; backlog detail is used only to disambiguate intent. Conflicts are flagged in §4.

---

## 1. Source Review — what is approved for US-13

### 1.1 Approved acceptance criteria (Visual MVP Issue 29 — authoritative)
1. Review screen shows **editable treatment**.
2. **Save** creates a **human-edit version**.
3. **Approve** advances the pipeline.
4. **Reject enables regenerate.**

### 1.2 Approved tasks (Visual MVP Issue 29)
- `T-13-01` Build Review screen — story mode.
- `T-13-02` Implement `PUT /assets/{id}` text update.
- `T-13-03` Wire Approve/Reject buttons to pipeline API.
- `T-13-04` Display rejection-note input on reject.

### 1.3 Backlog (FEAT-05) corroborating detail
- "Story ready for review → treatment text displayed in **editable textarea**."
- "Edit story text and save → **new `story.md` version on branch `human-edit`**."
- "Approve → approval recorded and pipeline advances to **script generation**."
- "Reject with note → pipeline stays at story stage and **regenerate is enabled**."

### 1.4 Scope classification

| Capability | Classification | Basis |
|---|---|---|
| Display generated `story.md` text in the Review screen | **Required** | AC-1; implied by "editable treatment" |
| Editable textarea pre-filled with current treatment | **Required** | AC-1, backlog FEAT-05 |
| Save edited text → new `asset_versions` row, `branch=human-edit`, `is_ai_generated=false` | **Required** | AC-2, backlog FEAT-05, T-13-02 |
| `PUT /assets/{id}` (or equivalent) text-update endpoint | **Required** | T-13-02 |
| `GET /assets/{id}/content` read endpoint to fetch story **content bytes** for the editor — **story text only; NO asset browser / history / diff / search** | **Required (enabler) — ratified in-scope (`D-37`)** | No current content-read API exists (see §3); AC-1 cannot be met without it. Authorized as a minimal enabler by `D-37`. |
| Approve button → `POST /pipeline/approve` (GRANT) advancing to SCRIPT | **Required** | AC-3, T-13-03 |
| Reject button → `POST /pipeline/approve` (REJECT + note); pipeline stays at STORY | **Required** | AC-4, T-13-03/04 |
| Reject **surfaces** that regenerate is available (UI affordance/empty state) | **Required (UI only)** | AC-4 wording "enables" = makes available |
| Actually triggering regeneration (`POST /pipeline/regenerate`, re-invoke agent, max-3, note→agent, version increment) | **Out of scope — belongs to US-09** | §4; US-12 brief §10/§13 |
| Promote approved story to `branch=main` / mark "approved version" | **Out of scope — ratified (`D-37`)** | §4.2 — Option A adopted: no promotion/copy/extra write; "approved story" = latest STORY version + `APPROVED` `approvals` row |
| New audit event on human-edit save (e.g. `ASSET_STORED`/`HUMAN_EDIT`) | **Optional** | Not in AC; recommend lightweight `ASSET_STORED` for parity with US-12 |
| Diff / side-by-side AI-draft vs human-edit view | **Out of scope** | Not in AC; US-22 asset history territory |
| Rich-text / markdown WYSIWYG editor | **Out of scope** | AC says "editable textarea"; plain text only for MVP |
| Concurrent-edit locking / autosave | **Out of scope** | Not in AC; single-user MVP |

---

## 2. Acceptance Criteria Mapping (user action → behavior → data → evidence)

### AC-1 — Review screen shows editable treatment
- **User action:** Navigate to Review while pipeline is `AWAITING_APPROVAL` / `current_stage=STORY` (Dashboard "Go to Review").
- **Expected system behavior:** Review (story mode) loads the latest `STORY` asset (`branch=ai-draft`), fetches its content, and renders it inside an editable `<textarea>` pre-filled with the treatment text. Read-only metadata (version, branch, AI badge) is shown.
- **Expected data changes:** None (read-only load).
- **Verification evidence required:** Screenshot/DOM of the Review screen showing the treatment text in an editable field; network trace showing the content-read call returning the stored `story.md` bytes; confirmation the rendered text equals the MinIO object content (hash match against the US-12 `asset_versions` row).

### AC-2 — Save creates a human-edit version
- **User action:** Edit text in the textarea, click **Save**.
- **Expected system behavior:** API stores the edited bytes via the existing `store_asset` path with `stage=STORY`, `branch=human-edit`, `is_ai_generated=false`, version = next in the `(project, STORY)` chain; pipeline status is **unchanged** (still `AWAITING_APPROVAL`/`STORY`).
- **Expected data changes:** New `asset_versions` row: incremented `version`, `branch=human-edit`, `is_ai_generated=false`, new `content_hash`/`minio_key`; MinIO object for the edited bytes (dedup if identical). Optional `ASSET_STORED` audit row.
- **Verification evidence required:** New `asset_versions` row (SQL) with `branch=human-edit`, `is_ai_generated=false`, version > the US-12 ai-draft version; MinIO object present at the new key with matching `content_hash`; pipeline status still `AWAITING_APPROVAL`/`STORY` after save.

### AC-3 — Approve advances pipeline
- **User action:** Click **Approve**.
- **Expected system behavior:** `POST /pipeline/approve` `{stage:STORY, decision:GRANT}` → Temporal `approve` signal → workflow advances STORY → SCRIPT (current M2 stub behavior). Immutable `approvals` row + `APPROVAL_RECORDED` audit written (already implemented in US-08).
- **Expected data changes:** New `approvals` row (`stage=STORY`, `decision=APPROVED`); `APPROVAL_RECORDED` audit row; worker `sync_pipeline_status` moves run to next stage (`current_stage=SCRIPT`, status back to `RUNNING` then the stub's `AWAITING_APPROVAL`).
- **Verification evidence required:** `approvals` row for STORY/APPROVED; `APPROVAL_RECORDED` audit row; `GET /pipeline/status` showing stage transition off STORY; Temporal workflow history showing the approve signal and advance.

### AC-4 — Reject enables regenerate
- **User action:** Enter a note, click **Reject**.
- **Expected system behavior:** `POST /pipeline/approve` `{stage:STORY, decision:REJECT, note}` (note required) → Temporal `reject` signal → workflow **stays at STORY** awaiting a future approve/regenerate. The Review UI then shows that regeneration is available (affordance/empty-state copy). **No agent re-invocation occurs in US-13.**
- **Expected data changes:** New `approvals` row (`stage=STORY`, `decision=REJECTED`, `rationale=note`); `APPROVAL_RECORDED` audit row with the note. No new STORY asset version (regeneration is US-09).
- **Verification evidence required:** `approvals` row STORY/REJECTED with stored note; `APPROVAL_RECORDED` audit including the note; `GET /pipeline/status` still `current_stage=STORY`; UI shows the regenerate affordance as available (not executing).

---

## 3. Architecture Impact

Classification key: **Required** = needed to meet US-13 AC · **Optional** = improves UX, not gating · **Not required** = no change.

### 3.1 API
| Item | Classification | Notes / current state |
|---|---|---|
| `PUT /assets/{id}` text-update endpoint creating a `human-edit` version | **Required** | T-13-02. Does not exist. Reuses `store_asset(branch="human-edit", is_ai_generated=False)`. Owns its transaction (commit in route). |
| Asset **content-read** endpoint `GET /assets/{id}/content` returning stored bytes | **Required — ratified in-scope (`D-37`)** | No content API today — `GET /assets` returns metadata only (`api/app/routes/assets.py`). The editor needs the bytes. MinIO `download_bytes` already exists on the adapter. **Scope pinned by `D-37`: returns story text only — NO asset browser, NO asset history, NO asset diff, NO search.** |
| `GET /assets?project_id=&stage=STORY` filtering to locate the latest review target | **Optional** | `GET /assets` exists but does not filter by stage; UI can filter client-side for MVP. Stage filter is a small nicety (backlog T-22-01 territory). |
| `POST /pipeline/approve` (GRANT/REJECT + note) | **Not required (reuse)** | Fully implemented in US-08 (`api/app/routes/pipeline.py`); validates active run, stage match, required reject note, sends signals, writes approvals + audit. |
| New approve/reject contract or signal names | **Not required** | Reuse; changing would break US-08 contract (D-26/D-32). |
| `POST /pipeline/regenerate` | **Not required (US-09)** | Explicitly out of scope. |

### 3.2 UI (web)
| Item | Classification | Notes / current state |
|---|---|---|
| Review screen **story mode**: load + render treatment in editable textarea | **Required** | `web/src/routes/ReviewPage.tsx` exists but renders generic stub copy and a reject-note box only — no story content, no editable textarea, no Save. T-13-01. |
| **Save** button → call text-update endpoint; reflect new version | **Required** | T-13-01/02. |
| Approve/Reject buttons wired to pipeline API | **Not required (reuse)** | Already wired in `ReviewPage.tsx` (`approvePipeline` GRANT/REJECT). |
| Rejection-note input | **Not required (reuse)** | Already present (`reject-note` textarea). T-13-04 effectively satisfied; keep + ensure shown on reject path. |
| "Regenerate available" affordance after reject | **Required (display only)** | New copy/disabled-state; must not call a regenerate API. |
| AI-vs-human diff view, autosave, markdown preview | **Not required** | Out of scope (§1.4). |

### 3.3 Workflow (Temporal)
| Item | Classification | Notes |
|---|---|---|
| `SparkPipelineWorkflow` changes | **Not required** | Approve already advances STORY→SCRIPT; reject already holds at STORY (M2 + US-12). US-13 is API+UI only. |
| New signals / timeouts | **Not required** | Reuse approve/reject signals and existing approval timeout. |

### 3.4 Asset versioning
| Item | Classification | Notes |
|---|---|---|
| Write `branch=human-edit` version on save | **Required** | `store_asset`/`add_version` already accept `branch` + `is_ai_generated`; no schema change. Version increments along existing `(project, STORY)` chain. |
| Promote approved version to `branch=main` / mark approved | **Not required — ratified (`D-37`)** | Option A adopted: no promotion/copy/extra write on approve. "Approved story" = latest STORY version + `APPROVED` `approvals` row. See §4.2. |

### 3.5 Audit
| Item | Classification | Notes |
|---|---|---|
| `APPROVAL_RECORDED` on approve/reject | **Not required (reuse)** | Emitted by US-08. |
| `ASSET_STORED` (or `HUMAN_EDIT`) on save | **Optional (recommended)** | Mirrors US-12 worker pattern for traceability of human edits; uses existing `audit_events` columns — **no migration**. |

### 3.6 Database
| Item | Classification | Notes |
|---|---|---|
| Schema migration | **Not required** | `asset_versions` already has `branch`, `version`, `is_ai_generated`, `metadata_json`; `approvals` and `audit_events` already exist. No `0003_*` migration for US-13. |

---

## 4. Scope Control — preventing creep

### 4.1 Story boundary register
| Capability | Belongs to | Rationale |
|---|---|---|
| Review/edit/save story; approve advances; reject holds + surfaces regenerate availability | **US-13** | Visual MVP Issue 29 ACs |
| `POST /pipeline/regenerate`; re-invoke `run_story_agent`; pass rejection note to agent context; **max 3 regenerations** (429); version increment on regenerate | **US-09 Regenerate after rejection** | Visual MVP Issue 15; US-12 brief §10/§13 mark regenerate explicitly unwired |
| Screenwriter agent reading the approved story; lineage edge `story.md → script.fountain`; SCRIPT_REVIEW | **US-14** | Visual MVP Issue 30; depends on US-13 closed |
| Asset version browser / history grouping, AI-vs-human diff | **US-22** | FEAT-12 asset history |
| Audit trail viewer screen | **US-23** | FEAT-13 |

**Primary creep risk:** treating AC-4 "Reject **enables** regenerate" as "implement regeneration." It does not. US-13 only proves the reject path keeps the pipeline at STORY and exposes the affordance; the regenerate **action** is US-09. Do not add `POST /pipeline/regenerate` or worker re-invocation in US-13.

### 4.2 RATIFIED — "approved story" resolution (`D-37`, 2026-06-10)
Source context (now resolved):
- **US-12 brief §5** had stated: *"promotion to `main` is US-13 scope, not US-12."*
- **Visual MVP Issue 29 ACs** do **not** list any promotion/branch-merge step; AC-3 is simply "Approve advances pipeline."

**Ratified outcome — Option A adopted as `D-37`:** US-13 does **not** promote branches and performs **no copy-to-`main` and no additional asset write during approval**. The contract for an "approved story" is precisely:
- **(a)** the **latest STORY asset version** (newest `asset_versions` row for `stage=STORY` — the human-edit version if edited, else the ai-draft version), **and**
- **(b)** an **`APPROVED` `approvals` record for `stage=STORY`**.

**US-14 and later stages resolve the approved story** by reading the latest approved STORY version, gated by the `APPROVED` `approvals` row. This keeps US-13 at 3 SP and avoids branch-merge machinery (which the US-12 brief §13 lists as a non-goal / "LakeFS" territory).

`D-37` **supersedes** the US-12 brief §5 "promotion to `main`" aside. Rationale: the canonical Visual MVP ACs contain no promotion step, branch-merge is an explicit MVP non-goal, and Option A is the smallest change that still gives US-14 a deterministic "approved story" to consume. **This governance question is closed — no remaining sign-off required.**

---

## 5. Verification Plan — minimum evidence to close US-13

Run on the same Olares environment used for US-12 closure (Temporal + worker + shared Ollama already deployed).

1. **Setup:** Start from a pipeline at `AWAITING_APPROVAL`/`STORY` with a US-12 `ai-draft` `story.md` present (reuse the US-12 run or a fresh `POST /ideas` → `POST /pipeline/start`).
2. **AC-1:** Load Review (story mode); capture screenshot + content-read response; confirm rendered text == MinIO object bytes for the ai-draft version.
3. **AC-2:** Edit text, Save; capture SQL row (`branch=human-edit`, `is_ai_generated=false`, version incremented) + MinIO object + unchanged pipeline status.
4. **AC-4 (reject):** Reject with a note; capture `approvals` (REJECTED + note) + `APPROVAL_RECORDED` audit + `GET /pipeline/status` still STORY + UI regenerate affordance visible (not executing).
5. **AC-3 (approve):** Approve; capture `approvals` (APPROVED) + `APPROVAL_RECORDED` + status transition off STORY (→ SCRIPT stub) + Temporal history advance.
6. **Regression:** Confirm US-12 ACs still pass (story generation unaffected); `pytest` unit suites for the new API endpoint(s); web unit/build (`npm test`, `npm run build`) green; `ruff`/`mypy` clean.
7. **Evidence package:** `evidence/us-13-verification/<env>-<date>/US-13-ACCEPTANCE-PACKAGE.md` mapping AC-1..AC-4 to logs/SQL/screenshots, mirroring the US-12 package format.

**Exit gate:** AC-1..AC-4 each PASS with evidence; no workflow/schema change introduced; regenerate confirmed *available but not executed*; CI gates green.

---

## 6. Risk Assessment

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **Scope creep into US-09** (building regenerate execution under AC-4) | Medium | Medium | Freeze AC-4 as UI affordance only; no `/pipeline/regenerate`; call out in PR description and review checklist. |
| R2 | **Missing content-read API** blocks AC-1 | High (gap is real) | High | **RESOLVED (`D-37`)** — minimal `GET /assets/{id}/content` (reuse `download_bytes`) is now authorized **in-scope** as a required enabler (story text only; no browser/history/diff/search) per §3.1. |
| R3 | **"Approved story" ambiguity** (§4.2) leaks into US-14 | Medium | Medium | **RESOLVED (`D-37`)** — Option A ratified: "approved story" = latest STORY version + `APPROVED` `approvals` row; no promotion/copy/extra write; US-14 resolves via the latest approved STORY version. |
| R4 | **Save creates wrong branch/flag** (e.g. `main`/`is_ai_generated=true`) breaking lineage & AC-2 | Low | High | Explicit `branch="human-edit"`, `is_ai_generated=False`; unit test asserts both; verification SQL check. |
| R5 | **Pipeline-state coupling** — save attempted when not `AWAITING_APPROVAL`/`STORY` | Low | Medium | Guard the update path (or document it as state-agnostic asset write); ensure save does not mutate pipeline status. |
| R6 | **Approve race** — user edits then approves; which version is "approved"? | Medium | Medium | Define order: Save before Approve; approval references the **latest STORY version** per the ratified `D-37` contract (§4.2). |
| R7 | **Auth surface** — new `PUT/GET` asset routes must honor Bearer middleware (US-25) for mutations | Low | Medium | Mutating `PUT` requires Bearer; content `GET` follows existing `GET /assets` policy. |
| R8 | **No new audit on human edit** reduces traceability (SC-05) | Low | Low | Recommended optional `ASSET_STORED` audit on save (no migration). |

---

## 7. Non-goals (US-13)
- `POST /pipeline/regenerate` / agent re-invocation / max-3 limit / note-to-agent (US-09).
- Screenwriter agent or any SCRIPT-stage work (US-14).
- Branch merge UI / LakeFS / approved-version promotion machinery (excluded by the ratified `D-37` / §4.2 — no promotion, copy, or extra asset write on approve).
- Asset history browser, AI-vs-human diff, markdown WYSIWYG, autosave, multi-user locking.
- Any Temporal workflow, signal, or DB schema change.

---

## 8. Readiness verdict
US-13 is **READY FOR IMPLEMENTATION AUTHORIZATION**. All governance questions are closed: the §4.2 "approved story" resolution and the §3.1 content-read enabler are both **ratified via `D-37` (2026-06-10)** — there are **no remaining open governance questions**. It is a **small, mostly additive API+UI story** on top of closed dependencies: approve/reject and asset-versioning infrastructure already exist; the net-new work is one content-read enabler (`GET /assets/{id}/content`, story text only), one text-update endpoint (`PUT /assets/{id}`), and the Review story-mode screen. **No DB schema migration and no Temporal workflow/signal changes.** The US-09 regeneration boundary holds: US-13 only surfaces the regenerate affordance and does not execute it. Estimated 3 SP holds.

*Governance review complete; ratified via `D-37`. Brief remains uncommitted in the working tree. Implementation not started.*
