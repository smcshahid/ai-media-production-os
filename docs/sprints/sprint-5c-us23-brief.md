# Sprint 5C — US-23 Asset History UI (governance brief)

**Status:** **SUBMITTED** — awaiting governance ACCEPT. Implementation **not authorized**.  
**Parent program:** Spark Full Phase 2 ([spark-full-phase2-governance-brief.md](./spark-full-phase2-governance-brief.md) **ACCEPT**)  
**Story:** US-23 Asset History UI · FEAT-12 · EPIC-06 · **P1** · 3 SP  
**Prerequisites (closed):** US-22 ✅ · US-20 ✅ · US-V02 ✅ · US-26 ✅  
**Baseline:** `v0.9.0-us22`  
**Proposed decision record:** **D-58** (append at implementation start after plan ACCEPT)

---

## 0. Story classification — read-only visualization only

US-23 delivers a **creator-facing asset history browser** that visualizes data from the **US-22 API** (`GET /assets/history`). Users browse versions per stage, inspect metadata, and preview/download bytes via the existing content-read route. It is **not** a restore console, editor, or workflow tool.

| Authorized in US-23 | Forbidden in US-23 |
|---|---|
| Read-only **UI** consuming `GET /assets/history` | **Restore** / rollback / promote version |
| Stage-grouped version **list** (tabs or sections) | **Asset editing** (PUT/POST beyond existing review flows) |
| **Metadata panel** per row (`version`, `branch`, `is_ai_generated`, `content_hash`, `created_at`, `frame_index`) | Workflow / Temporal changes |
| **Preview/download** via `GET /assets/{asset_id}/content` | Schema migrations |
| Nav link / dedicated route (e.g. `/history`) | Version **diff** / side-by-side compare (Phase 3) |
| Decision record **D-58** (proposed) | Audit trail table as primary screen (deferred) |
| Olares verify (UI smoke + API regression) | Lineage editing |

**Dependency:** All version data **MUST** come from US-22 (D-57). No parallel history query logic in the web client beyond presentation helpers.

---

## 1. Objective

Creators can **browse every stored version** per stage without SQL or raw JSON:

```
Assets / History page → stage sections → version rows → metadata panel → preview/download
```

| Dimension | Intent |
|---|---|
| **User value** | See regen chains, human-edit vs ai-draft, storyboard batch frames |
| **System value** | Makes D-57 API tangible; completes SC-P2-03 / SC-P2-04 pairing |
| **Phase 2 boundary** | **Visibility only** — same append-only semantics as US-22 |

---

## 2. Source review — US-22 API (frozen)

### 2.1 Primary data source

**Route:** `GET /assets/history?project_id={uuid}`

Optional filters (v1 UI may omit run filter): `stage`, `pipeline_run_id`

**Response:** `{ project_id, stages: [{ stage, versions: [...] }] }`

**Reference:** D-57 · `docs/sprints/sprint-5b-us22-implementation-plan.md` §1.4

### 2.2 Content access (reuse)

| Stage | Preview |
|---|---|
| STORY, SCRIPT | Text preview via `getAssetContent(assetId)` |
| STORYBOARD | Image blob URL |
| VIDEO | Download link / blob (no HTML5 player — same as Phase 1) |
| IDEA | Metadata only (content-read not available today) |

**No new download routes.**

### 2.3 Complementary surfaces (unchanged)

| Surface | Relationship |
|---|---|
| US-20 Lineage | Approved-chain provenance; history shows **all** versions |
| US-19 Export | Approved bundle download; history is inspect-only |
| Review pages | Gate approvals; history does not replace review |

---

## 3. Proposed UI scope (D-58 preview)

### 3.1 Placement

| Surface | Detail |
|---|---|
| **Primary** | Route **`/history`** (or extend **Assets** page with history section) |
| **Nav** | AppShell link **History** (always visible when authenticated) |
| **Data** | `getAssetHistory(projectId)` in `web/src/api/client.ts` |

### 3.2 Component contract

| Rule | Detail |
|---|---|
| **Layout** | Vertical stage sections (IDEA → VIDEO) or horizontal tabs — **HTML/CSS only** |
| **Rows** | One row per `versions[]` entry; newest first (API order preserved) |
| **STORYBOARD** | Show `frame_index` in row label |
| **Interaction** | Click row → metadata panel; optional preview pane for readable stages |
| **Badges** | `is_ai_generated`, `branch` (e.g. ai-draft / human-edit) |
| **Forbidden** | Restore buttons, promote, delete, edit-in-place, diff view |

### 3.3 Empty / loading states

Same patterns as LineageViewer / Export page — loading spinner, error alert, empty project guidance.

---

## 4. Acceptance criteria

| ID | Criterion | Verification |
|---|---|---|
| AC-1 | All stages with data visible when history API returns them | Manual / component test |
| AC-2 | Versions **newest first** within each stage (matches API) | Vitest sort helper |
| AC-3 | Metadata panel shows required fields | Component test |
| AC-4 | STORYBOARD rows show `frame_index` | Visual / test |
| AC-5 | Preview works for STORY via content-read | Olares spot-check |
| AC-6 | **Read-only** — no mutation affordances | UI audit |
| AC-7 | Lineage + export regression unchanged | US-23 verify script |

---

## 5. Explicit exclusions

| Exclusion | Rationale |
|---|---|
| Restore / rollback | Out of product scope (D-38 append-only) |
| Asset editing | Frozen review PUT flows only |
| Version diff UI | Phase 3 / separate brief |
| Audit event browser | Deferred |
| Workflow changes | Phase 2 visibility only |
| Schema / API changes | Consume D-57 as-is; extend API only via new brief |

---

## 6. Verification strategy (preview)

| Step | Action | Pass |
|---|---|---|
| S-23-01 | Web build + vitest | PASS |
| S-23-02 | `GET /assets/history` still 200 (API deploy unchanged) | PASS |
| S-23-03 | Content-read spot-check from UI-selected asset_id | PASS |
| S-23-04 | Lineage + export regression | PASS |
| S-23-05 | No new API mutation routes | Static audit |

Scripts: `deploy/k8s/us23-verify/` (to be authored at implementation).

---

## 7. Dependencies

| Dependency | Status |
|---|---|
| US-22 `GET /assets/history` | **CLOSED** (`v0.9.0-us22`) |
| US-21 Realtime | Independent |
| US-V03 | Blocked on US-23 + US-21 |

---

## 8. Authorization boundary

| Stage | Status |
|---|---|
| Phase 2 program brief | **ACCEPT** |
| **US-23 brief** | **SUBMITTED** |
| Implementation plan | Not started |
| Code / deploy | **Not authorized** |

Upon brief ACCEPT: author implementation plan → governance review → D-58 → implement.

---

## 9. Document control

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-06-11 | Initial submission — Phase 2 story 2B-1 |
