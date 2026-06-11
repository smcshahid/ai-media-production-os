# Sprint 4C — US-V02 Verification Plan

**Status:** **Olares PASS** — verification plan EXECUTED 2026-06-11 · governance closure pending.  
**Parent brief:** `docs/sprints/sprint-4c-usv02-brief.md` (**ACCEPT**)  
**Story:** US-V02 Spark Full demo acceptance validation · P0 · 2 SP  
**Baseline:** `v0.6.0-us19` (`aimpos-api:us19`, `aimpos-worker:us18`)  
**Goal:** Final Spark Full acceptance package and **M6 sign-off evidence**

**Authorization boundary:** Olares verify scripts, evidence collection, verification report, acceptance package, closure documentation. **No product code. No new APIs. No schema changes.**

---

## 0. Plan summary

| Phase | Deliverable |
|---|---|
| Pre-flight | Fresh project, ComfyUI, ffmpeg, image/tag check |
| Execute | Normative demo S-00..S-24 incl. **US-V01 path + A-01**, **VIDEO stage**, **export** |
| Durability | Worker restart procedure after terminal `COMPLETED` (SC-F05 / SC-V06) |
| Collect | SQL attestation V-01..V-12 + export inline checks |
| Package | `evidence/us-v02-verification/olares-<date>/US-V02-ACCEPTANCE-PACKAGE.md` |
| Close | Verification report + governance closure + tag `v0.7.0-usv02` (proposed) |

**Estimated wall-clock:** 60–90 min (SCRIPT regen + 2× STORYBOARD ComfyUI batches + VIDEO gen/regen + export + worker restart).

**Regression gate (local, before Olares):** API 88 · worker 39 · web 23 — no new unit tests required; baseline from US-19 closure.

**Critical D-51 difference from US-V01:** STORYBOARD approve (**S-14**) **MUST NOT** set `COMPLETED`. Terminal success occurs only after **VIDEO approve** (**S-19**).

---

## 1. Olares execution procedure

### 1.1 Environment

| Field | Value |
|---|---|
| Host | `olares@10.0.0.34` |
| Namespace | `aimpos-mwayolares` |
| API access | ClusterIP `aimpos-api:8000` via curl from Olares host |
| Auth | `Authorization: Bearer $TOKEN` |
| Postgres | `aimpos-postgres-0`; `psql -U aimpos -d aimpos_spark` |
| Secrets | `$TOKEN`, `$PGPW` sourced on Olares (same pattern as US-V01/US-19) |

### 1.2 Pre-flight (PF-01..PF-07)

| ID | Action | Pass criteria |
|---|---|---|
| PF-01 | Confirm deploy images ≥ baseline | `aimpos-api:us19`, `aimpos-worker:us18` (or tags ≥ `v0.6.0-us19`) |
| PF-02 | Alembic 0003 present | STORYBOARD multi-frame partial indexes |
| PF-03 | ComfyUI launcher `POST http://127.0.0.1:3000/api/start` | Queue HTTP 200 |
| PF-04 | API `GET /health` | postgres, redis, minio green |
| PF-05 | Create **fresh project** | `POST /projects` → new UUID; **not** prior acceptance runs |
| PF-06 | Assert no active run on project | `GET /pipeline/status` → no `RUNNING`/`AWAITING_APPROVAL` or idle |
| PF-07 | ffmpeg in worker pod | `kubectl exec deploy/aimpos-worker -- ffmpeg -version` exits 0 |

Export for evidence: `PROJECT`, `RUN_ID` (after S-03), cluster IP, image tags, start timestamp.

### 1.3 Deploy and run (operator sequence)

```bash
# From dev machine — after building/importing images on Olares:
scp deploy/k8s/usv02-verify/*.sh olares@10.0.0.34:/tmp/

# On Olares — optional image deploy if not already at us19/us18:
# API_TAR=/tmp/aimpos-api-us19.tar WORKER_TAR=/tmp/aimpos-worker-us18.tar bash /tmp/deploy_usv02.sh

# Full E2E (creates project or uses PROJECT=):
bash /tmp/run_remote.sh
```

