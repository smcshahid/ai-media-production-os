# Sprint 4A — US-18 Generate Short Video Clip (governance brief)

**Status:** **SUBMITTED FOR REVIEW**  
**Parent program:** [Spark Full Governance Brief](./spark-full-governance-brief.md) (**ACCEPT**)  
**Story:** US-18 "Generate short video clip" · FEAT-10 AI Short Video Generation · EPIC-05 · P0 · 8 SP  
**Prerequisites (all closed):** US-05 ✅ · US-06 ✅ · US-07 ✅ · US-08 ✅ · US-09 ✅ · US-16 ✅ · US-17 ✅ · US-V01 ✅  
**Blocks:** US-19 (video review UI + formal COMPLETED UX) · US-20 (lineage to video) · US-V02 (Spark Full acceptance)  
**Does not authorize:** US-19 web player · US-20/21 UI · export ZIP · implementation code

**Canonical source:** `GitHub Issues - Full MVP (Superseded).md` → Issue 46 `[US-18]`  
**Baseline:** `v0.4.0-usv01` (`93214fc`)

**Implementation remains unauthorized** until this brief receives governance **ACCEPT**.

---

## 0. Story classification — video generation only

US-18 adds the **VIDEO pipeline stage** and produces a **stored MP4 artifact** from the approved storyboard batch. It is **not** a review UI story, export story, or lineage UI story.

| Authorized in US-18 | Forbidden in US-18 |
|---|---|
| `PipelineStage.VIDEO` + SCR | Video review HTML5 player (US-19) |
| `run_video_agent` Temporal activity | Export ZIP / manifest (US-21) |
| FFmpeg slideshow baseline (phase 1) | Lineage graph UI (US-20) |
| ComfyUI i2v enhancement path (phase 2, optional) | Multi-scene / multi-project |
| Workflow: STORYBOARD approve → VIDEO gen → VIDEO gate | Keycloak / RBAC |
| Lineage edges frame → video (PostgreSQL) | WebSocket status |
| Olares verify scripts + evidence | Modifying Visual MVP closure records |
| Decision records D-48..D-51 (proposed) | Per-frame video approval |

---

## 1. Objective

Extend the Spark pipeline **one stage** after approved storyboard:

```
… → STORYBOARD approve → run_video_agent → AWAITING_APPROVAL / VIDEO
```

| Dimension | Intent |
|---|---|
| **User value** | A playable short video derived from approved frames — first motion artifact |
| **System value** | Minimal VIDEO stage contract; provenance from frames to MP4 |
| **Spark Full boundary** | Generation only; human approve-at-VIDEO UI deferred to US-19 |

### 1.1 Minimal viable VIDEO stage

The smallest correct increment:

1. **Workflow** continues after STORYBOARD approval (no `COMPLETED` at STORYBOARD).
2. **Worker** reads approved storyboard batch per **D-46**, produces one MP4.
3. **Asset** stored append-only at `stage=VIDEO` with metadata.
4. **Lineage** links each storyboard frame (or batch) → video.
5. **Status** lands at `AWAITING_APPROVAL` / `current_stage=VIDEO`.
6. **Audit** records generation method and duration.

No preview polish, no export, no graph visualization in US-18.

---

## 2. Source review

### 2.1 Full MVP acceptance criteria (Issue 46 — authoritative)

| # | Criterion | US-18 treatment |
|---|---|---|
| AC-1 | `scene_video` artifact | MP4 stored MinIO + `asset_versions` |
| AC-2 | MP4 15–30 s, ≤480p | FFmpeg slideshow enforces caps; i2v must respect same |
| AC-3 | Lineage frames → video | `lineage_edges` in same transaction as asset insert |
| AC-4 | `VIDEO_REVIEW` on success | Map to `AWAITING_APPROVAL` / `VIDEO` (existing status enum) |
| AC-5 | Slideshow fallback on failure | Phase 1 baseline; phase 2 i2v falls back to phase 1 |

### 2.2 Approved tasks (Issue 46 — mapped to phases)

