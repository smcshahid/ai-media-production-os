# Sprint 5B — US-22 Asset History API (governance brief)

**Status:** **CLOSED** — governance ACCEPT 2026-06-11 · tag `v0.9.0-us22`  
**Closure report:** `docs/sprints/sprint-5b-us22-closure-report.md`
**Parent program:** Spark Full Phase 2 ([spark-full-phase2-governance-brief.md](./spark-full-phase2-governance-brief.md) **ACCEPT**)  
**Story:** US-22 Browse asset versions · FEAT-12 · EPIC-06 · **P1** · 3 SP  
**Prerequisites (closed):** US-V02 ✅ · US-20 ✅ · US-05 ✅ · US-12 ✅ · US-16 ✅  
**Baseline:** `v0.8.0-us20`  
**Proposed decision record:** **D-57** (append at implementation start after plan ACCEPT)

---

## 0. Story classification — read-only version visibility only

US-22 delivers **creator-facing asset version history** over existing `asset_versions` rows: grouped, ordered metadata and content-read by version. It is **not** a restore console, rollback tool, or asset editor.

| Authorized in US-22 | Forbidden in US-22 |
|---|---|
| Read-only asset history **API** (GET only) | **Restore** / rollback to prior version |
| List versions **grouped by stage**, newest first | **Mutation** (PUT/POST/PATCH/DELETE on versions) |
| Per-version metadata: `version`, `branch`, `is_ai_generated`, `content_hash`, `created_at` | Asset **editing** endpoints beyond existing review flows |
| Content-read by `asset_id` (reuse `GET /assets/{id}/content`) | Workflow / Temporal changes |
| Optional filter by `project_id`, `stage`, `pipeline_run_id` | Schema migrations (unless defect — requires SCR) |
| Olares verify + evidence | Lineage editing (US-20 closed — read-only) |
| Decision record **D-57** (proposed) | Diff UI, side-by-side compare (defer **US-23**) |

**Scope split (Phase 2):** US-22 = **API contract**; **US-23** = version browser UI with preview/download. This brief does **not** authorize US-23 screens.

---

## 1. Objective

After any pipeline activity, the creator (or support) can **inspect every stored version** per stage without SQL:

```
Project → GET asset history → versions grouped by stage (newest first) → content-read per row
```

| Dimension | Intent |
|---|---|
| **User value** | See regen chains, human-edit vs ai-draft, batch frame versions |
| **System value** | Surfaces append-only `asset_versions` investment from D-38/D-43/D-47 |
| **Phase 2 boundary** | **Read-only visibility** — approval and regen semantics unchanged |

---

## 2. Source review — existing data model

### 2.1 `asset_versions` (PostgreSQL)

| Column | History use |
|---|---|
| `id` | Row identity; content-read key |
| `project_id` | Scope filter |
| `pipeline_run_id` | Optional run filter (nullable for IDEA / human uploads) |
| `stage` | Group key (IDEA, STORY, SCRIPT, STORYBOARD, VIDEO) |
| `version` | Monotonic per `(project_id, stage)`; STORYBOARD shares batch version + `metadata_json.frame_index` |
| `content_hash` | Integrity display |
| `is_ai_generated`, `branch` | Provenance display |
| `metadata_json` | Frame index, duration, etc. |
| `created_at` | Sort tie-breaker |

**Model reference:** `api/app/infrastructure/db/models/asset_version.py`

### 2.2 Existing API surface

| Route | Today | US-22 relationship |
|---|---|---|
| `GET /assets?project_id=` | Flat list, `created_at DESC` | **Extend or supersede** with grouped/history contract |
| `GET /assets/{id}/content` | Bytes for readable stages | **Reuse** — no duplicate download path |
| `PUT /assets/{id}` | Human-edit STORY only | **Frozen** — not in US-22 scope |
| `POST /assets` | Human upload | **Frozen** — not in US-22 scope |
| `GET /lineage/{run_id}` | Provenance chain (US-20) | **Complementary** — lineage shows approved chain; history shows **all** versions |

### 2.3 STORYBOARD batch semantics (D-43)

