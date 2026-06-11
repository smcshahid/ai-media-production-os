# Sprint 5B — US-22 Implementation Plan

**Status:** **ACCEPT** — implementation authorized.  
**Parent brief:** `docs/sprints/sprint-5b-us22-brief.md` (**ACCEPT**)  
**Story:** US-22 Browse asset versions · FEAT-12 · EPIC-06 · P1 · 3 SP  
**Baseline:** `v0.8.0-us20` (`db54981`)  
**Decision record:** **D-57** — append to `DECISIONS.md` at **implementation start** (after this plan ACCEPT)

---

## 0. Implementation summary

US-22 adds **`GET /assets/history`** to return a **read-only**, **stage-grouped** view of all `asset_versions` rows for a project. Content bytes remain on the existing **`GET /assets/{asset_id}/content`** route. No worker, schema, web UI, or workflow changes.

| Layer | Net-new | Reuse |
|---|---|---|
| API | `GET /assets/history`; history query + grouping service | `AssetVersion` model; `AssetVersionRepository`; `ProjectRepository`; existing content-read route |
| Worker | — | **No changes** |
| Web | — | **No changes** (US-23) |
| DB schema | **None** | `asset_versions` SELECT only |
| Verify | `deploy/k8s/us22-verify/` | US-V02 project `76aa4418-d92d-45f7-954c-a10383ea511a` |

**Estimated effort:** ≈ 3 SP · ~2 days

### Visibility-only mandate (mandatory)

Asset history is **visibility only**. Any design or code that violates the following is **out of scope** and requires a new governance brief.

| # | Requirement |
|---|---|
| **V-22.1** | **GET only** on history routes — no POST, PUT, PATCH, DELETE for history |
| **V-22.2** | **No `asset_versions` writes** from US-22 code paths (no INSERT, UPDATE, DELETE) |
| **V-22.3** | **No restore / rollback / promote** endpoints or semantics |
| **V-22.4** | **No schema changes** — no Alembic migrations; no new tables or columns |
| **V-22.5** | **No workflow / Temporal changes** |
| **V-22.6** | **`GET /assets` unchanged** — flat list remains for US-05 backward compatibility |

### Explicitly out of scope (US-22)

Rollback · restore · asset editing expansion · version diff UI · audit trail browser · lineage mutation · WebSocket (US-21) · Asset History **UI** (US-23) · publishing · collaboration · export contract changes (D-52..D-54)

---

## 1. D-57 — Asset History API read contract

**Record in `DECISIONS.md` as D-57** at implementation start.

### 1.1 Route identity

| Field | Value |
|---|---|
| HTTP route | **`GET /assets/history`** |
| Auth | Bearer token (same as protected routes) |
| Methods allowed | **GET only** |
| Response `Content-Type` | `application/json` |

**Route registration:** Declare **`/assets/history` before** `/assets/{asset_id}` paths in `assets.py` so FastAPI does not treat `history` as a UUID.

### 1.2 Query parameters

| Param | Required | Rule |
|---|---|---|
| `project_id` | **Yes** | UUID — scope all rows |
| `stage` | No | Filter to one `AssetStage` value; omit = all stages present |
| `pipeline_run_id` | No | Filter rows where `asset_versions.pipeline_run_id = run_id`; **IDEA rows** with `pipeline_run_id IS NULL` **remain included** when unfiltered; when run filter applied, include IDEA if `stage=IDEA` and row belongs to same `project_id` |

### 1.3 Eligibility and errors

| Condition | HTTP | Detail |
|---|---|---|
| Unknown `project_id` | **404** | Project does not exist |
| Valid project (empty history) | **200** | `stages: []` |
| Missing auth | **401** | Standard auth middleware |
| Invalid `stage` enum | **422** | Validation error |

### 1.4 Response schema (v1)

```json
{
  "project_id": "uuid",
  "stages": [
    {
      "stage": "STORY",
      "versions": [
        {
          "asset_id": "uuid",
          "version": 2,
          "content_hash": "sha256…",
          "is_ai_generated": false,
          "branch": "human-edit",
          "pipeline_run_id": "uuid-or-null",
          "metadata": {},
          "created_at": "2026-06-11T12:00:00Z"
        }
      ]
    }
  ]
}
```

| Field | Rule |
|---|---|
| `stages[]` | One object per stage **that has ≥1 row** after filters |
| `stages[].stage` | `IDEA` \| `STORY` \| `SCRIPT` \| `STORYBOARD` \| `VIDEO` |
| `versions[]` | **All** matching `asset_versions` rows for that stage (includes regen artifacts) |
| `asset_id` | Maps to `asset_versions.id` — use with **`GET /assets/{asset_id}/content`** |
| `metadata` | Copy of `metadata_json` or `{}`; STORYBOARD **must** include `frame_index` when set |
| `minio_key` | **Omitted** from history response (content via existing content-read) |