**`run_remote.sh`** responsibilities: source secrets; create fresh project if unset; tee timestamped log to `/tmp/usv02-verify-<timestamp>.log`; invoke `verify_usv02.sh`; exit with script RC.

### 1.4 Normative execution sequence

All API calls via ClusterIP with Bearer token. Steps **S-01..S-13** mirror US-V01; **S-14+** extend for Spark Full.

| Step | HTTP / action | Capture for evidence | Pass criteria |
|---|---|---|---|
| **S-00** | ComfyUI launcher start | Log `comfyui_ready` | Queue reachable |
| **S-01** | `POST /projects` | `PROJECT` UUID | HTTP 201 |
| **S-02** | `POST /ideas` | Idea JSON | HTTP 201 |
| **S-03** | `POST /pipeline/start` | `RUN_ID`; HTTP 201 | Run created |
| **S-04** | Poll `GET /pipeline/status` | `T_story_gate` | `AWAITING_APPROVAL` / `STORY` |
| **S-05** | `GET /assets` STORY → `PUT /assets/{id}` | human-edit version | New STORY version |
| **S-06** | `POST /pipeline/approve` STORY APPROVED | Approval JSON | SCRIPT stage entered |
| **S-07** | Poll until SCRIPT gate | — | `AWAITING_APPROVAL` / `SCRIPT` |
| **S-08** | `POST /pipeline/approve` SCRIPT REJECT + note | Rationale stored | D-42 setup |
| **S-09** | `POST /pipeline/regenerate` SCRIPT | HTTP 200 | D-38, D-42 |
| **S-10** | Poll until SCRIPT gate | — | Post-regen gate |
| **S-11** | `POST /pipeline/approve` SCRIPT APPROVED | — | STORYBOARD entered |
| **S-12** | Poll STORYBOARD gate batch v1 | `SB_V1`; frame count 4 | D-43..D-45 |
| **S-12a** | `POST /pipeline/approve` STORYBOARD REJECT + note | A-01 note text | D-47 setup |
| **S-12b** | `POST /pipeline/regenerate` STORYBOARD | HTTP 200 | D-38, D-47 |
| **S-12c** | Poll STORYBOARD gate batch v2 | `SB_V2`; frame count 4 | v2 complete |
| **S-13** | `GET /assets/{frame_id}/content` | HTTP 200; PNG magic | content-read |
| **S-14** | `POST /pipeline/approve` STORYBOARD APPROVED | **`POST_SB_STATUS`** | **≠ `COMPLETED`** (D-51) |
| **S-15** | Poll until VIDEO gate | `T_video_gate` | `AWAITING_APPROVAL` / `VIDEO` |
| **S-16** | SQL + asset inspect | `VIDEO_ID`, `VIDEO_V1` | D-48 metadata |
| **S-17** | `GET /assets/{video_id}/content` | HTTP 200; MP4 `ftyp` | SC-F02 |
| **S-18** | `POST /pipeline/approve` VIDEO REJECT + note | Rejection stored | D-50 setup |
| **S-19** | `POST /pipeline/regenerate` VIDEO | HTTP 200 | D-38, D-50 |
| **S-20** | Poll until VIDEO gate (post-regen) | `VIDEO_V2` > `VIDEO_V1` | Version incremented |
| **S-21** | `POST /pipeline/approve` VIDEO APPROVED | **`FINAL_STATUS`** | **`COMPLETED`** (D-51) |
| **S-22** | Lineage SQL inline | `LINEAGE_COUNT=4` STORYBOARD→VIDEO | SC-F03 |
| **S-23** | `GET /export/{run_id}` | ZIP bytes; HTTP 200 | D-52 |
| **S-24** | Unzip + manifest + hash verify | `FILE_COUNT=9`; `HASH_VERIFY=PASS` | D-52, D-53 |
| **S-25** | SQL `BUNDLE_EXPORTED` | audit payload | D-54 |
| **S-26** | Negative export 409 (if candidate run exists) | `NEGATIVE http=409` | D-52 gate |
| **S-27** | Full SQL attestation §4 | All V-* outputs saved | AC-11, AC-12 |
| **S-28** | Worker restart procedure §6 | DR-01..08 log | SC-F05, SC-V06 |

