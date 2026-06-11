# US-22 Acceptance Package — Olares Verification

**Status:** **PASS**  
**Date:** 2026-06-11  
**Baseline:** `v0.8.0-us20`  
**API image:** `docker.io/library/aimpos-api:us22`  
**Olares E2E:** **PASS** (`FAIL=0`, `VERIFY_RC=0`)

---

## Verification summary

| Check | Result | Evidence |
|---|---|---|
| S-22-01 `GET /assets/history` HTTP 200 | **PASS** | `logs/us22-verify.log` |
| S-22-02 Stage groups | **PASS** | IDEA, STORY, SCRIPT, STORYBOARD, VIDEO |
| S-22-03 **API vs SQL row parity** | **PASS** | 15 = 15 |
| S-22-04 **STORY regen history** | **PASS** | 2 versions, newest first [2, 1] |
| S-22-05 STORYBOARD `frame_index` | **PASS** | 8 frames |
| S-22-06 **Content-read spot check** | **PASS** | HTTP 200 |
| S-22-07 **Lineage regression** | **PASS** | HTTP 200 |
| S-22-08 **Export regression** | **PASS** | HTTP 200 |
| V-22-L05 **Row count unchanged** | **PASS** | 125 = 125 |

**Closure recommendation:** **READY** — Olares evidence collected; governance closure review may proceed.

---

## Run attestation

| Field | Value |
|---|---|
| **PROJECT_ID** | `76aa4418-d92d-45f7-954c-a10383ea511a` |
| **RUN_ID** | `042983f7-0f55-48c3-9d65-fce89a684625` |
| **Asset rows (project)** | 15 |
| **Global asset_versions** | 125 (unchanged) |

---

## Artifacts

| File | Description |
|---|---|
| `logs/us22-verify.log` | Full verify output |
| `logs/history-response.json` | Captured history response |
| `sql/v22-l*.txt` | SQL attestation |

**Verify script:** `deploy/k8s/us22-verify/verify_us22.sh`
