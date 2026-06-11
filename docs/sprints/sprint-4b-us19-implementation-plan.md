# Sprint 4B — US-19 Implementation Plan

**Status:** **CLOSED** — Olares PASS · tag `v0.6.0-us19`  
**Parent brief:** `docs/sprints/sprint-4b-us19-brief.md` (**ACCEPT** 2026-06-11)  
**Story:** US-19 Export production bundle · FEAT-15 · EPIC-05 · P1 · 3 SP  
**Baseline:** `v0.5.0-us18` (`e764f5d`)  
**Decision records:** **D-52** through **D-54** — append to `DECISIONS.md` at **implementation start** (after this plan ACCEPT)

---

## 0. Implementation summary

US-19 adds **`GET /export/{pipeline_run_id}`** to stream a **deterministic ZIP bundle** of all **approved** assets for a **COMPLETED** pipeline run, plus **`manifest.json`** and a **`BundleExported`** audit event. A minimal **Export** screen provides a download button when the project is complete.

| Layer | Net-new | Reuse |
|---|---|---|
| `aimpos-core` | `AuditEventType.BUNDLE_EXPORTED` | Existing audit enum pattern |
| API | `GET /export/{pipeline_run_id}`; export service (ZIP + manifest) | MinIO read; `AssetVersionRepository`; `ApprovalRepository`; `PipelineRunRepository` |
| Worker | — | **No Temporal activity** in Phase 1 (sync API build) |
| Web | Export page / download CTA on COMPLETED project | Auth client; pipeline status hook |
| DB schema | **None** — read-only over existing tables | `pipeline_runs`, `asset_versions`, `approvals`, `audit_events` |
| Verify | `deploy/k8s/us19-verify/` | US-18 verify path to COMPLETED run |

**Estimated effort:** ≈ 3 SP · ~2–3 days

### Explicitly out of scope (US-19)

Publishing · collaboration · asset management console · lineage UI · video review / HTML5 player · WebSocket · cloud sync · multi-format export · worker-side `finalize_export` (deferred unless audit latency requires async) · `GET /lineage` (US-20)

---

## 1. D-52 — Export bundle contract

**Record in `DECISIONS.md` as D-52** at implementation start.

### 1.1 Eligibility (COMPLETED runs only)

| Rule | Detail |
|---|---|
| **Gate** | `pipeline_runs.status` **MUST** equal **`COMPLETED`** for the requested `pipeline_run_id` |
| **Reject** | `409 Conflict` when status is `RUNNING`, `AWAITING_APPROVAL`, `FAILED`, `PENDING`, or `IDLE` |
| **Unknown run** | `404 Not Found` when `pipeline_run_id` does not exist |
| **Auth** | Bearer token required (same as all protected routes) |
| **Project scope** | Run **MUST** belong to a valid project; export does not cross projects |
| **Re-export** | Allowed — each download is idempotent in **content** (same approved versions → same bytes) but **`exported_at`** in manifest may differ |

**Rationale:** Export is a **delivery** action on a finished scene, not a recovery path for partial pipelines.

### 1.2 ZIP identity

| Field | Value |
|---|---|
| HTTP route | **`GET /export/{pipeline_run_id}`** |
| Response `Content-Type` | **`application/zip`** |
| Response `Content-Disposition` | **`attachment; filename="aimpos-export-{pipeline_run_id}.zip"`** |
| Archive logical name | **`export.zip`** (internal convention; filename above is HTTP delivery name) |
| Compression | DEFLATE (stdlib `zipfile` or equivalent) |
| Streaming | **Required** — stream ZIP to client; do not persist bundle to MinIO |

### 1.3 Deterministic contents

ZIP **MUST** contain **exactly** these entries (no extra files, no directory-only entries):

