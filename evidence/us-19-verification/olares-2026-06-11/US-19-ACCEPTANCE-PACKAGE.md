# US-19 Acceptance Package — Olares Verification

**Status:** **PASS**  
**Date:** 2026-06-11  
**Baseline:** `v0.5.0-us18`  
**Image:** `docker.io/library/aimpos-api:us19`  
**Local regression:** **PASS** (API 88 / web 23)  
**Olares E2E:** **PASS** (`FAIL=0`, `VERIFY_RC=0`)

---

## Verification summary

| Check | Result | Evidence |
|---|---|---|
| S-19-01 GET /export (COMPLETED) | **PASS** | `logs/us19-verify-pass.log` L3–5: HTTP 200, ~1.6 MB, PK magic |
| S-19-02 ZIP file count (9) | **PASS** | L6–7: manifest + 8 assets |
| S-19-03 manifest v1 fields | **PASS** | L8–9: `manifest_version`, `pipeline_run_id`, `project_id`, `files` |
| S-19-04 hash verify | **PASS** | L10–11: SHA-256 matches manifest |
| S-19-05 BUNDLE_EXPORTED audit | **PASS** | L12–13: count ≥ 1 |
| S-19-06 non-COMPLETED 409 | **PASS** | L14–15: AWAITING_APPROVAL run → HTTP 409 |
| D-52 deterministic bundle | **PASS** | 9 entries, MinIO-sourced bytes |
| D-53 manifest contract | **PASS** | v1 schema with hashes, versions, approval timestamps |
| D-54 export audit | **PASS** | `BUNDLE_EXPORTED` with `manifest_hash`, `file_count`, `zip_size_bytes` |
| API-only (no worker/Temporal) | **PASS** | Export route in API only |
| Local unit regression | **PASS** | `local-2026-06-11/logs/pytest-api.txt`, `vitest-web.txt` |

**Closure recommendation:** **READY** — Olares evidence collected; governance review may proceed.

---

## Run attestation

| Field | Value |
|---|---|
| **PROJECT** | `70898838-3a6c-4567-8483-371fca866b46` |
| **RUN_ID** | `2f94f2c3-5904-4011-ac50-6d2320244720` |
| **Terminal status** | `COMPLETED` (US-18 attested run) |
| **Export size** | 1,598,229 bytes |
| **Verify log** | `logs/us19-verify-pass.log` |
| **Remote log** | `/tmp/us19-verify-20260611-175527.log` |

---

## Acceptance criteria mapping

### AC-1 — Export gate (COMPLETED only)

- **Trigger:** `GET /export/{pipeline_run_id}` on COMPLETED run.
- **Result:** HTTP 200, `application/zip` stream (L3–5).
- **Negative:** AWAITING_APPROVAL run `27b1011c-bf8c-48f0-9ea9-eb3333a56a7b` → HTTP 409 (L14–15).

### AC-2 — Deterministic bundle (D-52)

- **Result:** 9 ZIP entries in fixed order: `manifest.json`, `idea.txt`, `story.md`, `script.fountain`, `frames/frame_01.png`…`frame_04.png`, `scene_video.mp4` (L6–7).
- **Source:** MinIO bytes at approved versions; bundle not persisted to MinIO.

### AC-3 — Manifest integrity (D-53)

- **Result:** `manifest_version=1`, 8 file records with path, stage, version, `content_hash`, `approval_at`, `asset_id`, `size_bytes` (L8–9).
- **Hash verify:** On-disk SHA-256 matches manifest for all 8 assets (L10–11).

### AC-4 — Export audit (D-54)

- **Result:** `BUNDLE_EXPORTED` audit event appended per download (L12–13).
- **Payload:** `manifest_hash`, `file_count=8`, `zip_size_bytes`, `exported_at`.

### AC-5 — Export UI

- **Local:** Export page + Dashboard CTA for COMPLETED projects (web vitest 23 passed).
- **Olares:** API contract verified; UI not exercised on cluster (download-only, no new player).

---

## Governance contracts

| Contract | Olares evidence |
|---|---|
| **D-52** | 9-entry ZIP, COMPLETED gate, 409 on non-COMPLETED |
| **D-53** | manifest.json v1 with required fields and 8 file records |
| **D-54** | `BUNDLE_EXPORTED` audit with manifest_hash, file_count, zip_size_bytes |

---

## Re-run command

```bash
scp deploy/k8s/us19-verify/*.sh olares@10.0.0.34:/tmp/
# After building aimpos-api:us19:
ssh olares@10.0.0.34 'API_TAR=/tmp/aimpos-api-us19.tar bash /tmp/deploy_us19.sh'
ssh olares@10.0.0.34 'RUN_ID=2f94f2c3-5904-4011-ac50-6d2320244720 bash /tmp/run_remote.sh'
```

**Note:** Uses US-18 COMPLETED run; no new pipeline execution required for export-only verification.
