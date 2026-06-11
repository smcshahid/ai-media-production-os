# Sprint 4B — US-19 Export Production Bundle (governance brief)

**Status:** **CLOSED** — governance ACCEPT 2026-06-11 · tag `v0.6.0-us19` · M6a export complete.  
**Implementation plan:** `docs/sprints/sprint-4b-us19-implementation-plan.md` (**ACCEPT**)  
**Implementation report:** `docs/sprints/sprint-4b-us19-implementation-report.md` (**Olares PASS**)  
**Parent program:** Spark Full (`docs/sprints/spark-full-governance-brief.md` **ACCEPT**)

---

## 0. Story classification — export and delivery only

US-19 delivers a **downloadable ZIP bundle** of all **approved** pipeline assets for a **COMPLETED** run, including the approved `scene_video.mp4`. It is **not** a publishing story, collaboration story, asset-management console, or lineage visualization story.

| Authorized in US-19 | Forbidden in US-19 |
|---|---|
| `GET /export/{pipeline_run_id}` ZIP download | Publishing to external platforms |
| `manifest.json` with content hashes + approval metadata | Multi-user collaboration / sharing links |
| `finalize_export` Temporal activity (if needed for audit) | Asset history console (US-22/23) |
| Export screen with download button (web) | Lineage graph UI (US-20) |
| `BundleExported` audit event | Realtime / WebSocket updates |
| Olares verify scripts + evidence | Video HTML5 review UI (COMPLETED already at VIDEO approve per D-51) |
| Decision records D-52..D-54 (proposed) | Audio tracks, video editing, re-encoding |
| | Per-project archive management / cloud sync |

**Scope note:** Backlog Issue 47 labels “US-19” as video preview; **this governance brief supersedes that sequencing** for Spark Full. Human VIDEO approval and `COMPLETED` were attested in US-18 (D-51). US-19 is **export and portable delivery** of the completed scene.

---

## 1. Objective

After pipeline **COMPLETED** (VIDEO approved), the creator can **download one ZIP** containing every approved artifact plus a verifiable manifest:

```
COMPLETED run → Export action → ZIP (assets + manifest.json) → local delivery
```

| Dimension | Intent |
|---|---|
| **User value** | Portable archive of the finished scene — idea through video |
| **System value** | Hash-verifiable bundle; audit trail of export |
| **Spark Full boundary** | Delivery only; no downstream publishing pipeline |

### 1.1 Minimal viable export

1. **Gate:** Export allowed only when `pipeline_runs.status = COMPLETED` for the run.
2. **ZIP contents:** Approved assets at latest version per stage — `idea`, `story`, `script`, `frame_*.png` (4), `scene_video.mp4`.
3. **Manifest:** JSON listing each file path, `content_hash`, stage, version, approval timestamps, model IDs where applicable.
4. **Integrity:** Manifest hashes match MinIO bytes at export time.
5. **Audit:** `BundleExported` event with run_id, file count, manifest hash.
6. **UI:** Single Export screen / button on completed project — download only.

No cloud upload, no share URLs, no edit-in-place.

---

## 2. Source review

### 2.1 Acceptance criteria (from Full MVP SC-11 / US-21 mapping)

| # | Criterion | US-19 treatment |
|---|---|---|
| AC-1 | ZIP contains approved assets | All stages through VIDEO at approved versions |
| AC-2 | `manifest.json` with hashes + metadata | Generated at export; stable schema v1 |
| AC-3 | Hash verification | Manifest `content_hash` matches file SHA-256 |
| AC-4 | Audit on export | `BundleExported` in `audit_events` |

### 2.2 Backlog task mapping

| Backlog task | US-19 mapping |
|---|---|
| T-21-01 `finalize_export` activity | Optional — use if audit side-effects need worker |
| T-21-02 `GET /export/{pipeline_run_id}` | **Core** ZIP builder |
| T-21-03 manifest.json generator | **Core** |
| T-21-04 Export screen + download | **Core** (minimal UI) |

### 2.3 Dependencies

| Dependency | Status |
|---|---|
| US-18 VIDEO stage + COMPLETED at VIDEO approve | **CLOSED** (`v0.5.0-us18`) |
| US-08 project/run model | ✅ |
| US-26 asset storage / content-read | ✅ |
| D-46..D-51 approval + versioning contracts | ✅ |

---

## 3. Proposed decision records (for ACCEPT)

### D-52 — Export eligibility

**Decision:** Export **MUST** be rejected (`409` or `422`) unless the latest pipeline run for the project has `status=COMPLETED`. Partial runs, failed runs, and in-progress runs **MUST NOT** export.

### D-53 — Bundle composition

**Decision:** ZIP **MUST** include exactly one file per logical artifact at the **approved version** per stage:

| Stage | File(s) |
|---|---|
| IDEA | `idea.txt` (or canonical text from asset) |
| STORY | `story.md` |
| SCRIPT | `script.fountain` |
| STORYBOARD | `frame_01.png` … `frame_04.png` |
| VIDEO | `scene_video.mp4` |

Storyboard frames ordered by `metadata_json.frame_index`. No superseded versions in bundle.

### D-54 — Manifest schema v1

**Decision:** `manifest.json` **MUST** include:

- `pipeline_run_id`, `project_id`, `exported_at` (ISO8601)
- `files[]`: `{ "path", "stage", "version", "content_hash", "approval_at" }`
- `manifest_version`: `"1"`

Hashes are SHA-256 hex of raw file bytes (same as `asset_versions.content_hash`).

---

## 4. API and schema impact

| Surface | Change |
|---|---|
| `GET /export/{pipeline_run_id}` | **New** — streams `application/zip` |
| Alembic | **None expected** — reuse existing tables |
| Web | Export route + download button on completed project |
| Worker | Optional `finalize_export` for audit-only side effects |

**No new routes for:** lineage, publishing, asset CRUD, collaboration.

---

## 5. Olares verification strategy (outline)

Mirror US-18 pattern: `deploy/k8s/us19-verify/`

| Step | Action | Pass |
|---|---|---|
| PF-01 | Images ≥ `us18` | api + worker tags |
| PF-02 | Completed run from US-18 path | SQL `status=COMPLETED` |
| S-19-01 | `GET /export/{run_id}` | HTTP 200, ZIP magic `PK` |
| S-19-02 | Unzip + count files | ≥ expected artifact count |
| S-19-03 | Parse manifest | All hashes match extracted files |
| S-19-04 | SQL audit | `BundleExported` row present |
| S-19-05 | Negative: non-COMPLETED run | HTTP 4xx |

---

## 6. Explicit non-goals

- Publishing (YouTube, social, CDN upload)
- Collaboration (comments, shared links, multi-editor)
- Asset management console / version browser (US-22/23)
- Lineage visualization (US-20)
- Video re-review UI (deferred — D-51 satisfied in US-18)
- Neo4j / external graph stores
- WebSocket progress for export

---

## 7. Governance ask

| Item | Request |
|---|---|
| Brief | **ACCEPT** to authorize implementation plan |
| D-52..D-54 | **ACCEPT** or amend at review |
| US-19 scope | Export + delivery only — confirm no scope expansion |

**Upon ACCEPT:** Implementation plan required before code authorization (same gate as US-18).

---

## 8. Document history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-06-11 | Initial submission at US-18 closure; export-focused US-19 |
