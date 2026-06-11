# Sprint 4A — US-18 Implementation Report

**Date:** 2026-06-11  
**Status:** **LOCAL PASS — Olares PASS**  
**Parent brief:** `docs/sprints/sprint-4a-us18-brief.md` (**ACCEPT**)  
**Implementation plan:** `docs/sprints/sprint-4a-us18-implementation-plan.md` (**ACCEPT**)  
**Baseline:** `v0.4.0-usv01`  
**Olares evidence:** `evidence/us-18-verification/olares-2026-06-11/US-18-ACCEPTANCE-PACKAGE.md`

---

## 1. Summary

US-18 implements the **VIDEO pipeline stage** with **FFmpeg slideshow** baseline, **ComfyUI i2v fallback stub**, D-48..D-51 contracts, and API extensions for VIDEO regenerate + MP4 content-read. **COMPLETED** now occurs only after **VIDEO approval** (D-51).

| Deliverable | Status |
|---|---|
| Core enums `PipelineStage.VIDEO`, `AssetStage.VIDEO` | ✅ |
| `run_video_agent` + slideshow + store | ✅ |
| Workflow VIDEO stage | ✅ |
| API regenerate + content-read | ✅ |
| FFmpeg in worker Dockerfile | ✅ |
| D-48..D-51 in `DECISIONS.md` | ✅ |
| Unit tests | ✅ 83 API / 39 worker |
| Olares verify scripts | ✅ `deploy/k8s/us18-verify/` |
| Olares E2E evidence | ✅ **PASS** — `PROJECT=70898838-3a6c-4567-8483-371fca866b46`, `RUN_ID=2f94f2c3-5904-4011-ac50-6d2320244720` |

**Closure:** Olares evidence collected; ready for governance closure review.

---

## 2. Contract implementation

| Contract | Implementation |
|---|---|
| **D-48** | `store_video_asset()` — `scene_video.mp4`, `{project_id}/VIDEO/{hash}`, metadata JSON |
| **D-49** | `fetch_approved_storyboard_batch()` — D-46 gate, 4 PNGs |
| **D-50** | VIDEO regenerate API + `fetch_latest_video_rejection_rationale()` |
| **D-51** | `_STAGE_ORDER` includes VIDEO; COMPLETED after VIDEO approve |
| **Fallback** | `try_comfyui_i2v()` raises → `render_slideshow_mp4()`; pipeline continues |
| **Approval** | Whole-video approve/reject via existing `/pipeline/approve` (UI = US-19) |

---

## 3. Local test results

| Suite | Result | Log |
|---|---|---|
| API unit | **83 passed** | `evidence/us-18-verification/local-2026-06-11/logs/pytest-api.txt` |
| Worker unit | **39 passed** (1 ffmpeg integration deselected) | `evidence/us-18-verification/local-2026-06-11/logs/pytest-worker.txt` |

New tests: `test_assets_us18.py`, `test_regenerate_video_stage_happy_path`, `test_video_activity.py`, `test_video_slideshow.py`.

---

## 4. Olares verification

**Scripts:** `deploy/k8s/us18-verify/verify_us18.sh`, `run_remote.sh`, `deploy_us18.sh`

**Result (2026-06-11):** **PASS** — full path STORY → SCRIPT → STORYBOARD → VIDEO → regen → COMPLETED.

| Step | Result |
|---|---|
| ffmpeg in worker | PASS |
| STORYBOARD approve ≠ COMPLETED (D-51) | PASS |
| VIDEO gate + MP4 content-read | PASS (480×480, 20s, slideshow fallback) |
| Lineage 4 edges | PASS |
| VIDEO reject + regen v2 (D-50) | PASS |
| VIDEO approve → COMPLETED (D-51) | PASS |

**Log:** `evidence/us-18-verification/olares-2026-06-11/logs/us18-verify-pass.log`

**Fixes applied during verification:**
- Slideshow scale filter: fit within 854×480 box (512×512 ComfyUI frames).
- `deploy_us18.sh`: `rollout restart` after image import (same tag refresh).
- Verify script: 4-frame STORYBOARD gate, MP4 magic via python3, regen version polling.

---

## 5. Files changed

| Area | Key files |
|---|---|
| Core | `packages/aimpos-core/.../pipeline.py`, `asset.py` |
| Worker | `app/temporal/activities/video.py`, `app/agents/video/*`, `app/tools/assets.py`, `app/tools/video_i2v.py`, `spark_pipeline.py`, `Dockerfile` |
| API | `app/routes/assets.py`, `app/routes/pipeline.py` |
| Governance | `DECISIONS.md` D-48..D-51 |
| Verify | `deploy/k8s/us18-verify/*` |
| Tests | `api/tests/unit/test_assets_us18.py`, `test_pipeline_regenerate.py`, worker video tests |

---

## 6. Explicit non-goals (respected)

No export · publishing · audio · video editing · lineage UI · WebSocket · collaboration · US-19 player UI.

---

## 7. Next steps

1. Governance closure review (Olares evidence attached)
2. Tag proposal: `v0.5.0-us18` (upon closure authorization)
3. US-19 — video review UI / HTML5 player