### 1.5 Idea payload (canonical)

```json
{
  "project_id": "<PROJECT>",
  "title": "US-V02 Spark Full Acceptance",
  "paragraph": "A marine biologist on a remote station must decide whether to broadcast a discovery that could save the reef or keep it secret from corporate harvesters arriving at dawn.",
  "style_note": "cinematic"
}
```

### 1.6 Poll configuration

| Gate | Max wait | Interval | Fail on |
|---|---|---|---|
| STORY | 15 min | 15 s | `FAILED` |
| SCRIPT | 15 min | 15 s | `FAILED` |
| STORYBOARD (each batch) | 30 min | 20 s | `FAILED`; `< 4` frames at gate |
| VIDEO (initial) | 20 min | 20 s | `FAILED` |
| VIDEO (post-regen) | 10 min | 10 s | `FAILED`; version not incremented |
| Post-VIDEO approve → COMPLETED | 1 min | 5 s | Not `COMPLETED` |

### 1.7 Script layout (proposed — bash only, no product code)

```
deploy/k8s/usv02-verify/
  verify_usv02.sh          # Full E2E S-00..S-28 + inline export/SQL checks
  collect_usv02.sh         # Post-run SQL attestation → evidence/sql/
  run_remote.sh            # Source secrets; create project; tee log
  deploy_usv02.sh          # Import aimpos-api:us19 + aimpos-worker:us18; rollout restart
  prep_comfyui.sh          # Reuse or symlink US-V01 launcher pattern
  create_project.sh        # Fresh project helper
```

**Composition note:** `verify_usv02.sh` composes patterns from `usv01-verify`, `us18-verify`, and `us19-verify` into one authoritative run. Sub-scripts may delegate to shared helpers but **must not** modify product code.

### 1.8 Forbidden during execution

- Manual SQL to unblock pipeline progression
- Reusing project UUIDs from US-V01/US-18/US-19 acceptance runs as the primary attestation run
- Patching API/worker images mid-run without documenting defect protocol
- Skipping A-01 STORYBOARD regen path or VIDEO regen path

---

## 2. D-37 through D-54 attestation mapping

Integrated attestation for the **full Olares run** (Visual MVP path + VIDEO + export).

| ID | Decision | Validated at | SQL / log evidence | Pass criteria |
|---|---|---|---|---|
| **D-37** | Approved story, no branch promotion | S-05, S-06 | V-03 STORY rows; approvals STORY/APPROVED | Latest STORY is `human-edit`; no STORY insert on S-06 |
| **D-38** | Append-only regen | S-09, S-12b, S-19 | V-04, V-47, V-10 | Monotonic versions; prior hashes unchanged |
| **D-39** | `script.fountain` semantics | S-07, S-11 | V-06 partial | SCRIPT row; lineage STORY→SCRIPT |
| **D-40** | Fountain validation | S-07, S-11 | Implicit | SCRIPT stored successfully |
| **D-41** | Approved script, no promotion | S-11, S-12 | V-03 | No SCRIPT insert on S-11 |
| **D-42** | Script regen inputs | S-08, S-09 | V-04; worker log | Regen only after SCRIPT reject |
| **D-43** | Storyboard frame contract | S-12, S-12c | V-05, V-47 | Shared `version`; `frame_index` 1..4 |
| **D-44** | Batch completeness | S-12, S-12c | V-05, V-47 | Exactly 4 frames per batch |
| **D-45** | Frame count = 4 | S-12, S-12c | V-05, V-47 | `COUNT=4` per version |
| **D-46** | Approved batch, no promotion | S-14 | V-03 | STORYBOARD row count stable on S-14 |
| **D-47** | Storyboard regen inputs | S-12a, S-12b | V-47 | v1 intact; v2 new hashes; regen audit |
| **D-48** | VIDEO asset contract | S-16, S-17 | V-09 | `scene_video.mp4`; MinIO metadata; MP4 readable |
| **D-49** | Approved storyboard as video input | S-15, S-16 | V-09, V-11 | 4 STORYBOARD lineage edges to VIDEO |
| **D-50** | VIDEO regen input contract | S-18, S-19 | V-10 | Regen after VIDEO reject; v2 append-only |
| **D-51** | Terminal at VIDEO approval | **S-14, S-21** | **V-01, V-20** | S-14 status **≠ COMPLETED**; S-21 → `COMPLETED` |
| **D-52** | Export bundle contract | S-23, S-26 | Export log; V-12 | 9 entries; HTTP 200; 409 negative |
| **D-53** | Manifest contract v1 | S-24 | Export log | manifest fields + 8 file records |
| **D-54** | Export audit contract | S-25 | V-12 | `BUNDLE_EXPORTED` with required payload keys |

