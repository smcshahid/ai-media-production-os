# Release Evidence — v0.13.0-phase3d

**Date:** 2026-06-17  
**Release:** `v0.13.0-phase3d`  
**Baseline:** Phase 3D complete · M7 (`v0.12.0-usv03`)

---

## Pre-release gates

| Gate | Result | Evidence |
|------|--------|----------|
| Manifest validation | **PASS** | `scripts/release/validate-manifest.py` fail=0 |
| API unit tests | **114 passed** | `api/tests/unit` |
| Web vitest | **43 passed** | `web` npm test |
| Phase 3D local verify | **PASS** | `make verify-phase3d` FAIL=0 |
| Release notes | **Generated** | `docs/release/notes/v0.13.0-phase3d.md` |

---

## Pinned images (manifest)

| Service | Image |
|---------|-------|
| API | `docker.io/library/aimpos-api:v0.13.0-phase3d` |
| Web | `docker.io/library/aimpos-web:v0.13.0-phase3d` |
| Worker | `docker.io/library/aimpos-worker:v0.13.0-phase3d` |

Source: `deploy/release/manifest.yaml`

---

## Phase 3 deliverables included

- Phases 3A–3D mission closures
- Audit trail, export, pagination, run history, version diff
- Olares web entrance + release distribution package
- `make verify-all` / `make verify-all-olares`
- US-V04 release attestation (D-73)
- Operational runbooks (5)

---

## Git release artifacts

| Field | Value |
|-------|-------|
| Commit | `b57ef90` |
| Tag | `v0.13.0-phase3d` |
| Remote | `origin/main` pushed |

| Artifact | Path |
|----------|------|
| VERSION | `VERSION` |
| Release notes | `docs/release/notes/v0.13.0-phase3d.md` |
| Release process | `docs/release/RELEASE-PROCESS.md` |
| Readiness report | `RELEASE-READINESS-REPORT.md` |

---

## Olares deployment validation

See `evidence/release-v0.13.0-phase3d/OLARES-DEPLOYMENT-REPORT.md` (post-deploy).

---

## Sign-off

| Role | Status |
|------|--------|
| Release Manager | RC verified locally |
| Verification Lead | Unit + manifest gates PASS |
| Olares validation | See deployment report |