| Backlog task | Phase | US-18 mapping |
|---|---|---|
| T-18-01 ComfyUI image-to-video workflow | **2** | Enhancement path only |
| T-18-02 `run_video_agent` activity | **1** | Core deliverable |
| T-18-03 Slideshow fallback (FFmpeg) | **1** | **Baseline — authorize first** |
| T-18-04 Store video + metadata | **1** | Core deliverable |
| T-18-05 Lineage frames → video | **1** | Core deliverable |
| T-18-06 End-to-end GPU test Olares | **1+2** | Verify scripts |

### 2.3 Workflow impact (mandatory SCR)

**Current (Visual MVP):** `_STAGE_ORDER = (STORY, SCRIPT, STORYBOARD)` → after STORYBOARD approve → `COMPLETED`.

**Target (US-18):** `_STAGE_ORDER = (STORY, SCRIPT, STORYBOARD, VIDEO)` → after STORYBOARD approve → VIDEO generation → `AWAITING_APPROVAL`/`VIDEO` → *(US-19: VIDEO approve → `COMPLETED`)*.

| Component | Change |
|---|---|
| `aimpos_core.enums.PipelineStage` | Add `VIDEO = "VIDEO"` (SCR required) |
| `SparkPipelineWorkflow` | Append VIDEO to stage loop; remove terminal `COMPLETED` until VIDEO approved |
| `sync_pipeline_status` | Emit `VIDEO` stage transitions |
| API `/pipeline/status` | Expose `VIDEO` in `stages` list |
| Web dashboard stepper | **Out of US-18** — may show unknown stage until US-19 |

**Regression note:** Visual MVP US-V01 attested `COMPLETED` at STORYBOARD. US-18 **intentionally changes** terminal semantics per Spark Full ACCEPT. US-V02 will re-attest full path.

---

## 3. Generation strategy

### 3.1 Phase 1 — FFmpeg slideshow baseline (authorize first)

**Primary shipping path.** CPU-only; no ComfyUI dependency for acceptance.

| Parameter | Value |
|---|---|
| Input | 4 PNG frames from **approved storyboard batch** (D-46) ordered by `frame_index` |
| Output | H.264 MP4 in MP4 container |
| Duration | **15–30 s** total (equal time per frame or weighted) |
| Resolution | **≤480p** (scale frames down if needed; e.g. max width 854) |
| Frame rate | 24 fps recommended |
| Codec | `libx264`; `-pix_fmt yuv420p` for browser compatibility |
| Method tag | `metadata_json.source = "slideshow"` |

**Implementation sketch (not authorized until ACCEPT):**

```
fetch_approved_storyboard_batch(project_id) → 4 PNG bytes from MinIO
→ ffmpeg -framerate N -i frame_%d.png -c:v libx264 -vf scale=... -t T out.mp4
→ validate duration/resolution → store asset + lineage
```

**Failure handling:** If FFmpeg fails or output invalid → activity retry (max 2); no partial VIDEO rows (mirror D-44 atomicity for single artifact).

### 3.2 Phase 2 — ComfyUI i2v enhancement path (stretch, same story)

**Optional upgrade** after phase 1 Olares PASS. Does **not** block US-19 if deferred.

| Parameter | Value |
|---|---|
| Workflow | Pin JSON under `configs/comfyui/workflows/` (AnimateDiff or SVD — **select during implementation plan** after Olares VRAM probe) |
| GPU | **D-08** sequencer: idle ComfyUI storyboard workloads before video i2v |
| Fallback | Any ComfyUI/queue/VRAM failure → **automatic phase 1 slideshow** (Issue 46 AC-5) |
| Method tag | `metadata_json.source = "comfyui_i2v"` |
| Audit | Record workflow name + model id when i2v succeeds |

**Governance rule:** Phase 2 failure **must not** fail the pipeline if slideshow fallback succeeds.

### 3.3 Input resolution (approved storyboard)

| Rule | Source |
|---|---|
| Use **latest approved batch** | **D-46** — `MAX(version)` STORYBOARD rows after STORYBOARD `APPROVED` |
| Exactly **4 frames** | **D-45** |
| Order by `metadata_json.frame_index` ascending | **D-43** |
| Do **not** read rejected batches | **D-47** immutability |

---

## 4. Proposed decision records

To be appended to `DECISIONS.md` at implementation start (after ACCEPT).

### D-48 — VIDEO asset contract (proposed)

**Decision:** Each successful `run_video_agent` invocation stores **one** new `asset_versions` row:

