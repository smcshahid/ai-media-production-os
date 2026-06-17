# Scope Change Request — Multi-Scene Pipeline Extension

**SCR ID:** SCR-2026-002 (proposed)  
**Date:** 2026-06-17  
**Status:** **DRAFT — For governance review**  
**Requestor:** Product Architect  
**Baseline release:** `v0.13.0-phase3d`  
**Authority:** `MVP Scope Freeze.md` §11 · `PHASE-NEXT-RECOMMENDATION.md`

---

## Summary

Authorize extension of the AIMPOS-Spark pipeline from **one scene per script** to a **bounded multi-scene pilot (2–3 scenes)** per production run, with scene-scoped storyboard batches, videos, export manifest v2, and extended Temporal workflow — while preserving single-scene regression path.

**Recommendation:** **Option 1 — Proceed with 2–3 scene pilot** (Section 8).

**Stop-condition evaluation:** No platform redesign required. Lineage/history can support scene semantics via `metadata_json` (precedent: D-43 `frame_index`). Migration risk is **low** (additive metadata, backward-compatible read paths).

---

## 1. Business justification

### 1.1 Why multi-scene matters

| Stakeholder need | Current state | With multi-scene |
|------------------|---------------|------------------|
| Episodic / serial content | One 15–30s clip per run | 2–3 connected scenes per production |
| Creator output value | ~1 minute total video max | ~2–6 minutes (scenes × video duration) |
| Competitive positioning | Demo / proof platform | Short-form series prototype |
| Business Capability 3.1 | **Deferred** | Partial delivery (script breakdown) |

### 1.2 Evidence from product usage

| Evidence | Source | Implication |
|----------|--------|-------------|
| 12+ pipeline runs on **one project** | Phase 3B acceptance | Iteration validated; scale limit is content model not stability |
| 447 cumulative audit events (Olares) | Phase 3B/3C | Heavy verification; platform ready for scope expansion |
| US-V01: 2× SCRIPT regen, 2× STORYBOARD batch | Visual MVP closure | Creators **do** iterate versions — multi-scene extends iteration axis |
| Phase 3B US-30 diff driven by PO regen pain | Phase 3B closure | Review UX exists for text; visual stages lack scene-level compare |
| `#1 creator bottleneck = single scene` | PHASE-NEXT-RECOMMENDATION | Post-3D assessment; deployment no longer binding |
| Fountain validator **hard-rejects** `scene_count != 1` | D-40, `validate_fountain()` | **Explicit code enforcement** of single-scene — SCR required to change |
| Export ZIP fixed 9 files, 1 video | D-52 | Product contract assumes one scene |

### 1.3 Expected creator value

| Metric | Estimate | Confidence |
|--------|----------|------------|
| Output duration | 2–3× per run | High |
| Use cases unlocked | Short skits, multi-beat ads, mini-episodes | Medium |
| Time to complete run | 2–3× GPU wall-clock | High (linear with scenes) |
| Reduced external editing | Fewer manual joins in NLE | Medium |

**Value hypothesis:** Creators who complete one-scene runs successfully will produce **more publishable content per session** without leaving AIMPOS — the primary post-3D value lever.

---

## 2. Domain model impact

### 2.1 Entity analysis

| Entity | Current semantics | Multi-scene impact | Change type |
|--------|-------------------|-------------------|-------------|
| **Project** | One seeded project per deployment | Unchanged at pilot | None |
| **PipelineRun** | One linear run; `current_stage` is global enum | Add optional `scene_index` / `total_scenes` in run metadata or derive from workflow | **Extend** (metadata or workflow state) |
| **Asset (AssetVersion)** | Versioned per `(project_id, stage)`; STORYBOARD uses `frame_index` in metadata | Add **`scene_index`** (1-based) in `metadata_json` for SCRIPT, STORYBOARD, VIDEO | **Extend** (metadata convention) |
| **Story** | Single treatment for whole production | Story covers **all scenes** (one STORY asset) OR per-scene story segments — **pilot: one STORY, multi-scene script** | **Semantic** (agent prompt) |
| **Script** | Exactly **1** Fountain scene (D-40) | **2–3** scenes in one `script.fountain` OR one script asset per scene — **pilot: one file, N scenes** | **Contract change** |
| **Storyboard** | 4 frames per batch at shared `version` (D-43) | **4 frames per scene**; `metadata_json.scene_index` + `frame_index` | **Extend** |
| **Video** | One `scene_video.mp4` per run (D-48) | **One MP4 per scene** at distinct versions or paths | **Extend** |
| **Approval** | One approval per **stage** per run | Approve script (all scenes) once; storyboard/video **per scene** OR batch — **pilot: script once; storyboard/video per scene loop** | **Extend** |
| **LineageEdge** | Parent→child asset graph | Edges remain; scene boundary via metadata on nodes | **Read model** |
| **AuditEvent** | Append-only; stage in payload | Add `scene_index` to payload when applicable | **Extend** |