### 2.1 Brief AC mapping

| AC | Step(s) | Primary evidence |
|---|---|---|
| AC-1 Fresh project | PF-05, S-01 | Project UUID in log |
| AC-2 Start pipeline | S-03 | `run_id` |
| AC-3 Story edit + approve | S-05, S-06 | PUT + approval |
| AC-4 Script reject/regen/approve | S-08 – S-11 | V-04 |
| AC-5 Storyboard A-01 path | S-12a – S-14 | V-47 |
| AC-6 VIDEO reject/regen/approve | S-18 – S-21 | V-10 |
| AC-7 COMPLETED at VIDEO | S-21 | V-01, V-20 |
| AC-8 Export download | S-23 | Export log |
| AC-9 Manifest hashes | S-24 | `HASH_VERIFY=PASS` |
| AC-10 BUNDLE_EXPORTED | S-25 | V-12 |
| AC-11 Lineage to video | S-22, S-27 | V-11 |
| AC-12 Gates + model invocations | S-27 | V-02, V-08 |
| AC-13 Worker restart | S-28 | §6 DR log |

### 2.2 Success criteria mapping

| ID | Evidence ID | Source |
|---|---|---|
| SC-01 | V-01 | COMPLETED after VIDEO |
| SC-02 | V-08 | Local `model_id`; no cloud URLs |
| SC-11 | S-23..S-25 | Export + manifest + audit |
| SC-F01 | V-02 | VIDEO APPROVED row |
| SC-F02 | S-17, V-09 | MP4 content-read + metadata |
| SC-F03 | V-11 | Lineage to VIDEO |
| SC-F04 | V-05, V-47 | STORYBOARD batches match US-V01 semantics |
| SC-F05 | §6 | Worker restart at terminal |
| SC-V04 | V-04, V-05, V-09, V-10 | Full asset chain |
| SC-V05 | V-08 | Agent audit completeness |
| SC-V06 | §6 | Same as SC-F05 |
| SC-V07 | V-07 | Δ start → STORY gate < 5 min |

---

## 3. Export bundle verification (D-52)

Executed at **S-23** after terminal `COMPLETED`. Reuses US-19 verify semantics.

### 3.1 Procedure

| ID | Action | Pass criteria |
|---|---|---|
| E-01 | `GET /export/{RUN_ID}` with Bearer token | HTTP **200** |
| E-02 | Save response to `/tmp/usv02-export.zip` | Size > 0 |
| E-03 | Verify ZIP magic | First bytes `PK` (`50 4b`) |
| E-04 | Unzip to `/tmp/usv02-export/` | No errors |
| E-05 | Count files | **`FILE_COUNT=9`** exactly |
| E-06 | Verify entry paths (deterministic order) | See §3.2 |
| E-07 | Negative test (optional if candidate exists) | Non-COMPLETED run → HTTP **409** |

