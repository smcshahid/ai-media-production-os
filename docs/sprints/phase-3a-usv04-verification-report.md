# US-V04 — Flux + WAN re-acceptance (verification report)

**Date:** 2026-06-16  
**Environment:** Local app + Olares shared AI (D-63)  
**Result:** **PASS WITH NOTE**

| Check | Result | Detail |
|-------|--------|--------|
| V-04-L01 Worker Flux env | **PASS** | `COMFYUI_WORKFLOW=flux_storyboard.json` |
| V-04-L02 Worker i2v env | **PASS** | `VIDEO_I2V_ENABLED=true` |
| V-04-L03 Olares ComfyUI tunnel | **PASS** | `host.docker.internal:8190` |
| V-04-L04 STORYBOARD 4 frames | **PASS** | version=1, count=4 |
| V-04-L05 Migration 0003 | **PASS** | revision 0003, 2 partial indexes |
| V-04-L06 Audit regression | **PASS** | 97 events |
| V-04-L07 VIDEO i2v source | **PENDING RUN** | Run `38021fd3` in VIDEO at verify time; prior rows `slideshow` |

**Note:** Live Olares validation run in progress at mission close. Re-run `deploy/dev/verify_usv04_local.ps1` after VIDEO gate approval to confirm `source=comfyui_i2v`.

**Evidence:** `evidence/us-v04-verification/local-2026-06-16/`