| # | ZIP path | Source stage | Resolution rule |
|---|---|---|---|
| 1 | `manifest.json` | — | Generated at export time (§2) |
| 2 | `idea.txt` | IDEA | Single row: `version=1` for project (seed/submitted idea) |
| 3 | `story.md` | STORY | Asset at **approved version** on run (`approvals` STORY APPROVED → match version used at gate) |
| 4 | `script.fountain` | SCRIPT | Asset at approved version on run |
| 5 | `frames/frame_01.png` | STORYBOARD | Batch at approved `MAX(version)`; `frame_index=1` |
| 6 | `frames/frame_02.png` | STORYBOARD | `frame_index=2` |
| 7 | `frames/frame_03.png` | STORYBOARD | `frame_index=3` |
| 8 | `frames/frame_04.png` | STORYBOARD | `frame_index=4` |
| 9 | `scene_video.mp4` | VIDEO | Asset at approved version on run (latest approved VIDEO for completed run) |

**Total file count:** **9** entries (1 manifest + 8 assets).

### 1.4 Deterministic ordering

| Rule | Detail |
|---|---|
| ZIP entry order | Fixed table order §1.3 (manifest first, then idea → story → script → frames 01–04 → video) |
| Frame order | By `metadata_json.frame_index` ascending (1..4) |
| Superseded versions | **Excluded** — only approved-version bytes per stage |
| Empty / missing asset | Export **MUST fail** with `500` + audit `PIPELINE_FAILED` payload only if invariant broken on COMPLETED run (should not occur on healthy COMPLETED attestation) |

### 1.5 Byte source

All asset bytes **MUST** be loaded from MinIO via `asset_versions.minio_key` at export time (never from cache of superseded rows).

### 1.6 Resolution query (evidence)

```sql
-- Eligibility
SELECT id, project_id, status, current_stage
FROM pipeline_runs
WHERE id = :pipeline_run_id AND status = 'COMPLETED';

-- Approved VIDEO version (example)
SELECT av.id, av.version, av.content_hash
FROM asset_versions av
JOIN approvals a ON a.pipeline_run_id = :run_id
  AND a.stage = 'VIDEO' AND a.decision = 'APPROVED'
WHERE av.project_id = :project_id AND av.stage = 'VIDEO'
ORDER BY av.version DESC
LIMIT 1;
```

---

## 2. D-53 — Manifest contract

**Record in `DECISIONS.md` as D-53** at implementation start.

### 2.1 Schema version

| Field | Value |
|---|---|
| **`manifest_version`** | **`"1"`** (string) |

### 2.2 Required top-level fields

| Key | Type | Rule |
|---|---|---|
| **`manifest_version`** | string | Always `"1"` |
| **`pipeline_run_id`** | string (UUID) | Requested run |
| **`project_id`** | string (UUID) | Owning project |
| **`exported_at`** | string (ISO8601 UTC) | Timestamp when ZIP build started (e.g. `2026-06-11T17:17:38.216989Z`) |
| **`files`** | array | One object per ZIP asset entry (§1.3 rows 2–9; **exclude** manifest itself from `files[]`) |

### 2.3 Required `files[]` entry fields

| Key | Type | Rule |
|---|---|---|
| **`path`** | string | ZIP path (e.g. `frames/frame_03.png`) |
| **`stage`** | string | `IDEA` \| `STORY` \| `SCRIPT` \| `STORYBOARD` \| `VIDEO` |
| **`version`** | integer | `asset_versions.version` |
| **`content_hash`** | string | SHA-256 hex (same as `asset_versions.content_hash`) |
| **`approval_at`** | string (ISO8601) \| null | From `approvals.created_at` for APPROVED row on run+stage; IDEA may use project seed time or null |
| **`asset_id`** | string (UUID) | `asset_versions.id` |
| **`size_bytes`** | integer | Byte length in ZIP |

### 2.4 Optional `files[]` fields

| Key | When |
|---|---|
| `model_id` | Present in `metadata_json` for AI-generated assets |
| `frame_index` | STORYBOARD only (1..4) |
| `branch` | STORY human-edit vs ai-draft if useful for audit |

### 2.5 Integrity rule

For every `files[]` entry, **`content_hash`** **MUST** equal SHA-256 of the corresponding bytes embedded in the ZIP. Verify script recomputes hashes from extracted files.

### 2.6 Example (truncated)

