# Sprint 5A — US-20 Lineage Viewer (governance brief)

**Status:** **CLOSED** — governance ACCEPT 2026-06-11 · tag `v0.8.0-us20`  
**Closure report:** `docs/sprints/sprint-5a-us20-closure-report.md`
**Implementation plan:** `docs/sprints/sprint-5a-us20-implementation-plan.md` (**ACCEPT**)  
**Implementation report:** `docs/sprints/sprint-5a-us20-implementation-report.md`  
**Parent program:** Spark Full Phase 2 ([spark-full-phase2-governance-brief.md](./spark-full-phase2-governance-brief.md) **ACCEPT**)  
**Story:** US-20 View asset lineage chain · FEAT-14 · EPIC-04 · **P1** · 3 SP  
**Prerequisites (all closed):** US-V02 ✅ · US-18 ✅ · US-19 ✅ · US-16 ✅ · US-14 ✅  
**Baseline:** `v0.7.0-usv02` (`905f1f1`)

---

## 0. Story classification — read-only visibility only

US-20 delivers **creator-facing lineage visibility** for a completed pipeline run: an ordered view of how assets connect from idea through video, backed by existing PostgreSQL data. It is **not** a provenance editor, workflow story, or asset-management console.

| Authorized in US-20 | Forbidden in US-20 |
|---|---|
| `GET /lineage/{pipeline_run_id}` read API | Lineage **editing** or manual edge insert/delete |
| Minimal web lineage viewer (list/tree) | Lineage **repair** / backfill scripts in product |
| Read `lineage_edges` + join `asset_versions` | Neo4j or external graph database |
| Synthetic **IDEA root** node in API response (no new edges) | Temporal / workflow changes |
| Olares verify scripts + evidence | Asset **mutation** (PUT/POST on versions) |
| Decision records D-55, D-56 (proposed) | Collaboration / sharing / multi-user |
| Link from Export or Dashboard when COMPLETED | Interactive graph layout frameworks |

**Scope note:** Visual MVP Issue 40 AC excluded the video node; **Phase 2 and US-V02 require VIDEO in the chain**. US-20 extends the backlog AC to **idea → story → script → frames → video**.

---

## 1. Objective

After pipeline **COMPLETED**, the creator can **inspect provenance** without SQL:

```
COMPLETED run → Lineage action → ordered chain (API + minimal UI)
```

| Dimension | Intent |
|---|---|
| **User value** | Understand how the finished scene was derived — which story led to script, frames, and video |
| **System value** | Surfaces existing `lineage_edges` investment; supports demo and support without psql |
| **Phase 2 boundary** | **Visibility only** — generation and edge creation remain in worker activities (unchanged) |

### 1.1 Minimal viable lineage

1. **Gate:** Lineage readable for runs that exist; primary UX when `pipeline_runs.status = COMPLETED`.
2. **API:** Return ordered nodes with stage, version, `asset_id`, `content_hash`, key metadata — derived from DB joins.
3. **UI:** Simple vertical list or indented tree — no force-directed graph, no drag-and-drop.
4. **Accuracy:** Response **MUST** be consistent with `lineage_edges` for edge-backed relationships.
5. **IDEA root:** Include IDEA asset as **logical root** when present for the project (see §2.3) — **without** writing new edges.

No edge editing, no “fix lineage” admin tools.

---

## 2. Source review — existing data model

### 2.1 `lineage_edges` (PostgreSQL)

```text
lineage_edges
  id          UUID PK
  parent_id   FK → asset_versions.id
  child_id    FK → asset_versions.id
  created_at  timestamp
  UNIQUE (parent_id, child_id)
```

**Properties today:**

- Directed edges only; no edge metadata column.
- Append-only by worker convention (no API delete).
- No `pipeline_run_id` on edge — scope inferred via joined `asset_versions.pipeline_run_id`.

**Model reference:** `api/app/infrastructure/db/models/lineage_edge.py`

### 2.2 `asset_versions` (join surface)

| Column | Lineage use |
|---|---|
| `id` | Node identity in API |
| `project_id` | Project scope filter |
| `pipeline_run_id` | Run scope filter (nullable for human uploads) |
| `stage` | IDEA, STORY, SCRIPT, STORYBOARD, VIDEO |
| `version` | Display + ordering within stage |
| `content_hash` | Integrity display |
| `is_ai_generated`, `branch` | Node metadata |
| `metadata_json` | STORYBOARD `frame_index`; VIDEO `logical_filename`, duration, etc. |

**Model reference:** `api/app/infrastructure/db/models/asset_version.py`

### 2.3 Edge topology produced by Phase 1 (unchanged)

Worker activities **already insert** edges at generation time:

| Transition | Writer | Pattern |
|---|---|---|
| STORY → SCRIPT | `run_script_agent` | 1 edge per SCRIPT generation (regen → new SCRIPT child, new edge from same approved STORY parent per D-42) |
| SCRIPT → STORYBOARD | `store_storyboard_batch` | 1 edge per frame (SCRIPT parent → each PNG child) |
| STORYBOARD → VIDEO | `store_video_asset` | 1 edge per approved frame → VIDEO child (4 edges per VIDEO version; D-48/D-49) |