### 3.2 Required ZIP entries (D-52)

| # | Path | Stage |
|---|---|---|
| 1 | `manifest.json` | — |
| 2 | `idea.txt` | IDEA |
| 3 | `story.md` | STORY |
| 4 | `script.fountain` | SCRIPT |
| 5 | `frames/frame_01.png` | STORYBOARD |
| 6 | `frames/frame_02.png` | STORYBOARD |
| 7 | `frames/frame_03.png` | STORYBOARD |
| 8 | `frames/frame_04.png` | STORYBOARD |
| 9 | `scene_video.mp4` | VIDEO |

**Fail if:** extra files, directory-only entries, missing paths, or HTTP export before `COMPLETED`.

---

## 4. Manifest hash verification (D-53)

Executed at **S-24** immediately after unzip.

### 4.1 Manifest schema checks

Python (or equivalent) assertions on `/tmp/usv02-export/manifest.json`:

| Field | Expected |
|---|---|
| `manifest_version` | `"1"` |
| `pipeline_run_id` | equals `$RUN_ID` |
| `project_id` | equals `$PROJECT` |
| `exported_at` | ISO-8601 string present |
| `files` | array length **8** |

Each `files[]` entry **MUST** include: `path`, `stage`, `version`, `content_hash`, `approval_at`, `asset_id`, `size_bytes`.

### 4.2 Hash verification procedure

For each record in `manifest.files`:

1. Read `/tmp/usv02-export/{path}` bytes from disk.
2. Compute SHA-256 hex digest.
3. Assert digest equals `content_hash`.

**Pass token:** `MANIFEST=PASS` then `HASH_VERIFY=PASS`.

**Fail if:** any mismatch, missing file on disk, or hash computed over wrong path.

### 4.3 Cross-check with database (optional evidence)

Compare manifest `content_hash` values against `asset_versions.content_hash` for the approved versions referenced in export — confirms MinIO source-of-truth alignment (D-52).

---

## 5. Export audit verification (D-54)

Executed at **S-25**.

```sql
SELECT event_type,
       payload->>'manifest_hash' AS manifest_hash,
       payload->>'file_count' AS file_count,
       payload->>'zip_size_bytes' AS zip_size_bytes,
       payload->>'exported_at' AS exported_at,
       created_at
FROM audit_events
WHERE pipeline_run_id = '$RUN_ID'
  AND event_type = 'BUNDLE_EXPORTED'
ORDER BY created_at DESC
LIMIT 1;
```

| Check | Expected |
|---|---|
| Row exists | ≥ 1 `BUNDLE_EXPORTED` for run |
| `file_count` | `8` (asset files; manifest excluded from count) |
| `manifest_hash` | non-null; matches SHA-256 of `manifest.json` if recomputed |
| `zip_size_bytes` | matches downloaded ZIP size from E-02 |

---

## 6. Worker durability validation (SC-F05 / SC-V06 / AC-13)

**When:** After **S-21** (`COMPLETED`) and export attestation (**S-23..S-25**). Pipeline must be in terminal success state — **not** mid-generation.

### 6.1 Procedure

| Step | Action | Record |
|---|---|---|
| DR-01 | Capture baseline | `GET /pipeline/status?project_id=$PROJECT` → save JSON |
| DR-02 | Capture run row | V-01 SQL output |
| DR-03 | Restart worker | `kubectl rollout restart deployment/aimpos-worker -n aimpos-mwayolares` |
| DR-04 | Wait ready | `kubectl rollout status deployment/aimpos-worker --timeout=300s` |
| DR-05 | Wait 30 s | Allow worker registration |
| DR-06 | Re-poll status | `GET /pipeline/status` × 3 at 10 s intervals |
| DR-07 | Compare | `status`, `current_stage`, `run_id` unchanged |
| DR-08 | Optional SQL | `pipeline_runs` row unchanged |