- Multiple rows share same `version` integer; distinguish via `metadata_json.frame_index`.
- History API **MUST** return all frame rows; grouping **MAY** nest frames under batch version or flatten with frame metadata — decision in D-57 / implementation plan.

---

## 3. Proposed API contract (D-57 preview)

**Primary route (proposed):**

`GET /assets/history?project_id={uuid}`

Optional query params: `stage`, `pipeline_run_id`

**Response shape (v1 preview):**

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
          "created_at": "ISO8601"
        }
      ]
    }
  ]
}
```

| Rule | Detail |
|---|---|
| Methods | **GET only** on history routes |
| Ordering | **Newest first** within each stage (`version DESC`, then `created_at DESC`; STORYBOARD by `frame_index` within batch) |
| Mutations | **None** — no restore, promote, or delete |
| Errors | 404 unknown project; 401 auth |

Exact field names and grouping finalized in **D-57** at implementation start.

---

## 4. Acceptance criteria

| ID | Criterion | Verification |
|---|---|---|
| AC-1 | Versions **grouped by stage** for a project | API response structure |
| AC-2 | **Newest first** within each stage | Unit test + Olares SQL spot-check |
| AC-3 | Each row exposes `is_ai_generated`, `branch`, `content_hash` | JSON schema test |
| AC-4 | STORYBOARD batches include all frame rows with `frame_index` | SQL vs API count |
| AC-5 | **Read-only** — no new mutation routes | Route audit |
| AC-6 | Content-read via existing `GET /assets/{id}/content` | Spot-check US-V02 project |
| AC-7 | Phase 1 regression (lineage, export, pipeline) | US-22 verify regression steps |

---

## 5. Explicit exclusions

| Exclusion | Rationale |
|---|---|
| Rollback / restore | Out of product scope; append-only model (D-38) |
| Asset editing | Existing PUT/POST unchanged; not expanded |
| Version diff / side-by-side | **US-23** UI scope |
| Lineage editing | US-20 C-01 frozen |
| Workflow / Temporal | Phase 2 visibility only |
| Audit trail browser | US-23 backlog may reuse `audit_events` read — separate brief |
| Schema changes | Read existing tables only |

---

## 6. Verification strategy (preview)

Read-path Olares attestation against US-V02 project (regen artifacts present):

| Step | Action | Pass |
|---|---|---|
| S-22-01 | `GET /assets/history?project_id=` | HTTP 200 |
| S-22-02 | Stage groups present | IDEA, STORY, SCRIPT, STORYBOARD, VIDEO |
| S-22-03 | STORY version count ≥ 2 (regen path) | SQL parity |
| S-22-04 | STORYBOARD frame count | 4 × batch versions as stored |
| S-22-05 | No mutation routes added | Static route audit |
| S-22-06 | Lineage + export regression | US-20 / US-19 spot-check |

Scripts: `deploy/k8s/us22-verify/` (to be authored at implementation).

---

## 7. Dependencies and sequencing

| Dependency | Status |
|---|---|
| US-20 Lineage Viewer | **CLOSED** (`v0.8.0-us20`) |
| US-V02 COMPLETED run + regen artifacts | ✅ |
| US-23 Asset History UI | **Blocked on US-22** API ACCEPT + implement |
| US-21 Realtime | Independent |

---

## 8. Risks

| ID | Risk | Mitigation |
|---|---|---|
| R-22-01 | Scope creep to restore/promote | Brief §0 forbid list; D-57 GET-only |
| R-22-02 | Duplicate of flat `GET /assets` | History route adds grouping + ordering contract |
| R-22-03 | STORYBOARD grouping confusion | D-57 documents batch + frame_index rules |
| R-22-04 | UI work in US-22 | Defer all screens to US-23 |

---

## 9. Authorization boundary

| Stage | Status |
|---|---|
| Phase 2 program brief | **ACCEPT** |
| **US-22 brief** | **ACCEPT** |
| Implementation plan | **SUBMITTED** — awaiting ACCEPT |
| Code / deploy | **Not authorized** |

Upon brief ACCEPT: author implementation plan → governance review → D-57 → implement.

---

## 10. Document control

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-06-11 | Initial submission — Phase 2 story 2A-2 |
| **1.1** | **2026-06-11** | **ACCEPT; implementation plan authorized** |
