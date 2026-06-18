# Release Evidence — v0.17.1-phase7-character-hardening

**Date:** 2026-06-18  
**Release:** `v0.17.1-phase7-character-hardening`  
**Baseline:** `v0.17.0-phase7-character-bible`  
**Acceptance:** US-V08B **ACCEPTED**

---

## Pre-release gates

| Gate | Result | Evidence |
|------|--------|----------|
| Core character tests | **3 passed** | `evidence/us-v08b-verification/local-2026-06-18/logs/pytest-core-character.txt` |
| API unit tests | **128 passed** | `evidence/us-v08b-verification/local-2026-06-18/logs/pytest-api.txt` |
| Worker unit tests | **60 passed** | `evidence/us-v08b-verification/local-2026-06-18/logs/pytest-worker.txt` |
| Web vitest | **PASS** | `evidence/us-v08b-verification/local-2026-06-18/logs/vitest-web.txt` |
| Phase 7.5 local verify | **PASS** | `deploy/dev/verify_usv08b_local.ps1` FAIL=0 |
| Olares E2E PATH A–F | **PASS** | `evidence/us-v08b-verification/olares-2026-06-18/` |
| Alembic head | **0007** | `api/alembic/versions/0007_character_snapshot.py` |

---

## Olares authoritative runs

| Path | Run ID | Episode | Snapshot |
|------|--------|---------|----------|
| A | `adf931ba-b63e-4fb1-aa19-cbe8b432d7b3` | 56 | 1 |
| B | `959ab565-2336-405d-9fe5-8110325a1a8d` | 57 | 3 |
| C1 | `19aa82c2-18e7-44b6-b022-f70cf7b4d152` | 58 | 3 |
| C2 | `67d00c52-3446-4d42-bc28-8a1b7f90fad4` | 59 | 3 |
| D run1 | `a6894d3e-df8e-412b-9e13-73add88060c2` | 62 | `Maya-D-a1` |
| D run2 | `cf274c65-ecf5-4c56-9f8b-6b5bbb88a15f` | 63 | `Maya-D-a1-Edited` |
| E | `cf274c65-ecf5-4c56-9f8b-6b5bbb88a15f` | 63 | stable after delete |

---

## Pinned images (manifest)

| Service | Image |
|---------|-------|
| API | `docker.io/library/aimpos-api:v0.17.1-phase7-character-hardening` |
| Web | `docker.io/library/aimpos-web:v0.17.1-phase7-character-hardening` |
| Worker | `docker.io/library/aimpos-worker:v0.17.1-phase7-character-hardening` |

Olares acceptance images: `usv08b-phase75` (pre-release tag; retag on cut).

Source: `deploy/release/manifest.yaml`

---

## Phase 7.5 deliverables included

- Export-time character snapshot (TD-P7-01 closed)
- Character CRUD UX + governed DELETE
- Worker/export snapshot-first continuity
- Manifest v5 governance notes
- US-V08B verification suite + supplemental PATH D/E
- Operational runbooks (character, export, verification standards)

---

## Git release artifacts

| Field | Value |
|-------|-------|
| Commit | `1eb6021` |
| Tag | `v0.17.1-phase7-character-hardening` |
| Remote | `origin/main` |

| Artifact | Path |
|----------|------|
| VERSION | `VERSION` |
| Release notes | `docs/release/notes/v0.17.1-phase7-character-hardening.md` |
| Acceptance | `US-V08B-ACCEPTANCE-PACKAGE.md` |
| Closure | `PHASE-7.5-CHARACTER-HARDENING-CLOSURE.md` |
| Readiness | `RELEASE-READINESS-RECOMMENDATION.md` |
| PASS/FAIL matrix | `evidence/us-v08b-verification/olares-2026-06-18/PASS-FAIL-MATRIX.md` |

---

## Sign-off

| Role | Status |
|------|--------|
| US-V08B | **ACCEPTED** |
| Phase 7.5 | **ACCEPTED** |
| Release readiness | **GO** |