### 6.2 Pass criteria

| Field | Pre-restart | Post-restart |
|---|---|---|
| `status` | `COMPLETED` | `COMPLETED` |
| `current_stage` | `null` | `null` |
| `run_id` | `$RUN_ID` | `$RUN_ID` |

**Fail action:** Log incident; do **not** manual DB repair; file defect against workflow durability; full re-run after hotfix on underlying story.

### 6.3 Out of scope

- Restart mid-`RUNNING` generation
- API or Postgres restart (worker-only per inherited SC-V06 pattern)

---

## 7. SQL attestation queries

Run via `psql` on Olares postgres pod. Substitute `$PROJECT`, `$RUN_ID`.

### V-01 — Terminal state (SC-01, AC-7, D-51)

```sql
SELECT id, status, current_stage, updated_at
FROM pipeline_runs WHERE id = '$RUN_ID';
-- Expected: status=COMPLETED, current_stage IS NULL
```

### V-20 — D-51 regression (STORYBOARD approve ≠ terminal)

```sql
-- Capture immediately after S-14 in verify log; also attest via approvals timeline:
SELECT stage, decision, created_at FROM approvals
WHERE pipeline_run_id = '$RUN_ID' AND stage = 'STORYBOARD' AND decision = 'APPROVED';
-- Verify log must show POST_SB_STATUS != COMPLETED at S-14
```

### V-02 — Human gate decisions (AC-12, SC-F01)

```sql
SELECT stage, decision, LEFT(rationale, 80) AS rationale, created_at
FROM approvals WHERE pipeline_run_id = '$RUN_ID'
ORDER BY created_at;
-- Expected minimum:
--   STORY/APPROVED, SCRIPT/REJECTED, SCRIPT/APPROVED,
--   STORYBOARD/REJECTED (A-01), STORYBOARD/APPROVED,
--   VIDEO/REJECTED, VIDEO/APPROVED
```

### V-03 — No asset write on approve (D-37, D-41, D-46, D-51)

```sql
SELECT stage, COUNT(*) FROM asset_versions
WHERE project_id = '$PROJECT'
GROUP BY stage ORDER BY stage;
-- STORYBOARD count stable across S-14; no new STORY/SCRIPT rows on approve steps
```

### V-04 — SCRIPT regen immutability (D-38, D-42)

```sql
SELECT version, branch, content_hash, created_at
FROM asset_versions
WHERE project_id = '$PROJECT' AND stage = 'SCRIPT'
ORDER BY version;
-- Expected: ≥2 rows; distinct content_hash
```

### V-05 — Storyboard batch structure (D-43, D-45)

```sql
SELECT version,
       COUNT(*) AS frame_count,
       array_agg(metadata_json->>'frame_index' ORDER BY (metadata_json->>'frame_index')::int) AS frames
FROM asset_versions
WHERE project_id = '$PROJECT' AND stage = 'STORYBOARD'
GROUP BY version ORDER BY version;
-- Expected: v1 → 4 frames; v2 → 4 frames
```

### V-47 — D-47 extension (A-01)

Same queries as US-V01 plan §4 V-47 — v1 intact, v2 created, STORYBOARD regen audit.

### V-09 — VIDEO asset + metadata (D-48, SC-F02)

```sql
SELECT version, content_hash,
       metadata_json->>'logical_filename' AS filename,
       metadata_json->>'duration_sec' AS duration_sec,
       metadata_json->>'width' AS width,
       metadata_json->>'height' AS height,
       metadata_json->>'source' AS source
FROM asset_versions
WHERE project_id = '$PROJECT' AND stage = 'VIDEO'
ORDER BY version;
-- Expected: scene_video.mp4; duration 15-30; width/height ≤480p band
```

### V-10 — VIDEO regen immutability (D-38, D-50)

```sql
SELECT version, content_hash, created_at
FROM asset_versions
WHERE project_id = '$PROJECT' AND stage = 'VIDEO'
ORDER BY version;
-- Expected: ≥2 rows after S-19; v1 hashes unchanged when v2 appended
```

