# Sprint 5A — US-20 Implementation Plan

**Status:** **ACCEPT** — implementation authorized.  
**Parent brief:** `docs/sprints/sprint-5a-us20-brief.md` (**ACCEPT WITH CONDITION C-01**)  
**Story:** US-20 Lineage Viewer · FEAT-14 · EPIC-04 · P1 · 3 SP  
**Baseline:** `v0.7.0-usv02` (`905f1f1`)  
**Decision records:** **D-55**, **D-56** — append to `DECISIONS.md` at **implementation start** (after this plan ACCEPT)

---

## 0. Implementation summary

US-20 adds **`GET /lineage/{pipeline_run_id}`** to return a **read-only** provenance view over existing `lineage_edges` and `asset_versions`, plus a **minimal list/tree** on the Export page (or `/lineage`). No worker, schema, or workflow changes.

| Layer | Net-new | Reuse |
|---|---|---|
| API | `GET /lineage/{pipeline_run_id}`; lineage query service | `LineageEdge` model; `AssetVersionRepository`; `ApprovalRepository`; `PipelineRunRepository`; export resolver patterns |
| Worker | — | **No changes** |
| Web | Lineage list/tree component | Export page; `api/client.ts`; pipeline status hook |
| DB schema | **None** | `lineage_edges`, `asset_versions` read-only |
| Verify | `deploy/k8s/us20-verify/` | US-V02 COMPLETED run for API-only attestation |

**Estimated effort:** ≈ 3 SP · ~2–3 days

### Governance condition C-01 (mandatory)

The implementation **MUST** satisfy all of the following. Any design or code that violates C-01 is **out of scope** and requires a new governance brief.

| # | Requirement |
|---|---|
| **C-01.1** | The **synthetic IDEA root** is **presentation-only** — included in the API/UI response for creator readability; it is **not** a persisted lineage fact. |
| **C-01.2** | **No `lineage_edges` rows are written** — no INSERT, UPSERT, or ORM create in API, worker, scripts, or verify tooling. |
| **C-01.3** | **No `lineage_edges` rows are modified** — no UPDATE or DELETE. |
| **C-01.4** | **No lineage backfill** — no migration scripts, one-off repair jobs, or admin endpoints to populate missing IDEA→STORY edges. |
| **C-01.5** | **No schema changes** — no Alembic migrations; no new tables or columns for lineage. |

**IDEA handling under C-01:** When `asset_versions` contains `stage=IDEA`, `version=1` for the run's project, the API adds an IDEA node with `synthetic: true` (or equivalent flag) and **`parent_asset_ids: []`**. This node **MUST NOT** appear in the `edges[]` array unless a real `lineage_edges` row exists (it does not today).

### Explicitly out of scope (US-20)

Graph database · graph visualization framework (D3, Cytoscape, vis.js, etc.) · lineage editing/repair · asset history browser (US-22/23) · workflow/Temporal changes · WebSocket (US-21) · publishing · collaboration · export contract changes (D-52..D-54)

---

## 1. D-55 — Lineage API read contract

**Record in `DECISIONS.md` as D-55** at implementation start.

### 1.1 Route identity

| Field | Value |
|---|---|
| HTTP route | **`GET /lineage/{pipeline_run_id}`** |
| Auth | Bearer token (same as protected routes) |
| Methods allowed | **GET only** — no POST, PUT, PATCH, DELETE |
| Response `Content-Type` | `application/json` |

### 1.2 Eligibility and errors

| Condition | HTTP | Detail |
|---|---|---|
| Unknown `pipeline_run_id` | **404** | Run does not exist |
| Valid run (any status) | **200** | Lineage is readable for attestation; **UI gate** remains COMPLETED |
| Missing run auth | **401** | Standard auth middleware |

**Note:** Unlike export (D-52), lineage read **MAY** return 200 for non-COMPLETED runs to support debugging; **UI shows lineage only when COMPLETED** (D-56). Verify script uses COMPLETED US-V02 run.

### 1.3 Response schema (v1)

```json
{
  "pipeline_run_id": "uuid",
  "project_id": "uuid",
  "nodes": [
    {
      "asset_id": "uuid",
      "stage": "IDEA",
      "version": 1,
      "content_hash": "sha256…",
      "is_ai_generated": false,
      "branch": "main",
      "metadata": {},
      "parent_asset_ids": [],
      "synthetic": true
    }
  ],
  "edges": [
    { "parent_asset_id": "uuid", "child_asset_id": "uuid" }
  ]
}
```

| Field | Rule |
|---|---|
| `nodes[]` | One entry per displayed asset node |
| `edges[]` | **Exact mirror** of `lineage_edges` rows scoped to run (see §1.5) — **excludes synthetic IDEA link** |
| `synthetic` | **Required on IDEA node when presentation-only**; omitted or `false` for edge-backed nodes |
| `parent_asset_ids` | Derived from `edges[]` for each node (empty for synthetic IDEA) |

