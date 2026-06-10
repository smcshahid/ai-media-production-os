# Sprint 3C — US-13 Implementation Plan

**Status:** DRAFT — for governance review. No code authorized by this document.
**Parent brief:** `docs/sprints/sprint-3c-us13-brief.md` (RATIFIED via `D-37`, 2026-06-10).
**Story:** US-13 Review and edit story · FEAT-05 · P0 · 3 SP.
**Baseline:** `v0.3.0-us12` (`main` @ US-12 closure).

---

## 0. Implementation summary

US-13 is a **small, additive API + UI story** with **no DB migration and no Temporal changes**. Net-new work:

| Layer | Net-new | Reuse |
|---|---|---|
| API | `GET /assets/{id}/content`, `PUT /assets/{id}` | `POST /pipeline/approve`, `GET /assets`, `store_asset` |
| Web | Review story-mode screen (load/edit/save + reject affordance) | Approve/Reject wiring, nav, polling |
| Worker | — | — |
| DB | — | `asset_versions`, `approvals`, `audit_events` |

**Estimated effort:** 3 SP · ~2–3 days (1 backend + 1 frontend track, sequential dependency on content-read before UI integration).

---

## 1. Story breakdown

### 1.1 Backend tasks

| ID | Task | Files (expected) | Depends on |
|---|---|---|---|
| B-01 | Add `AssetVersionRepository.get(id)` lookup | `api/app/infrastructure/db/repositories/asset_version.py` | — |
| B-02 | Implement `GET /assets/{asset_id}/content` | `api/app/routes/assets.py` | B-01 |
| B-03 | Implement `PUT /assets/{asset_id}` text-update (human-edit) | `api/app/routes/assets.py`, optionally `api/app/domain/assets/service.py` | B-01 |
| B-04 | Add optional `ASSET_STORED` audit on human-edit save | `api/app/routes/assets.py` (or thin domain helper) | B-03 |
| B-05 | Register routes in OpenAPI; ensure auth middleware applies | `api/app/routes/assets.py` (no middleware change) | B-02, B-03 |
| B-06 | Unit tests for content-read + text-update routes | `api/tests/unit/test_assets_content_route.py`, extend `test_assets_route.py` | B-02, B-03 |

**B-02 constraints (`D-37`):** Returns raw story text bytes only. No list/filter/search endpoints. Reject non-STORY stages with 400/422. Reject non-text content types if ever encountered (defensive).

**B-03 constraints:** Accepts UTF-8 markdown body. Always writes `stage=STORY` (from existing row), `branch=human-edit`, `is_ai_generated=false`. Does **not** mutate `pipeline_runs`. Does **not** promote/copy on approve (`D-37`).

### 1.2 Frontend tasks

| ID | Task | Files (expected) | Depends on |
|---|---|---|---|
| F-01 | Add API client helpers: `getAssetContent(id)`, `updateAssetText(id, text)` | `web/src/api/client.ts`, `web/src/api/types.ts` | B-02, B-03 |
| F-02 | Implement Review **story mode**: load latest STORY asset, fetch content, editable textarea | `web/src/routes/ReviewPage.tsx` (or extract `StoryReviewPanel.tsx`) | F-01 |
| F-03 | Add **Save** button + dirty-state handling; show version/branch/AI badge metadata | same as F-02 | F-02 |
| F-04 | Post-reject **regenerate affordance** (copy only; no API call) | `web/src/routes/ReviewPage.tsx` | existing reject handler |
| F-05 | Remove stub copy ("Stub stage output…"); gate story mode on `current_stage=STORY` | `web/src/routes/ReviewPage.tsx` | F-02 |
| F-06 | Unit tests: story review display mapping, save payload shape | `web/src/tests/storyReview.test.ts` (or extend existing) | F-02 |

**F-02 asset selection logic:** `listAssets(projectId)` → filter `stage === "STORY"` → pick highest `version` (the latest row, whether `ai-draft` or `human-edit`). This is the editor's working copy until Save creates a new human-edit version.

**F-04 affordance:** After successful reject while still at STORY review, show message such as "Regeneration will be available in a future update (US-09)" or a disabled "Regenerate" button with tooltip — must **not** call `/pipeline/regenerate`.

### 1.3 Tests

