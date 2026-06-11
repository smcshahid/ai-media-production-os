# Sprint 5D — US-21 Implementation Report

**Date:** 2026-06-10  
**Status:** **IMPLEMENTED** — local PASS · Olares **PASS**  
**Baseline:** `v0.10.0-us23`  
**Decision record:** **D-59**

---

## Summary

US-21 delivers **WebSocket pipeline status push** with **Redis pub/sub** fan-out, **shared `PipelineStatusRead` mapper**, and **Live/Polling fallback** in `usePipelineStatus`.

| Deliverable | Status |
|---|---|
| D-59 | ✅ |
| `/ws/pipeline` + hub + listener | ✅ |
| Worker Redis publish in `sync_pipeline_status` | ✅ |
| Web `pipelineSocket` + indicator | ✅ |
| Olares verify | ✅ **PASS** |

---

## Local tests

| Suite | Result |
|---|---|
| API | 106 passed |
| Web | 36 passed |
| Worker publish | 2 passed |

---

## Olares

Images `aimpos-api:us21` + `aimpos-worker:us21` · `FAIL=0`

---

## Files changed

| Area | Key paths |
|---|---|
| Decisions | `DECISIONS.md` (D-59) |
| API | `domain/pipeline/status_read.py`, `infrastructure/realtime/*`, `routes/pipeline_ws.py` |
| Worker | `infrastructure/pipeline_publish.py`, `activities/pipeline_status.py` |
| Web | `api/pipelineSocket.ts`, `hooks/usePipelineStatus.ts`, `PipelineConnectionIndicator.tsx` |
| Verify | `deploy/k8s/us21-verify/` |