```json
{
  "manifest_version": "1",
  "pipeline_run_id": "2f94f2c3-5904-4011-ac50-6d2320244720",
  "project_id": "70898838-3a6c-4567-8483-371fca866b46",
  "exported_at": "2026-06-11T17:20:00.000000Z",
  "files": [
    {
      "path": "idea.txt",
      "stage": "IDEA",
      "version": 1,
      "content_hash": "b9ea8c572010737fe73cfa3e6a3833a1cd8c16eeee20e3367433c9a38f1b0541",
      "approval_at": null,
      "asset_id": "…",
      "size_bytes": 512
    }
  ]
}
```

### 2.7 Manifest placement

`manifest.json` **MUST** be the **first** entry in the ZIP (§1.4). It **MUST NOT** appear in its own `files[]` list.

---

## 3. D-54 — Export audit contract

**Record in `DECISIONS.md` as D-54** at implementation start.

### 3.1 Event type

| Field | Value |
|---|---|
| Enum | **`AuditEventType.BUNDLE_EXPORTED`** = `"BUNDLE_EXPORTED"` |
| Location | `packages/aimpos-core/aimpos_core/events/audit.py` |
| Table | Append-only `audit_events` (existing schema) |

### 3.2 When to record

| Rule | Detail |
|---|---|
| **Trigger** | After ZIP bytes successfully assembled and **before** response stream completes |
| **Failure** | If ZIP build fails, record **no** `BUNDLE_EXPORTED`; return 5xx |
| **Re-export** | Each successful download appends **one** new audit row (export is an auditable action, not idempotent in audit log) |

### 3.3 Required payload (`audit_events.payload_json`)

| Key | Type | Rule |
|---|---|---|
| **`pipeline_run_id`** | string (UUID) | Exported run |
| **`project_id`** | string (UUID) | Owning project |
| **`file_count`** | integer | **8** (asset files excluding manifest) |
| **`manifest_hash`** | string | SHA-256 hex of **`manifest.json`** bytes as stored in ZIP |
| **`zip_size_bytes`** | integer | Total ZIP size |
| **`exported_at`** | string (ISO8601) | Same as manifest top-level |
| **`manifest_version`** | string | `"1"` |

### 3.4 Optional payload fields

| Key | When |
|---|---|
| `content_hashes` | Array of 8 asset hashes (deterministic order §1.3) — aids SQL attestation without unzipping |
| `client_hint` | `"api"` (constant for US-19) |

### 3.5 Relationship to `PIPELINE_COMPLETED`

| Event | When |
|---|---|
| `PIPELINE_COMPLETED` | Already emitted at VIDEO approve (US-18 / D-51) |
| `BUNDLE_EXPORTED` | **Separate** — only on export download; does not change pipeline status |

---

## 4. Export eligibility (summary)

Cross-reference **§1.1** (D-52). Implementation checklist:

| Check | HTTP | Test ID |
|---|---|---|
| Run exists | 404 if missing | T-05 |
| Run COMPLETED | 200 + ZIP | T-01 |
| Run AWAITING_APPROVAL | 409 | T-06 |
| Run FAILED | 409 | T-07 |
| No auth token | 401 | T-08 |

**API handler flow:**

1. Load `pipeline_run` by id → 404  
2. Assert `status == COMPLETED` → 409  
3. Resolve approved asset set (§1.3)  
4. Build manifest (§2)  
5. Stream ZIP (§1.2)  
6. Append `BUNDLE_EXPORTED` (§3)  
7. Return streamed response  

---

## 5. API and web design

### 5.1 API module layout

| File | Responsibility |
|---|---|
| `api/app/routes/export.py` | Route + auth + eligibility |
| `api/app/domain/export/service.py` | Asset resolution, manifest builder, ZIP stream |
| `api/app/domain/export/manifest.py` | Schema v1 + hash helpers |
| `api/app/main.py` | Register router |

### 5.2 Web (minimal)

| Surface | Behavior |
|---|---|
| Route | `/export` or Export tab linked from Dashboard when `status === "COMPLETED"` |
| UI | Project name, run id (truncated), **Download bundle** button |
| Download | `fetch` / blob → save as `aimpos-export-{runId}.zip` |
| **No** | Preview player, lineage graph, publish buttons, asset version browser |

