# US-21 Acceptance Package — Olares Verification

**Status:** **PASS**  
**Date:** 2026-06-10  
**Baseline:** `v0.10.0-us23`  
**API image:** `docker.io/library/aimpos-api:us21`  
**Worker image:** `docker.io/library/aimpos-worker:us21`  
**Olares E2E:** **PASS** (`FAIL=0`)

---

## Verification summary

| Check | Result | Evidence |
|---|---|---|
| S-21-01 WebSocket auth + subscribe | **PASS** | `WS_SMOKE=PASS` |
| S-21-02 REST parity | **PASS** | status COMPLETED |
| S-21-05 Poll fallback HTTP 200 | **PASS** | |
| S-21-06 Redis health | **PASS** | |
| S-21-07 History/lineage/export | **PASS** | 200/200/200 |
| S-21-08 asset_versions unchanged | **PASS** | 125 = 125 |

**Closure recommendation:** **READY**

---

## Run attestation

| Field | Value |
|---|---|
| **PROJECT_ID** | `76aa4418-d92d-45f7-954c-a10383ea511a` |
| **RUN_ID** | `042983f7-0f55-48c3-9d65-fce89a684625` |

**Log:** `logs/us21-verify.log`