### 1.4 Node selection — approved chain (align with export)

For **COMPLETED** runs, the **primary display chain** uses the same approved-version resolution as export (`api/app/domain/export/resolver.py`):

| Stage | Selection rule |
|---|---|
| IDEA | `get_at_version(project_id, IDEA, 1)` — **synthetic root** (C-01.1) |
| STORY | Latest version at STORY approve gate |
| SCRIPT | Latest version at SCRIPT approve gate |
| STORYBOARD | Approved batch: `max_version` + 4 frames by `frame_index` |
| VIDEO | Latest approved VIDEO version |

**Additional nodes (optional in v1):** Regen artifacts (extra SCRIPT/STORYBOARD/VIDEO versions) **MAY** be omitted from the primary ordered list to keep UI minimal; `edges[]` **MUST** still include **all** run-scoped edges from SQL for parity verification.

**Implementation choice (recommended):** Return **two sections** or flags:

- `display_chain[]` — ordered approved nodes (IDEA synthetic → … → VIDEO)
- `edges[]` — full edge set for SQL parity

Alternatively, return all nodes but mark `in_display_chain: true|false`. Plan leaves choice to implementer; **verify asserts `edges[]` parity regardless**.

### 1.5 Edge query (source of truth)

```sql
-- All edges where both endpoints belong to the same project and
-- at least one endpoint references the pipeline run
SELECT le.parent_id, le.child_id
FROM lineage_edges le
JOIN asset_versions p ON le.parent_id = p.id
JOIN asset_versions c ON le.child_id = c.id
WHERE p.project_id = :project_id
  AND c.project_id = :project_id
  AND (p.pipeline_run_id = :run_id OR c.pipeline_run_id = :run_id);
```

**C-01 enforcement:** This query is **SELECT only**. Repository layer **MUST NOT** expose write methods for lineage in US-20.

### 1.6 Ordering (display chain)

| Order | Stage | Sort key |
|---|---|---|
| 1 | IDEA | synthetic root |
| 2 | STORY | version DESC → approved row |
| 3 | SCRIPT | version DESC → approved row |
| 4 | STORYBOARD | `metadata_json.frame_index` ASC (1..4) |
| 5 | VIDEO | approved version |

### 1.7 C-01 attestation (implementation checklist)

| Check | Implementation |
|---|---|
| No INSERT into `lineage_edges` | Grep CI gate; no repository write |
| No migration files | `alembic/versions/` unchanged |
| Synthetic flag on IDEA | Response JSON + unit test |
| `edges[]` ⊆ SQL | Verify script S-20-03 |

---

## 2. D-56 — Lineage UI scope

**Record in `DECISIONS.md` as D-56** at implementation start.

### 2.1 Placement

| Surface | Detail |
|---|---|
| **Primary** | Section on **`ExportPage`** below download CTA when `status === COMPLETED` |
| **Optional** | Dedicated route **`/lineage`** (same component; deep-link friendly) |
| **Nav** | AppShell link visible when COMPLETED (mirror Export link pattern) |

### 2.2 Component contract

| Rule | Detail |
|---|---|
| **Layout** | Vertical **list** or **indented tree** — CSS/HTML only |
| **Forbidden** | Force-directed graph, canvas graph libraries, node-drag editors |
| **Data source** | `GET /lineage/{run_id}` via `api/client.ts` |
| **Interaction** | Click row → metadata panel (stage, version, `content_hash`, `frame_index`, `synthetic` badge on IDEA) |
| **Preview link** | Optional `<a>` to existing asset content URL pattern — **read-only** |
| **Loading/error** | Same patterns as Export page |
| **Empty state** | Hidden when not COMPLETED |

### 2.3 Synthetic IDEA presentation (C-01.1)

| UI element | Behavior |
|---|---|
| IDEA row | Label **"Idea (presentation root)"** or badge `synthetic` |
| Tooltip/copy | "Not stored as a lineage edge; shown for context only." |
| No edit affordance | No buttons that imply mutation |

### 2.4 Explicit UI exclusions

Asset version browser (US-23) · audit table (US-23 backlog) · lineage edit/repair · share/export from lineage · graph zoom/pan

---

## 3. Architecture

### 3.1 API module layout (proposed)

```
api/app/domain/lineage/
  types.py           # LineageNode, LineageEdge, LineageResponse
  resolver.py        # build_lineage(run) — SELECT joins only
  service.py         # orchestration; 404 on missing run
api/app/routes/lineage.py
api/app/infrastructure/db/repositories/lineage_edge.py   # read-only queries
```

**Reuse:** Export resolver helpers for approved asset IDs; do **not** duplicate business rules inline in route.

### 3.2 Web module layout (proposed)

```
web/src/lib/lineageDisplay.ts     # sort/format nodes for list/tree
web/src/components/LineageViewer.tsx
web/src/routes/LineagePage.tsx    # optional thin wrapper
web/src/api/client.ts             # getLineage(runId)
web/src/api/types.ts              # LineageResponse types
```