| Field | Value |
|---|---|
| `stage` | `VIDEO` |
| `branch` | `ai-draft` |
| `is_ai_generated` | `true` |
| `content_type` | `video/mp4` |
| Logical name | `scene_video.mp4` (display only; MinIO key remains content-addressed) |
| `version` | Monotonic per `(project_id, VIDEO)` — `COALESCE(MAX(version),0)+1` |
| `metadata_json` (required) | `duration_sec`, `width`, `height`, `codec`, `source` (`slideshow` \| `comfyui_i2v`), `frame_count` (4) |
| `metadata_json` (optional) | `workflow`, `fps`, `file_size_bytes` |

Storage is **append-only** — no UPDATE of prior VIDEO rows or MinIO objects. Regeneration appends `version+1`.

**Verification:** Unit test + Olares SQL single VIDEO row per generation; content-read returns MP4 magic `ftyp`.

---

### D-49 — Approved storyboard as video input (proposed)

**Decision:** `run_video_agent` **MUST** resolve video inputs exclusively from the **approved storyboard batch** per **D-46**: all `asset_versions` where `stage=STORYBOARD` at `MAX(version)` for the project, with an existing `approvals` row `stage=STORYBOARD`, `decision=APPROVED` on the active run. Frames **MUST** be loaded by `content_hash` / MinIO key — never from in-memory cache of superseded batches.