### 1.5 Stage ordering (response)

**`stages[]` order** (canonical pipeline order):

| Order | Stage |
|---|---|
| 1 | IDEA |
| 2 | STORY |
| 3 | SCRIPT |
| 4 | STORYBOARD |
| 5 | VIDEO |

Stages with no rows are **omitted** (not empty placeholders).

### 1.6 Version ordering within stage (newest first)

| Stage | Sort key |
|---|---|
| IDEA, STORY, SCRIPT, VIDEO | `version DESC`, then `created_at DESC` |
| STORYBOARD | `version DESC`, then `metadata.frame_index ASC` (1..4 within batch) |

**Rationale:** Newest batch/version first; within a STORYBOARD batch, frames in shot order (matches US-16/US-17 conventions).

### 1.7 STORYBOARD flattening (D-43)

- Each frame is **one row** in `versions[]` (not nested batch objects).
- Rows sharing the same `version` integer appear consecutively after sort (4 rows per batch).
- Verify asserts **API row count = SQL row count** for `stage=STORYBOARD`.

### 1.8 Content-read reuse (no new download route)

| Need | Route |
|---|---|
| Preview / download bytes | **`GET /assets/{asset_id}/content`** (existing) |
| IDEA text | Not content-readable today — history lists metadata only; **no US-22 change** to IDEA content-read |

Document in API OpenAPI summary: history returns IDs; clients fetch bytes via content-read.

### 1.9 SQL source of truth (read-only)

```sql
SELECT id, project_id, pipeline_run_id, stage, version,
       content_hash, is_ai_generated, branch, metadata_json, created_at
FROM asset_versions
WHERE project_id = :project_id
  AND (:stage IS NULL OR stage = :stage)
  AND (
    :pipeline_run_id IS NULL
    OR pipeline_run_id = :pipeline_run_id
    OR (stage = 'IDEA' AND :include_idea_for_run = true)
  )
ORDER BY stage, version DESC, created_at DESC;
```

**V-22 enforcement:** Repository method is **SELECT only**. No write methods added for history.

### 1.10 Parity verification rule

For unfiltered project history:

```text
SUM(len(stage.versions) for stage in response.stages)
  == COUNT(*) FROM asset_versions WHERE project_id = :project_id
```

When `stage` filter applied, counts must match filtered SQL COUNT.

---

## 2. Architecture

### 2.1 API module layout (proposed)

```
api/app/domain/asset_history/
  types.py           # AssetHistoryVersion, AssetHistoryStage, AssetHistoryResponse
  resolver.py        # group_and_sort(rows) — pure functions
  service.py         # get_asset_history(project_id, filters)
api/app/routes/assets.py   # add GET /assets/history (above {asset_id} routes)
api/app/infrastructure/db/repositories/asset_version.py
                         # list_history_for_project(...) — read-only query
```

**Reuse:** `ProjectRepository.get()` for 404 gate; map ORM rows to D-57 types; **do not** duplicate content-read logic.

### 2.2 Relationship to existing routes

| Route | US-22 impact |
|---|---|
| `GET /assets?project_id=` | **Unchanged** — flat `created_at DESC` list |
| `GET /assets/history` | **New** — grouped, stage-ordered contract |
| `GET /assets/{id}/content` | **Unchanged** |
| `PUT /assets/{id}` | **Unchanged** — not expanded |
| `POST /assets` | **Unchanged** |
| `GET /lineage/{run_id}` | **Unchanged** — regression in verify |

### 2.3 Web / US-23 boundary

US-22 delivers **API only**. US-23 will add `getAssetHistory()` in `web/src/api/client.ts` and stage-tab UI. **No web files in US-22** unless a one-line OpenAPI smoke is needed (not required).

---

## 3. Olares verification strategy

Read-path only — **no pipeline re-run**. Reuse US-V02 project after US-22 API deploy.

### 3.1 Scripts

```
deploy/k8s/us22-verify/
  verify_us22.sh       # S-22-01..S-22-07
  run_remote.sh
  deploy_us22.sh       # optional API image import
```

### 3.2 Verify inputs

| Variable | Value |
|---|---|
| `PROJECT_ID` | `76aa4418-d92d-45f7-954c-a10383ea511a` (US-V02) |
| `RUN_ID` | `042983f7-0f55-48c3-9d65-fce89a684625` (optional run filter step) |