### 5.3 OpenAPI

Document `GET /export/{pipeline_run_id}` with 200 (zip), 401, 404, 409 responses.

---

## 6. Olares verification strategy

Mirror US-18: `deploy/k8s/us19-verify/` + evidence pack. **No product code in verify-only commits** after initial implementation.

### 6.1 Pre-flight (PF-01..PF-05)

| ID | Action | Pass |
|---|---|---|
| PF-01 | Images ≥ `us18` | `aimpos-api:us19`, worker unchanged or tagged |
| PF-02 | API `/health` | postgres, redis, minio green |
| PF-03 | Completed run available | Reuse US-18 verify path **or** fresh run through VIDEO approve |
| PF-04 | SQL attestation | `pipeline_runs.status=COMPLETED` for test `RUN_ID` |
| PF-05 | Local unit regression | API + web counts documented |

### 6.2 Normative sequence (S-19-xx)

| Step | Action | Capture |
|---|---|---|
| S-19-00 | Ensure COMPLETED run (full path or reuse) | `PROJECT`, `RUN_ID` |
| S-19-01 | `GET /export/{RUN_ID}` | HTTP 200; save `/tmp/us19-export.zip` |
| S-19-02 | ZIP magic | First bytes `PK` |
| S-19-03 | Unzip file count | **9** entries |
| S-19-04 | Manifest parse | `manifest_version=1`; required fields present |
| S-19-05 | Hash verify | Recompute SHA-256 for each file vs manifest |
| S-19-06 | SQL audit | `BUNDLE_EXPORTED` row for run |
| S-19-07 | Negative: export AWAITING run | HTTP 409 (separate fixture or mid-run project) |
| S-19-08 | Re-export | Second 200; second audit row |

### 6.3 SQL attestation (V-19-xx)

| ID | Query purpose | Expected |
|---|---|---|
| V-19-01 | Run eligibility | `status=COMPLETED` |
| V-19-02 | Asset counts per stage | IDEA 1, STORY 1, SCRIPT 1, STORYBOARD 4, VIDEO 1 at approved versions |
| V-19-03 | Audit export | ≥1 `BUNDLE_EXPORTED` for run |
| V-19-04 | Manifest hash | Payload `manifest_hash` matches extracted manifest |

### 6.4 Pass / fail

| Verdict | Condition |
|---|---|
| **PASS** | ZIP deterministic set; manifest valid; hashes match; audit present; 409 on non-COMPLETED |
| **CONDITIONAL** | Local tests only — **insufficient for ACCEPT** |
| **FAIL** | Missing files; hash mismatch; export allowed on incomplete run |

### 6.5 Verify scripts

```
deploy/k8s/us19-verify/
  verify_us19.sh          # main E2E
  run_remote.sh           # secrets + invoke
  deploy_us19.sh          # optional api:us19 rollout
  create_project.sh       # reuse us18 pattern if fresh run needed
```

**Reuse option:** If a COMPLETED run exists from US-18 Olares evidence, verify may accept `RUN_ID` env override to skip full pipeline (document in script header).

---

## 7. Evidence package structure

```
evidence/us-19-verification/
  local-<date>/
    logs/
      pytest-api.txt
      vitest-web.txt
  olares-<date>/
    US-19-ACCEPTANCE-PACKAGE.md
    logs/
      us19-verify.log
      us19-export.zip          # optional retained artifact (git if <1MB else attestation only)
    sql/
      v19-01-run-status.txt
      v19-02-asset-counts.txt
      v19-03-bundle-exported-audit.txt
    manifest-extract.json      # parsed manifest from Olares run
    metadata.json              # PROJECT, RUN_ID, API_IMAGE, VERIFY_RC, timestamps
```

### 7.1 Acceptance package sections (template)