| ID | Task | Type | Covers |
|---|---|---|---|
| T-01 | `GET /assets/{id}/content` — happy path returns bytes + correct content-type | API unit | AC-1 enabler |
| T-02 | `GET /assets/{id}/content` — 404 unknown id, 404 missing blob | API unit | error paths |
| T-03 | `GET /assets/{id}/content` — reject non-STORY stage (if enforced) | API unit | `D-37` scope pin |
| T-04 | `PUT /assets/{id}` — creates `human-edit` version, increments version, `is_ai_generated=false` | API unit | AC-2 |
| T-05 | `PUT /assets/{id}` — pipeline status unchanged (mock/no run mutation) | API unit | AC-2, R5 |
| T-06 | `PUT /assets/{id}` — 404 unknown id; 401 without token | API unit | auth + validation |
| T-07 | Approve/reject regression — existing `test_pipeline_approve.py` still green | API unit | AC-3, AC-4 reuse |
| T-08 | `store_asset` branch/is_ai_generated passthrough (if not covered by T-04) | API unit | R4 |
| T-09 | Web: `toDisplayStatus` + story asset selection helper | Web unit | AC-1 UI logic |
| T-10 | Web: build + lint pass | CI | regression |
| T-11 | Smoke: `scripts/smoke/test_us13_story_review.py` (new) | Smoke (optional gate) | E2E AC-1..4 |

**T-11 smoke outline:** Reuse `_compose.py` ephemeral project pattern from US-12. Steps: `POST /ideas` → `POST /pipeline/start` → poll to `AWAITING_APPROVAL`/`STORY` → `GET /assets` + content-read → `PUT` human-edit → verify SQL → reject with note → verify stage held → fresh run or reset → approve → verify stage advances. Gate behind live stack env vars (same pattern as `test_us12_story.py`).

### 1.4 Verification tasks

| ID | Task | Deliverable |
|---|---|---|
| V-01 | Run full AC-1..AC-4 evidence collection on Olares (or compose with Ollama if sufficient) | `evidence/us-13-verification/<env>-<date>/` |
| V-02 | Write `US-13-ACCEPTANCE-PACKAGE.md` mapping each AC to logs/SQL/screenshots | evidence package |
| V-03 | Capture DB evidence: `asset_versions` (ai-draft + human-edit rows), `approvals`, `audit_events` | SQL dumps in evidence/logs |
| V-04 | Capture MinIO evidence: `mc stat` / `mc cat` for story objects | evidence/logs |
| V-05 | Capture UI evidence: Review screen screenshots (editable treatment, post-reject affordance) | evidence/screenshots |
| V-06 | Regression: US-12 smoke still passes; CI green (`ci-api.yml`) | CI log reference in package |
| V-07 | Confirm no `/pipeline/regenerate` added; no workflow/schema diff in PR | PR checklist item |

---

## 2. Acceptance criteria traceability

| AC | User-visible outcome | Implementation tasks | Verification |
|---|---|---|---|
| **AC-1** | Review screen shows editable treatment | B-01, B-02, B-05, B-06 (T-01..T-03) · F-01, F-02, F-05, F-06 (T-09) | V-01, V-05 |
| **AC-2** | Save creates human-edit version | B-03, B-04, B-05, B-06 (T-04..T-06, T-08) · F-01, F-03 (T-09) | V-01, V-03, V-04 |
| **AC-3** | Approve advances pipeline | F-02 (reuse existing approve handler) · T-07 regression | V-01, V-03 |
| **AC-4** | Reject enables regenerate (affordance only) | F-04 · T-07 regression | V-01, V-05, V-07 |

### Visual MVP task mapping (T-13-01..04)

| Backlog task | Implementation tasks |
|---|---|
| T-13-01 Build Review screen — story mode | F-02, F-03, F-05 |
| T-13-02 Implement `PUT /assets/{id}` text update | B-03, B-06 (T-04..T-06) |
| T-13-03 Wire Approve/Reject to pipeline API | Already done; F-02 integrates into story mode; T-07 regression |
| T-13-04 Display rejection-note input on reject | Already done; F-04 adds post-reject affordance |

---

## 3. API contract

### 3.1 `GET /assets/{asset_id}/content` (new — required enabler)

**Purpose:** Return stored bytes for a single asset version so the Review editor can pre-fill the textarea (AC-1). Authorized by `D-37`; story text only.

| Field | Value |
|---|---|
| Method / path | `GET /assets/{asset_id}/content` |
| Auth | Bearer token required (same as all non-`/health` routes) |
| Path param | `asset_id` — UUID of an `asset_versions` row |