### 2.2 Recommended scene model (pilot)

```
Project
  └── PipelineRun
        ├── STORY (1 asset, whole production)
        ├── SCRIPT (1 asset, 2–3 Fountain scenes)
        └── For each scene_index in 1..N:
              ├── STORYBOARD batch (4 frames, scene_index in metadata)
              ├── VIDEO (1 MP4, scene_index in metadata)
              └── Approvals at SCRIPT (once), STORYBOARD (per scene), VIDEO (per scene)
```

**Precedent:** STORYBOARD already uses batch metadata (`frame_index`, `frame_count`) without schema migration beyond 0003 partial indexes. Scene index follows same pattern.

### 2.3 Fountain / script contract change

**Current (D-40):** `scene_count != 1` → validation failure.

**Proposed (pilot):** `2 <= scene_count <= 3` → pass; each scene has heading + dialogue.

---

## 3. Architecture impact

### 3.1 Temporal workflows

| Area | Current | Change |
|------|---------|--------|
| `SparkPipelineWorkflow` | Linear loop: STORY → SCRIPT → STORYBOARD → VIDEO | **Outer scene loop** after SCRIPT approve: for each scene, STORYBOARD → approve → VIDEO → approve |
| Workflow state | `current_stage`, `completed_stages` | Add `current_scene_index`, `scenes_total` |
| Signals | `approve(stage)`, `reject`, `regenerate` | Extend to `approve(stage, scene_index?)` or encode scene in stage string — **design choice in implementation plan** |
| Timeouts | VIDEO 90 min (WAN i2v) | Multiply by scene count; cap N=3 |
| Determinism | D-51 terminal at VIDEO | Terminal after **last scene VIDEO** approve |

**Risk:** Workflow versioning — new workflow code for new runs only; existing completed runs untouched.

### 3.2 Asset versioning

| Stage | Versioning today | Multi-scene |
|-------|------------------|-------------|
| STORY | Monotonic per project | Unchanged |
| SCRIPT | Monotonic per project | Unchanged (one file, N scenes) |
| STORYBOARD | Batch version + frame_index | Batch version + **scene_index** + frame_index |
| VIDEO | Monotonic per project | Monotonic; **filter/group by scene_index** in metadata |

**Index consideration:** STORYBOARD partial unique index `(project_id, stage, version, frame_index)` may need `(scene_index)` in index or composite batch key — **Alembic migration likely required** for STORYBOARD uniqueness across scenes at same version. This is **additive migration**, not redesign.

### 3.3 Audit model

- Append-only preserved
- Payload extension: optional `scene_index`, `scene_count`
- Export audit unchanged in spirit; more events per run

### 3.4 History model (D-57)

- `GET /assets/history` groups by stage
- **Change:** Sub-group STORYBOARD/VIDEO by `metadata_json.scene_index`
- IDEA/STORY/SCRIPT unchanged
- **Backward compatible:** rows without `scene_index` treated as scene 1

### 3.5 Lineage model (D-55)

- Display chain from `resolve_export_files` — must include all scene assets
- SQL edges: script → frames → video per scene
- IDEA synthetic node unchanged

### 3.6 Diff model (D-67)

- Story/Script text diff unchanged
- **Deferred in pilot:** STORYBOARD frame diff, cross-scene script diff

### 3.7 Run history model (D-68)

- `PipelineRunSummary` adds optional `scene_count`, `completed_scenes`
- Dashboard shows scene progress when RUNNING

### 3.8 Export (D-52/D-53)

- **manifest_version=2**
- ZIP layout example (3 scenes):

```
manifest.json
idea.txt
story.md
script.fountain
scenes/scene_01/frames/frame_01.png … frame_04.png
scenes/scene_01/scene_video.mp4
scenes/scene_02/…
```

- **Breaking for manifest v1 consumers** — version field gates parsing

### 3.9 Web UI

