# Phase 3B — Local acceptance package

**Date:** 2026-06-17  
**Environment:** Local Docker (API + web + worker) + Olares AI tunnels (D-63)  
**Result:** **PASS**

## Preconditions

- API/web rebuilt with Phase 3B routes and UI  
- Project: `aa40cf32-f806-4f76-9ba0-4942d19e72e4`

## Automated verification

```
deploy/dev/verify_phase3b_local.ps1  FAIL=0
  audit export JSON  60744 bytes
  audit export CSV   43365 bytes
  pipeline runs      12
  audit events       111
  history stages     5
```

## Unit / build

| Suite | Result |
|-------|--------|
| `api/tests/unit` | 113 passed |
| `web` vitest | 41 passed |
| `web` build | PASS |

## Olares cluster

```
deploy/dev/verify_phase3b_olares.ps1  FAIL=0
  audit export JSON/CSV/run  HTTP 200
  pipeline runs              HTTP 200 (10 runs)
  audit read + history       HTTP 200
  audit_events unchanged     447 → 447
```

API image `docker.io/library/aimpos-api:dev` imported to Olares k3s (`aimpos-mwayolares`).

## New tests

- `api/tests/unit/test_audit_export.py`
- `api/tests/unit/test_pipeline_runs.py`
- `web/src/tests/textDiff.test.ts`