**Success — 200 OK**

```
Content-Type: text/markdown; charset=utf-8
Body: raw UTF-8 bytes of the stored object (story treatment text)
```

No JSON wrapper. The client reads `response.text()`.

**Errors**

| Status | Condition |
|---|---|
| 401 | Missing/invalid Bearer token |
| 404 | `asset_id` not found |
| 404 | Blob missing in MinIO (orphaned row) |
| 400 or 422 | `stage != STORY` (scope pin per `D-37` — no generic asset browser) |
| 502 | MinIO download failure |

**Not in scope:** query params, pagination, search, diff, history listing, content negotiation beyond `text/markdown`.

### 3.2 `PUT /assets/{asset_id}` (new — text update)

**Purpose:** Persist human-edited story text as a new version (AC-2).

| Field | Value |
|---|---|
| Method / path | `PUT /assets/{asset_id}` |
| Auth | Bearer token required |
| Path param | `asset_id` — UUID of the asset version being edited (establishes `project_id` + `stage`) |

**Request body (JSON)**

```json
{
  "text": "# Story Treatment\n\n..."
}
```

| Field | Type | Required | Constraints |
|---|---|---|---|
| `text` | string | yes | Non-empty after trim; UTF-8; max length TBD (recommend 50–50 000 chars, matching idea bounds spirit) |

**Success — 200 OK**

```json
{
  "id": "<uuid>",
  "project_id": "<uuid>",
  "stage": "STORY",
  "version": 2,
  "content_hash": "<sha256-hex>",
  "minio_key": "<project_id>/STORY/<hash>",
  "is_ai_generated": false,
  "branch": "human-edit",
  "metadata_json": null,
  "created_at": "<iso8601>"
}
```

Same shape as existing `AssetRead` (`GET /assets` list item).

**Behavior**

1. Load existing row by `asset_id`; 404 if missing.
2. Validate `stage == STORY`; reject other stages.
3. Encode `text` as UTF-8 bytes.
4. Call `store_asset(data=..., stage=STORY, project_id=..., branch="human-edit", is_ai_generated=False, content_type="text/markdown")`.
5. Optionally append `ASSET_STORED` audit (recommended, not gating).
6. Commit transaction. **Do not** update `pipeline_runs`.

**Errors**

| Status | Condition |
|---|---|
| 401 | Missing/invalid token |
| 404 | Unknown `asset_id` |
| 422 | Empty `text`; wrong `stage` |
| 502 | MinIO upload failure |

**Not in scope:** Updating an existing row in-place (always append new version). Branch promotion. Pipeline status mutation.

### 3.3 Reused endpoints (no contract change)

#### `GET /assets?project_id={uuid}`
- **Use:** List asset metadata; UI filters `stage=STORY`, picks max `version`.
- **Response:** `AssetRead[]` (existing).
- **Change:** None.

#### `POST /pipeline/approve`
- **Use:** Approve (AC-3) and reject (AC-4).
- **Request (existing):**

```json
{
  "project_id": "<uuid>",
  "stage": "STORY",
  "decision": "GRANT" | "REJECT" | "APPROVED" | "REJECTED",
  "note": "optional; required when REJECTED"
}
```

- **Response (existing):** `PipelineApproveResponse` with `approval_id`, `decision`, `stage`, `status`, `current_stage`.
- **Change:** None. GRANT/REJECT aliases already normalized in `pipeline.py`.

#### `GET /pipeline/status?project_id={uuid}`
- **Use:** Gate Review page (`AWAITING_APPROVAL` + `STORY` → display REVIEW); poll after approve/reject.
- **Change:** None.

#### `POST /ideas`, `POST /pipeline/start`
- **Use:** Verification setup only.
- **Change:** None.

---

## 4. Asset versioning behavior

### 4.1 Branch semantics

| Branch | Writer | When | `is_ai_generated` |
|---|---|---|---|
| `ai-draft` | Worker `run_story_agent` / `store_story_markdown` | US-12 story generation completes | `true` |
| `human-edit` | API `PUT /assets/{id}` | User clicks Save on Review screen | `false` |

No `main` branch write in US-13 (`D-37`). No copy-on-approve.

### 4.2 Version increment rules

Versions increment along the `(project_id, stage)` chain — **not** per branch:

```
(project_id=P, stage=STORY):
  v1  branch=ai-draft     is_ai_generated=true   ← US-12
  v2  branch=human-edit  is_ai_generated=false  ← US-13 Save (first edit)
  v3  branch=human-edit  is_ai_generated=false  ← US-13 Save (second edit)
```