- Dashboard stepper: scene sub-progress
- Review: storyboard gallery per scene; video per scene
- History: scene tabs for STORYBOARD/VIDEO

**No new infrastructure services.** No Neo4j. No new broker.

---

## 4. Governance impact

### 4.1 D-records affected (must amend or supersede)

| ID | Topic | Impact |
|----|-------|--------|
| **D-40** | Fountain `scene_count == 1` | **Supersede** — allow 2–3 |
| **D-41** | Approved script resolution | Extend — all scenes in one approved SCRIPT |
| **D-43** | Storyboard batch metadata | **Extend** — add `scene_index` |
| **D-44** | Batch completeness | Per scene — 4 frames each |
| **D-45** | Fixed 4 frames | Unchanged per scene |
| **D-46** | Approved storyboard batch | **Per scene** MAX(version) filtered by scene_index |
| **D-48** | VIDEO asset contract | **Extend** — one MP4 per scene |
| **D-49** | Storyboard as video input | Filter frames by scene |
| **D-51** | Terminal at VIDEO approve | Terminal after **final scene** VIDEO |
| **D-52** | Export ZIP 9 files | **Supersede** — manifest v2 multi-scene layout |
| **D-53** | Manifest v1 | **Extend** — v2 schema |
| **D-55/D-56** | Lineage UI | More nodes; scene labels |
| **D-57/D-58** | History API/UI | Scene grouping |

**Not broken (unchanged):** D-37..D-39 (story), D-38 (append-only), D-61..D-63 (AI engines), D-64..D-73 (Phase 3 observability).

### 4.2 Existing assumptions broken

| Assumption | Location |
|------------|----------|
| Exactly one Fountain scene | `validate_fountain()`, US-14 |
| Single storyboard batch per run | US-16 verify, export resolver |
| Single video per run | US-18, export |
| Fixed 9-file ZIP | US-19 verify scripts |
| 4 approval gates total | Becomes 4 + 2×(N-1) for N scenes (storyboard+video per extra scene) — **pilot: 4 + 2×(N-1) = 8 gates for 3 scenes** |

### 4.3 Acceptance strategy

| Gate | Description |
|------|-------------|
| **SCR-2026-002 ACCEPT** | PO + Lead Architect written approval |
| **US-V05** (proposed) | 2-scene Olares E2E: idea → export manifest v2 |
| **Regression** | US-V03 Path A single-scene subset still PASS |
| **Governance brief** | Phase 4 Multi-Scene Pilot charter |
| **Implementation plans** | Per WP before code |

---

## 5. Scope alternatives

### Option 1 — 2–3 scene pilot (recommended)

| Dimension | Assessment |
|-----------|------------|
| **Description** | One STORY; script with 2–3 scenes; loop storyboard+video per scene |
| **Complexity** | **Medium** — workflow loop + metadata + export v2 |
| **Risk** | **Medium** — contained by scene cap |
| **Value** | **High** — proves multi-scene without episodic scale |
| **GPU cost** | ~2–3× current run |
| **Timeline** | 10–14 weeks |

### Option 2 — Unlimited scenes

| Dimension | Assessment |
|-----------|------------|
| **Description** | N scenes from story planner; unbounded loop |
| **Complexity** | **High** |
| **Risk** | **High** — GPU time, UX complexity, export size |
| **Value** | High at scale; overkill for pilot |
| **Timeline** | 18–24 weeks |

**Rejected for pilot** — no evidence of need beyond 2–3 scenes.

### Option 3 — Episode model

| Dimension | Assessment |
|-----------|------------|
| **Description** | Multiple PipelineRuns as "episodes" under a series project |
| **Complexity** | **High** — requires multi-project or series entity |
| **Risk** | **High** — tenancy model change |
| **Value** | High long-term; wrong first step |
| **Timeline** | 16–20 weeks + multi-project SCR |

**Deferred** — requires multi-project (Scope Freeze §1.2).

### Comparison matrix

| Criterion | Option 1 (2–3) | Option 2 (unlimited) | Option 3 (episode) |
|-----------|----------------|---------------------|-------------------|
| SCR complexity | Medium | High | High |
| Schema change | Additive | Additive + scale | Structural |
| Workflow change | Loop | Loop | Multi-run |
| Matches evidence | **Yes** | Over-scoped | No multi-project signal |
| Regression risk | Manageable | High | High |

---

## 6. Migration strategy

### 6.1 Is migration needed?