**US-V02 Olares attestation (reference):**

| parent.stage | child.stage | count (A-01 + VIDEO regen path) |
|---|---|---|
| STORY | SCRIPT | 2 |
| SCRIPT | STORYBOARD | 8 |
| STORYBOARD | VIDEO | 8 |

**IDEA → STORY:** No `lineage_edges` row is written today. IDEA is stored via `POST /ideas` as `asset_versions` stage=IDEA, version=1. US-20 **MAY** expose IDEA as the **first logical node** linked by `project_id` (and run context) **without** mutating edges or worker code.

### 2.4 What US-20 does not change

| Layer | US-20 impact |
|---|---|
| Worker / Temporal | **None** — no new `insert_lineage_edge` calls |
| Schema | **None** — read-only over existing tables |
| D-37..D-54 | **Frozen** |
| Export (US-19) | **None** — manifest already lists assets; lineage is complementary |

---

## 3. Proposed decision records (for implementation start)

Record in `DECISIONS.md` as **D-55** and **D-56** when implementation plan is authorized — **not at brief ACCEPT**.

### D-55 — Lineage API read contract (proposed)

**Route:** `GET /lineage/{pipeline_run_id}`

**Response shape (illustrative):**

```json
{
  "pipeline_run_id": "uuid",
  "project_id": "uuid",
  "nodes": [
    {
      "asset_id": "uuid",
      "stage": "STORY",
      "version": 2,
      "content_hash": "sha256…",
      "is_ai_generated": false,
      "branch": "human-edit",
      "metadata": {},
      "parent_asset_ids": ["uuid"]
    }
  ],
  "edges": [
    { "parent_asset_id": "uuid", "child_asset_id": "uuid" }
  ]
}
```

| Rule | Detail |
|---|---|
| **Auth** | Bearer token (same as protected routes) |
| **404** | Unknown `pipeline_run_id` |
| **Read-only** | GET only; no POST/PUT/DELETE |
| **Edge source of truth** | `lineage_edges` rows where both endpoints belong to run (via asset join) |
| **IDEA root** | If IDEA asset exists for project, include as node with `parent_asset_ids: []` |
| **STORYBOARD** | Multiple frame nodes distinguished by `metadata.frame_index` |
| **VIDEO** | Include latest **approved** VIDEO version for COMPLETED run (align with export resolver) |
| **Ordering** | Topological order: IDEA (logical) → STORY → SCRIPT → STORYBOARD frames (1..4) → VIDEO |

### D-56 — Lineage UI scope (proposed)

| Rule | Detail |
|---|---|
| **Placement** | Section on **Export** page and/or dedicated `/lineage` route |
| **Visibility gate** | Show when pipeline status is **COMPLETED** (same gate as export CTA) |
| **Component** | Vertical **list** or simple **indented tree** — no graph library requirement |
| **Interaction** | Click/highlight node → show metadata panel (stage, version, hash, frame_index) |
| **Content preview** | **Optional** — link to existing `GET /assets/{id}/content` (reuse; no new read path) |
| **Out of scope** | Edit, delete, merge, branch promotion, share links |

---

## 4. Acceptance criteria

| # | Criterion | Verification |
|---|---|---|
| AC-1 | Ordered chain includes **IDEA → STORY → SCRIPT → STORYBOARD (4 frames) → VIDEO** | API + UI on COMPLETED run |
| AC-2 | Edge-backed relationships match `lineage_edges` | Olares SQL vs API diff |
| AC-3 | Click/select node shows metadata (stage, version, hash) | UI smoke / manual |
| AC-4 | Data from PostgreSQL only — no graph DB | Architecture review |
| AC-5 | **Read-only** — no lineage or asset mutation endpoints | API audit |
| AC-6 | Phase 1 regression — US-V02 export + COMPLETED semantics unchanged | US-20 verify + export spot-check |

### 4.1 Backlog mapping (Issue 40 / T-20-*)

| Task | US-20 mapping |
|---|---|
| T-20-01 `GET /lineage/{pipeline_run_id}` | **Core** API |
| T-20-02 Lineage component on Export screen | **Core** minimal UI |
| T-20-03 Chain visualization (list/tree) | **Core** — no force graph |

---

## 5. API and web impact

### 5.1 Authorized (after plan ACCEPT)

| Surface | Change |
|---|---|
| API | New `GET /lineage/{pipeline_run_id}` |
| API domain | Lineage query service (join edges + assets) |
| Web | Lineage list/tree component; nav link when COMPLETED |
| Tests | API unit tests (mock DB); web component test (static fixture) |
| Verify | `deploy/k8s/us20-verify/` |

### 5.2 Explicitly forbidden

| Surface | Reason |
|---|---|
| `POST/PUT/DELETE /lineage/*` | Visibility only |
| Worker activity changes | No new edge writes |
| Alembic migration | No schema change |
| Neo4j / Redis graph | D-56 |
| WebSocket (US-21) | Separate story |

---

## 6. Olares verification strategy

