# US-23 Acceptance Package — Olares Verification

**Status:** **PASS**  
**Date:** 2026-06-10  
**Baseline:** `v0.9.0-us22`  
**API image:** `docker.io/library/aimpos-api:us22` (unchanged)  
**Olares E2E:** **PASS** (`FAIL=0`)

---

## Verification summary

| Check | Result | Evidence |
|---|---|---|
| S-23-01 Web bundle `/history` (local) | **PASS** | Local build grep |
| S-23-02 `GET /assets/history` HTTP 200 | **PASS** | `logs/us23-verify.log` |
| S-23-03 D-57 parity (15 rows) | **PASS** | API 15 = SQL 15 |
| S-23-04 Content-read spot check | **PASS** | HTTP 200 |
| S-23-05 Lineage regression | **PASS** | HTTP 200 |
| S-23-06 Export regression | **PASS** | HTTP 200 |
| S-23-07 API image unchanged (`us22`) | **PASS** | `aimpos-api:us22` |
| S-23-08 `asset_versions` unchanged | **PASS** | 125 = 125 |

**Closure recommendation:** **READY** — Olares evidence collected; governance closure may proceed.

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
| `logs/us23-verify.log` | Full verify output |

**Verify script:** `deploy/k8s/us23-verify/verify_us23.sh`