| Section | Content |
|---|---|
| Verification summary | D-52..D-54, AC-1..AC-4 PASS/FAIL table |
| Run attestation | `PROJECT`, `RUN_ID`, export HTTP status, byte size |
| AC mapping | AC-1 ZIP contents, AC-2 manifest, AC-3 hashes, AC-4 audit |
| Governance contracts | D-52 bundle, D-53 manifest, D-54 audit |
| Closure recommendation | READY / NOT READY |

---

## 8. Acceptance criteria traceability

| AC | Contract | Verification |
|---|---|---|
| AC-1 ZIP contains approved assets | D-52 §1.3 | S-19-03, S-19-05 |
| AC-2 manifest.json with hashes + metadata | D-53 | S-19-04, S-19-05 |
| AC-3 Hash verification | D-53 §2.5 | S-19-05 |
| AC-4 Audit on export | D-54 | S-19-06, V-19-03 |

---

## 9. Implementation task checklist (execution order — post plan ACCEPT)

| Order | ID | Task | Track |
|---|---|---|---|
| 1 | G-01 | Append D-52..D-54 to `DECISIONS.md` | Governance |
| 2 | G-02 | Add `BUNDLE_EXPORTED` to `AuditEventType` | Core |
| 3 | A-01 | `resolve_export_assets(run_id)` — approved version per stage | API |
| 4 | A-02 | `build_manifest_v1()` | API |
| 5 | A-03 | `stream_export_zip()` — deterministic order | API |
| 6 | A-04 | `GET /export/{pipeline_run_id}` route + 409 gate | API |
| 7 | A-05 | Append audit on successful build | API |
| 8 | W-01 | Export page + download button (COMPLETED only) | Web |
| 9 | W-02 | API client helper `downloadExport(runId)` | Web |
| 10 | T-01..T-08 | Unit tests (§10) | QA |
| 11 | T-09 | API/web regression | QA |
| 12 | V-01 | Olares verify scripts + acceptance package | Evidence |

---

## 10. Unit test plan

| ID | File | Assertion |
|---|---|---|
| T-01 | `test_export_happy_path.py` | COMPLETED run → 200, ZIP has 9 entries, PK magic |
| T-02 | `test_export_manifest.py` | Required manifest fields; 8 file entries |
| T-03 | `test_export_hashes.py` | Manifest hashes match embedded bytes |
| T-04 | `test_export_deterministic.py` | Two builds same run → same asset hashes/order |
| T-05 | `test_export_not_found.py` | Unknown run_id → 404 |
| T-06 | `test_export_not_completed.py` | AWAITING_APPROVAL → 409 |
| T-07 | `test_export_failed_run.py` | FAILED → 409 |
| T-08 | `test_export_auth.py` | No token → 401 |
| T-09 | Regression | API suite green; web vitest green |

Tests use mocked MinIO with fixture bytes; no Olares required for unit tier.

---

## 11. Risk review

| ID | Risk | Mitigation |
|---|---|---|
| R1 | Wrong STORY version (human-edit vs ai-draft) | Resolve via approval timestamp + version at gate |
| R2 | Large ZIP memory pressure | Stream ZIP; cap single-file size via existing asset limits |
| R3 | COMPLETED run missing asset | Fail loud 500; Olares full path catches |
| R4 | Scope creep to lineage UI | PR checklist §0 |
| R5 | Re-export audit noise | Accepted — each download auditable per D-54 |
| R6 | Brief vs backlog US-19 naming | Governance brief supersedes Issue 47 preview scope |

---

## 12. Governance next steps

| Step | Action |
|---|---|
| 1 | Review **this plan** → ACCEPT / AMEND / REJECT |
| 2 | On ACCEPT → authorize implementation (code changes) |
| 3 | Append D-52..D-54 to `DECISIONS.md` |
| 4 | Implement tasks §9 order 1–12 |
| 5 | Olares PASS → implementation report → closure tag `v0.6.0-us19` (proposed) |

**Implementation code remains unauthorized until this plan is ACCEPTED.**

---

## Document control

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-06-11 | Initial plan — brief ACCEPT; D-52 bundle, D-53 manifest, D-54 audit |

**Parent:** `docs/sprints/sprint-4b-us19-brief.md` (ACCEPT)

*End of document.*
