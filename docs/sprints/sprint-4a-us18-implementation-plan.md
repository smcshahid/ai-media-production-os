# Sprint 4A — US-18 Implementation Plan

**Status:** **AUTHORIZED FOR PLANNING** — implementation code **not authorized** until governance ACCEPT of this plan  
**Parent brief:** `docs/sprints/sprint-4a-us18-brief.md` (**ACCEPT** 2026-06-11)  
**Story:** US-18 Generate short video clip · FEAT-10 · EPIC-05 · P0 · 8 SP  
**Baseline:** `v0.4.0-usv01` (`93214fc`)  
**Decision records:** **D-48** through **D-51** — append to `DECISIONS.md` at **implementation start** (after this plan ACCEPT)  
**SCR:** **SCR-2026-002** (proposed) — add `VIDEO` stage; move terminal `COMPLETED` to VIDEO approval

---

## 0. Implementation summary

US-18 adds the **VIDEO pipeline stage** and **`run_video_agent`** activity. Phase 1 ships **FFmpeg slideshow** (CPU baseline); Phase 2 adds **ComfyUI i2v** with mandatory slideshow fallback. **STORYBOARD approve no longer terminates the run** — workflow advances to VIDEO generation, then **`AWAITING_APPROVAL` / `VIDEO`**. **`COMPLETED` occurs only on VIDEO approve** (D-51).

| Layer | Net-new | Reuse |
|---|---|---|
| `aimpos-core` | `PipelineStage.VIDEO`, `AssetStage.VIDEO` | Existing enums pattern |
| API | Extend `POST /pipeline/regenerate` (VIDEO); extend `GET /assets/{id}/content` (MP4) | `POST /pipeline/approve` (stage-agnostic); status routes |
| Temporal workflow | Append `VIDEO` to `_STAGE_ORDER`; `run_video_agent` in loop | Approve/reject/regenerate loop (US-09); stage-agnostic signals |
| Worker | `run_video_agent`, `store_video_asset()`, `fetch_approved_storyboard_batch()`, FFmpeg slideshow, optional i2v | `gpu/sequencer`, audit helpers, `insert_lineage_edge` |
| Web | — | **No changes** (US-19 video player) |
| DB schema | Prefer **no migration** — `stage` columns are varchar; add `VIDEO` value only | `asset_versions`, `lineage_edges`, `approvals`, `audit_events` |
| Config | Optional `configs/comfyui/workflows/` i2v JSON (Phase 2) | Existing compose worker image + **add FFmpeg** |
| Verify | `deploy/k8s/us18-verify/` | US-V01 / US-16 verify patterns |

**Estimated effort:** Phase 1 ≈ 5–6 SP · Phase 2 ≈ +3 SP · ~4–6 days Phase 1

### Explicitly out of scope (US-18)

Export · publishing · lineage UI · realtime/WebSocket updates · collaboration · audio generation · video editing · HTML5 review player (US-19) · ZIP manifest (US-21) · `GET /lineage` (US-20)

---

## 1. D-48 — VIDEO asset contract

**Record in `DECISIONS.md` as D-48** at implementation start.

### 1.1 Filename convention

| Field | Value |
|---|---|
| Logical artifact name | **`scene_video.mp4`** |
| Purpose | Human-readable label in docs, export manifest (future US-21), and acceptance evidence |
| Bytes identity | Content-addressed SHA-256 hash (same as all assets) |
| MinIO path | **`{project_id}/VIDEO/{content_hash}`** via existing `build_object_key()` — filename is **not** a path segment |

### 1.2 Storage semantics

| Field | Value |
|---|---|
| `asset_versions.stage` | **`VIDEO`** (`AssetStage.VIDEO`) |
| `asset_versions.branch` | **`ai-draft`** |
| `asset_versions.is_ai_generated` | **`true`** |
| `asset_versions.pipeline_run_id` | Active run id (same as STORY/SCRIPT/STORYBOARD) |
| `asset_versions.version` | Monotonic per `(project_id, VIDEO)` — see §1.4 |
| MinIO key | `{project_id}/VIDEO/{content_hash}` |
| MinIO `content_type` | **`video/mp4`** |
| Validation before persist | MP4 magic bytes (`ftyp` at offset 4); non-zero size; duration/resolution within caps (§1.3) |

**Atomicity:** One successful generation produces **exactly one** new `asset_versions` row and **one** MinIO object. Failed attempts leave **zero** VIDEO rows (mirror D-44 single-artifact rule).