### 3.3 Verify steps

| Step | Action | Pass criteria |
|---|---|---|
| S-22-01 | `GET /assets/history?project_id=` | HTTP 200; JSON parse |
| S-22-02 | Stage groups | IDEA, STORY, SCRIPT, STORYBOARD, VIDEO present |
| S-22-03 | **API vs SQL row parity** | Sum of `versions[]` lengths == `COUNT(*)` from `asset_versions` |
| S-22-04 | STORY newest first | First STORY row has `max(version)` from SQL |
| S-22-05 | STORYBOARD frames | All rows include `metadata.frame_index`; count matches SQL |
| S-22-06 | STORY regen visibility | STORY `versions.length >= 2` on US-V02 project |
| S-22-07 | Content-read spot-check | `GET /assets/{latest_story_id}/content` HTTP 200 |
| S-22-08 | Lineage regression | `GET /lineage/{RUN_ID}` HTTP 200 unchanged |
| S-22-09 | Export regression | `GET /export/{RUN_ID}` HTTP 200 unchanged |
| S-22-10 | No asset row mutation | `COUNT(*)` from `asset_versions` before/after verify identical |

### 3.4 SQL attestation

| ID | Query | Evidence file |
|---|---|---|
| V-22-L01 | Total asset_versions count for project | `sql/v22-l01-total-rows.txt` |
| V-22-L02 | Count per stage | `sql/v22-l02-by-stage.txt` |
| V-22-L03 | STORY max version + row count | `sql/v22-l03-story-versions.txt` |
| V-22-L04 | STORYBOARD rows with frame_index | `sql/v22-l04-storyboard-frames.txt` |
| V-22-L05 | No writes | `asset_versions` COUNT before/after |

### 3.5 Evidence package

`evidence/us-22-verification/olares-<date>/US-22-ACCEPTANCE-PACKAGE.md`

---

## 4. Local testing

| Suite | New tests | Target |
|---|---|---|
| API unit | `test_asset_history.py` | 404 project; grouping; newest-first; STORYBOARD sort; stage filter; run filter; SQL parity mock; no write calls |
| Regression | `test_lineage.py`, `test_export.py`, `test_assets_*` | Unchanged PASS |

**Baseline before implementation:** API 94 · worker 39 · web 26 (US-20 closure).

---

## 5. Acceptance criteria mapping

| AC | Plan section | Verification |
|---|---|---|
| AC-1 Grouped by stage | §1.4, §1.5 | S-22-02 |
| AC-2 Newest first | §1.6 | S-22-04, unit tests |
| AC-3 Metadata fields | §1.4 | JSON schema tests |
| AC-4 STORYBOARD frames | §1.7 | S-22-05, V-22-L04 |
| AC-5 Read-only | §0 V-22, §1.1 | Route audit + V-22-L05 |
| AC-6 Content-read reuse | §1.8 | S-22-07 |
| AC-7 Phase 1 regression | §3.3 S-22-08/09 | Lineage + export spot-check |

---

## 6. Risks and mitigations

| ID | Risk | Mitigation |
|---|---|---|
| R-22-01 | Restore/promote scope creep | PR checklist §0; D-57 GET-only |
| R-22-02 | Breaking `GET /assets` consumers | Leave flat route unchanged |
| R-22-03 | Route shadowing `/assets/history` | Register before `{asset_id}` paths |
| R-22-04 | STORYBOARD sort confusion | §1.6/§1.7 + SQL parity |
| R-22-05 | UI work in US-22 | Zero web diff; defer to US-23 |
| R-22-06 | `pipeline_run_id` filter drops IDEA | §1.2 IDEA inclusion rule |

---

## 7. Implementation checklist (post–plan ACCEPT)

| # | Task | Owner |
|---|---|---|
| 1 | Append **D-57** to `DECISIONS.md` | Dev |
| 2 | `list_history_for_project()` + domain service | Dev |
| 3 | `GET /assets/history` route | Dev |
| 4 | API unit tests | Dev |
| 5 | `deploy/k8s/us22-verify/` | Dev |
| 6 | Olares verify + acceptance package | Ops |
| 7 | Implementation report | Dev |

---

## 8. Authorization boundary

| Stage | Status |
|---|---|
| Brief | **ACCEPT** |
| Implementation plan | **ACCEPT** |
| **Code / deploy** | **Implemented** — Olares PASS; closure review pending |

Upon plan ACCEPT: implementation may begin. Olares evidence required before story closure (same pattern as US-20).

---

## 9. Document control

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-06-11 | Initial plan — D-57, visibility-only, Olares verify |