Implementation uses existing `AssetVersionRepository.next_version(project_id, STORY)` inside `store_asset`. Identical bytes produce a new version row but may deduplicate the MinIO blob (same `content_hash` key).

### 4.3 Editor working copy selection (UI)

On Review load:

1. `listAssets(projectId)` → filter `stage === "STORY"`.
2. Select row with **maximum `version`** (latest).
3. If user has not saved yet, this is typically the `ai-draft` v1 from US-12.
4. After Save, refresh list; latest becomes the new `human-edit` version.

### 4.4 Approved story resolution (`D-37` — for US-14 consumers)

After AC-3 (Approve):

- **Approved story** = newest `asset_versions` row where `stage=STORY` **plus** an `approvals` row with `stage=STORY`, `decision=APPROVED`.
- If the user saved edits, the approved content is the latest `human-edit` version.
- If the user approved without saving, the approved content is the `ai-draft` version.
- US-14 `run_script_agent` should call a shared helper: `fetch_latest_story(project_id)` ordered by `version DESC` where an APPROVED approval exists for that run/stage. (US-14 scope — document the contract here; implement in US-14.)

---

## 5. Approval behavior

### 5.1 Approve path (AC-3)

```
User clicks "Approve"
  → POST /pipeline/approve { project_id, stage: "STORY", decision: "GRANT" }
  → API validates: active run, status=AWAITING_APPROVAL, stage match
  → temporal.signal_approve(workflow_id, "STORY")
  → INSERT approvals (decision=APPROVED)
  → INSERT audit APPROVAL_RECORDED
  → COMMIT
  → Worker workflow: _approval_granted=true
  → wait_condition exits reject-or-approve wait
  → completed_stages.append("STORY")
  → Loop advances to SCRIPT: sync RUNNING → run_stub_stage → sync AWAITING_APPROVAL
  → GET /pipeline/status: current_stage=SCRIPT (or RUNNING briefly)
```

**No additional asset write on approve** (`D-37`).

### 5.2 Reject path (AC-4)

```
User enters note, clicks "Reject"
  → POST /pipeline/approve { project_id, stage: "STORY", decision: "REJECT", note }
  → API validates: note non-empty
  → temporal.signal_reject(workflow_id, "STORY", note)
  → INSERT approvals (decision=REJECTED, rationale=note)
  → INSERT audit APPROVAL_RECORDED (payload includes note)
  → COMMIT
  → Worker workflow: _approval_rejected=true
  → wait_condition exits; enters second wait: wait until _approval_granted
  → Pipeline stays at STORY / AWAITING_APPROVAL (no stage advance, no agent re-run)
  → UI shows regenerate affordance (display only)
```

**Regenerate execution** (re-invoke `run_story_agent`, new ai-draft version, note→agent) is **US-09** — not triggered here.

### 5.3 Post-reject user flows (in scope vs out)

| Flow | In US-13? |
|---|---|
| Reject → see "regenerate available" message | ✅ Yes (AC-4 affordance) |
| Reject → edit text → Save → Approve | ✅ Yes (AC-2 + AC-3) |
| Reject → click Regenerate → new ai-draft | ❌ No (US-09) |
| Reject → Approve without edit (accept ai-draft) | ✅ Yes (valid per `D-37`) |

---

## 6. Verification strategy

### 6.1 Environments

| Environment | Use |
|---|---|
| **Olares** (preferred) | Full E2E closure evidence; Temporal + worker + shared Ollama already deployed from US-12 |
| **Local compose** | Dev iteration + smoke script; CI unit tests only |

### 6.2 Per-AC evidence checklist

| AC | Evidence artifacts |
|---|---|
| AC-1 | Review screenshot with filled textarea; `GET /assets/{id}/content` response body; MinIO `mc cat` matching rendered text; `asset_versions` row reference (ai-draft v1) |
| AC-2 | `PUT /assets/{id}` request/response log; SQL showing new row `branch=human-edit`, `is_ai_generated=false`, `version=2`; MinIO object at new key; `GET /pipeline/status` unchanged `AWAITING_APPROVAL`/`STORY` |
| AC-3 | `approvals` row STORY/APPROVED; `APPROVAL_RECORDED` audit; `GET /pipeline/status` `current_stage=SCRIPT`; Temporal workflow history snippet |
| AC-4 | `approvals` row STORY/REJECTED with note; `APPROVAL_RECORDED` audit with note; status still STORY; UI screenshot showing regenerate affordance (no regenerate API call in network log) |