### 1.3 Required metadata (`metadata_json`)

| Key | Type | Rule |
|---|---|---|
| **`duration_sec`** | number | **15.0 ≤ duration_sec ≤ 30.0** (inclusive) |
| **`width`** | integer | **≤ 854** (480p band max width; height derived preserving aspect) |
| **`height`** | integer | Computed; **≤ 480** typical for 16:9 downscale |
| **`codec`** | string | e.g. `"h264"` |
| **`source`** | string | **`"slideshow"`** \| **`"comfyui_i2v"`** |
| **`frame_count`** | integer | **4** (frames consumed from approved batch) |
| **`fps`** | number | Optional; default **24** for slideshow |

### 1.4 Optional metadata

| Key | When |
|---|---|
| `workflow` | Phase 2 i2v — pinned workflow name |
| `file_size_bytes` | Always if cheap to compute |
| `fallback_from` | When i2v failed and slideshow used — value `"comfyui_i2v"` |
| `fallback_reason` | Truncated error string from i2v attempt |

### 1.5 Versioning behavior

| Behavior | Rule |
|---|---|
| Version assignment | `next_version = COALESCE(MAX(version), 0) + 1` for `(project_id, VIDEO)` |
| Append-only | Each generation/regeneration appends **one** new row + MinIO object |
| In-place update | **Forbidden** — no UPDATE of VIDEO rows or MP4 objects |
| Approve | **No asset write** — `approvals` row only (mirror D-37/D-41/D-46) |
| Regeneration | Fresh MP4 at `version+1`; prior versions immutable (**D-50**) |

### 1.6 Content-read (API)

Extend `GET /assets/{id}/content` to serve **`VIDEO`** stage with `media_type=video/mp4` (same pattern as STORYBOARD PNG in US-17). **No new route.**

### 1.7 Resolution query (evidence)

```sql
SELECT id, version, content_hash, minio_key, metadata_json
FROM asset_versions
WHERE project_id = :project_id AND stage = 'VIDEO'
ORDER BY version DESC
LIMIT 1;
```

---

## 2. D-49 — Input contract (approved storyboard batch only)

**Record in `DECISIONS.md` as D-49** at implementation start.

### 2.1 Authoritative input source

`run_video_agent` **MUST** resolve inputs **only** from the **approved storyboard batch** per **D-46**:

| Gate | Requirement |
|---|---|
| Approval exists | `approvals` row: `stage=STORYBOARD`, `decision=APPROVED`, `pipeline_run_id=active run` |
| Batch version | All frames at **`MAX(version)`** for `(project_id, STORYBOARD)` |
| Frame count | **Exactly 4** rows (**D-45**) |
| Frame order | `metadata_json.frame_index` ascending **1, 2, 3, 4** |
| Bytes source | Load PNG from MinIO via each row's `content_hash` / `minio_key` |

### 2.2 Forbidden inputs

| Forbidden | Rationale |
|---|---|
| Rejected or superseded STORYBOARD batches | D-47 immutability |
| Prior VIDEO MP4 bytes as generation input | D-50 hygiene |
| SCRIPT or STORY text injected into ComfyUI i2v prompt (Phase 2) | Out of scope; slideshow uses frames only |
| User-uploaded video | Out of scope |
| Partial frame subset | Whole-batch semantics |

### 2.3 Worker helper

**New:** `fetch_approved_storyboard_batch(settings, project_id, pipeline_run_id) -> ApprovedStoryboardBatch`

Returns: ordered list of 4 `{asset_version_id, content_hash, minio_key, frame_index}` + batch `version`.

**Preconditions (raise before generation):**

1. STORYBOARD `APPROVED` approval on run  
2. SQL returns exactly 4 frames at latest version  
3. Each MinIO `get_object` succeeds and passes PNG validation (reuse `validate_storyboard_frame`)

### 2.4 Resolution SQL (document in implementation report)

```sql
-- Prerequisite: STORYBOARD approved on this run
SELECT 1 FROM approvals
WHERE pipeline_run_id = :run_id AND stage = 'STORYBOARD' AND decision = 'APPROVED';

WITH latest AS (
  SELECT COALESCE(MAX(version), 0) AS v
  FROM asset_versions
  WHERE project_id = :project_id AND stage = 'STORYBOARD'
)
SELECT av.id, av.version, av.content_hash, av.minio_key,
       (av.metadata_json->>'frame_index')::int AS frame_index
FROM asset_versions av, latest
WHERE av.project_id = :project_id
  AND av.stage = 'STORYBOARD'
  AND av.version = latest.v
ORDER BY frame_index;
-- Expected: 4 rows, frame_index 1..4
```