### V-11 — Lineage chain to video (SC-F03, AC-11)

```sql
SELECT parent.stage AS parent_stage, child.stage AS child_stage, COUNT(*) AS edges
FROM lineage_edges le
JOIN asset_versions parent ON le.parent_id = parent.id
JOIN asset_versions child ON le.child_id = child.id
WHERE parent.project_id = '$PROJECT'
GROUP BY parent.stage, child.stage ORDER BY 1, 2;
-- Expected includes: STORY→SCRIPT, SCRIPT→STORYBOARD (8),
-- STORYBOARD→VIDEO (4 per approved batch lineage to final VIDEO version)
```

### V-08 — Local model invocations (SC-02, SC-V05)

```sql
SELECT event_type,
       payload->>'agent' AS agent,
       payload->>'stage' AS stage,
       model_id,
       created_at
FROM audit_events
WHERE pipeline_run_id = '$RUN_ID'
  AND event_type IN ('AGENT_TASK_COMPLETED', 'STAGE_STARTED')
ORDER BY created_at;
-- Expected: ≥6 AGENT_TASK_COMPLETED (story, script×2, storyboard×2, video×2)
-- All model_id non-null for AI completions
```

### V-07 — Time to first story (SC-V07)

```sql
-- Compute from log: T_story_gate - T_start < 300 seconds
```

### V-12 — Export audit (D-54)

See §5 SQL block.

---

## 8. Evidence package structure

```
evidence/us-v02-verification/
  local-<date>/
    logs/
      pytest-api-baseline.txt      # optional — 88 passed
      pytest-worker-baseline.txt     # optional — 39 passed
      vitest-baseline.txt            # optional — 23 passed
  olares-<date>/
    US-V02-ACCEPTANCE-PACKAGE.md   # Master attestation document
    logs/
      usv02-verify.log               # Full script stdout
      usv02-collect.log              # SQL attestation output
      worker-restart.log             # S-28 durability
      export-verify.log              # S-23..S-25 excerpt
      worker-tail-video.log          # VIDEO agent completion excerpts
    sql/
      v01-terminal.txt
      v02-approvals.txt
      v20-d51-storyboard-not-terminal.txt
      ...
      v12-bundle-exported.txt
    export/
      usv02-export.zip               # Downloaded bundle (optional archive)
      manifest.json                  # Extracted copy
    metadata.json                    # PROJECT, RUN_ID, images, timestamps
```

### 8.1 US-V02-ACCEPTANCE-PACKAGE.md sections

| § | Content |
|---|---|
| 1 | Verification summary (PASS/FAIL table) |
| 2 | Environment (Olares, images, fresh project UUID, run_id) |
| 3 | Brief AC mapping (AC-1..AC-13) |
| 4 | Spark Full SC-01, SC-11, SC-F01..F05 attestation |
| 5 | Inherited SC-V04..SC-V07 attestation |
| 6 | D-37..D-54 validation matrix with evidence links |
| 7 | Export bundle attestation (D-52..D-54) |
| 8 | D-51 regression (STORYBOARD ≠ COMPLETED) |
| 9 | Worker restart durability (SC-F05 / SC-V06) |
| 10 | Regression baseline (unit test counts) |
| 11 | M6 closure recommendation |

### 8.2 metadata.json template

```json
{
  "story": "US-V02",
  "date": "2026-06-11",
  "baseline_tag": "v0.6.0-us19",
  "project_id": "<uuid>",
  "run_id": "<uuid>",
  "api_image": "aimpos-api:us19",
  "worker_image": "aimpos-worker:us18",
  "amendment_a01": true,
  "storyboard_v1_version": 1,
  "storyboard_v2_version": 2,
  "video_v1_version": 1,
  "video_v2_version": 2,
  "export_file_count": 9,
  "manifest_hash_verify": "PASS",
  "final_status": "COMPLETED"
}
```