### 6.3 Evidence package structure

```
evidence/us-13-verification/<env>-<date>/
├── US-13-ACCEPTANCE-PACKAGE.md
└── logs/
    ├── 01-review-load-and-content.txt
    ├── 02-human-edit-save.txt
    ├── 03-reject-with-note.txt
    ├── 04-approve-advance.txt
    ├── 05-db-asset-versions.sql
    ├── 06-db-approvals-audit.sql
    └── 07-minio-story-objects.txt
```

### 6.4 Exit gate

- AC-1..AC-4 each **PASS** with mapped evidence.
- CI green: `ruff`, `mypy`, `pytest tests/unit`, `npm test`, `npm run build`.
- US-12 regression smoke passes.
- PR contains **no** workflow YAML changes, **no** Alembic migration, **no** `/pipeline/regenerate`.
- Governance checklist: US-09 boundary intact; `D-37` contract documented in PR description.

### 6.5 Recommended commit plan (post-implementation)

| # | Scope | Message (draft) |
|---|---|---|
| C1 | API content-read + text-update + unit tests | `feat(us13): asset content read + human-edit save endpoints` |
| C2 | Web Review story mode + client helpers + tests | `feat(us13): Review story mode with edit/save` |
| C3 | Smoke + evidence | `test(us13): story review smoke + acceptance evidence` |

---

## 7. Risk review (pre-implementation)

| # | Risk | Likelihood | Impact | Mitigation in plan |
|---|---|---|---|---|
| R1 | Scope creep into US-09 (implementing regenerate) | Medium | High | F-04 is display-only; V-07 PR checklist; no `regenerate` route in task list |
| R2 | `GET /assets/{id}/content` becomes generic asset browser | Low | Medium | Enforce `stage=STORY` guard in B-02; document in OpenAPI summary |
| R3 | `PUT` updates wrong branch/flags | Low | High | Hardcode `branch="human-edit"`, `is_ai_generated=False` in B-03; T-04 asserts both |
| R4 | Save mutates pipeline status | Low | Medium | B-03 must not touch `pipeline_runs`; T-05 verifies |
| R5 | Editor loads stale version (not max version) | Medium | Medium | F-02 selects `max(version)` among STORY rows; T-09 unit test |
| R6 | User approves without saving edits; US-14 reads wrong story | Low | Low | `D-37` contract: latest version at approve time is canonical; document in PR |
| R7 | Auth regression on new routes | Low | Medium | T-06 asserts 401; auth middleware unchanged (all routes protected) |
| R8 | `PUT` accepts edits when pipeline not at review | Low | Low | Optional guard: reject PUT if no active `AWAITING_APPROVAL` run for project (nice-to-have, not AC-gating) |
| R9 | Large story text exceeds request limits | Low | Low | Set `text` max length in Pydantic (recommend 50 000); return 422 |
| R10 | Missing `ASSET_STORED` audit reduces SC-05 traceability | Low | Low | B-04 optional but recommended |

### 7.1 Pre-implementation checklist (gate before first PR)

- [ ] Brief + `D-37` re-read by implementer
- [ ] Confirm `store_asset` signature supports `branch` + `is_ai_generated` (verified in baseline)
- [ ] Confirm `ReviewPage.tsx` approve/reject handlers work for STORY stage (verified in baseline)
- [ ] Confirm no Alembic `0003_*` planned
- [ ] Confirm US-14 story-fetch contract documented (§4.4)

---

## 8. Implementation sequence (recommended)

```
Day 1 (backend):
  B-01 → B-02 → B-03 → B-06 (T-01..T-06) → B-04 (optional)

Day 2 (frontend):
  F-01 → F-02 → F-03 → F-04 → F-05 → F-06 (T-09)

Day 3 (verification):
  T-07, T-10, T-11 → V-01..V-07 → evidence package → governance closure request
```

Backend must land before frontend integration (F-01 depends on API contracts).

---

## 9. Non-goals (reaffirmed)

Same as brief §7: no US-09 regenerate, no US-14 Screenwriter, no branch promotion (`D-37`), no asset browser/history/diff/search, no Temporal/DB schema changes, no markdown WYSIWYG.

---

*Implementation plan for governance review. No code written. Awaiting implementation authorization.*