---

## 3. D-50 — Regeneration contract

**Record in `DECISIONS.md` as D-50** at implementation start.

### 3.1 Regeneration inputs

VIDEO-stage `POST /pipeline/regenerate` with `stage=VIDEO` **MUST** supply `run_video_agent`:

| # | Input | Source |
|---|---|---|
| 1 | **Approved storyboard batch** | **D-49** — same 4 PNG frames; regen **does not** re-run storyboard |
| 2 | **Latest VIDEO rejection rationale** | `fetch_latest_video_rejection_rationale()` — latest `approvals.rationale` where `stage=VIDEO` AND `decision=REJECTED` for the run |

### 3.2 Forbidden on regen

- Reading prior VIDEO `asset_versions` or MinIO MP4 into the generator input  
- Mutating STORYBOARD rows or re-invoking `run_storyboard_agent`  
- Branch promotion or copy-to-main  

### 3.3 Append-only versioning

| Event | Asset effect |
|---|---|
| Initial VIDEO generation | `version = 1` (or `MAX+1`) |
| Each VIDEO regen after reject | New row at **`version+1`**; new MinIO object; new content_hash |
| Prior VIDEO versions | **Immutable** |

### 3.4 API extension

Add **`PipelineStage.VIDEO`** to `_SUPPORTED_REGENERATE_STAGES` in `api/app/routes/pipeline.py` (mirror STORYBOARD extension in US-17).

**Preconditions:** `AWAITING_APPROVAL` / `current_stage=VIDEO`; latest stage approval `REJECTED`; regen count ≤ 3 (US-09 cap).

### 3.5 Worker helper

**New:** `fetch_latest_video_rejection_rationale(settings, pipeline_run_id) -> str | None` in `worker/app/tools/assets.py` — mirror `fetch_latest_storyboard_rejection_rationale`.

**Phase 1 usage:** Rationale stored in audit (`REGENERATION_REQUESTED` payload); slideshow generator may optionally adjust crossfade timing caption — **not required for MVP**. Minimum: audit trail only.

### 3.6 Workflow wiring

Extend `_run_stage_generation` for `PipelineStage.VIDEO`:

```python
await workflow.execute_activity(
    run_video_agent,
    args=[project_id, run_id, rejection_note],
    start_to_close_timeout=timedelta(minutes=10),  # slideshow; amend if i2v
    retry_policy=RetryPolicy(maximum_attempts=2),
)
```

Pass `rejection_note` from `_state.last_rejection_note` on regen loop (same as STORYBOARD in US-17).

### 3.7 Audit

On regen request: existing `REGENERATION_REQUESTED` with `stage=VIDEO`.  
On successful regen: `ASSET_STORED` + `VIDEO_GENERATED` (or `AGENT_TASK_COMPLETED` with `agent=cinematography_video`) including `source`, `version`, `duration_sec`.

---

## 4. D-51 — Completion contract

**Record in `DECISIONS.md` as D-51** at implementation start. Requires **SCR-2026-002**.

### 4.1 Terminal semantics change

| Event | Visual MVP (prior) | US-18 (target) |
|---|---|---|
| STORYBOARD approve | Workflow exits loop → **`COMPLETED`** | Workflow **continues** to VIDEO stage |
| After `run_video_agent` success | — | **`AWAITING_APPROVAL` / `VIDEO`** |
| VIDEO approve | — | Workflow exits loop → **`COMPLETED`** |
| VIDEO reject | — | Stays **`AWAITING_APPROVAL` / `VIDEO`**; enables regen |

### 4.2 Workflow change

**File:** `worker/app/temporal/workflows/spark_pipeline.py`

| Change | Detail |
|---|---|
| `_STAGE_ORDER` | `(STORY, SCRIPT, STORYBOARD, **VIDEO**)` |
| Import | `run_video_agent` activity |
| Tail | Unchanged pattern: after **all** stages approved, `sync_pipeline_status(COMPLETED)` |

Because `COMPLETED` runs after the full loop, adding VIDEO automatically delays completion until VIDEO approve — **provided** STORYBOARD approve no longer short-circuits. Current code already completes after all stages in `_STAGE_ORDER`; **only enum extension required** for D-51 semantics.

### 4.3 Status transitions (VIDEO stage)

