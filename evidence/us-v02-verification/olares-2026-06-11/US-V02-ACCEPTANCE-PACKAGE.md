# US-V02 Acceptance Package — Olares Verification

**Status:** **PASS**  
**Date:** 2026-06-11  
**Baseline:** `v0.6.0-us19`  
**Images:** `docker.io/library/aimpos-api:us19`, `docker.io/library/aimpos-worker:us18`  
**Olares E2E:** **PASS** (`FAIL=0`, `VERIFY_RC=0`)

---

## Verification summary

| Check | Result | Evidence |
|---|---|---|
| Fresh project E2E | **PASS** | `logs/usv02-verify-pass.log` |
| D-37..D-47 Visual MVP path + A-01 | **PASS** | SQL `v47-d47-extension.txt`; log STORYBOARD regen |
| D-51 STORYBOARD approve ≠ COMPLETED | **PASS** | `POST_SB_STATUS=AWAITING_APPROVAL` |
| D-48..D-50 VIDEO stage + regen | **PASS** | `VIDEO_V2=2`; MP4 content-read |
| D-51 COMPLETED at VIDEO approve | **PASS** | `FINAL_STATUS=COMPLETED` |
| D-52 export bundle (9 entries) | **PASS** | `FILE_COUNT=9`; HTTP 200 |
| D-53 manifest + hash verify | **PASS** | `MANIFEST=PASS`; `HASH_VERIFY=PASS` |
| D-54 BUNDLE_EXPORTED audit | **PASS** | `BUNDLE_EXPORTED_COUNT=1` |
| Export 409 negative | **PASS** | `NEGATIVE http=409` |
| SC-F03 lineage to video | **PASS** | `LINEAGE_COUNT=4` |
| SC-F05 / SC-V06 worker durability | **PASS** | `logs/worker-restart.log` |
| SC-V07 time to first story | **PASS** | 45 s (< 5 min) |

**Closure recommendation:** **READY** — Olares evidence collected; governance closure review may proceed.

---

## Run attestation

| Field | Value |
|---|---|
| **PROJECT** | `76aa4418-d92d-45f7-954c-a10383ea511a` |
| **RUN_ID** | `042983f7-0f55-48c3-9d65-fce89a684625` |
| **Terminal status** | `COMPLETED` (after VIDEO approve) |
| **Export size** | 1,445,355 bytes |
| **Manifest hash** | `ea43d95a9da72b77ffed44dc78dffa12308be920031325002482e07899037542` |
| **Verify log** | `logs/usv02-verify-pass.log` |
| **Remote log** | `/tmp/usv02-verify-20260611-181858.log` |

---

## Acceptance criteria mapping

### AC-1..AC-7 — Pipeline path

- **Fresh project** → idea → start → STORY edit/approve → SCRIPT reject/regen/approve → STORYBOARD A-01 reject/regen/approve → VIDEO reject/regen/approve → **COMPLETED**.
- **D-51:** STORYBOARD approve left status `AWAITING_APPROVAL` (not `COMPLETED`).

### AC-8..AC-10 — Export

- **GET /export** HTTP 200, ~1.4 MB ZIP, PK magic.
- **9 files**; manifest v1; SHA-256 matches all 8 assets.
- **`BUNDLE_EXPORTED`** audit with `file_count=8`, `zip_size_bytes=1445355`.

### AC-11..AC-13 — Attestation & durability

- **Lineage:** 4 STORYBOARD→VIDEO edges to final video asset.
- **Human gates:** 7 approval rows (STORY, SCRIPT×2, STORYBOARD×2, VIDEO×2).
- **Worker restart:** `COMPLETED` stable; same `run_id` post-restart.

---

## D-37 through D-54 matrix

| ID | Result | Evidence |
|---|---|---|
| D-37 | **PASS** | human-edit STORY; no row on approve |
| D-38 | **PASS** | SCRIPT, STORYBOARD, VIDEO version chains |
| D-39..D-42 | **PASS** | `v04-script-versions.txt` (2 versions) |
| D-43..D-47 | **PASS** | `v05-storyboard-batches.txt`; A-01 path |
| D-48 | **PASS** | `scene_video.mp4`; 480×480; 20 s |
| D-49 | **PASS** | 4 frame lineage to VIDEO |
| D-50 | **PASS** | VIDEO reject + regen v2 |
| D-51 | **PASS** | V-20; terminal only after VIDEO |
| D-52 | **PASS** | 9-entry ZIP; 409 negative |
| D-53 | **PASS** | manifest v1 + hash verify |
| D-54 | **PASS** | `v12-bundle-exported.txt` |

---

## Success criteria

| ID | Result |
|---|---|
| SC-01 Idea → approved video | **PASS** |
| SC-02 Local inference | **PASS** (`qwen3:14b` on agent tasks) |
| SC-11 Export integrity | **PASS** |
| SC-F01..F05 | **PASS** |
| SC-V04..V07 | **PASS** (story gate 45 s) |

---

## Re-run command

```bash
scp deploy/k8s/usv02-verify/*.sh olares@10.0.0.34:/tmp/
ssh olares@10.0.0.34 'bash /tmp/run_remote.sh'
```

**Wall-clock:** ~4 min for this run (slideshow VIDEO; ComfyUI storyboard batches dominated earlier stages).