---

## 9. PASS / FAIL criteria

| Verdict | Condition |
|---|---|
| **PASS / ACCEPT** | All brief AC-1..AC-13; SC-01, SC-02, SC-11, SC-F01..F05, SC-V04..V07; D-37..D-54 incl. **D-51 regression (V-20)**; export E-01..E-07 + manifest hash verify; DR-01..08 pass; fresh project; no manual DB |
| **FAIL / REJECT** | Any check fails → defect on underlying story (US-09..US-19); hotfix + **full re-run** of US-V02 |

### 9.1 Mandatory pass tokens (verify log)

| Token | Step |
|---|---|
| `POST_SB_STATUS` not `COMPLETED` | S-14 |
| `FINAL_STATUS=COMPLETED` | S-21 |
| `MP4_MAGIC=PASS` | S-17 |
| `VIDEO_V2` > `VIDEO_V1` | S-20 |
| `LINEAGE_COUNT=4` (STORYBOARD→VIDEO) | S-22 |
| `ZIP_MAGIC=PASS` | E-03 |
| `FILE_COUNT=9` | E-05 |
| `MANIFEST=PASS` | §4.1 |
| `HASH_VERIFY=PASS` | §4.2 |
| `BUNDLE_EXPORTED_COUNT` ≥ 1 | S-25 |
| `SC-V06 worker restart: PASS` | S-28 |

### 9.2 Defect protocol

1. Capture full log + SQL outputs.
2. File defect against the **underlying feature story** (not US-V02).
3. Hotfix on authorized story branch; re-deploy images.
4. Re-run **complete** US-V02 from PF-01 (fresh project).

**M6 signed** when US-V02 governance closure ACCEPT follows Olares PASS.

---

## 10. Closure requirements

| # | Requirement | Deliverable |
|---|---|---|
| C-01 | Olares E2E PASS | `evidence/us-v02-verification/olares-<date>/logs/usv02-verify.log` with `FAIL=0` |
| C-02 | Acceptance package | `US-V02-ACCEPTANCE-PACKAGE.md` with all §8.1 sections |
| C-03 | SQL evidence | `evidence/.../sql/` directory populated |
| C-04 | Export evidence | Export log + optional `export/usv02-export.zip` |
| C-05 | Worker durability log | `worker-restart.log` |
| C-06 | Verification report | `docs/sprints/sprint-4c-usv02-verification-report.md` |
| C-07 | Governance closure ACCEPT | PO sign-off |
| C-08 | Repository commit | All evidence + docs committed |
| C-09 | Release tag | `v0.7.0-usv02` on feature-complete baseline |
| C-10 | Closure report | `docs/sprints/sprint-4c-usv02-closure-report.md` with commit SHA, tag, push confirmation |
| C-11 | README update | US-V02 **CLOSED**; Spark Full program status; M6 complete |

**No closure approval without Olares evidence** (same gate as US-V01/US-19).

---

## 11. Execution checklist

| # | Task | Owner | Done |
|---|---|---|---|
| 1 | Local regression green (88/39/23) | Dev | ☐ |
| 2 | Create `deploy/k8s/usv02-verify/` scripts | Dev | ☐ |
| 3 | PF-01..PF-07 pre-flight on Olares | Ops | ☐ |
| 4 | Execute S-00..S-28 incl. A-01 + VIDEO + export | Ops | ☐ |
| 5 | Execute DR-01..08 worker restart | Ops | ☐ |
| 6 | Run collect_usv02.sh SQL attestation | Ops | ☐ |
| 7 | Write US-V02-ACCEPTANCE-PACKAGE.md | Dev | ✅ |
| 8 | Write verification report | Dev | ✅ |
| 9 | Governance closure review | PO | ☐ |

---

## 12. Document control

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-06-11 | Initial plan — brief ACCEPT without amendment |

**Next step:** Implement `deploy/k8s/usv02-verify/` scripts (bash only) → Olares run → acceptance package → M6 closure.