| Data | Migration required? |
|------|---------------------|
| Existing `asset_versions` | **No** — null/missing `scene_index` = scene 1 |
| Existing `pipeline_runs` | **No** |
| STORYBOARD partial index | **Likely yes** — extend unique constraint for `(scene_index, frame_index)` at batch version |
| Export manifest | **No DB** — v2 for new exports only |

### 6.2 Backward compatibility

| Surface | Approach |
|---------|----------|
| API history | Default `scene_index=1` when absent |
| Export | v1 manifest for pre-SCR runs; v2 for multi-scene runs |
| Verify scripts | Retain single-scene Path A; add Path C multi-scene |
| Workflow | New runs only; in-flight runs complete on old workflow version |

### 6.3 Rollout strategy

1. SCR ACCEPT + Phase 4 governance brief
2. Alembic migration (if index change) — **0004** proposed
3. Worker workflow v2 behind feature flag `MULTI_SCENE_ENABLED` + `MAX_SCENES=3`
4. API/UI read paths scene-aware
5. US-V05 on Olares (2 scenes)
6. Enable by default after acceptance
7. Single-scene remains default when story produces 1 scene (validator allows 1–3)

**Migration risk:** **Acceptable** — additive metadata, optional migration 0004, no data backfill required.

---

## 7. Verification strategy

### 7.1 Acceptance criteria (US-V05 proposed)

- [ ] Fresh project; 2-scene script generated and approved
- [ ] Scene 1: storyboard batch (4 frames) → video → approve
- [ ] Scene 2: storyboard batch → video → approve
- [ ] Run status `COMPLETED` only after scene 2 video approve
- [ ] Export ZIP manifest_version=2; files under `scenes/scene_01/`, `scenes/scene_02/`
- [ ] Lineage includes all frames + both videos
- [ ] History UI shows scene grouping
- [ ] Audit events include scene_index where applicable

### 7.2 Olares verification

| Script | Purpose |
|--------|---------|
| `deploy/k8s/usv05-verify/verify_usv05.sh` | New — 2-scene E2E |
| `deploy/k8s/usv03-verify/verify_usv03.sh` | Regression subset — single-scene |
| `make verify-all-olares` | Extended after US-V05 |

**GPU budget:** ~2× single-scene run; schedule acceptance when GPU idle.

### 7.3 Regression requirements

| Suite | Requirement |
|-------|-------------|
| API unit | Existing 114+ tests PASS |
| Fountain validate | Update tests: reject 4+ scenes; accept 2–3 |
| Export v1 | Single-scene export still produces valid v1 OR v2 with one scene dir |
| Cross-feature XF-01..06 | Re-run on single-scene reference run |
| Phase 3D verify-all | FAIL=0 after Phase 4 merge |

---

## 8. Recommendation

### Decision: **A — Proceed with 2–3 scene pilot**

| Factor | Rationale |
|--------|-----------|
| Evidence | #1 post-3D creator bottleneck; 12+ runs prove stability |
| Architecture | Extends D-43 metadata pattern; no platform redesign |
| Lineage/history | Can support scene semantics — **stop condition NOT triggered** |
| Migration | Low risk, additive |
| Governance | Manageable SCR scope; clear D-record amendments |
| Alternative B (unlimited) | Over-scoped without usage evidence |
| Alternative C (do not proceed) | Leaves primary value lever unaddressed post-release |

### Conditions for proceeding

1. **WP-0 complete:** `v0.13.0-phase3d` released and Olares pinned deploy verified
2. SCR-2026-002 **ACCEPT** by PO + Lead Architect
3. Phase 4 governance brief authorized
4. Scene cap **hard-limited to 3** in validator and workflow
5. Single-scene regression mandatory in US-V05 package

### If governance rejects

Fall back to **Phase 4A — Market full-stack chart** (platform maturity) per PHASE-NEXT-RECOMMENDATION alternative path.

---

## 9. Stop-condition evaluation

| Stop condition | Result |
|----------------|--------|
| Requires platform redesign | **NO** — extends existing Temporal + metadata patterns |
| Lineage/history cannot support scene semantics | **NO** — metadata_json + read-layer grouping sufficient |
| Migration risk unacceptable | **NO** — additive, backward compatible |

**SCR preparation may proceed to governance review.**

---

## Document control

| Version | Date | Author |
|---------|------|--------|
| 0.1 DRAFT | 2026-06-17 | Phase 4 Preparation mission |

*No implementation authorized by this document. SCR acceptance required before Phase 4 implementation.*