```
STORYBOARD approve signal
  → sync RUNNING / VIDEO
  → run_video_agent
  → sync AWAITING_APPROVAL / VIDEO   ← AC-4 VIDEO_REVIEW gate

VIDEO reject (+ note)
  → AWAITING_APPROVAL / VIDEO (unchanged)
  → regenerate → RUNNING / VIDEO → run_video_agent → AWAITING_APPROVAL / VIDEO

VIDEO approve
  → stage completes → sync COMPLETED / current_stage=null
```

### 4.4 Dashboard / web impact

| Surface | US-18 behavior |
|---|---|
| API `GET /pipeline/status` | Exposes `VIDEO` in `stages`; `current_stage=VIDEO` at gate |
| Web dashboard stepper | May show unknown/4th step until **US-19** — **acceptable** |
| Review page | No VIDEO mode in US-18 — creator uses API/curl for verify |

### 4.5 Regression note

US-V01 attested `COMPLETED` at STORYBOARD. US-18 **intentionally breaks** that terminal point. **US-V02** will re-attest full Spark Full path.

---

## 5. Fallback behavior

### 5.1 Phase 1 — Slideshow baseline (primary)

| Step | Behavior |
|---|---|
| 1 | `fetch_approved_storyboard_batch()` → 4 PNG byte buffers |
| 2 | Write temp frame files or pipe to FFmpeg |
| 3 | Encode H.264 MP4: **24 fps**, total **15–30 s**, scale to **≤480p** |
| 4 | `validate_video_mp4()` — magic, duration, dimensions |
| 5 | `store_video_asset()` — MinIO + DB + lineage in one transaction |
| 6 | Audit `source=slideshow` |

**FFmpeg pin (implementation):**

```bash
ffmpeg -y -framerate 24 -i frame_%01d.png \
  -vf "scale='min(854,iw)':-2" \
  -c:v libx264 -pix_fmt yuv420p -movflags +faststart \
  -t 20 output.mp4
```

Duration: `-t` in **[15, 30]**; if 4 frames at 24fps = 6s, use **hold/frame repeat** or **min duration 15s** (e.g. `-loop 1 -t 3.75` per frame → 15s total).

### 5.2 Phase 2 — ComfyUI i2v with fallback

| Step | Behavior |
|---|---|
| 1 | Attempt `gpu_sequencer` idle + ComfyUI i2v workflow |
| 2 | On **any** failure (queue, timeout, VRAM, invalid output, validation fail) | Log warning; **do not fail activity yet** |
| 3 | Invoke **§5.1 slideshow** on same 4 frames |
| 4 | Set `metadata_json.source=slideshow`, `fallback_from=comfyui_i2v`, `fallback_reason=<truncated>` |
| 5 | Audit records fallback |

### 5.3 Success criteria for fallback path

| Check | Expected |
|---|---|
| i2v fails | Worker log contains `video_i2v_failed` + reason |
| Slideshow runs | Worker log contains `video_method=slideshow` |
| Pipeline | Reaches **`AWAITING_APPROVAL` / `VIDEO`** — **not** `FAILED` |
| Asset | Valid MP4 stored; D-48 metadata satisfied |
| Lineage | 4 STORYBOARD→VIDEO edges |

**Governance rule:** Fallback success **is** acceptance for AC-5. i2v-only failure without slideshow success **is** activity failure (retry → `FAILED` after exhaustion).

### 5.4 When entire activity fails

| Condition | Behavior |
|---|---|
| Both i2v and slideshow fail | Temporal retry (max 2); then `_mark_video_failed` → `FAILED` |
| Partial VIDEO row | **Forbidden** — zero rows on failure |
| STORYBOARD rows after failure | **Unchanged** |

---

## 6. Approval behavior (entire video)

US-18 wires **batch-level** VIDEO approval semantics in workflow + API. **Review UI is US-19**; verify scripts use curl.

### 6.1 Approve entire video

| Rule | Implementation |
|---|---|
| Scope | **One video artifact** — the latest `VIDEO` row at `MAX(version)` |
| API | `POST /pipeline/approve` `{ stage: "VIDEO", decision: "APPROVED" }` |
| Data | One `approvals` row: `stage=VIDEO`, `decision=APPROVED` |
| Asset write | **None** on approve (mirror D-46) |
| Workflow | `approve` signal → VIDEO stage completes → **`COMPLETED`** (D-51) |
| Per-segment / per-frame approve | **Forbidden** |

### 6.2 Reject entire video

