# Sprint 5B — US-22 Olares Verification Report

**Date:** 2026-06-11  
**Story:** US-22 Asset History API  
**Environment:** Olares `olares@10.0.0.34`, namespace `aimpos-mwayolares`  
**API image:** `docker.io/library/aimpos-api:us22`  
**Project:** `76aa4418-d92d-45f7-954c-a10383ea511a` (US-V02)  
**Result:** **PASS** (`FAIL=0`, `VERIFY_RC=0`)

---

## Verification steps

| Step | Result |
|---|---|
| S-22-01 GET /assets/history | **PASS** HTTP 200 |
| S-22-02 Stage groups | **PASS** — 5 stages |
| S-22-03 SQL parity | **PASS** — 15 = 15 |
| S-22-04 STORY regen | **PASS** — versions [2, 1] |
| S-22-05 STORYBOARD frames | **PASS** — 8 rows with frame_index |
| S-22-06 Content-read | **PASS** HTTP 200 |
| S-22-07 Lineage regression | **PASS** HTTP 200 |
| S-22-08 Export regression | **PASS** HTTP 200 |
| V-22-L05 No writes | **PASS** — 125 = 125 |

---

## Evidence

`evidence/us-22-verification/olares-2026-06-11/`

---

## Closure status

| Gate | Status |
|---|---|
| Local tests | **PASS** (101 API) |
| Olares verify | **PASS** |
| Governance closure | **READY TO SUBMIT** |
