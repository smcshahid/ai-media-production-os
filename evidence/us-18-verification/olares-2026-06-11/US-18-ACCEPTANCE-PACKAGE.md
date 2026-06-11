# US-18 Acceptance Package — Olares Verification

**Status:** **PASS**  
**Date:** 2026-06-11  
**Baseline:** `v0.4.0-usv01`  
**Images:** `docker.io/library/aimpos-api:us18`, `docker.io/library/aimpos-worker:us18`  
**Local regression:** **PASS** (API 83 / worker 39)  
**Olares E2E:** **PASS** (`FAIL=0`, `VERIFY_RC=0`)

---

## Verification summary

| Check | Result | Evidence |
|---|---|---|
| PF-02 ffmpeg in worker | **PASS** | `logs/us18-verify-pass.log` L7 |
| PF-04 API health | **PASS** | L9 |
| D-48 VIDEO asset contract | **PASS** | L38: `scene_video.mp4`, MinIO hash, metadata |
| D-49 approved storyboard input | **PASS** | 4 frames at version 1 before VIDEO gen |
| D-50 VIDEO regen contract | **PASS** | L44–49: reject note → version 2 append-only |
| D-51 COMPLETED at VIDEO approve | **PASS** | L32: not COMPLETED at STORYBOARD; L53–54: COMPLETED after VIDEO approve |
| AC-1 scene_video artifact | **PASS** | L38–41: HTTP 200, MP4 ftyp |
| AC-2 15–30s ≤480p | **PASS** | metadata `duration_sec=20.0`, `480×480` |
| AC-3 lineage frames→video | **PASS** | L43: `LINEAGE_COUNT=4` |
| AC-4 VIDEO review gate | **PASS** | L35–36: `AWAITING_APPROVAL` / `VIDEO` |
| AC-5 slideshow fallback | **PASS** | metadata `source=slideshow`, `fallback_from=comfyui_i2v` |
| Local unit regression | **PASS** | `local-2026-06-11/logs/pytest-*.txt` |

**Closure recommendation:** **READY** — Olares evidence collected; governance review may proceed.

---

## Run attestation

| Field | Value |
|---|---|
| **PROJECT** | `70898838-3a6c-4567-8483-371fca866b46` |
| **RUN_ID** | `2f94f2c3-5904-4011-ac50-6d2320244720` |
| **VIDEO asset (v1)** | `56a71197-fffc-4e39-8836-d038877494b7` |
| **VIDEO versions** | 1 (initial), 2 (post-regen) |
| **Terminal status** | `COMPLETED` |
| **Verify log** | `logs/us18-verify-pass.log` |
| **Remote log** | `/tmp/us18-verify-20260611-171540.log` |

---

## Acceptance criteria mapping

### AC-1 — `scene_video` artifact

- **Trigger:** STORYBOARD approved → VIDEO stage entered (L30–36).
- **Result:** One `asset_versions` row `stage=VIDEO`, `logical_filename=scene_video.mp4` in metadata (L38).
- **Content-read:** HTTP 200, 203994 bytes, MP4 magic verified (L39–41).

### AC-2 — MP4 15–30 s, ≤480p

- **Result:** `duration_sec=20.0`, `width=480`, `height=480`, `codec=h264` (L38).
- **Note:** Slideshow scales 512×512 ComfyUI frames down to fit 480p band (D-48).

### AC-3 — Lineage frames → video

- **Result:** 4 `lineage_edges` from STORYBOARD parents to VIDEO child (L43).

### AC-4 — VIDEO review gate on success

- **Result:** Pipeline reached `AWAITING_APPROVAL` / `VIDEO` before human approve (L35–36).

### AC-5 — Slideshow fallback on i2v failure

- **Result:** i2v disabled → slideshow used; pipeline succeeded; metadata records `fallback_from` / `fallback_reason` (L38).

---

## Governance contracts

| Contract | Olares evidence |
|---|---|
| **D-49** | Video gen after approved 4-frame STORYBOARD batch (L29–38) |
| **D-50** | VIDEO reject + regen → version 2, same storyboard frames (L44–49, SQL L59–60) |
| **D-51** | STORYBOARD approve → not COMPLETED (L32); VIDEO approve → COMPLETED (L53–54) |
| **One asset per generation** | v1 on first gen, v2 on regen only (SQL L58–60) |

---

## Re-run command

```bash
scp deploy/k8s/us18-verify/*.sh olares@10.0.0.34:/tmp/
# After building aimpos-api:us18 and aimpos-worker:us18:
ssh olares@10.0.0.34 'API_TAR=/tmp/aimpos-api-us18.tar WORKER_TAR=/tmp/aimpos-worker-us18.tar bash /tmp/deploy_us18.sh'
ssh olares@10.0.0.34 'bash /tmp/run_remote.sh'
```

**Deploy note:** `deploy_us18.sh` includes `rollout restart` so re-imported `:us18` tags pick up new layers.