| Rule | Implementation |
|---|---|
| Scope | Whole MP4 — single rejection |
| API | `POST /pipeline/approve` `{ stage: "VIDEO", decision: "REJECT", note: "..." }` |
| Data | One `approvals` row: `stage=VIDEO`, `decision=REJECTED`, `rationale=note` |
| Status after reject | **`AWAITING_APPROVAL` / `VIDEO`** |
| Regenerate | `POST /pipeline/regenerate` `{ stage: "VIDEO" }` per **D-50** |
| Re-run storyboard | **Forbidden** |

### 6.3 Pre-approve integrity

Before accepting approve at VIDEO gate, workflow/API assume:

- Exactly **one** latest VIDEO asset exists for the run (or at project `MAX(version)`)  
- Generation activity completed successfully  
- Status is `AWAITING_APPROVAL` / `VIDEO`

### 6.4 US-19 boundary

| In US-18 | In US-19 |
|---|---|
| Approve/reject/regenerate **signals** work | HTML5 `<video>` player on Review page |
| `GET /assets/{id}/content` serves MP4 | Poll to `COMPLETED` UX |
| Dashboard may not render VIDEO step | Stepper label "Video review" |
| `PipelineCompleted` audit | Formal completion UX copy |

---

## 7. Olares verification strategy

**Scripts:** `deploy/k8s/us18-verify/` (author at implementation)  
**Evidence:** `evidence/us-18-verification/olares-<date>/`

### 7.1 Pre-flight

| ID | Check | Pass |
|---|---|---|
| PF-01 | Images `aimpos-api:us18`, `aimpos-worker:us18` | Documented tags |
| PF-02 | `ffmpeg -version` in worker pod | Exit 0 |
| PF-03 | API `/health` | All green |
| PF-04 | Fresh project | New UUID |
| PF-05 | Baseline regression | API/worker/web unit counts documented |

### 7.2 Normative sequence

| Step | Action | Evidence |
|---|---|---|
| S-18-00 | Run pipeline through STORYBOARD gate | Reuse US-V01 subset or full path |
| S-18-01 | STORYBOARD batch approve | **Assert status ≠ COMPLETED** (D-51) |
| S-18-02 | Poll until `AWAITING_APPROVAL` / `VIDEO` | `T_VIDEO_GATE` timestamp |
| S-18-03 | List VIDEO assets | `version=1`, `source=slideshow` |
| S-18-04 | `GET /assets/{id}/content` | HTTP 200; MP4 `ftyp` |
| S-18-05 | SQL V-18-03 lineage | 4 edges STORYBOARD→VIDEO |
| S-18-06 | VIDEO reject + note | `approvals` REJECTED |
| S-18-07 | VIDEO regenerate | `version=2`; new hash |
| S-18-08 | VIDEO approve | **`COMPLETED`** (D-51) |
| S-18-09 | Optional worker restart at COMPLETED | SC-V06 pattern |

**Phase 2 addendum:** Log attestation that i2v attempted and fallback used when forcing i2v failure.

### 7.3 SQL attestation

| ID | Query | Expected |
|---|---|---|
| V-18-01 | Post-STORYBOARD approve status | Not `COMPLETED`; eventually `VIDEO` gate |
| V-18-02 | Latest VIDEO row + metadata | `duration_sec` ∈ [15,30]; `height` ≤ 480 |
| V-18-03 | Lineage STORYBOARD→VIDEO | **4** edges |
| V-18-04 | STORYBOARD count post-video | Unchanged (still 8 if US-V01 path) |
| V-18-05 | VIDEO regen audit | `REGENERATION_REQUESTED` stage=VIDEO |
| V-18-06 | Terminal after VIDEO approve | `COMPLETED` |

### 7.4 Pass / fail

| Verdict | Condition |
|---|---|
| **PASS** | Slideshow MP4 on Olares; D-48..D-51 evidenced; D-51 COMPLETED only after VIDEO approve |
| **CONDITIONAL** | Local tests only — **insufficient for ACCEPT** |
| **FAIL** | COMPLETED at STORYBOARD; no MP4; partial lineage |

### 7.5 Files

```
deploy/k8s/us18-verify/
  verify_us18.sh
  collect_us18.sh
  run_remote.sh
  create_project.sh          # reuse or symlink usv01 pattern

evidence/us-18-verification/olares-<date>/
  US-18-ACCEPTANCE-PACKAGE.md
  logs/us18-verify.log
  sql/v18-*.txt
  metadata.json
```