**Rationale:** Mirrors **D-41** (approved script for storyboard) and **D-42**/**D-47** input hygiene.

**Verification:** Olares verify asserts VIDEO generation occurs only after STORYBOARD approval; SQL lineage SCRIPT→STORYBOARD→VIDEO chain intact.

---

### D-50 — VIDEO regeneration input contract (proposed)

**Decision:** VIDEO-stage regeneration (`POST /pipeline/regenerate` with `stage=VIDEO`) **MUST** supply `run_video_agent` with:

1. **Approved storyboard batch** per **D-49** (unchanged frames — regen does **not** re-render storyboard in US-18), and  
2. **Latest VIDEO rejection rationale** — `rationale` from the most recent `approvals` row where `stage=VIDEO` and `decision=REJECTED` for the run.

**Prior VIDEO `asset_versions` rows and MinIO MP4 objects MUST NOT** be passed as generation input. Each regen produces a fresh MP4 at `version+1` (**D-38** append-only).

**Note:** Rejection/approve **signals** at VIDEO gate are wired in workflow; US-19 adds UI. US-18 **must** extend API `regenerate` to accept `stage=VIDEO` (501 today).

**Verification:** Reject → regen → new VIDEO version; prior MP4 hash unchanged; regen audit `REGENERATION_REQUESTED` stage=VIDEO.

---

### D-51 — Pipeline terminal moves to VIDEO approval (proposed)

**Decision:** `pipeline_runs.status = COMPLETED` **MUST NOT** be set when STORYBOARD is approved. The workflow **MUST** advance to VIDEO generation and await human approval at `current_stage=VIDEO`. **`COMPLETED` is set only after VIDEO `approve` signal** (implementation split: workflow logic in US-18; review UX in US-19).

**Rationale:** Spark Full ACCEPT; reverses Visual MVP terminal at STORYBOARD (US-17). Documented SCR-2026-002 (proposed) amends Scope Freeze §1.1 completion criterion.

**Verification:** After STORYBOARD approve, status is `AWAITING_APPROVAL`/`VIDEO`, not `COMPLETED`. US-19 verify completes path to `COMPLETED`.

---

## 5. Acceptance criteria mapping

### AC-1 — `scene_video` artifact

| Dimension | Detail |
|---|---|
| **Trigger** | STORYBOARD approved → workflow enters VIDEO stage |
| **System behavior** | `run_video_agent` produces valid MP4 bytes; stored MinIO; one `asset_versions` row |
| **Evidence** | Olares: `GET /assets/{id}/content` HTTP 200; MP4 `ftyp` magic; SQL `stage=VIDEO` |

### AC-2 — MP4 15–30 s, ≤480p

| Dimension | Detail |
|---|---|
| **System behavior** | FFmpeg `-t` enforces duration band; `-vf scale` caps dimension |
| **Evidence** | `metadata_json.duration_sec`, `width`, `height`; ffprobe in verify script optional |

### AC-3 — Lineage frames → video

| Dimension | Detail |
|---|---|
| **System behavior** | For each of 4 frame asset IDs: insert `lineage_edges` `(frame_id → video_id)` in same TX as VIDEO insert |
| **Evidence** | SQL: 4 edges STORYBOARD→VIDEO (or 1 batch edge if simplified — **prefer 4 edges** for US-20 chain) |

### AC-4 — VIDEO review gate on success

| Dimension | Detail |
|---|---|
| **System behavior** | After activity success: `sync_pipeline_status(AWAITING_APPROVAL, VIDEO)` |
| **Evidence** | Status JSON; dashboard may show REVIEW (US-19 polishes label) |

### AC-5 — Slideshow fallback on failure

| Dimension | Detail |
|---|---|
| **Phase 1** | Slideshow **is** the primary path |
| **Phase 2** | ComfyUI failure triggers slideshow; pipeline still reaches VIDEO gate |
| **Evidence** | Worker log `video_method=slideshow_fallback`; audit records fallback reason |

---

## 6. API and schema impact

### 6.1 Authorized changes (minimal)

| Surface | Change |
|---|---|
| `PipelineStage` enum | Add `VIDEO` |
| `POST /pipeline/regenerate` | Allow `stage=VIDEO` (extend from STORYBOARD pattern) |
| `GET /assets` | Return VIDEO rows (existing stage filter — no new route) |
| `GET /assets/{id}/content` | Serve `video/mp4` bytes (extend content-type handling) |
| Alembic | **Only if required** — prefer enum string storage without migration if column is varchar |

### 6.2 Explicitly no new routes in US-18

| Route | Story |
|---|---|
| `GET /lineage/{run_id}` | US-20 |
| `GET /export/{project_id}` | US-21 |
| Video-specific preview endpoint | US-19 (reuse content-read) |

---

## 7. Olares verification strategy

Mirror Visual MVP pattern: `deploy/k8s/us18-verify/` + evidence pack. **No product code in verify-only commits.**

### 7.1 Pre-flight (PF-01..PF-06)

| ID | Action | Pass |
|---|---|---|
| PF-01 | Images ≥ `us17` baseline | api + worker tags documented |
| PF-02 | FFmpeg available in worker container | `ffmpeg -version` in pod |
| PF-03 | ComfyUI probe (phase 2 only) | Optional WARN; slideshow must pass without |
| PF-04 | API health green | postgres, redis, minio |
| PF-05 | Fresh project | New UUID |
| PF-06 | Run through STORYBOARD gate | Reuse shortened path or full normative path |

### 7.2 Normative verify sequence (S-18-xx)

| Step | Action | Capture |
|---|---|---|
| S-18-01 | Complete STORYBOARD approve (4 frames) | Baseline batch version |
| S-18-02 | Assert status **not** `COMPLETED` | D-51 |
| S-18-03 | Poll until `AWAITING_APPROVAL` / `VIDEO` | `T_VIDEO_GATE` |
| S-18-04 | Assert VIDEO asset exists | asset id, version, hash |
| S-18-05 | Content-read MP4 | HTTP 200, bytes > 0, ftyp |
| S-18-06 | SQL lineage | 4 STORYBOARD→VIDEO edges |
| S-18-07 | SQL metadata | `duration_sec` ∈ [15,30], `height` ≤ 480 |
| S-18-08 | Optional: VIDEO reject + regen | D-50 new version |
| S-18-09 | Inline audit | generation event with `source` |

**Stop before VIDEO approve → COMPLETED** (that is US-19 verify scope).

### 7.3 SQL attestation (V-18-xx)

| ID | Query purpose |
|---|---|
| V-18-01 | Status = `AWAITING_APPROVAL`, `current_stage=VIDEO` |
| V-18-02 | VIDEO asset row + metadata_json |
| V-18-03 | Lineage count STORYBOARD→VIDEO = 4 |
| V-18-04 | STORYBOARD rows unchanged post-video-gen |
| V-18-05 | Audit: video generation completed |

### 7.4 Evidence layout

```
evidence/us-18-verification/
  olares-<date>/
    US-18-ACCEPTANCE-PACKAGE.md
    logs/us18-verify.log
    sql/v18-*.txt
    metadata.json
  local-<date>/logs/   # pytest baseline
```

### 7.5 Pass criteria

| Verdict | Condition |
|---|---|
| **PASS** | Phase 1 slideshow on Olares; D-48..D-51 evidenced; D-51 status not COMPLETED at STORYBOARD |
| **CONDITIONAL** | Local tests pass; Olares blocked on infra — **not sufficient for ACCEPT** |
| **FAIL** | No MP4 stored; COMPLETED still at STORYBOARD; partial lineage |

---

## 8. Explicit non-goals

US-18 **must not** include:

| Non-goal | Route to |
|---|---|
| HTML5 video player / Review UI mode | US-19 |
| Approve → `COMPLETED` UX | US-19 |
| `PipelineCompleted` audit event polish | US-19 |
| Export ZIP / manifest | US-21 |
| Lineage graph / tree UI | US-20 |
| `GET /lineage` API | US-20 |
| ComfyUI i2v as **only** path (no slideshow) | Rejected — violates AC-5 risk posture |
| Audio track / music / voiceover | Future |
| >480p, >30 s, or multi-clip edits | SCR required |
| Re-generate storyboard from VIDEO stage | Forbidden — VIDEO regen uses same frames per D-50 |
| Cloud video APIs (Runway, etc.) | Out of program scope |
| Schema redesign / Neo4j | Forbidden |
| Multi-project / create project API | Future |
| Modifying US-V01 evidence or acceptance package | Frozen |
| Gallery / script / story changes | Closed stories |

---

## 9. Dependencies and regression

### 9.1 Closed prerequisites

| Story | Contract used |
|---|---|
| US-17 | D-46 approved batch; STORYBOARD approve signal |
| US-16 | D-43/D-45 frame PNG contract |
| US-09 | Regenerate loop pattern (extend to VIDEO) |
| US-06 | GPU sequencer for phase 2 only |
| US-V01 | Baseline pipeline through STORYBOARD — **behavior change documented** |

### 9.2 Regression gates (local, pre-Olares)

| Suite | Minimum |
|---|---|
| API unit | No regression on existing tests + new VIDEO cases |
| Worker unit | `run_video_agent` unit tests with mocked FFmpeg |
| Web unit | **No change required** in US-18 (or skip-if-no-VIDEO-ui) |

---

## 10. Risks and mitigations

| ID | Risk | Mitigation |
|---|---|---|
| R18-01 | COMPLETED regression confuses dashboard | Document D-51; US-19 updates stepper |
| R18-02 | FFmpeg missing in worker image | Add to Dockerfile in implementation; PF-02 |
| R18-03 | MP4 too large for MinIO/browser | 480p/30s cap; content-read streaming |
| R18-04 | i2v blocks story delivery | Phase 2 optional; slideshow always available |
| R18-05 | Temporal history non-determinism | Fresh run for verify; follow US-09 fix pattern |
| R18-06 | Scope creep into US-19 UI | This §8 non-goals; governance review |

---

## 11. Implementation phases (post-ACCEPT)

| Phase | Scope | Closure |
|---|---|---|
| **1** | D-48..D-51 + slideshow + workflow VIDEO stage + verify | US-18 ACCEPT + tag `v0.5.0-us18` (proposed) |
| **2** | ComfyUI i2v + fallback | Same story amendment or `US-18b` if split |

**Estimated effort:** Phase 1 ≈ 5–6 SP · Phase 2 ≈ +3 SP (hardware-dependent)

---

## 12. Governance next steps

| Step | Action |
|---|---|
| 1 | Review this brief → **ACCEPT** / **ACCEPT WITH AMENDMENT** / **REJECT** |
| 2 | File SCR-2026-002: VIDEO stage + COMPLETED move (D-51) |
| 3 | Author implementation plan `sprint-4a-us18-implementation-plan.md` |
| 4 | Append D-48..D-51 to `DECISIONS.md` on implementation start |
| 5 | **No code** until step 1 ACCEPT |

---

## Document control

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-06-11 | Initial brief — Spark Full US-18 |

**Parent:** `docs/sprints/spark-full-governance-brief.md` (ACCEPT)

*End of document.*
