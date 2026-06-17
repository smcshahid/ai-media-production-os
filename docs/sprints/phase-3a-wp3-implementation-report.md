# WP-3 — Dev bootstrap hardening (implementation report)

**Date:** 2026-06-16  
**Decision:** D-65  
**Status:** **COMPLETE**

## Delivered

- **`scripts/dev/ensure-db-migrated.ps1`** — starts Postgres, runs `alembic upgrade head`, validates revision ≥ 0003 and STORYBOARD partial indexes  
- **`Makefile`** — `up-dev` / `up-dev-build` call migration gate before worker start; also starts `api` container  
- **`make verify-bootstrap`** — standalone gate check  
- **`deploy/dev/verify_bootstrap.sh`** — bash wrapper for CI/local

## Root cause addressed

Fresh local DB at Alembic 0002 caused `UniqueViolation` on frame 2 of storyboard batches (missing partial indexes from 0003).