Verification is **read-path only** — can run against an **existing COMPLETED run** (e.g. US-V02 pass) without re-executing the full pipeline.

### 6.1 Pre-flight

| ID | Check |
|---|---|
| PF-01 | Images ≥ `v0.7.0-usv02` baseline (or US-20 build under test) |
| PF-02 | `RUN_ID` of COMPLETED run available |
| PF-03 | API `/health` green |

### 6.2 Verify steps (proposed)

| Step | Action | Pass criteria |
|---|---|---|
| S-20-01 | `GET /lineage/{RUN_ID}` | HTTP 200; JSON schema |
| S-20-02 | Node count / stages | IDEA, STORY, SCRIPT, ≥4 STORYBOARD, VIDEO present |
| S-20-03 | Edge parity SQL | API `edges` count = `SELECT COUNT(*) FROM lineage_edges …` for run-scoped assets |
| S-20-04 | STORY→SCRIPT chain | ≥1 edge; matches v06-lineage pattern |
| S-20-05 | STORYBOARD→VIDEO | 4 edges to approved VIDEO asset (final version) |
| S-20-06 | Negative unknown run | HTTP 404 |
| S-20-07 | Export regression | `GET /export/{RUN_ID}` still 200 (US-19 unchanged) |

### 6.3 SQL attestation templates

```sql
-- V-20-L01 edge count for run-scoped assets
SELECT COUNT(*) FROM lineage_edges le
JOIN asset_versions p ON le.parent_id = p.id
JOIN asset_versions c ON le.child_id = c.id
WHERE p.pipeline_run_id = '$RUN_ID' OR c.pipeline_run_id = '$RUN_ID';

-- V-20-L02 stage pairs (reference US-V02)
SELECT p.stage, c.stage, COUNT(*)
FROM lineage_edges le
JOIN asset_versions p ON le.parent_id = p.id
JOIN asset_versions c ON le.child_id = c.id
WHERE p.project_id = '$PROJECT'
GROUP BY p.stage, c.stage ORDER BY 1, 2;

-- V-20-L03 STORYBOARD→VIDEO to final VIDEO
SELECT COUNT(*) FROM lineage_edges le
JOIN asset_versions p ON le.parent_id = p.id
JOIN asset_versions c ON le.child_id = c.id
WHERE c.id = '$FINAL_VIDEO_ASSET_ID' AND p.stage = 'STORYBOARD';
-- Expected: 4
```

### 6.4 Evidence layout (proposed)

```text
evidence/us-20-verification/olares-<date>/
  US-20-ACCEPTANCE-PACKAGE.md
  logs/us20-verify-pass.log
  sql/v20-l01-edges.txt
  sql/v20-l02-stage-pairs.txt
```

**Reuse run:** `RUN_ID=042983f7-0f55-48c3-9d65-fce89a684625` (US-V02) acceptable for API-only verify after US-20 deploy.

---

## 7. Dependencies and sequencing

| Dependency | Status |
|---|---|
| US-V02 COMPLETED + lineage attestation | ✅ |
| `lineage_edges` populated by worker | ✅ |
| `GET /assets/{id}/content` | ✅ (optional preview links) |
| Export page (US-19) | ✅ — host for lineage section |
| US-22 Asset History API | **Not required** — parallel Phase 2 story |

**Phase 2 sequence:** US-20 is **2A-1** entry (first implementation story after this brief ACCEPT).

---

## 8. Risks

| ID | Risk | Mitigation |
|---|---|---|
| R-20-01 | IDEA not edge-linked | D-55 synthetic root; document in API |
| R-20-02 | Multiple STORYBOARD batches clutter UI | Show **approved batch** frames only (match export resolver) |
| R-20-03 | Graph UI scope creep | D-56 list/tree only |
| R-20-04 | Regen chains multiply edges | Expected; UI groups by stage |
| R-20-05 | Phase 1 regression | S-20-07 export spot-check in verify |

---

## 9. Explicit exclusions

Aligned with Phase 2 brief §8 and governance ACCEPT constraints:

- Lineage editing, repair, or backfill in product code
- Graph database or Neo4j migration
- Workflow / Temporal / worker changes
- Asset mutation via lineage UI
- Collaboration, sharing, publishing
- Realtime push (US-21)
- Full asset history browser (US-22/23)
- **Implementation** until brief ACCEPT → plan ACCEPT

---

## 10. Project status

| Item | Status |
|---|---|
| **Spark Full Phase 2 brief** | **ACCEPT** |
| **US-20 brief** | **ACCEPT (C-01)** |
| **US-20 implementation plan** | **SUBMITTED** — awaiting ACCEPT |
| **Frontier** | **US-20** |
| **Implementation** | **Not authorized** (awaiting plan ACCEPT) |

**Next step:** Governance review of implementation plan. Upon ACCEPT, append D-55/D-56 and begin code — **subject to C-01.**

---

## 11. Document control

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-06-11 | Initial submission — Phase 2 entry story |
| **1.1** | **2026-06-11** | **ACCEPT WITH CONDITION C-01; implementation plan authorized** |