### 3.3 Registration

- `api/app/main.py` — include lineage router
- `web/src/App.tsx` — optional `/lineage` route
- `web/src/routes/ExportPage.tsx` — embed `LineageViewer`

---

## 4. Olares verification strategy

Read-path only — **no pipeline re-run required**. Reuse US-V02 COMPLETED run after US-20 API deploy.

### 4.1 Scripts

```
deploy/k8s/us20-verify/
  verify_us20.sh       # S-20-01..S-20-07
  run_remote.sh        # secrets + tee log
  deploy_us20.sh       # optional API image import
```

### 4.2 Verify steps

| Step | Action | Pass criteria |
|---|---|---|
| S-20-01 | `GET /lineage/{RUN_ID}` | HTTP 200; JSON parse |
| S-20-02 | Display chain stages | IDEA (synthetic), STORY, SCRIPT, ≥4 STORYBOARD, VIDEO |
| S-20-03 | **API vs SQL edge parity** | `len(edges)` == SQL COUNT (§1.5 query) |
| S-20-04 | Synthetic IDEA | IDEA node present; `synthetic=true`; **no edge** IDEA→STORY in `edges[]` |
| S-20-05 | STORYBOARD→VIDEO | 4 edges to final VIDEO asset_id |
| S-20-06 | Unknown run | HTTP 404 |
| S-20-07 | Export regression | `GET /export/{RUN_ID}` HTTP 200 unchanged |

### 4.3 SQL attestation

| ID | Query | Evidence file |
|---|---|---|
| V-20-L01 | Edge count for run-scoped assets | `sql/v20-l01-edges.txt` |
| V-20-L02 | Stage pair counts | `sql/v20-l02-stage-pairs.txt` |
| V-20-L03 | STORYBOARD→VIDEO to final VIDEO | `sql/v20-l03-sb-video.txt` |
| V-20-L04 | **No lineage writes** | `SELECT COUNT(*) FROM lineage_edges` before/after verify identical |

### 4.4 Evidence package

`evidence/us-20-verification/olares-<date>/US-20-ACCEPTANCE-PACKAGE.md`

---

## 5. Local testing

| Suite | New tests | Target |
|---|---|---|
| API unit | `test_lineage.py` | 404; edge parity mock; synthetic IDEA flag; no write calls |
| Web vitest | `lineageDisplay.test.ts`, component smoke | Ordered render; synthetic badge |
| Regression | Existing export tests | Unchanged PASS |

**Baseline before implementation:** API 88 · worker 39 · web 23 (US-V02 closure).

---

## 6. Acceptance criteria mapping

| AC | Plan section | Verification |
|---|---|---|
| AC-1 Ordered chain incl. video | §1.4, §2 | S-20-02 |
| AC-2 Edge parity | §1.5, §4.2 S-20-03 | SQL diff |
| AC-3 Node metadata UI | §2.2 | Manual / component test |
| AC-4 PostgreSQL only | §0, §3 | Architecture review |
| AC-5 Read-only | C-01, §1.1 | API audit + V-20-L04 |
| AC-6 Phase 1 regression | §4.2 S-20-07 | Export spot-check |

---

## 7. Risks and mitigations

| ID | Risk | Mitigation |
|---|---|---|
| R-20-01 | C-01 violation via "helpful" backfill | PR checklist §0; grep `lineage_edges` INSERT |
| R-20-02 | Display chain vs full edges confusion | Document `synthetic` + verify full `edges[]` parity |
| R-20-03 | Graph library creep | D-56 forbid list; code review |
| R-20-04 | Duplicated approved-version logic | Reuse export resolver helpers |
| R-20-05 | US-22 scope bleed | No version browser; lineage shows approved chain only |

---

## 8. Implementation checklist (post–plan ACCEPT)

| # | Task | Owner |
|---|---|---|
| 1 | Append D-55, D-56 to `DECISIONS.md` | Dev |
| 2 | `LineageEdgeRepository` (read-only) + domain service | Dev |
| 3 | `GET /lineage/{pipeline_run_id}` route | Dev |
| 4 | `LineageViewer` + Export page integration | Dev |
| 5 | API + web unit tests | Dev |
| 6 | `deploy/k8s/us20-verify/` | Dev |
| 7 | Olares verify + acceptance package | Ops |
| 8 | Implementation report | Dev |

---

## 9. Authorization boundary

| Stage | Status |
|---|---|
| Brief | **ACCEPT WITH CONDITION C-01** |
| Implementation plan | **ACCEPT** |
| **Code / deploy** | **Authorized** — Olares evidence required before closure |

Upon plan ACCEPT: implementation may begin. Olares evidence required before story closure (same pattern as US-18/US-19).

---

## 10. Document control

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-06-11 | Initial plan — C-01, D-55, D-56 |