---

## 8. Acceptance criteria traceability

| AC | Contract | Phase | Verification |
|---|---|---|---|
| AC-1 scene_video | D-48 | 1 | V-18-02, S-18-04 |
| AC-2 15–30s ≤480p | D-48 metadata | 1 | V-18-02 |
| AC-3 lineage frames→video | D-49 + store | 1 | V-18-03 |
| AC-4 VIDEO review gate | D-51 mid-pipeline | 1 | S-18-02 |
| AC-5 slideshow fallback | §5 | 1+2 | S-18-03 source=slideshow; phase 2 fallback log |

---

## 9. Implementation task checklist (execution order — post plan ACCEPT)

| Order | ID | Task | Track |
|---|---|---|---|
| 1 | G-01 | SCR-2026-002 + append D-48..D-51 to `DECISIONS.md` | Governance |
| 2 | E-01 | Add `VIDEO` to `PipelineStage` + `AssetStage` | Core |
| 3 | W-01 | Extend `_STAGE_ORDER`; wire `run_video_agent` | Workflow |
| 4 | A-01 | `fetch_approved_storyboard_batch()` | Worker |
| 5 | A-02 | `validate_video_mp4()` | Worker |
| 6 | A-03 | `render_slideshow_mp4()` (FFmpeg) | Worker |
| 7 | A-04 | `store_video_asset()` + lineage ×4 | Worker |
| 8 | A-05 | `run_video_agent` activity | Worker |
| 9 | A-06 | `fetch_latest_video_rejection_rationale()` | Worker |
| 10 | P-01 | Extend regenerate + content-read for VIDEO | API |
| 11 | D-01 | Ensure FFmpeg in worker Dockerfile | Deploy |
| 12 | T-01..T-08 | Unit tests (slideshow mock, D-51 status) | QA |
| 13 | T-09 | API/worker/web regression | QA |
| 14 | V-01 | Olares verify + acceptance package | Evidence |
| 15 | C-01 | *(Phase 2)* ComfyUI i2v workflow + fallback | Worker |

---

## 10. Unit test plan

| ID | File | Assertion |
|---|---|---|
| T-01 | `test_video_slideshow.py` | 4 PNGs → MP4; duration in band |
| T-02 | `test_video_validate.py` | Rejects non-MP4, wrong duration |
| T-03 | `test_video_store.py` | One row + 4 lineage edges; rollback on fail |
| T-04 | `test_video_fetch_batch.py` | Requires STORYBOARD APPROVED; exactly 4 frames |
| T-05 | `test_video_activity.py` | Happy path → AWAITING_APPROVAL sync |
| T-06 | `test_video_regen.py` | Reject + regen → version 2 |
| T-07 | `test_spark_pipeline_video.py` | STORYBOARD approve → not COMPLETED until VIDEO approve |
| T-08 | `test_video_i2v_fallback.py` | *(Phase 2)* i2v mock fail → slideshow success |
| T-09 | Regression | API + worker + web suites green |

---

## 11. Risk review

| ID | Risk | Mitigation |
|---|---|---|
| R1 | COMPLETED regression breaks dashboard | D-51 docs; US-19 fixes stepper |
| R2 | FFmpeg missing in container | D-01 Dockerfile; PF-02 |
| R3 | Duration < 15s with 4 frames | Explicit per-frame hold in FFmpeg |
| R4 | i2v blocks delivery | Phase 2 optional; §5 fallback mandatory |
| R5 | Temporal non-determinism on enum change | Fresh Olares run; no in-flight Visual MVP runs |
| R6 | Scope creep to US-19 UI | PR checklist §0 out-of-scope |
| R7 | MP4 content-read size | 480p/30s cap; streaming response |

---

## 12. Governance next steps

| Step | Action |
|---|---|
| 1 | Review **this plan** → ACCEPT / AMEND / REJECT |
| 2 | On ACCEPT → authorize implementation (code changes) |
| 3 | File SCR-2026-002 in `DECISIONS.md` or SCR log |
| 4 | Implement Phase 1 tasks §9 order 1–14 |
| 5 | Olares PASS → implementation report → closure tag `v0.5.0-us18` (proposed) |

**Implementation code remains unauthorized until this plan is ACCEPTED.**

---

## Document control

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-06-11 | Initial plan — brief ACCEPT |

**Parent:** `docs/sprints/sprint-4a-us18-brief.md` (ACCEPT)

*End of document.*
